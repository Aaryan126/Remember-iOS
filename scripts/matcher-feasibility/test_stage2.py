import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

import stage2 as s
import stage2_metrics as m
import stage2_reference as reference


def row(library="a", relation="same", probability=.9):
    return {"library": library, "relation": relation, "probabilities": [probability, (1 - probability) / 2, (1 - probability) / 2]}


class MetricTests(unittest.TestCase):
    def test_undefined_precision_not_perfect(self):
        result = m.metrics([row()], None)
        self.assertIsNone(result["precision"])
        self.assertEqual(result["recall"], 0)

    def test_missing_predictions_remain_false_negatives(self):
        item = {**row(), "probabilities": None}
        result = m.metrics([row(), item], .5)
        self.assertEqual((result["tp"], result["fn"], result["missingPredictionPairs"]), (1, 1, 1))
        self.assertEqual(result["recall"], .5)

    def test_uncertain_acceptance_separate(self):
        result = m.metrics([row(), row(relation="uncertain")], .5)
        self.assertEqual(result["precision"], 1)
        self.assertEqual(result["acceptedUncertainFraction"], 1)
        self.assertEqual(result["knownPairs"], 1)

    def test_tied_threshold_scores_cannot_split(self):
        rows = [row() for _ in range(30)] + [row(relation="unrelated") for _ in range(2)]
        self.assertIsNone(m.select_threshold(rows))

    def test_minimum_acceptance_required(self):
        self.assertIsNone(m.select_threshold([row() for _ in range(29)]))
        self.assertIsNotNone(m.select_threshold([row() for _ in range(30)]))

    def test_recall_selection_matches_bruteforce(self):
        rng = np.random.default_rng(17)
        rows = [{"library": str(i % 6), "relation": m.CLASSES[i % 3],
                 "probabilities": rng.dirichlet([3, 1, 1]).tolist()} for i in range(240)]
        candidate = m.select_threshold(rows, minimum_precision=.3, minimum_accepted=10)
        brute = []
        for threshold in {r["probabilities"][0] for r in rows}:
            result = m.metrics(rows, threshold)
            if result["precision"] is not None and result["precision"] >= .3 and result["acceptedKnownPairs"] >= 10:
                brute.append((result["macroLibraryRecall"], result["precision"], threshold))
        self.assertEqual(candidate["threshold"], max(brute)[2])

    def test_library_macro_not_pair_weighting(self):
        rows = [row("a") for _ in range(9)] + [row("b", probability=.1)]
        result = m.metrics(rows, .5)
        self.assertEqual(result["recall"], .9)
        self.assertEqual(result["macroLibraryRecall"], .5)

    def test_winning_class_required(self):
        self.assertFalse(m.accepted({**row(), "probabilities": [.4, .5, .1]}, .3))

    def test_bootstrap_reproducible(self):
        rows = [row("a"), row("b", "unrelated")]
        self.assertEqual(m.bootstrap(rows, .5, 50), m.bootstrap(rows, .5, 50))


class FeatureTests(unittest.TestCase):
    def test_empty_jaccard_is_zero(self):
        self.assertEqual(s.jaccard(set(), set()), 0)

    def test_cosine_missing_zero_and_incompatible(self):
        for a, b in [(None, [1]), ([0], [1]), ([1], [1, 0]), ([float("nan")], [1])]:
            self.assertIsNone(s.cosine(a, b))
        self.assertEqual(s.cosine([1, 0], [1, 0]), 1)

    def test_feature_symmetry_and_space_isolation(self):
        first, second = {"text": "Alpha 12 notes"}, {"text": "Beta 12 note"}
        a = {"status": "ok", "space": "mac-space", "contextual": [1, 0], "sentence": [0, 1]}
        b = {**a, "contextual": [0, 1]}
        self.assertEqual(s.pair_features(first, second, a, b, .3), s.pair_features(second, first, b, a, .3))
        self.assertEqual(s.pair_features(first, second, a, {**b, "space": "phone-space"}, .3)[:2], [None, None])

    def test_retrieval_excludes_self_and_ties_by_id(self):
        ids = ["c", "a", "b"]
        result = s.top_candidates(ids, [[1] * 3 for _ in ids], np.ones((3, 3)), k=1)
        self.assertEqual(result, {"c": ["a"], "a": ["b"], "b": ["a"]})

    def test_retrieval_missing_semantic_uses_lexical_only(self):
        result = s.top_candidates(["a", "b", "c"], [[None] * 3 for _ in range(3)], np.eye(3), k=1)
        self.assertEqual(result["a"], ["b"])

    def test_no_test_split_load(self):
        with self.assertRaisesRegex(ValueError, "cannot load heldout"):
            s.load_split("test")

    def test_embedding_checkpoint_text_binding(self):
        item = {"id": "fixture", "text": "Alpha"}
        record = {"id": "fixture", "textSHA256": s.content_sha("Beta"), "status": "unavailable"}
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            s.validate_embedding(item, record)

    def test_bad_normalization_rejected(self):
        item = {"id": "fixture", "text": "Alpha"}
        record = {"id": "fixture", "textSHA256": s.content_sha("Alpha"), "status": "ok", "space": "x",
                  "expectedSpace": "x", "contextual": [2, 0], "sentence": [1, 0]}
        with self.assertRaisesRegex(ValueError, "invalid embedding"):
            s.validate_embedding(item, record)

    def test_reference_fixtures_have_no_gold(self):
        document = {"libraries": [{"items": [{"id": str(i), "text": "Source " + str(i), "secretGold": True} for i in range(8)]}]}
        result = reference.fixtures([document])
        self.assertEqual(len(result["fixtures"]), 12)
        self.assertNotIn("secretGold", str(result))
        self.assertTrue(any(r["id"] == "edge-overflow-both" for r in result["fixtures"]))

    def test_pause_saves_progress_before_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            s.save(run / "control/pause-requested.json", {"requested": True})
            s.save(run / "embeddings/fixture.json", {"completed": True})
            with self.assertRaises(s.Paused):
                s.boundary(run, "fixture")
            records = list((run / "pauses").glob("*.json"))
            self.assertEqual(len(records), 1)
            self.assertEqual(s.read(records[0])["completedEmbeddingItems"], 1)

    def test_retrieval_reports_all_relevant_not_just_one(self):
        libraries = [{"id": "lib", "items": [{"id": i} for i in "abc"]}]
        gold = {"lib": [{"first": a, "second": b, "relation": "same"} for a, b in [("a", "b"), ("a", "c"), ("b", "c")]]}
        result = m.retrieval_metrics(libraries, gold, {"a": ["b"], "b": ["a"], "c": ["a"]})
        self.assertEqual(result["atLeastOneRecallAt10"], 1)
        self.assertEqual(result["allRelevantRecall"], .5)


if __name__ == "__main__":
    unittest.main()
