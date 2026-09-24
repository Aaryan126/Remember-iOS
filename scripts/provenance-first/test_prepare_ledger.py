import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("pf_prepare", Path(__file__).with_name("prepare_ledger.py"))
PREPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARE)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repository = self.root / "repo"
        self.repository.mkdir()
        self.override = patch.object(PREPARE, "REPOSITORY", self.repository)
        self.override.start()
        self.addCleanup(self.override.stop)
        self.output = self.repository / "Evaluation/ProvenanceFirst/runs/test/project"
        self.package = self.root / "GRDB.swift"
        for name in ("Package.swift", "GRDB/Database.swift",
                     "Sources/GRDBSQLite/module.modulemap", "Sources/GRDBSQLite/shim.h"):
            self.write(self.package / name, "fixture dependency\n")
        for name in PREPARE.PRODUCTION_SOURCES:
            self.write(self.repository / "Remember/Remember" / name, "// production fixture\n")
        self.write(self.repository / "Remember/Shared/CaptureInbox.swift", "// shared fixture\n")
        for name in PREPARE.HARNESS_SOURCES + ("prepare_project.py", "DiagnosticReplayApp.swift"):
            self.write(self.repository / "scripts/organization-diagnostics/ledger" / name, "// harness fixture\n")
        self.write(self.repository / "scripts/provenance-first/prepare_ledger.py", "# tool fixture\n")

    @staticmethod
    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_rejects_traversal_and_workspace_root(self):
        for value in (self.repository / "Remember", PREPARE.runs_root(),
                      PREPARE.runs_root() / "../outside/project"):
            with self.assertRaisesRegex(ValueError, "beneath"):
                PREPARE.prepare(value, self.package)

    def test_rejects_symlink_escape(self):
        allowed = PREPARE.runs_root()
        allowed.mkdir(parents=True)
        (allowed / "escape").symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "beneath"):
            PREPARE.prepare(allowed / "escape/project", self.package)

    def test_rejects_redirected_runs_root(self):
        allowed = PREPARE.runs_root()
        allowed.parent.mkdir(parents=True)
        allowed.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "redirected"):
            PREPARE.prepare(self.output, self.package)

    def test_rejects_existing_output_without_overwriting(self):
        self.write(self.output / "keep.txt", "unchanged")
        with self.assertRaisesRegex(ValueError, "already exists"):
            PREPARE.prepare(self.output, self.package)
        self.assertEqual((self.output / "keep.txt").read_text(), "unchanged")

    def test_missing_dependency_writes_nothing(self):
        with self.assertRaisesRegex(ValueError, "existing local GRDB"):
            PREPARE.prepare(self.output, self.root / "missing")
        self.assertFalse(self.output.exists())

    def test_missing_source_writes_nothing(self):
        (self.repository / "Remember/Remember/MemoryStore.swift").unlink()
        with self.assertRaisesRegex(ValueError, "missing source"):
            PREPARE.prepare(self.output, self.package)
        self.assertFalse(self.output.exists())

    def test_missing_package_module_map_writes_nothing(self):
        (self.package / "Sources/GRDBSQLite/module.modulemap").unlink()
        with self.assertRaisesRegex(ValueError, "module map"):
            PREPARE.prepare(self.output, self.package)
        self.assertFalse(self.output.exists())

    def test_dependency_symlink_cannot_escape_package(self):
        outside = self.root / "outside.swift"
        outside.write_text("not a package member")
        (self.package / "GRDB/escaped.swift").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink escapes"):
            PREPARE.prepare(self.output, self.package)
        self.assertFalse(self.output.exists())

    def test_rejects_remote_dependency_environment(self):
        with patch.dict(os.environ, {"SPI_BUILDER": "1"}):
            with self.assertRaisesRegex(ValueError, "remote dependency"):
                PREPARE.prepare(self.output, self.package)
        self.assertFalse(self.output.exists())

    def test_hashes_all_source_and_generated_bindings(self):
        result = PREPARE.prepare(self.output, self.package)
        binding_file = self.output / "Sources/bindings.json"
        bindings = json.loads(binding_file.read_text())
        self.assertEqual(result["bindingsSHA256"], PREPARE.digest(binding_file))
        self.assertEqual(result["bundleIdentifier"], PREPARE.BUNDLE_ID)
        for section in ("production", "harness", "tooling"):
            for path, expected in bindings[section].items():
                self.assertEqual(PREPARE.digest(self.repository / path), expected)
        for path, expected in bindings["generated"].items():
            self.assertEqual(PREPARE.digest(self.output / path), expected)
        for path, expected in bindings["grdb"].items():
            self.assertEqual(PREPARE.digest(self.package / path), expected)
        self.assertIn("Sources/GRDBSQLite/shim.h", bindings["grdb"])
        self.assertTrue((self.output / "Sources/MemoryStore.swift").is_symlink())
        self.assertFalse((self.output / "Sources/DiagnosticReplayApp.swift").exists())

    def test_launcher_and_project_are_isolated(self):
        launcher = PREPARE.launcher_text(PREPARE.runs_root())
        self.assertIn(str(PREPARE.runs_root()), launcher)
        self.assertIn('appendingPathComponent("ProvenanceFirst")', launcher)
        self.assertIn("resolvingSymlinksInPath", launcher)
        self.assertNotIn('.contains("/Evaluation/', launcher)
        for prohibited in ("MemoryStore.live(", "URLSession", "requestAssets(", ".synchronize("):
            self.assertNotIn(prohibited, launcher)
        project = PREPARE.project_text(self.package)
        self.assertIn(PREPARE.BUNDLE_ID, project)
        self.assertIn("XCLocalSwiftPackageReference", project)
        self.assertNotIn("XCRemoteSwiftPackageReference", project)
        self.assertNotIn("OrganizationLedgerProbe", project)

    def test_source_change_changes_binding_identity(self):
        first = PREPARE.prepare(self.output, self.package)
        self.write(self.repository / "Remember/Remember/MemoryStore.swift", "// changed source\n")
        second = PREPARE.prepare(self.output.with_name("other-project"), self.package)
        self.assertNotEqual(first["bindingsSHA256"], second["bindingsSHA256"])

    def test_production_list_excludes_app_entry_point_and_models(self):
        self.assertIn("VideoContentExtractor.swift", PREPARE.PRODUCTION_SOURCES)
        self.assertIn("D3ProjectOrganizer.swift", PREPARE.PRODUCTION_SOURCES)
        self.assertNotIn("RememberApp.swift", PREPARE.PRODUCTION_SOURCES)
        self.assertTrue(all(name.endswith(".swift") for name in PREPARE.PRODUCTION_SOURCES))

    def test_existing_cached_package_layout_and_sqlite_bindings(self):
        package = PREPARE.HERE.parents[1] / (
            "Evaluation/iOS27/safeguards/build/"
            "GRDB.swift-b83108d10f42680d78f23fe4d4d80fc88dab3212"
        )
        if not package.is_dir():
            self.skipTest("optional locally cached package unavailable; no download permitted")
        bindings = PREPARE.package_bindings(package)
        for path in (package / "Sources/GRDBSQLite").rglob("*"):
            if path.is_file():
                self.assertEqual(bindings[str(path.relative_to(package))], PREPARE.digest(path))
        self.assertIn("Sources/GRDBSQLite/module.modulemap", bindings)
        self.assertIn("Sources/GRDBSQLite/shim.h", bindings)


if __name__ == "__main__":
    unittest.main()
