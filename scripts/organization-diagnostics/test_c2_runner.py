"""Synthetic CPU-only runner checks; no production model, labels or inference."""
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import c2_common as c


class RunnerArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="c2-runner-test-")
        self.addCleanup(self.temporary.cleanup)
        self.runpath = Path(self.temporary.name)
        self.run_patch = patch.object(c, "RUN", self.runpath)
        self.run_patch.start()
        self.addCleanup(self.run_patch.stop)

    def test_immutable_unit_retries_and_detects_tampering(self):
        path = self.runpath / "unit.json"
        value = {"id": "synthetic", "score": 0.75}
        c.unit(path, value)
        c.unit(path, value)
        self.assertEqual(c.read_unit(path), value)
        with self.assertRaises(ValueError):
            c.unit(path, {"id": "synthetic", "score": 0.5})
        saved = c.read(path)
        saved["payload"]["score"] = 0.5
        path.write_text(json.dumps(saved))
        with self.assertRaisesRegex(ValueError, "checksum"):
            c.read_unit(path)

    def test_unit_rejects_nonfinite_values(self):
        with self.assertRaises(ValueError):
            c.unit(self.runpath / "bad.json", {"score": float("nan")})
        self.assertFalse((self.runpath / "bad.json").exists())

    def test_worker_rejects_duplicate_and_releases_lock(self):
        with c.worker():
            with self.assertRaisesRegex(RuntimeError, "Another C2 worker"):
                with c.worker():
                    self.fail("Duplicate worker entered")
        with c.worker():
            pass

    def test_pause_preserves_saved_units_and_resume_records_request(self):
        unit_path = self.runpath / "saved.json"
        c.unit(unit_path, {"id": "saved", "score": 0.25})
        before = c.digest(unit_path)
        self.assertFalse(c.request_pause()["safeToClose"])
        with patch.object(c, "space", return_value={}):
            with c.worker():
                with self.assertRaises(c.Paused):
                    c.boundary("synthetic-boundary")
            self.assertEqual(c.digest(unit_path), before)
            with c.worker(resume=True):
                c.boundary("synthetic-resumed")
        self.assertFalse((self.runpath / "control/pause-requested.json").exists())
        self.assertEqual(len(list((self.runpath / "resumptions").glob("*.json"))), 1)
        self.assertEqual(c.digest(unit_path), before)

    def test_pair_key_is_symmetric_and_exact_text_sensitive(self):
        self.assertEqual(c.pair_key("coral", "ocean"), c.pair_key("ocean", "coral"))
        self.assertNotEqual(c.pair_key("coral", "ocean"), c.pair_key("Coral", "ocean"))

    def test_resume_rejects_runtime_drift(self):
        manifest = {"sources": {}, "external": {}, "runtime": {"syntheticVersion": 1}}
        c.publish(self.runpath / "manifest.json", manifest)
        with patch.object(c, "runtime", return_value={"syntheticVersion": 1}):
            self.assertEqual(c.verify_bindings(), manifest)
        with patch.object(c, "runtime", return_value={"syntheticVersion": 2}):
            with self.assertRaisesRegex(ValueError, "runtime changed"):
                c.verify_bindings()

    def parity_fixture(self, *, passed=True, seeds=("17", "29", "41")):
        c.publish(self.runpath / "manifest.json", {"synthetic": True})
        reports = {}
        for seed in seeds:
            path = self.runpath / f"parity/seed-{seed}.json"
            c.publish(path, {"passed": True, "cases": [{"id": f"case-{i}"} for i in range(16)]})
            reports[seed] = c.digest(path)
        c.publish(self.runpath / "parity/complete.json", {
            "passed": passed, "casesPerSeed": 16,
            "manifestSHA256": c.digest(self.runpath / "manifest.json"), "reports": reports})

    def test_parity_receipt_accepts_complete_bound_reports(self):
        from c2_run import verify_parity_receipt
        self.parity_fixture()
        self.assertTrue(verify_parity_receipt()["passed"])

    def test_parity_receipt_rejects_failed_status(self):
        from c2_run import verify_parity_receipt
        self.parity_fixture(passed=False)
        with self.assertRaisesRegex(ValueError, "not passed"):
            verify_parity_receipt()

    def test_parity_receipt_rejects_missing_seed(self):
        from c2_run import verify_parity_receipt
        self.parity_fixture(seeds=("17", "29"))
        with self.assertRaisesRegex(ValueError, "seed coverage"):
            verify_parity_receipt()

    def test_parity_receipt_rejects_modified_report(self):
        from c2_run import verify_parity_receipt
        self.parity_fixture()
        (self.runpath / "parity/seed-17.json").write_text('{"passed":false}')
        with self.assertRaisesRegex(ValueError, "report changed"):
            verify_parity_receipt()

    def test_parity_receipt_rejects_changed_manifest(self):
        from c2_run import verify_parity_receipt
        self.parity_fixture()
        (self.runpath / "manifest.json").write_text('{"synthetic":"changed"}')
        with self.assertRaisesRegex(ValueError, "manifest changed"):
            verify_parity_receipt()


