import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location("ledger_prepare", Path(__file__).with_name("prepare_project.py"))
PREPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARE)


class ProjectPreparationTests(unittest.TestCase):
    def test_bindings_are_real_production_sources(self):
        self.assertIn("MemoryStore.swift", PREPARE.PRODUCTION_SOURCES)
        self.assertIn("Provenance.swift", PREPARE.PRODUCTION_SOURCES)
        self.assertIn("ProjectViewModel.swift", PREPARE.PRODUCTION_SOURCES)
        self.assertNotIn("RememberApp.swift", PREPARE.PRODUCTION_SOURCES)
        for name in PREPARE.PRODUCTION_SOURCES:
            self.assertTrue((PREPARE.REPOSITORY / "Remember/Remember" / name).is_file())

    def test_local_package_and_separate_app_identity(self):
        project = PREPARE.project_text(Path('/cache/GRDB.swift'))
        self.assertIn("XCLocalSwiftPackageReference", project)
        self.assertNotIn("XCRemoteSwiftPackageReference", project)
        self.assertIn("SimpleStudio.Remember.OrganizationLedgerProbe", project)
        self.assertNotIn("PACKAGE_PATH", project)

    def test_rejects_personal_or_production_destination_before_writes(self):
        with self.assertRaisesRegex(ValueError, "beneath"):
            PREPARE.prepare(PREPARE.REPOSITORY / "Remember", Path("/missing/package"))

    def test_rejects_missing_dependency_without_download(self):
        with self.assertRaisesRegex(ValueError, "existing local GRDB"):
            PREPARE.prepare(PREPARE.REPOSITORY / "Evaluation/OrganizationDiagnostics/runs/missing-package-probe",
                            Path("/missing/package"))

    def test_harness_never_opens_live_store_or_invokes_models(self):
        source = "\n".join((PREPARE.HERE / name).read_text() for name in PREPARE.HARNESS_SOURCES)
        for call in ("MemoryStore.live(", "defaultDatabaseURL(", ".synchronize(", "requestAssets(", "URLSession"):
            self.assertNotIn(call, source)
        self.assertIn("MemoryStore(databaseURL: root.appendingPathComponent", source)


if __name__ == "__main__":
    unittest.main()
