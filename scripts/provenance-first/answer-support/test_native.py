"""Pure/mocked native orchestration tests; never boot a simulator or run a model."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import as_native as n


class NativeTests(unittest.TestCase):
    def test_path_escape(self):
        root = Path("/tmp/answer-native-test")
        for name in ("../outside", ".", "/elsewhere"):
            with self.assertRaises(ValueError): n.inside(root, name)

    def test_source_identity_matches_history(self):
        self.assertEqual(n.source_uuid("localc01"), n.old_coverage.source_uuid("s01"))

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / "alias").symlink_to("/tmp")
            with self.assertRaises(ValueError): n.inside(root, "alias/data")

    def test_completed_group_not_signaled(self):
        process = MagicMock()
        process.poll.return_value = 0
        with patch.object(n.os, "killpg") as kill:
            n.stop_group(process)
            kill.assert_not_called()

    def test_active_group_is_stopped(self):
        process = MagicMock()
        process.poll.side_effect = [None, 0]
        process.pid = 98123
        with patch.object(n.os, "killpg") as kill:
            n.stop_group(process)
            kill.assert_called_once_with(98123, n.signal.SIGTERM)
            process.wait.assert_called_once_with(timeout=5)

    def test_group_escalation(self):
        process = MagicMock()
        process.poll.side_effect = [None, 0]
        process.pid = 98123
        process.wait.side_effect = [n.subprocess.TimeoutExpired("fake", 5), 0]
        with patch.object(n.os, "killpg") as kill:
            n.stop_group(process)
            self.assertEqual(kill.call_count, 2)
            self.assertEqual(kill.call_args.args, (98123, n.signal.SIGKILL))

    def test_existing_readiness_is_not_a_generation_control(self):
        path = n.c.WORK / "mac-readiness.json"
        if not path.exists(): self.skipTest("metadata receipt not present")
        with patch.object(n.c, "boundary"), patch.object(n, "execute") as execute:
            saved = n.mac_readiness()
        self.assertEqual(saved["generationRequests"], 0)
        self.assertFalse(saved["controlsQualified"])
        execute.assert_not_called()

    def test_frozen_native_build_readonly(self):
        self.assertIsNone(n.old_native.verify_build())

    def test_reuses_all_old_native_projection_invariants(self):
        # Regression only; the older fixed fixtures are not fresh evaluation data.
        source = n.old_native.c.RUN / "input.json"
        runs = n.c.load(source)["runs"]
        with patch.object(n, "OUTPUT", n.old_native.OUTPUT):
            rows = [n.verify_run(run, source, n.old_native.BINDINGS) for run in runs]
        self.assertEqual(len(rows), 24)
        self.assertTrue(all(row["restartVerified"] for row in rows))
        self.assertEqual(sum(row["prefixes"] for row in rows), 288)

    def test_changed_query_scope_rejected(self):
        source = n.old_native.c.RUN / "input.json"
        run = copy.deepcopy(n.c.load(source)["runs"][0])
        query = run["queries"][0]
        query["scope"] = "includeHistory" if query["scope"] == "current" else "current"
        with patch.object(n, "OUTPUT", n.old_native.OUTPUT):
            with self.assertRaisesRegex(ValueError, "query scope"):
                n.verify_run(run, source, n.old_native.BINDINGS)

    def test_changed_expected_archive_rejected(self):
        source = n.old_native.c.RUN / "input.json"
        run = copy.deepcopy(n.c.load(source)["runs"][0])
        next(iter(run["events"][0]["expectedState"].values()))["archived"] = True
        with patch.object(n, "OUTPUT", n.old_native.OUTPUT):
            with self.assertRaisesRegex(ValueError, "coverage differs"):
                n.verify_run(run, source, n.old_native.BINDINGS)

    def test_run_rejects_unbounded_maximum_before_dispatch(self):
        with patch.object(n, "sim") as sim:
            for maximum in (0, -1, None, True):
                with self.assertRaises(ValueError): n.run(n.c.RUN / "input.json", maximum)
            sim.assert_not_called()

    def test_new_launcher_preserves_replay_but_uses_isolated_paths(self):
        launcher = n.native_build.launcher_text()
        self.assertIn(str(n.c.RUN), launcher)
        self.assertNotIn(str(n.old_native.c.RUN), launcher)
        self.assertIn('appendingPathComponent("AnswerSupportHistory")', launcher)
        self.assertIn("try await HistoryProbe.run", launcher)
        self.assertIn('diagnosticRequire(beneath(output, workspace)', launcher)
        self.assertIn("ANSWER_HISTORY_REPLAY_FINISHED", launcher)

    def test_new_project_sources_and_package_are_isolated_exact_copies(self):
        files = n.native_build.source_files()
        self.assertTrue(all(path.is_relative_to(n.c.RUN) for path in files))
        self.assertFalse(any(".git" in path.parts for path in files))
        for filename in ("HistoryIndex.swift", "HistoryProbe.swift"):
            self.assertEqual(files[n.native_build.PROJECT / "Sources" / filename],
                             (n.old_native.PROJECT / "Sources" / filename).read_bytes())
        project = files[n.native_build.PROJECT / f"{n.native_build.NAME}.xcodeproj/project.pbxproj"].decode()
        self.assertIn(n.native_build.BUNDLE, project)
        self.assertNotIn(n.old_native.BUNDLE, project)
        self.assertIn(str(n.native_build.PACKAGE), project)
        self.assertNotIn(str(n.native_build.original_package()), project)

    def test_known_preexecution_failure_can_be_certified_without_retry(self):
        source = n.c.RUN / "input.json"
        if not source.exists(): self.skipTest("fresh batch unavailable")
        run = n.c.load(source)["runs"][0]
        original_digest = n.c.digest
        def digest(path):
            if Path(path).name == "native-build-v2.json": return "new-build-test-binding"
            if Path(path).parent.name == "native-recoveries": return "recovery-test-binding"
            return original_digest(path)
        with tempfile.TemporaryDirectory() as folder, patch.object(n, "OUTPUT", Path(folder) / "absent"), \
             patch.object(n.c, "digest", side_effect=digest), patch.object(n.c, "publish") as publish:
            digest_value = n.known_preflight_recovery(run, source, dict(bundle=n.BUNDLE))
            self.assertIsNotNone(digest_value)
            record = publish.call_args.args[1]
            self.assertFalse(record["ledgerExecuted"])
            self.assertFalse(record["automaticUnknownRetry"])
            self.assertTrue(record["originalReservationPreserved"])


if __name__ == "__main__": unittest.main()
