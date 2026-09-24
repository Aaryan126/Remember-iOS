"""Fast tests; no models, device, downloads, or benchmark inference."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import common as c


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="remember-pf2-test-")
        self.work = Path(self.temp.name)
        self.override = patch.object(c, "WORK", self.work)
        self.override.start()

    def tearDown(self):
        self.override.stop()
        self.temp.cleanup()

    def test_immutable_retry_keeps_mtime(self):
        path = self.work / "unit.json"
        c.unit(path, {"answer": 4}, "binding")
        stamp = path.stat().st_mtime_ns
        c.unit(path, {"answer": 4}, "binding")
        self.assertEqual(path.stat().st_mtime_ns, stamp)
        self.assertEqual(c.read_unit(path, "binding"), {"answer": 4})
        with self.assertRaises(ValueError):
            c.unit(path, {"answer": 5}, "binding")

    def test_changed_binding_rejected(self):
        path = self.work / "unit.json"
        c.unit(path, {"answer": 4}, "binding")
        with self.assertRaises(ValueError):
            c.read_unit(path, "different")

    def test_corrupt_payload_rejected(self):
        path = self.work / "unit.json"
        c.unit(path, {"answer": 4}, "binding")
        value = c.read(path)
        value["payload"]["answer"] = 5
        c.pf1.atomic(path, value)
        with self.assertRaises(ValueError):
            c.read_unit(path, "binding")

    def test_escape_rejected(self):
        with self.assertRaises(ValueError):
            c.publish(self.work / ".." / "escape.json", {})

    def test_symlink_escape_rejected(self):
        (self.work / "escape").symlink_to(self.work.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            c.publish(self.work / "escape" / "unit.json", {})

    def test_pause_precedes_work(self):
        c.pf1.atomic(self.work / "pause.request.json", {})
        with self.assertRaises(c.Paused):
            c.boundary()

    def test_worker_closes_after_failure(self):
        with self.assertRaises(RuntimeError):
            with c.worker():
                raise RuntimeError("test failure")
        self.assertFalse(c.read(self.work / "worker.json")["running"])

    def test_resume_preserves_pause_if_binding_bad(self):
        c.pf1.atomic(self.work / "pause.request.json", {})
        c.publish(self.work / "runs/preflight/binding.json", {"hashes": {str(self.work / "missing"): "bad"}})
        with self.assertRaises(FileNotFoundError):
            with c.worker(resume=True):
                self.fail("bad binding must not resume")
        self.assertTrue((self.work / "pause.request.json").exists())

    def test_resume_retains_pause_history(self):
        c.pf1.atomic(self.work / "pause.request.json", {"requested": True})
        with c.worker(resume=True):
            self.assertFalse((self.work / "pause.request.json").exists())
        history = list((self.work / "runs").glob("pause-*.json"))
        self.assertEqual(len(history), 1)
        self.assertEqual(c.read(history[0]), {"requested": True})


if __name__ == "__main__":
    unittest.main()
