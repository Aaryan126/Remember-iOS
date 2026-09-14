import tempfile
import unittest
from pathlib import Path

from evaluation_snapshot import inventory, publish


class SnapshotTests(unittest.TestCase):
    def test_inventory_is_stable_and_detects_content_and_path_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "evidence.json").write_text("abc")
            first = inventory(root)
            self.assertEqual(first["files"], 1)
            self.assertEqual(first["bytes"], 3)
            self.assertEqual(first, inventory(root))
            (root / "worker.lock").write_text("mutable")
            self.assertEqual(first, inventory(root))
            (root / "evidence.json").write_text("abd")
            second = inventory(root)
            self.assertNotEqual(first, second)
            (root / "evidence.json").rename(root / "renamed.json")
            self.assertNotEqual(second, inventory(root))

    def test_missing_directory_and_symlink_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(ValueError):
                inventory(root / "missing")
            (root / "link").symlink_to(root)
            with self.assertRaises(ValueError):
                inventory(root)

    def test_publish_is_idempotent_and_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "snapshot.json"
            publish(path, {"version": 1})
            original = path.read_bytes()
            publish(path, {"version": 1})
            self.assertEqual(original, path.read_bytes())
            with self.assertRaises(ValueError):
                publish(path, {"version": 2})
            self.assertEqual(original, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