class SyntheticFeatureTests(unittest.TestCase):
    def setUp(self):
        try:
            from c2_models import Features
        except ModuleNotFoundError as error:
            if error.name in {"numpy", "sklearn"}:
                self.skipTest("Requires the existing evaluation Python environment")
            raise
        baseline = {"classOrder": ["same", "related", "unrelated"],
                    "scalerMean": [0.0] * 6, "scalerScale": [1.0] * 6,
                    "coefficients": [[0.0] * 6 for _ in range(3)],
                    "intercept": [1.0, 0.0, -1.0]}
        hybrid = {"kind": "logistic", "mean": [0.0] * 11, "scale": [1.0] * 11,
                  "coefficient": [0.0] * 10 + [1.0], "intercept": 0.0}
        frozen = {"vocabulary": {"coral": 0}, "ngramRange": [1, 2],
                  "lowercase": True, "tokenPattern": r"(?u)\b\w\w+\b", "norm": "l2", "idf": [1.0]}
        def read_fixture(path):
            if path.name == "tfidf.json":
                return frozen
            if path.name == "baseline.json":
                return {"model": baseline}
            if path.name in {f"hybrid-{seed}.json" for seed in (17, 29, 41)}:
                return {"model": hybrid}
            raise AssertionError(f"Unexpected fixture read: {path}")
        embedding = {"status": "ok", "contextual": [1.0, 0.0],
                     "sentence": [1.0, 0.0], "space": "synthetic"}
        with patch.object(c, "read", side_effect=read_fixture):
            self.features = Features({"a": "coral 7", "b": "coral 7"}, {"a": embedding, "b": embedding})

    def test_feature_order_and_baseline_argmax(self):
        values = self.features.values("a", "b")
        self.assertEqual(values, [1.0] * 6 + [0.0, 0.0, 1.0, 1.0])
        scored = self.features.scores(values)
        expected = math.exp(1) / (math.exp(1) + 1 + math.exp(-1))
        self.assertAlmostEqual(scored["baseline"]["score"], expected)
        self.assertTrue(scored["baseline"]["eligible"])

    def test_hybrid_adds_clipped_neural_logit(self):
        values = self.features.values("a", "b")
        scored = self.features.scores(values, {"17": 0.75, "29": 0.0, "41": 1.0})
        self.assertAlmostEqual(scored["hybrid"]["17"], 0.75)
        self.assertAlmostEqual(scored["hybrid"]["29"], 1e-6)
        self.assertAlmostEqual(scored["hybrid"]["41"], 1 - 1e-6)

    def test_missing_embedding_features_disable_scores(self):
        values = self.features.values("a", "b")
        values[0] = None
        result = self.features.scores(values, {"17": 0.75})
        self.assertEqual(result["baseline"], {"score": None, "eligible": False})
        self.assertIsNone(result["hybrid"]["17"])


if __name__ == "__main__":
    unittest.main()
