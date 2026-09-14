import importlib
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import screening2_common as common
import screening2_runtime as runtime


class RuntimeContinuationTests(unittest.TestCase):
    def test_missing_empty_and_file_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "empty").mkdir()
            (root / "file").write_bytes(b"abc")
            for path in (root / "missing", root / "empty", root / "file"):
                self.assertEqual(runtime.logical_bytes(path), common.logical_bytes(path))

    def test_nested_hidden_empty_and_unicode_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".hidden").mkdir()
            (root / ".hidden" / "数据").write_bytes(b"abc")
            (root / "empty").write_bytes(b"")
            (root / "large").write_bytes(b"a" * 10000)
            self.assertEqual(runtime.logical_bytes(root), 10003)
            self.assertEqual(runtime.logical_bytes(root), common.logical_bytes(root))

    def test_links_match_legacy_without_directory_recursion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "nested"
            nested.mkdir()
            (nested / "value").write_bytes(b"hello")
            (root / "file-link").symlink_to(nested / "value")
            (root / "dir-link").symlink_to(nested, target_is_directory=True)
            (root / "broken").symlink_to(root / "absent")
            self.assertEqual(runtime.logical_bytes(root), 10)
            self.assertEqual(runtime.logical_bytes(root), common.logical_bytes(root))
            self.assertEqual(runtime.logical_bytes(root / "dir-link"), common.logical_bytes(root / "dir-link"))

    def test_each_scan_sees_changes_without_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = root / "item"
            item.write_bytes(b"1")
            self.assertEqual(runtime.logical_bytes(root), 1)
            item.write_bytes(b"12345")
            self.assertEqual(runtime.logical_bytes(root), 5)
            item.unlink()
            self.assertEqual(runtime.logical_bytes(root), 0)

    def test_hard_links_count_each_directory_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "first").write_bytes(b"123")
            os.link(root / "first", root / "second")
            self.assertEqual(runtime.logical_bytes(root), 6)
            self.assertEqual(runtime.logical_bytes(root), common.logical_bytes(root))

    def test_special_files_are_not_opened(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            os.mkfifo(root / "pipe")
            self.assertEqual(runtime.logical_bytes(root), 0)

    def test_enumeration_errors_are_not_silently_undercounted(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(runtime.os, "scandir", side_effect=PermissionError("denied")):
                with self.assertRaises(PermissionError):
                    runtime.logical_bytes(Path(directory))

    def snapshot(self, used, free, planned):
        with patch.object(runtime, "logical_bytes", side_effect=[used, 0]), \
             patch.object(runtime.shutil, "disk_usage", return_value=SimpleNamespace(free=free)):
            return runtime.capacity_snapshot(planned)

    def test_exact_cap_boundary(self):
        record = self.snapshot(4 * common.GIB - 10, 12 * common.GIB, 10)
        self.assertTrue(record["withinCap"])
        self.assertFalse(self.snapshot(4 * common.GIB - 9, 12 * common.GIB, 10)["withinCap"])

    def test_exact_free_reserve_boundary(self):
        self.assertTrue(self.snapshot(0, 10 * common.GIB + 10, 10)["withinReserve"])
        self.assertFalse(self.snapshot(0, 10 * common.GIB + 9, 10)["withinReserve"])

    def test_invalid_planned_size_rejected(self):
        for planned in (-1, 1.5, None):
            with self.assertRaises(ValueError):
                runtime.capacity_snapshot(planned)

    def test_decisions_match_original_inequalities(self):
        for used in (0, 4 * common.GIB - 1, 4 * common.GIB, 5 * common.GIB):
            for free in (9 * common.GIB, 10 * common.GIB, 11 * common.GIB):
                for planned in (0, 1, 2 * 1024**2):
                    record = self.snapshot(used, free, planned)
                    expected = used + planned <= 4 * common.GIB and free - planned >= 10 * common.GIB
                    self.assertEqual(record["withinCap"] and record["withinReserve"], expected)

    def test_success_does_not_write_telemetry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(runtime, "capacity_snapshot", return_value=self.snapshot(0, 20 * common.GIB, 1)):
                self.assertTrue(runtime.StorageGuard(root)(1))
            self.assertEqual(list(root.iterdir()), [])

    def test_failure_keeps_exact_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = self.snapshot(123, 9 * common.GIB, 456)
            with patch.object(runtime, "capacity_snapshot", return_value=snapshot):
                self.assertFalse(runtime.StorageGuard(root)(456))
            files = list((root / "runtime-continuations" / runtime.ATTEMPT / "storage-pauses").glob("*.json"))
            self.assertEqual(len(files), 1)
            result = common.read(files[0])
            self.assertEqual({key: result[key] for key in snapshot}, snapshot)

    def test_guard_aliases_restore_even_after_error(self):
        modules = [importlib.import_module(name) for name in runtime.MODULES]
        before = {m.__name__: m.capacity for m in modules if hasattr(m, "capacity")}
        neural = importlib.import_module("screening2_neural")
        fit, predict = neural.fit, neural.predict
        guard = lambda planned=0: True
        with self.assertRaisesRegex(RuntimeError, "test exit"):
            with runtime.installed_guard(guard):
                for module in modules:
                    if module.__name__ in before:
                        self.assertIs(module.capacity, guard)
                self.assertIs(neural.fit, fit)
                self.assertIs(neural.predict, predict)
                raise RuntimeError("test exit")
        for module in modules:
            if module.__name__ in before:
                self.assertIs(module.capacity, before[module.__name__])

    def test_unexpected_override_rejected(self):
        neural = importlib.import_module("screening2_neural")
        with patch.object(neural, "capacity", lambda planned=0: True):
            with self.assertRaisesRegex(ValueError, "unexpected storage guard"):
                with runtime.installed_guard(lambda planned=0: True):
                    self.fail("override should fail closed")

    def test_original_boundary_still_pauses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            common.save(root / "manifest.json", {"test": True})
            with patch.object(runtime, "capacity_snapshot", return_value=self.snapshot(0, 9 * common.GIB, 1)), \
                 patch.object(common, "requested", False), runtime.installed_guard(runtime.StorageGuard(root)):
                with self.assertRaises(common.Paused):
                    common.boundary(root, "test-boundary")
            self.assertEqual(common.read(root / "control/pause-requested.json")["reason"], "storage_budget")
            self.assertEqual(len(list((root / "pauses").glob("*.json"))), 1)

    def test_preserved_lineage_excludes_only_mutable_control_and_logs(self):
        values = {"worker.lock": "a", "logs/x": "b", "control/pause.json": "c",
                  "runtime-continuations/x": "d", "screen/fold-1/A1.json": "e",
                  "fits/x/spec.json": "f", "recovery/1.json": "g"}
        with patch.object(common, "files_in", return_value=values):
            self.assertEqual(runtime.preserved_files(Path("unused")),
                             {key: values[key] for key in ("screen/fold-1/A1.json", "fits/x/spec.json", "recovery/1.json")})

    def test_continuation_directory_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "elsewhere").mkdir()
            (root / "runtime-continuations").symlink_to(root / "elsewhere", target_is_directory=True)
            with self.assertRaises(ValueError):
                runtime.folder_for(root)

    def test_completed_resume_never_executes_training(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(runtime.sys, "argv", ["runtime", "run", "--run", "unused", "--resume"]), \
                 patch.object(common, "paths", return_value=(root, root / "external")), \
                 patch.object(common, "setup"), patch.object(runtime, "verify", return_value={"complete": True}), \
                 patch.object(runtime.original, "execute") as execute, patch("builtins.print"):
                runtime.main()
                execute.assert_not_called()

    def test_original_results_and_new_sources_are_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run, external, sources = root / "run", root / "external", root / "sources"
            folder = runtime.folder_for(run)
            for path in (run, external, sources, folder / "source-snapshots"):
                path.mkdir(parents=True, exist_ok=True)
            for name in runtime.SOURCES:
                (sources / name).write_bytes(b"source")
                (folder / "source-snapshots" / name).write_bytes(b"source")
            common.save(run / "manifest.json", {"original": True})
            common.save(run / "result.json", {"prediction": .7})
            (external / "model").write_bytes(b"model")
            common.save(folder / "benchmark.json", {"passed": True})
            def bindings():
                return {name: common.sha(sources / name) for name in runtime.SOURCES}
            record = {"sourceBindings": bindings(), "originalManifestSHA256": common.sha(run / "manifest.json"),
                      "storageCapBytes": 4 * common.GIB, "freeReserveBytes": 10 * common.GIB,
                      "modelDataEvaluationSettingsChanged": False,
                      "preservedEvidence": {"result.json": common.sha(run / "result.json")},
                      "preservedModelExports": {"model": common.sha(external / "model")},
                      "benchmarkSHA256": common.sha(folder / "benchmark.json")}
            common.save(folder / "manifest.json", record)
            with patch.object(runtime.original, "verify", return_value={"complete": False}), \
                 patch.object(runtime, "source_bindings", side_effect=bindings), patch.object(common, "HERE", sources):
                self.assertTrue(runtime.verify(run, external)["continuationVerified"])
                common.save(run / "new-result.json", {"new": True})
                self.assertTrue(runtime.verify(run, external)["continuationVerified"])
                (run / "result.json").write_text('{"prediction": 0.2}')
                with self.assertRaisesRegex(ValueError, "artifact mismatch"):
                    runtime.verify(run, external)
                (sources / runtime.SOURCES[0]).write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError, "source freeze changed"):
                    runtime.verify(run, external)


if __name__ == "__main__":
    unittest.main()
