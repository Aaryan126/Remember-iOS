import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("unified_phone_deploy", Path(__file__).with_name("deploy.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ResourceTests(unittest.TestCase):
    def snapshot(self, free=12, growth=30):
        return {"freeBytes": free * module.d.GIB, "conservativeGrowthBytes": growth * module.d.GIB}

    def test_keeps_free_space_reserve(self):
        with patch.object(module.d.guard, "resource_snapshot", return_value=self.snapshot(free=10)):
            with self.assertRaisesRegex(RuntimeError, "10 GiB"):
                module.resources(1)

    def test_keeps_cumulative_cap(self):
        with patch.object(module.d.guard, "resource_snapshot", return_value=self.snapshot(growth=32)):
            with self.assertRaisesRegex(RuntimeError, "32 GiB"):
                module.resources(1)

    def test_reservation_is_counted_at_both_boundaries(self):
        snapshot = self.snapshot(free=11, growth=31)
        with patch.object(module.d.guard, "resource_snapshot", return_value=snapshot):
            self.assertEqual(module.resources(module.d.GIB), snapshot)
            with self.assertRaises(RuntimeError):
                module.resources(module.d.GIB + 1)

    def test_pause_blocks_dispatch(self):
        with patch.object(Path, "exists", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "paused"):
                module.resources()


if __name__ == "__main__":
    unittest.main()
