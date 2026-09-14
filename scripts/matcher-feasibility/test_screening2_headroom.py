from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import screening2_headroom as headroom

common = headroom.common
runtime = headroom.runtime


class HeadroomTests(unittest.TestCase):
    def snapshot(self, used, free, planned):
        return {"usedBytes": used, "freeBytes": free, "plannedBytes": planned,
                "storageCapBytes": 4 * common.GIB, "freeReserveBytes": 10 * common.GIB,
                "withinCap": used + planned <= 4 * common.GIB,
                "withinReserve": free - planned >= 10 * common.GIB}

    def test_exact_temporary_boundary(self):
        guard = headroom.StorageGuard(Path("unused"))
        for excess in (0, 1):
            value = self.snapshot(headroom.TEMPORARY_CAP - 10 + excess, 12 * common.GIB, 10)
            with patch.object(runtime, "capacity_snapshot", return_value=value):
                self.assertEqual(guard.measurement(10)["withinCap"], excess == 0)

    def test_final_cap_returns_to_four(self):
        guard = headroom.StorageGuard(Path("unused"))
        with patch.object(runtime, "capacity_snapshot", return_value=self.snapshot(4 * common.GIB, 12 * common.GIB, 1)):
            self.assertTrue(guard.measurement(1)["withinCap"])
            guard.finalizing = True
            self.assertFalse(guard.measurement(1)["withinCap"])
            self.assertEqual(guard.measurement(1)["storageCapBytes"], headroom.FINAL_CAP)

    def test_free_reserve_not_relaxed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for excess in (0, -1):
                value = self.snapshot(0, 10 * common.GIB + 10 + excess, 10)
                with patch.object(runtime, "capacity_snapshot", return_value=value):
                    self.assertEqual(headroom.StorageGuard(root)(10), excess == 0)

    def test_planned_size_validation_reused(self):
        for planned in (-1, 1.5, None):
            with self.assertRaises(ValueError):
                headroom.StorageGuard(Path("unused")).measurement(planned)

    def test_failure_telemetry_has_actual_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = self.snapshot(5 * common.GIB, 12 * common.GIB, 10)
            with patch.object(runtime, "capacity_snapshot", return_value=value):
                self.assertFalse(headroom.StorageGuard(root)(10))
            records = list((headroom.folder_for(root) / "storage-pauses").glob("*.json"))
            self.assertEqual(len(records), 1)
            record = common.read(records[0])
            self.assertEqual(record["storageCapBytes"], headroom.TEMPORARY_CAP)
            self.assertEqual(record["freeReserveBytes"], headroom.FREE_RESERVE)
            self.assertEqual(record["usedBytes"], value["usedBytes"])

    def test_final_boundary_pauses_before_audit_if_over_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            common.save(root / "manifest.json", {"test": True})
            guard = headroom.StorageGuard(root)
            value = self.snapshot(4 * common.GIB + 1, 12 * common.GIB, 2 * 1024**2)
            with patch.object(runtime, "capacity_snapshot", return_value=value), patch.object(common, "requested", False):
                with headroom.installed_policy(guard):
                    headroom.original.boundary(root, "confirmation")
                    with self.assertRaises(common.Paused):
                        headroom.original.boundary(root, "final-audit")
            self.assertTrue(guard.finalizing)
            self.assertFalse((headroom.folder_for(root) / "final-storage-checks").exists())

    def test_successful_boundary_saves_final_check_and_restores_functions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            guard = headroom.StorageGuard(root)
            before = headroom.original.boundary
            capacity = common.capacity
            execute = headroom.original.execute
            value = self.snapshot(3 * common.GIB, 12 * common.GIB, 2 * 1024**2)
            with patch.object(runtime, "capacity_snapshot", return_value=value), patch.object(common, "requested", False):
                with self.assertRaisesRegex(RuntimeError, "test"):
                    with headroom.installed_policy(guard):
                        self.assertIs(headroom.original.execute, execute)
                        headroom.original.boundary(root, "final-audit")
                        raise RuntimeError("test")
            self.assertIs(headroom.original.boundary, before)
            self.assertIs(common.capacity, capacity)
            records = list((headroom.folder_for(root) / "final-storage-checks").glob("*.json"))
            self.assertEqual(len(records), 1)
            self.assertTrue(common.read(records[0])["finalizing"])

    def test_user_pause_remains_effective_under_temporary_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            common.save(root / "manifest.json", {"test": True})
            common.request_pause(root)
            with patch.object(common, "requested", False), headroom.installed_policy(headroom.StorageGuard(root)):
                with self.assertRaises(common.Paused):
                    headroom.original.boundary(root, "confirmation")

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "elsewhere").mkdir()
            (root / "runtime-continuations").symlink_to(root / "elsewhere", target_is_directory=True)
            with self.assertRaises(ValueError):
                headroom.folder_for(root)

    def test_completed_resume_does_not_train(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(headroom.sys, "argv", ["headroom", "run", "--run", "unused", "--resume"]), \
                 patch.object(common, "paths", return_value=(root, root / "external")), \
                 patch.object(common, "setup"), patch.object(headroom, "verify", return_value={"complete": True}), \
                 patch.object(headroom.original, "execute") as execute, patch("builtins.print"):
                headroom.main()
                execute.assert_not_called()

    def test_manifest_lineage_and_final_cap_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run, external, sources = root / "run", root / "external", root / "sources"
            folder = headroom.folder_for(run)
            prior = runtime.folder_for(run)
            for path in (external, sources, prior, folder / "source-snapshots"):
                path.mkdir(parents=True, exist_ok=True)
            for name in headroom.SOURCES:
                (sources / name).write_bytes(b"source")
                (folder / "source-snapshots" / name).write_bytes(b"source")
            common.save(prior / "manifest.json", {"prior": True})
            common.save(run / "selection.json", {"selected": ["C3", "D3"]})
            (external / "model").write_bytes(b"weights")
            bindings = {name: common.sha(sources / name) for name in headroom.SOURCES}
            manifest = {"sourceBindings": bindings, "temporaryCapBytes": headroom.TEMPORARY_CAP,
                        "finalCapBytes": headroom.FINAL_CAP, "freeReserveBytes": headroom.FREE_RESERVE,
                        "modelDataEvaluationSettingsChanged": False, "testAccess": False,
                        "preservedEvidence": {"selection.json": common.sha(run / "selection.json")},
                        "priorContinuationFiles": common.files_in(prior),
                        "preservedModelExports": {"model": common.sha(external / "model")}}
            common.save(folder / "manifest.json", manifest)
            with patch.object(runtime, "verify", return_value={"complete": False}) as upstream, \
                 patch.object(headroom, "source_bindings", return_value=bindings), patch.object(common, "HERE", sources):
                self.assertTrue(headroom.verify(run, external)["headroomVerified"])
                upstream.return_value = {"complete": True}
                with self.assertRaisesRegex(ValueError, "missing final storage"):
                    headroom.verify(run, external)
                common.save(folder / "final-storage-checks" / "1.json", {
                    "finalizing": True, "storageCapBytes": headroom.FINAL_CAP,
                    "withinCap": True, "withinReserve": True})
                with patch.object(runtime, "logical_bytes", side_effect=[headroom.FINAL_CAP, 0]):
                    self.assertTrue(headroom.verify(run, external)["headroomVerified"])
                with patch.object(runtime, "logical_bytes", side_effect=[headroom.FINAL_CAP, 1]):
                    with self.assertRaisesRegex(ValueError, "retained screening"):
                        headroom.verify(run, external)
                upstream.return_value = {"complete": False}
                (run / "selection.json").write_text('{"selected": ["A1"]}')
                with self.assertRaisesRegex(ValueError, "artifact mismatch"):
                    headroom.verify(run, external)


if __name__ == "__main__":
    unittest.main()
