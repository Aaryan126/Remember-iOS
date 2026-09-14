import unittest
import json
import random
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import tempfile
from organization_eval import cluster_metrics, memberships, score, validate, decision_metrics, edge_metrics, digest, verify_frozen_score


class ScorerTests(unittest.TestCase):
    def setUp(self):
        self.gold = {"a": {"x"}, "b": {"x"}, "c": {"y"}, "d": {"y"}}

    def test_perfect_and_uuid_invariance(self):
        actual = {"a": {"z"}, "b": {"z"}, "c": {"q"}, "d": {"q"}}
        m = cluster_metrics(self.gold, actual)
        self.assertEqual((m["tp"], m["fp"], m["fn"], m["tn"]), (2, 0, 0, 4))
        self.assertEqual(m["bcubedF1"], 1)

    def test_collapsed(self):
        m = cluster_metrics(self.gold, {i: {"all"} for i in self.gold})
        self.assertAlmostEqual(m["pairPrecision"], 1 / 3)
        self.assertEqual(m["pairRecall"], 1)
        self.assertEqual(m["bcubedPrecision"], .5)

    def test_fragmented_precision_undefined(self):
        m = cluster_metrics(self.gold, {i: {i} for i in self.gold})
        self.assertIsNone(m["pairPrecision"])
        self.assertEqual(m["pairRecall"], 0)
        self.assertEqual(m["bcubedRecall"], .5)

    def test_overlapping_perfect(self):
        gold = {"a": {"x"}, "b": {"x", "y"}, "c": {"y"}}
        self.assertEqual(cluster_metrics(gold, gold)["bcubedF1"], 1)
        collapsed = {i: {"z"} for i in gold}
        m = cluster_metrics(gold, collapsed)
        self.assertEqual(m["fp"], 1)
        self.assertLess(m["bcubedRecall"], 1)

    def test_empty_and_ambiguous(self):
        self.assertIsNone(cluster_metrics({}, {})["pairRecall"])
        m = cluster_metrics(self.gold, self.gold, self.gold)
        self.assertEqual(m["ambiguousItems"], 4)
        self.assertIsNone(m["bcubedF1"])

    def test_missing_predictions_fail(self):
        with self.assertRaises(ValueError): cluster_metrics(self.gold, {"a": {"x"}})
        with self.assertRaises(ValueError): memberships({"a": []}, ["a"])
        with self.assertRaises(ValueError): memberships({"a": ["x", "x"]}, ["a"])

    def test_invalid_and_label_leak(self):
        raw = {"schemaVersion": 1, "libraries": [{"id": "l", "split": "heldout", "slice": "english",
            "items": [{"id": "a", "text": "hello", "kind": "text", "timestamp": 1, "gold": "x"}]}]}
        with self.assertRaises(ValueError): validate(raw)

    def test_failed_run_not_success(self):
        raw = {"schemaVersion": 1, "libraries": [{"id": "l", "split": "heldout", "slice": "english",
            "items": [{"id": "a", "text": "hello", "kind": "text", "timestamp": 1}]}]}
        labels = {"schemaVersion": 1, "libraries": [{"id": "l", "memberships": {"a": ["x"]}}]}
        result = {"schemaVersion": 1, "runs": [{"runID": "r", "libraryID": "l", "mode": "local",
                 "order": "chronological", "repeat": 0, "status": "blocked"}]}
        value = score(raw, labels, result)
        self.assertEqual(value["aggregates"][0]["completedRuns"], 0)
        self.assertNotIn("metrics", value["runs"][0])

    def test_merges_are_separate_from_final_groups(self):
        events = [{"kind": "merge", "assignments": {"a": ["m"], "b": ["m"]}},
                  {"kind": "merge", "assignments": {"a": ["n"], "c": ["n"]}}]
        m = decision_metrics({"events": events}, self.gold, [])
        self.assertEqual(m["retrospectivelyProhibitedMerges"], 1)
        self.assertEqual(m["retrospectiveMergePrecision"], .5)
        self.assertIsNone(decision_metrics({"events": []}, self.gold, [])["retrospectiveMergePrecision"])

    def test_edge_mapping_without_title_or_uuid_match(self):
        run = {"memberships": {"a": ["1"], "b": ["1"], "c": ["2"], "d": ["2"]},
               "edges": [{"first": "1", "second": "2"}]}
        label = {"relationships": [{"first": "x", "second": "y", "related": True}]}
        self.assertEqual(edge_metrics(run, self.gold, label)["recall"], 1)

    def test_scoring_rejects_post_freeze_label_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs, labels, contract, freeze = [root / p for p in ("inputs", "labels", "contract", "freeze")]
            inputs.write_text("input"); labels.write_text("labels"); contract.write_text("contract")
            frozen = {"inputsSHA256": digest(inputs), "labelsSHA256": digest(labels),
                      "contractSHA256": digest(contract), "scorerSHA256": digest(Path(__file__).with_name("organization_eval.py"))}
            freeze.write_text(json.dumps(frozen))
            results = {"manifest": {"inputsSHA256": digest(inputs), "freezeSHA256": digest(freeze)}}
            self.assertTrue(verify_frozen_score(inputs, labels, results, freeze, contract)["scorerBound"])
            labels.write_text("changed after prediction")
            with self.assertRaisesRegex(ValueError, "labels mismatch"):
                verify_frozen_score(inputs, labels, results, freeze, contract)

    def test_scoring_rejects_different_freeze_or_scorer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs, labels, contract, freeze = [root / p for p in ("inputs", "labels", "contract", "freeze")]
            inputs.write_text("input"); labels.write_text("labels"); contract.write_text("contract")
            frozen = {"inputsSHA256": digest(inputs), "labelsSHA256": digest(labels), "scorerSHA256": "wrong"}
            freeze.write_text(json.dumps(frozen))
            results = {"manifest": {"inputsSHA256": digest(inputs), "freezeSHA256": "wrong"}}
            with self.assertRaisesRegex(ValueError, "this freeze"):
                verify_frozen_score(inputs, labels, results, freeze, contract)
            results["manifest"]["freezeSHA256"] = digest(freeze)
            with self.assertRaisesRegex(ValueError, "scorer changed"):
                verify_frozen_score(inputs, labels, results, freeze, contract)

    def test_seeded_overlap_metrics_against_exact_reference(self):
        # Independent small-set oracle uses rational arithmetic, including self-neighbors.
        for seed in range(100):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                ids = [str(i) for i in range(rng.randint(2, 12))]
                gold = {i: set(rng.sample(range(5), rng.randint(1, 3))) for i in ids}
                predicted = {i: set(rng.sample(range(6), rng.randint(1, 3))) for i in ids}
                actual = cluster_metrics(gold, predicted)
                counts = dict(tp=0, fp=0, fn=0, tn=0)
                for first, second in combinations(ids, 2):
                    related = bool(gold[first] & gold[second])
                    joined = bool(predicted[first] & predicted[second])
                    counts[{(True, True): "tp", (False, True): "fp",
                            (True, False): "fn", (False, False): "tn"}[related, joined]] += 1
                for key, expected in counts.items():
                    self.assertEqual(actual[key], expected)
                for key, denominator in (("bcubedPrecision", predicted), ("bcubedRecall", gold)):
                    per_item = []
                    for first in ids:
                        neighbors = [second for second in ids if denominator[first] & denominator[second]]
                        terms = [Fraction(min(len(gold[first] & gold[second]),
                                              len(predicted[first] & predicted[second])),
                                          len(denominator[first] & denominator[second])) for second in neighbors]
                        per_item.append(sum(terms) / len(terms))
                    self.assertAlmostEqual(actual[key], float(sum(per_item) / len(per_item)))
                renamed = {i: {f"opaque-{group}" for group in predicted[i]} for i in reversed(ids)}
                self.assertEqual(actual, cluster_metrics(gold, renamed))

    def test_missing_runs_and_extraction_failures_remain_visible(self):
        inputs = {"schemaVersion": 1, "libraries": [{"id": "l", "split": "heldout", "slice": "english",
                  "items": [{"id": "a", "text": "hello", "kind": "text", "timestamp": 1}]}]}
        labels = {"schemaVersion": 1, "libraries": [{"id": "l", "memberships": {"a": ["x"]}}]}
        results = {"schemaVersion": 1, "manifest": {"expectedRunIDs": ["attempted", "missing"]},
                   "runs": [{"runID": "attempted", "libraryID": "l", "mode": "local", "order": "chronological",
                             "repeat": 0, "status": "timeout", "mediaMode": "extracted",
                             "availability": {"unavailableEmbeddingIDs": ["a"]},
                             "extractions": [{"itemID": "a", "status": "no_source_evidence", "expectedNoEvidence": True}]}]}
        actual = score(inputs, labels, results)
        self.assertEqual(actual["missingRequestedRuns"], ["missing"])
        self.assertNotIn("metrics", actual["runs"][0])
        self.assertEqual(actual["runs"][0]["extractionCoverage"]["expectedNoEvidenceIDs"], ["a"])
        self.assertEqual(actual["aggregates"][0]["unavailableEmbeddingObservations"], 1)
        self.assertEqual(actual["aggregates"][0]["noEvidenceExtractions"], 1)


if __name__ == "__main__": unittest.main()
