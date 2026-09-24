import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import control as c


class Resources(unittest.TestCase):
    def test_inclusive_limits(self):
        row = c.accounting(10*c.GIB, 28*c.GIB, c.GIB, c.GIB)
        self.assertEqual(row["conservativeGrowthBytes"], 18*c.GIB)

    def test_global_decline_is_not_reset(self):
        with self.assertRaisesRegex(ValueError, "18 GiB"):
            c.accounting(20*c.GIB, 39*c.GIB, 0, 0)

    def test_scoped_and_external_count_even_if_free_increases(self):
        self.assertEqual(c.accounting(40*c.GIB, 30*c.GIB, 2*c.GIB, 3*c.GIB)
                         ["conservativeGrowthBytes"], 5*c.GIB)
        with self.assertRaises(ValueError): c.accounting(40*c.GIB, 30*c.GIB, 17*c.GIB, 2*c.GIB)

    def test_reserve_and_invalid_values(self):
        with self.assertRaisesRegex(ValueError, "reserve"): c.accounting(9*c.GIB, 9*c.GIB, 0, 0)
        for invalid in (-1, 1.0, True):
            with self.assertRaisesRegex(ValueError, "invalid"): c.accounting(20*c.GIB, 20*c.GIB, invalid, 0)


class DurableArtifacts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.work, self.run = self.root / "work", self.root / "run"
        self.work.mkdir()
        self.patches = [patch.object(c, "WORK", self.work), patch.object(c, "RUN", self.run)]
        for item in self.patches: item.start()

    def tearDown(self):
        for item in reversed(self.patches): item.stop()
        self.temp.cleanup()

    def test_idempotent_output_preserves_mtime(self):
        path = self.work / "unit.json"
        c.publish(path, {"id": 1})
        before = (c.digest(path), path.stat().st_mtime_ns)
        c.publish(path, {"id": 1})
        self.assertEqual(before, (c.digest(path), path.stat().st_mtime_ns))
        with self.assertRaisesRegex(ValueError, "immutable"): c.publish(path, {"id": 2})

    def test_path_escape_and_symlinks(self):
        with self.assertRaises(ValueError): c.publish(self.root / "escape.json", {})
        (self.work / "link").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): c.publish(self.work / "link/escape.json", {})

    def test_worker_pause_resume(self):
        with patch.object(c, "verify_preserved"), patch.object(c, "resources", return_value={}):
            c.pause()
            with self.assertRaises(c.Paused):
                with c.worker(): pass
            self.assertFalse(c.load(self.work / "worker.json")["running"])
            with c.worker(resume=True):
                c.publish(self.work / "unit.json", {"complete": True})
                self.assertTrue(c.load(self.work / "worker.json")["running"])
            self.assertEqual(len(list(self.work.glob("pause-resumed-*.json"))), 1)
            self.assertFalse(c.load(self.work / "worker.json")["running"])

    def test_worker_stops_after_error(self):
        with patch.object(c, "verify_preserved"), patch.object(c, "resources", return_value={}):
            with self.assertRaises(RuntimeError):
                with c.worker(): raise RuntimeError("test failure")
            self.assertFalse(c.load(self.work / "worker.json")["running"])

    def test_lock_refuses_concurrent_writer(self):
        with patch.object(c, "verify_preserved"), patch.object(c, "resources", return_value={}):
            with c.worker():
                with self.assertRaises(BlockingIOError):
                    with c.worker(): pass


if __name__ == "__main__": unittest.main()
