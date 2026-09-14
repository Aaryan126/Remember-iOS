import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import prepare
from validation_policy import calibrate, evaluate_frozen, gates, metrics, select_threshold

POLICY = prepare.read(prepare.DATA / "contract.json")


def rows(positives=100, negatives=10, split="calibration"):
    return [{"id": f"p{i}", "library": "example", "split": split,
             "relation": "same" if i < positives else "related", "score": .9 if i < positives else .1}
            for i in range(positives + negatives)]


def reference():
    return {"precision": 73 / 76, "macroRecall": .299390243902439,
            "acceptedKnown": 76, "missingKnown": 0}


class PolicyTests(unittest.TestCase):
    def test_historical_narrow_failure_preserved(self):
        candidate = {"precision": 153 / 161, "macroRecall": .6256, "acceptedKnown": 161, "missingKnown": 0}
        result = gates(candidate, reference(), POLICY)
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["precision"])
        self.assertAlmostEqual(result["requiredPrecision"], 73 / 76 - .01)

    def test_historical_passing_seed(self):
        candidate = {"precision": 136 / 143, "macroRecall": .5565, "acceptedKnown": 143, "missingKnown": 0}
        self.assertTrue(gates(candidate, reference(), POLICY)["passed"])

    def test_selector_uses_full_precision_rule(self):
        values = rows(300, 108)
        for index, row in enumerate(values):
            row["score"] = .9 if index < 152 or 300 <= index < 307 else .8 if index in (152, 307) else .1
        selected = select_threshold(values, POLICY, reference(), hybrid=True)
        self.assertEqual(selected["threshold"], .9)
        self.assertTrue(gates(selected["metrics"], reference(), POLICY)["passed"])
        # Old absolute95% selection alone would choose the lower .8 threshold.
        self.assertEqual(select_threshold(values, POLICY)["threshold"], .8)

    def test_exact_boundary_is_inclusive(self):
        baseline = {"precision": .96, "macroRecall": .25, "acceptedKnown": 100, "missingKnown": 0}
        candidate = {"precision": .95, "macroRecall": .30, "acceptedKnown": 30, "missingKnown": 0}
        self.assertTrue(gates(candidate, baseline, POLICY)["passed"])

    def test_missing_baseline_never_wins(self):
        self.assertIsNone(select_threshold(rows(), POLICY, None, hybrid=True))

    def test_missing_known_scores_block_selection(self):
        values = rows()
        values[-1]["score"] = None
        self.assertIsNone(select_threshold(values, POLICY))

    def test_no_acceptance_is_not_perfect_precision(self):
        self.assertIsNone(metrics(rows(), None)["precision"])

    def test_uncertain_never_satisfies_count(self):
        values = rows(29, 0) + [{"id": "u", "library": "example", "split": "calibration", "relation": "uncertain", "score": 1.}]
        self.assertIsNone(select_threshold(values, POLICY))
        self.assertEqual(metrics(values, .5)["acceptedUncertain"], 1)

    def test_tied_negative_cannot_be_omitted(self):
        values = rows(30, 2)
        for row in values:
            row["score"] = .9
        self.assertIsNone(select_threshold(values, POLICY))

    def test_baseline_winning_constraint_is_retained(self):
        values = rows(30, 0)
        values[0]["eligible"] = False
        self.assertIsNone(select_threshold(values, POLICY))

    def test_bad_scores_and_duplicate_ids_rejected(self):
        for score in (float("nan"), float("inf"), -.1, 1.1, True, "0.9"):
            with self.subTest(score=score), self.assertRaises(ValueError):
                metrics([rows()[0] | {"score": score}], .5)
        with self.assertRaises(ValueError):
            metrics([rows()[0], rows()[0]], .5)

    def test_wrong_splits_cannot_calibrate(self):
        for split in ("pilot", "train", "evaluation"):
            with self.subTest(split=split), self.assertRaises(ValueError):
                select_threshold(rows(split=split), POLICY)

    def test_coverage_and_labels_must_align(self):
        base, hybrid = rows(), rows()
        with self.assertRaises(ValueError):
            calibrate(base, hybrid[:-1], POLICY)
        hybrid[0]["relation"] = "unrelated"
        with self.assertRaises(ValueError):
            calibrate(base, hybrid, POLICY)

    def test_evaluation_cannot_retune(self):
        base = rows(split="evaluation")
        hybrid = [r | {"score": .6} for r in base]
        result = evaluate_frozen(base, hybrid, {"baseline": .9, "hybrid": .8}, POLICY)
        self.assertEqual(result["hybrid"]["acceptedKnown"], 0)
        self.assertFalse(result["qualification"]["passed"])

    def test_sweep_matches_independent_brute_force(self):
        rng = random.Random(17)
        for _ in range(20):
            values = rows()
            for row in values:
                row["score"] = rng.choice([.1, .4, .7, .9])
                row["library"] = rng.choice(["a", "b", "c"])
            ranked = []
            for threshold in {r["score"] for r in values}:
                accepted = [r for r in values if r["score"] >= threshold]
                precision = sum(r["relation"] == "same" for r in accepted) / len(accepted)
                recalls = []
                for lib in {r["library"] for r in values}:
                    positives = [r for r in values if r["library"] == lib and r["relation"] == "same"]
                    if positives:
                        recalls.append(sum(r["score"] >= threshold for r in positives) / len(positives))
                if len(accepted) >= 30 and precision >= .95:
                    ranked.append((sum(recalls) / len(recalls), precision, threshold))
            selected = select_threshold(values, POLICY)
            self.assertEqual(selected["threshold"] if selected else None, max(ranked)[2] if ranked else None)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.corpus = prepare.read(prepare.DATA / "pilot.json")

    def test_projection_counts_and_privacy_boundary(self):
        inputs, gold, report = prepare.validate_corpus(self.corpus, POLICY)
        self.assertEqual(report["libraries"], 4)
        self.assertEqual(report["sources"], 40)
        self.assertEqual(report["pairs"], 180)
        self.assertEqual(report["relations"], {"same": 52, "related": 36, "unrelated": 56, "uncertain": 36})
        self.assertFalse(report["qualificationReady"])
        for library in inputs["libraries"]:
            self.assertEqual(set(library), {"id", "items"})
            for item in library["items"]:
                self.assertEqual(set(item), {"id", "text", "modality"})
        self.assertEqual(len({p["id"] for p in gold["pairs"]}), 180)

    def test_bridge_is_not_transitive(self):
        _, gold, _ = prepare.validate_corpus(self.corpus, POLICY)
        lookup = {frozenset((p["first"], p["second"])): p["relation"] for p in gold["pairs"]}
        self.assertEqual(lookup[frozenset(("festival-01", "festival-09"))], "same")
        self.assertEqual(lookup[frozenset(("festival-04", "festival-09"))], "same")
        self.assertEqual(lookup[frozenset(("festival-01", "festival-04"))], "related")

    def test_pilot_cannot_be_released(self):
        with self.assertRaises(ValueError):
            prepare.validate_corpus(self.corpus, POLICY, release=True)

    def test_invalid_membership_and_relation_rejected(self):
        for change in ("membership", "relation", "id", "empty", "duplicate-text"):
            corpus = copy.deepcopy(self.corpus)
            library = corpus["libraries"][0]
            if change == "membership":
                library["items"][0]["memberships"] = ["absent"]
            elif change == "relation":
                library["relatedThreads"] = [["ramp", "ramp"]]
            elif change == "id":
                library["items"][0]["id"] = library["items"][1]["id"]
            elif change == "empty":
                library["items"][0]["text"] = " "
            else:
                library["items"][0]["text"] = library["items"][1]["text"]
            with self.subTest(change=change), self.assertRaises(ValueError):
                prepare.validate_corpus(corpus, POLICY)

    def release_fixture(self):
        corpus = copy.deepcopy(self.corpus)
        corpus["purpose"] = "qualification-release"
        for lib, split in zip(corpus["libraries"], ["train", "train", "calibration", "evaluation"]):
            lib["split"] = split
        policy = POLICY | {"requiredSplits": {"train": 2, "calibration": 1, "evaluation": 1},
                           "itemsPerLibrary": 10, "librariesPerStoryFamily": 1}
        return corpus, policy

    def test_split_and_template_leakage_rejected(self):
        for key in ("storyFamily", "templateFamily"):
            corpus, policy = self.release_fixture()
            corpus["libraries"][2][key] = corpus["libraries"][0][key]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "split leakage"):
                prepare.validate_corpus(corpus, policy, release=True)

    def test_cross_split_near_duplicate_rejected(self):
        corpus, policy = self.release_fixture()
        corpus["libraries"][2]["items"][0]["text"] = corpus["libraries"][0]["items"][0]["text"] + " Updated."
        with self.assertRaisesRegex(ValueError, "near duplicate"):
            prepare.validate_corpus(corpus, policy, release=True)

    def test_release_counts_checked_and_review_not_implied(self):
        corpus, policy = self.release_fixture()
        _, _, report = prepare.validate_corpus(corpus, policy, release=True)
        self.assertFalse(report["qualificationReady"])
        with self.assertRaisesRegex(ValueError, "split size"):
            prepare.validate_corpus(corpus, policy | {"requiredSplits": {"train": 5, "calibration": 1, "evaluation": 1}}, release=True)

    def test_publication_resumes_but_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            prepare.publish(path, {"a": 1})
            prepare.publish(path, {"a": 1})
            with self.assertRaises(ValueError):
                prepare.publish(path, {"a": 2})
            self.assertEqual(json.loads(path.read_text()), {"a": 1})

    def test_prepare_resume_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            first = prepare.prepare(run)
            self.assertEqual(first, prepare.prepare(run))
            self.assertFalse(first["trainingStarted"])
            (run / "pilot-gold.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "artifact changed"):
                prepare.verify(run)

    def test_partial_publication_resumes(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            inputs, _, _ = prepare.validate_corpus(self.corpus, POLICY)
            prepare.publish(run / "pilot-inputs.json", inputs)
            self.assertEqual(prepare.prepare(run)["checkpoint"], "P0")

    def test_source_tamper_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            prepare.prepare(run)
            with patch.object(prepare, "bindings", return_value={"changed": "hash"}):
                with self.assertRaisesRegex(ValueError, "sources changed"):
                    prepare.verify(run)

    def test_low_disk_stops_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory) / "absent"
            usage = type("Usage", (), {"free": 10 * prepare.GIB})()
            with patch.object(prepare.shutil, "disk_usage", return_value=usage):
                with self.assertRaisesRegex(ValueError, "reserve"):
                    prepare.prepare(run)
            self.assertFalse(run.exists())


if __name__ == "__main__":
    unittest.main()
