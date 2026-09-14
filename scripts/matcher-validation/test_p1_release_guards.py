"""Release verification regressions using only isolated synthetic files."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import p1_release


class ReleaseVerificationGuardsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.run = self.root / "run"
        self.run.mkdir()
        self.manifest_path = self.run / "complete.json"
        self.sources = [self.root / "sources" / name for name in ("first.txt", "second.txt")]
        self.artifacts = [self.root / "release" / name for name in ("first.json", "second.json")]
        for index, path in enumerate(self.sources + self.artifacts):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"Synthetic verification fixture {index}\n")
        self.manifest = {
            "checkpoint": "P1",
            "complete": True,
            "readyForP2": True,
            "stopForUserReview": True,
            "trainingStarted": False,
            "productionQualified": False,
            "oldTestOpened": False,
            "sources": self.inventory(self.sources),
            "artifacts": self.inventory(self.artifacts),
        }
        for target, name, value in (
            (p1_release, "ROOT", self.root),
            (p1_release, "RUN", self.run),
        ):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for target, name, value in (
            (p1_release.p1, "assignment", {}),
            (p1_release, "source_paths", self.sources),
            (p1_release, "expected_artifacts", self.artifacts),
        ):
            # The artifact-inventory helper is introduced by the accompanying fix.
            patcher = patch.object(target, name, return_value=value, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)

    def inventory(self, paths):
        return {str(path.relative_to(self.root)): p1_release.digest(path) for path in paths}

    def write_manifest(self, manifest=None):
        value = self.manifest if manifest is None else manifest
        self.manifest_path.write_text(json.dumps(value, sort_keys=True) + "\n")

    def assert_rejected(self, manifest):
        self.write_manifest(manifest)
        with self.assertRaises(ValueError):
            p1_release.verify()

    def test_valid_manifest_roundtrip_is_read_only(self):
        self.write_manifest()
        before = {
            str(path.relative_to(self.root)): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in self.root.rglob("*") if path.is_file()
        }
        first = p1_release.verify()
        second = p1_release.verify()
        self.assertEqual(first, second)
        self.assertIs(first["verified"], True)
        self.assertEqual(first["checkpoint"], "P1")
        self.assertIs(first["readyForP2"], True)
        self.assertIs(first["trainingStarted"], False)
        self.assertEqual(first["completeSHA256"], p1_release.digest(self.manifest_path))
        after = {
            str(path.relative_to(self.root)): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in self.root.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)

    def test_empty_inventories_are_rejected(self):
        self.assert_rejected(self.manifest | {"sources": {}, "artifacts": {}})

    def test_missing_inventory_entry_is_rejected(self):
        for collection in ("sources", "artifacts"):
            with self.subTest(collection=collection):
                manifest = deepcopy(self.manifest)
                manifest[collection].pop(next(iter(manifest[collection])))
                self.assert_rejected(manifest)

    def test_extra_inventory_entry_is_rejected_even_with_correct_hash(self):
        extra = self.root / "unlisted.txt"
        extra.write_text("A real file does not belong in either declared inventory.\n")
        for collection in ("sources", "artifacts"):
            with self.subTest(collection=collection):
                manifest = deepcopy(self.manifest)
                manifest[collection]["unlisted.txt"] = p1_release.digest(extra)
                self.assert_rejected(manifest)

    def test_missing_manifest_key_is_rejected(self):
        for key in self.manifest:
            with self.subTest(key=key):
                manifest = deepcopy(self.manifest)
                del manifest[key]
                self.assert_rejected(manifest)

    def test_extra_manifest_key_is_rejected(self):
        self.assert_rejected(self.manifest | {"uncheckedCompletion": True})

    def test_wrong_checkpoint_is_rejected(self):
        self.assert_rejected(self.manifest | {"checkpoint": "P0"})

    def test_invalid_state_flags_are_rejected(self):
        for flag in (
            "complete", "readyForP2", "stopForUserReview",
            "trainingStarted", "productionQualified", "oldTestOpened",
        ):
            with self.subTest(flag=flag):
                self.assert_rejected(self.manifest | {flag: not self.manifest[flag]})

    def test_state_flags_require_booleans(self):
        for flag in (
            "complete", "readyForP2", "stopForUserReview",
            "trainingStarted", "productionQualified", "oldTestOpened",
        ):
            for value in (int(self.manifest[flag]), str(self.manifest[flag]).lower(), None):
                with self.subTest(flag=flag, value=value):
                    self.assert_rejected(self.manifest | {flag: value})

    def test_changed_source_bytes_are_rejected(self):
        self.write_manifest()
        self.sources[0].write_text("Changed synthetic source\n")
        with self.assertRaises(ValueError):
            p1_release.verify()

    def test_changed_artifact_bytes_are_rejected(self):
        self.write_manifest()
        self.artifacts[0].write_text("Changed synthetic artifact\n")
        with self.assertRaises(ValueError):
            p1_release.verify()

    def test_wrong_recorded_hash_is_rejected(self):
        for collection in ("sources", "artifacts"):
            with self.subTest(collection=collection):
                manifest = deepcopy(self.manifest)
                manifest[collection][next(iter(manifest[collection]))] = "0" * 64
                self.assert_rejected(manifest)


if __name__ == "__main__":
    unittest.main()
