"""Deterministic generation orchestration tests; never compile or invoke a model."""
from contextlib import ExitStack
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import as_generation as g


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        self.stack.enter_context(patch.object(g.c, "WORK", root / "work"))
        self.stack.enter_context(patch.object(g.c, "RUN", root / "run"))
        self.stack.enter_context(patch.object(g.c, "boundary", return_value={}))
        self.runtime = dict(os="fictional test OS", availability="available", contextSize=8192)
        self.build = dict(runtime=self.runtime)
        g.c.publish(g.c.WORK / "generation-build.json", self.build)

    def fake_process(self, spec, output=None, missing_terminal=False):
        value = dict(schemaVersion=1, unit=spec["id"], syntheticOnly=True, status="ok",
                     output=output or spec["expected"], runtime=self.runtime,
                     nativeDeadlineSeconds=60, cancellationGraceSeconds=2)
        process = MagicMock()
        process.poll.return_value = process.returncode = 0
        def launch(*args, **kwargs):
            text = "no terminal\n" if missing_terminal else "ANSWER_SUPPORT_RESULT " + json.dumps(value) + "\n"
            kwargs["stdout"].write(text.encode())
            return process
        return launch

    def test_four_states_twice_exact_gold(self):
        specs = g.controls_spec()
        self.assertEqual(len(specs), 8)
        self.assertEqual({r["expected"]["verdict"] for r in specs}, g.policy.VERDICTS)
        for row in specs: g.policy.validate_output(row["expected"], row["packet"])
        for index in range(0, 8, 2):
            self.assertEqual(specs[index]["packet"], specs[index+1]["packet"])

    def test_packet_strips_labels_scores_and_future(self):
        packet = copy.deepcopy(g.controls_spec()[0]["packet"])
        packet.update(gold="secret", category="supported", futureEvents=["future"])
        packet["candidates"][0].update(score=1, expectedAnswer="secret")
        encoded = json.dumps(g.model_packet(packet))
        self.assertNotIn("secret", encoded)
        self.assertNotIn("score", encoded)
        self.assertNotIn("future", encoded)
        self.assertNotIn("sourceId", encoded)
        self.assertNotIn("s01", encoded)

    def test_packet_keeps_native_opaque_version_provenance(self):
        packet = copy.deepcopy(g.controls_spec()[0]["packet"])
        row = packet["candidates"][0]
        for field in ("sourceID", "versionID", "snapshotID"):
            row[field] = "E640A5D5-1C68-4F46-95D4-7773CFF36B35"
        result = g.model_packet(packet)["candidates"][0]
        self.assertEqual(result["sourceID"], row["sourceID"])
        self.assertNotIn("sourceId", result)

    def test_packet_rejects_bad_provenance_types_and_missing_version(self):
        mutations = ({"revision": True}, {"revision": -1}, {"revision": 17},
                     {"isArchived": "false"}, {"isCurrentVersion": 1},
                     {"versionID": "s01"}, {"sourceID": "E640A5D5-1C68-4F46-95D4-7773CFF36B35"},
                     {"locatorAvailability": "invented-media-location"}, {"id": []})
        for fields in mutations:
            with self.subTest(fields=fields):
                packet = copy.deepcopy(g.controls_spec()[0]["packet"])
                packet["candidates"][0].update(fields)
                with self.assertRaises(ValueError): g.model_packet(packet)

    def test_current_packet_rejects_history(self):
        for fields in ({"isArchived": True}, {"isCurrentVersion": False}):
            packet = copy.deepcopy(g.controls_spec()[0]["packet"])
            packet["candidates"][0].update(fields)
            with self.assertRaisesRegex(ValueError, "historical evidence"): g.model_packet(packet)

    def test_packet_rejects_oversize_not_truncates(self):
        packet = copy.deepcopy(g.controls_spec()[0]["packet"])
        packet["candidates"][0]["quote"] = "x" * 801
        with self.assertRaisesRegex(ValueError, "no silent truncation"): g.model_packet(packet)

    def test_packet_rejects_extra_candidates(self):
        packet = copy.deepcopy(g.controls_spec()[0]["packet"])
        packet["candidates"] *= 4
        with self.assertRaises(ValueError): g.model_packet(packet)

    def test_stage_a_rejects_benchmark_unit(self):
        spec = copy.deepcopy(g.controls_spec()[0])
        spec["id"] = "development-dev01-q1"
        with patch.object(g.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "eight frozen neutral"): g.request_control(spec, self.build)
            popen.assert_not_called()

    def test_stage_a_rejects_changed_control(self):
        spec = copy.deepcopy(g.controls_spec()[0])
        spec["packet"]["question"] = "Changed question"
        with self.assertRaises(ValueError): g.request_control(spec, self.build)

    def test_global_reservation_limit(self):
        for i in range(144): g.c.publish(g.c.WORK / "generation-reservations" / f"prior-{i}.json", {})
        with self.assertRaisesRegex(ValueError, "144 generation"): g.request_control(g.controls_spec()[0], self.build)

    def test_stage_a_reservation_limit(self):
        for i in range(8): g.c.publish(g.c.WORK / "generation-reservations" / f"control-old-{i}.json", {})
        with self.assertRaisesRegex(ValueError, "eight Stage A"): g.request_control(g.controls_spec()[0], self.build)

    def test_unknown_reservation_is_not_retried(self):
        spec = g.controls_spec()[0]
        g.c.publish(g.c.WORK / "generation-reservations" / (spec["id"] + ".json"), {})
        with patch.object(g.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "unresolved generation"): g.request_control(spec, self.build)
            popen.assert_not_called()

    def test_completed_success_reused_without_inference(self):
        spec = g.controls_spec()[0]
        with patch.object(g.subprocess, "Popen", side_effect=self.fake_process(spec)) as popen:
            first = g.request_control(spec, self.build)
            second = g.request_control(spec, self.build)
            self.assertEqual(popen.call_count, 1)
        self.assertTrue(first["passed"])
        self.assertEqual(first, second)
        self.assertTrue(first["hostProcessExited"])

    def test_invalid_quote_remains_error(self):
        spec = g.controls_spec()[0]
        output = copy.deepcopy(spec["expected"])
        output["evidence"][0]["quote"] = "Invented quote."
        with patch.object(g.subprocess, "Popen", side_effect=self.fake_process(spec, output)):
            result = g.request_control(spec, self.build)
        self.assertFalse(result["passed"])
        self.assertIsNotNone(result["validationError"])
        self.assertEqual(result["output"], output)

    def test_missing_terminal_saved_as_unknown(self):
        spec = g.controls_spec()[0]
        with patch.object(g.subprocess, "Popen", side_effect=self.fake_process(spec, missing_terminal=True)):
            result = g.request_control(spec, self.build)
        self.assertFalse(result["passed"])
        self.assertFalse(result["executionKnown"])
        self.assertEqual(result["requestCount"], 1)

    def test_pause_before_dispatch_spends_no_request(self):
        with patch.object(g.c, "boundary", side_effect=g.c.Paused("test")):
            with self.assertRaises(g.c.Paused): g.request_control(g.controls_spec()[0], self.build)
        self.assertFalse((g.c.WORK / "generation-reservations").exists())

    def test_failed_control_stops_before_next_request(self):
        with patch.object(g, "verify_build", return_value=self.build), patch.object(g, "request_control",
             return_value=dict(passed=False)) as request:
            with self.assertRaisesRegex(ValueError, "neutral control failed"): g.controls()
            self.assertEqual(request.call_count, 1)

    def test_runtime_mismatch_is_not_accepted(self):
        spec = g.controls_spec()[0]
        value = dict(schemaVersion=1, unit=spec["id"], syntheticOnly=True, status="ok", runtime={},
                     nativeDeadlineSeconds=60, cancellationGraceSeconds=2)
        with self.assertRaisesRegex(ValueError, "runtime mismatch"):
            g.parse_terminal("ANSWER_SUPPORT_RESULT " + json.dumps(value), spec["id"], self.runtime)

    def test_duplicate_terminal_is_error(self):
        with self.assertRaisesRegex(ValueError, "duplicate terminal"):
            g.parse_terminal("ANSWER_SUPPORT_RESULT {}\nANSWER_SUPPORT_RESULT {}", "control", self.runtime)

    def test_build_snapshots_sources_before_compile_and_rejects_change(self):
        # Use an absent receipt path by choosing a separate temporary work folder.
        with patch.object(g.c, "WORK", g.c.WORK / "fresh"), patch.object(g, "BINARY", g.c.RUN / "fake-build/probe"), \
             patch.object(g, "runtime_identity", return_value=self.runtime), \
             patch.object(g, "source_bindings", side_effect=[{"source": "before"}, {"source": "after"}]):
            g.c.publish(g.c.WORK / "mac-readiness.json", dict(test=True))
            def compile_fake(*args, **kwargs):
                self.assertTrue((g.c.WORK / "generation-build-reserved.json").exists())
                g.BINARY.write_bytes(b"test-only-not-executable")
                return "mocked compile"
            with patch.object(g.native, "execute", side_effect=compile_fake):
                with self.assertRaisesRegex(ValueError, "changed during compilation"): g.build()
            self.assertFalse((g.c.WORK / "generation-build.json").exists())

    def test_unresolved_build_not_retried(self):
        with patch.object(g.c, "WORK", g.c.WORK / "fresh"), patch.object(g, "BINARY", g.c.RUN / "fake-build/probe"), \
             patch.object(g.native, "execute") as execute:
            g.c.publish(g.c.WORK / "generation-build-reserved.json", {})
            with self.assertRaisesRegex(ValueError, "unresolved generation build"): g.build()
            execute.assert_not_called()


if __name__ == "__main__": unittest.main()
