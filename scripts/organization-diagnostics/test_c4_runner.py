from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import c2_common as c
import c4_run as run


class RunnerTests(unittest.TestCase):
    def test_atomic_unit_retries_and_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unit.json"
            c.unit(path, {"saved": True})
            before = path.stat().st_mtime_ns
            c.unit(path, {"saved": True})
            self.assertEqual(before, path.stat().st_mtime_ns)
            self.assertEqual(c.read_unit(path), {"saved": True})
            with self.assertRaises(ValueError):
                c.unit(path, {"changed": True})

    def test_pause_ack_and_resume_clear_only_own_request(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(run, "RUN", Path(directory)), patch.object(c, "space", return_value={}):
            self.assertFalse(run.pause()["safeToClose"])
            with run.worker():
                with self.assertRaises(c.Paused):
                    run.boundary("test")
            self.assertEqual(len(list((Path(directory) / "pauses").glob("*.json"))), 1)
            with run.worker(resume=True):
                self.assertFalse((Path(directory) / "control/pause-requested.json").exists())
                run.boundary("resumed")

    def test_resource_failure_is_not_swallowed(self):
        with patch.object(c, "space", side_effect=ValueError("reserve")):
            with self.assertRaisesRegex(ValueError, "reserve"):
                run.boundary("test")

    def test_binding_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                run.checked_files({"../outside": "invalid"}, Path(directory))


if __name__ == "__main__":
    unittest.main()
