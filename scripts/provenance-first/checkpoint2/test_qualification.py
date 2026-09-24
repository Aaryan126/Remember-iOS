"""Synthetic tests for selection, gates and immutable qualification receipts."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import common as c
import qualify_runtime as q


def rows():
    scores = [0.01, 0.49, 0.51, 0.975, 0.9804, 0.981, 0.989, 0.991, 0.994, 0.996, 0.999]
    return [{"id": f"{library}-{i:02d}", "library": library, "first": "a", "second": "b", "score": score}
            for library in ("libA", "libB") for i, score in enumerate(scores)]


class SelectionTests(unittest.TestCase):
    def test_selection_is_input_order_independent(self):
        self.assertEqual(q.select(rows(), ["libA-03"], 2), q.select(list(reversed(rows())), ["libA-03"], 2))

    def test_deduplication_retains_reasons(self):
        selection = q.select(rows(), ["libA-00"], 2)
        selected = next(r for r in selection if r["id"] == "libA-00")
        self.assertEqual(selected["reasons"], ["original-control", "library-low"])
        self.assertEqual(len(selection), len({r["id"] for r in selection}))

    def test_each_library_has_three_score_anchors(self):
        selection = q.select(rows(), [], 2)
        for library in ("libA", "libB"):
            reasons = [reason for r in selection if r["library"] == library for reason in r["reasons"]]
            self.assertEqual(sum(r.startswith("library-") for r in reasons), 3)

    def test_closest_both_sides_and_ties(self):
        selection = q.select(rows(), [], 2)
        self.assertEqual([r["id"] for r in selection if "threshold-0.99-below" in r["reasons"]], ["libA-06", "libB-06"])
        self.assertEqual([r["id"] for r in selection if "threshold-0.99-at-or-above" in r["reasons"]], ["libA-07", "libB-07"])

    def test_labels_not_used_or_emitted(self):
        changed = [{**r, "relation": "bad", "newScore": 1-r["score"]} for r in rows()]
        self.assertEqual(q.select(changed, [], 2), q.select(rows(), [], 2))

    def test_missing_original_fails(self):
        with self.assertRaises(ValueError):
            q.select(rows(), ["missing"], 2)

    def test_duplicate_ids_fail(self):
        with self.assertRaises(ValueError):
            q.select(rows() + rows()[:1], [], 2)

    def test_invalid_score_fails(self):
        for score in (float("nan"), float("inf"), -1, 1.1, True):
            with self.subTest(score=score), self.assertRaises(ValueError):
                q.select([{**rows()[0], "score": score}] + rows()[1:], [], 2)

    def test_path_escape_id_fails(self):
        with self.assertRaises(ValueError):
            q.select([{**rows()[0], "id": "../bad"}] + rows()[1:], [], 2)

    def test_insufficient_side_does_not_reduce_sample(self):
        with self.assertRaises(ValueError):
            q.select(rows(), [], 100)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.vector = {"id": "a", "channels": {"contextual": {"cosine": 1., "relativeNormDelta": 0.},
                                                "sentence": {"cosine": 1., "relativeNormDelta": 0.}}}
        self.pair = {"id": "a--b", "savedFeatureDelta": 0., "freshFeatureDelta": 0., "directionalDelta": 0.,
                     "combinedDelta": 0., "currentScore": 0.5, "historicalScore": 0.5}

    def test_exact_bounds_pass(self):
        for metric in ("savedFeatureDelta", "freshFeatureDelta", "directionalDelta", "combinedDelta"):
            self.pair[metric] = q.BOUNDS[metric]
        self.vector["channels"]["sentence"] = {"cosine": q.BOUNDS["minimumCosine"], "relativeNormDelta": q.BOUNDS["relativeNormDelta"]}
        self.assertEqual(q.check_rows([self.vector], [self.pair]), [])

    def test_each_error_metric_fails_without_rounding(self):
        for metric in ("savedFeatureDelta", "freshFeatureDelta", "directionalDelta", "combinedDelta"):
            value = {**self.pair, metric: q.BOUNDS[metric] * 1.0001}
            self.assertEqual(q.check_rows([self.vector], [value])[0]["metric"], metric)

    def test_tiny_threshold_crossing_fails(self):
        for threshold in q.THRESHOLDS:
            value = {**self.pair, "currentScore": threshold, "historicalScore": threshold - 1e-10}
            self.assertEqual(q.check_rows([self.vector], [value])[0]["metric"], "threshold-decision")

    def test_cosine_and_norm_failures(self):
        self.vector["channels"]["sentence"] = {"cosine": 0.99, "relativeNormDelta": 0.1}
        self.assertEqual(len(q.check_rows([self.vector], [self.pair])), 2)

    def test_nan_metric_fails(self):
        self.pair["combinedDelta"] = float("nan")
        self.assertEqual(len(q.check_rows([self.vector], [self.pair])), 1)

    def test_vector_validation_rejects_wrong_identity_shape_space(self):
        record = {"id": "a", "textSHA256": c.text_hash("text"), "space": q.preflight.SPACE,
                  "status": "ok", "contextual": [1.] * 512, "sentence": [1.] * 512}
        q.valid_vector(record, "a", "text")
        for key, value in (("id", "b"), ("space", "other"), ("contextual", [1.]), ("sentence", [0.] * 512),
                           ("sentence", [float("nan")] * 512), ("textSHA256", "other")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                q.valid_vector({**record, key: value}, "a", "text")

    def test_neural_validation_rejects_truncated_and_wrong_mean(self):
        good = {"id": "a--b", "weightsSHA256": "weights", "directions": [0.2, 0.4], "score": 0.3}
        q.valid_neural(good, "a--b", "weights")
        for key, value in (("directions", [0.3]), ("directions", [float("nan"), 0.3]), ("score", 0.4),
                           ("weightsSHA256", "bad"), ("id", "wrong")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                q.valid_neural({**good, key: value}, "a--b", "weights")


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="remember-runtime-test-")
        self.work = Path(self.temp.name)
        self.folder = self.work / "runs/runtime-qualification-01"
        self.patches = [patch.object(c, "WORK", self.work), patch.object(q, "FOLDER", self.folder),
                        patch.object(c, "verify_saved_preflight")]
        for value in self.patches:
            value.start()
        parent = self.work / "runs/preflight/binding.json"
        c.publish(parent, {})
        self.manifest = {"thresholds": list(q.THRESHOLDS), "bounds": q.BOUNDS, "hashes": {},
                         "preflightBindingSHA256": c.digest(parent), "weightsSHA256": "w",
                         "pairs": [{"id": "a--b"}], "sources": {"a": {"text": "text", "textSHA256": c.text_hash("text")}}}
        self.path = self.folder / "manifest.json"
        c.publish(self.path, self.manifest)
        self.binding = c.digest(self.path)

    def tearDown(self):
        for value in reversed(self.patches):
            value.stop()
        self.temp.cleanup()

    def test_empty_and_valid_resume(self):
        self.assertEqual(q.verify()[2], {"embeddings": 0, "neural": 0})
        c.unit(self.folder / "neural/a--b.json", {"id": "a--b", "weightsSHA256": "w", "directions": [0.5, 0.5], "score": 0.5}, self.binding)
        self.assertEqual(q.verify()[2]["neural"], 1)

    def test_unknown_receipt_fails(self):
        c.publish(self.folder / "neural/unknown.json", {})
        with self.assertRaises(ValueError):
            q.verify()

    def test_renamed_receipt_identity_fails(self):
        c.unit(self.folder / "neural/a--b.json", {"id": "wrong", "weightsSHA256": "w", "directions": [0.5, 0.5], "score": 0.5}, self.binding)
        with self.assertRaises(ValueError):
            q.verify()

    def test_symlink_receipt_fails(self):
        (self.folder / "neural").mkdir()
        (self.folder / "neural/a--b.json").symlink_to(self.path)
        with self.assertRaises(ValueError):
            q.verify()

    def test_criteria_change_fails(self):
        changed = deepcopy(self.manifest)
        changed["bounds"]["combinedDelta"] = 1.
        c.pf1.atomic(self.path, changed)
        with self.assertRaises(ValueError):
            q.verify()


if __name__ == "__main__":
    unittest.main()
