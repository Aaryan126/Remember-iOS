"""Mocked v2 generation tests: no compiler, native process, or model execution."""
from contextlib import ExitStack
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import v2_generation as g


class GenerationV2Tests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        self.stack.enter_context(patch.object(g.c, "WORK", root / "work"))
        self.stack.enter_context(patch.object(g.c, "RUN", root / "run"))
        self.stack.enter_context(patch.object(g, "OLD_WORK", root / "old"))
        self.stack.enter_context(patch.object(g, "SOURCE", root / "run/generation-build/AnswerSupportProbe.swift"))
        self.stack.enter_context(patch.object(g, "BINARY", root / "run/generation-build/probe"))
        self.stack.enter_context(patch.object(g.c, "boundary", return_value={}))
        self.stack.enter_context(patch.object(g.c, "verify_frozen", return_value={}))
        self.stack.enter_context(patch.object(g.c, "verify_prior", return_value={}))
        self.runtime = dict(os="fictional test OS", availability="available", contextSize=8192)
        self.build = dict(runtime=self.runtime)
        self.stack.enter_context(patch.object(g, "verify_build", return_value=self.build))
        self.stack.enter_context(patch.object(g, "runtime_identity", return_value=self.runtime))
        g.c.publish(g.c.WORK / "generation-build.json", self.build)
        g.c.publish(g.c.WORK / "frozen.json", dict(test=True))
        prior = g.OLD_WORK / "generation-reservations/control-extract-1.json"
        prior.parent.mkdir(parents=True)
        prior.write_text('{"requestCount":1}')

    def output(self, spec, answer_index=0):
        return dict(verdict=spec["expected"]["verdict"], answer=spec["expected"]["answers"][answer_index],
                    evidence=copy.deepcopy(spec["expected"]["evidence"]))

    def fake_process(self, spec, output=None, missing=False, wrong_runtime=False, refusal=False):
        value = dict(schemaVersion=1, unit=spec["id"], syntheticOnly=True, status="error" if refusal else "ok",
                     output=output or self.output(spec), runtime={} if wrong_runtime else self.runtime,
                     nativeDeadlineSeconds=60, cancellationGraceSeconds=2)
        if refusal: value.update(output=None, error="fictional mocked refusal")
        process = MagicMock()
        process.poll.return_value = process.returncode = 0
        def launch(*args, **kwargs):
            text = "missing terminal\n" if missing else "ANSWER_SUPPORT_RESULT " + json.dumps(value) + "\n"
            kwargs["stdout"].write(text.encode())
            return process
        return launch

    def run_control(self, spec, output=None, **kwargs):
        with patch.object(g.subprocess, "Popen", side_effect=self.fake_process(spec, output, **kwargs)):
            return g.request_control(spec, self.build)

    def test_fresh_four_states_twice(self):
        specs = g.controls_spec()
        self.assertEqual(len(specs), 8)
        self.assertEqual({r["expected"]["verdict"] for r in specs}, g.host_policy.VERDICTS)
        self.assertNotIn("ORBIT-27", json.dumps(specs))
        for row in specs:
            for index in range(len(row["expected"]["answers"])):
                g.host_policy.validate_output(self.output(row, index), row["packet"])
        for i in range(0, 8, 2): self.assertEqual(specs[i]["packet"], specs[i+1]["packet"])

    def test_only_prompt_and_guide_granularity_change(self):
        self.assertEqual(g.instructions().replace(g.NEW_PROMPT_PHRASE, g.OLD_PROMPT_PHRASE), g.old.INSTRUCTIONS)
        self.assertEqual(g.generated_source().replace(g.NEW_GUIDE, g.OLD_GUIDE), g.OLD_SOURCE.read_text())
        self.assertEqual(g.SCHEMA, g.old.SCHEMA)

    def test_compact_and_full_reviewed_source_are_accepted(self):
        spec = g.controls_spec()[0]
        self.assertTrue(g.control_correct(self.output(spec), spec["expected"]))
        self.assertTrue(g.control_correct(self.output(spec, 1), spec["expected"]))

    def test_unapproved_surrounding_text_and_paraphrase_rejected(self):
        spec = g.controls_spec()[0]
        for text in ("code: LARCH-58", "The locker code is LARCH-58.", "LARCH-58.", "LARCH"):
            output = self.output(spec)
            output["answer"] = text
            self.assertFalse(g.control_correct(output, spec["expected"]))

    def test_no_gold_or_answer_forms_enter_native_request(self):
        spec = copy.deepcopy(g.controls_spec()[0])
        spec["packet"]["gold"] = "secret annotation"
        request = g.verified_request(spec, self.build)
        self.assertNotIn("secret annotation", json.dumps(request))
        self.assertNotIn('"answers"', request["packet"])
        self.assertNotIn("expected", request["packet"])

    def test_old_spent_request_counts_in_new_reservation(self):
        spec = g.controls_spec()[0]
        result = self.run_control(spec)
        reservation = g.c.load(g.c.WORK / "generation-reservations" / (spec["id"] + ".json"))
        self.assertTrue(result["passed"])
        self.assertEqual(reservation["priorReservations"], 1)
        self.assertEqual(reservation["cumulativeReservations"], 2)

    def test_global_145_cap(self):
        for i in range(144):
            (g.OLD_WORK / "generation-reservations" / f"historic-{i}.json").write_text("{}")
        with patch.object(g.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "145 cumulative"): g.request_control(g.controls_spec()[0], self.build)
            popen.assert_not_called()

    def test_checkpoint_eight_cap(self):
        for i in range(8): g.c.publish(g.c.WORK / "generation-reservations" / f"prior-{i}.json", {})
        with self.assertRaisesRegex(ValueError, "eight v2"): g.request_control(g.controls_spec()[0], self.build)

    def test_unknown_reservation_never_retried(self):
        spec = g.controls_spec()[0]
        g.c.publish(g.c.WORK / "generation-reservations" / (spec["id"] + ".json"), {})
        with patch.object(g.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "unresolved v2 generation"): g.request_control(spec, self.build)
            popen.assert_not_called()

    def test_benchmark_and_modified_control_refused(self):
        for alteration in (dict(id="evaluation-eval01-q1"), dict(packet={})):
            spec = copy.deepcopy(g.controls_spec()[0])
            spec.update(alteration)
            with patch.object(g.subprocess, "Popen") as popen:
                with self.assertRaisesRegex(ValueError, "eight frozen fresh controls"): g.request_control(spec, self.build)
                popen.assert_not_called()

    def test_out_of_order_request_refused(self):
        with self.assertRaisesRegex(ValueError, "frozen order"):
            g.request_control(g.controls_spec()[1], self.build)

    def test_saved_unit_reused_without_dispatch(self):
        spec = g.controls_spec()[0]
        first = self.run_control(spec)
        with patch.object(g.subprocess, "Popen") as popen:
            self.assertEqual(first, g.request_control(spec, self.build))
            popen.assert_not_called()

    def test_raw_tamper_rejected_on_resume(self):
        spec = g.controls_spec()[0]
        self.run_control(spec)
        raw = g.c.RUN / "generation-raw" / (spec["id"] + ".log")
        raw.write_text(raw.read_text() + "changed")
        with self.assertRaisesRegex(ValueError, "raw/input/reservation changed"):
            g.request_control(spec, self.build)

    def test_valid_different_repeat_form_fails_repeat_gate(self):
        first, second = g.controls_spec()[:2]
        self.run_control(first)
        result = self.run_control(second, self.output(second, 1))
        self.assertTrue(result["contentPassed"])
        self.assertFalse(result["repeatMatched"])
        self.assertFalse(result["passed"])
        self.assertEqual(g.verify_unit(second, self.build), result)
        with patch.object(g.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "earlier v2 control failed"):
                g.request_control(g.controls_spec()[2], self.build)
            popen.assert_not_called()

    def test_failed_first_control_stops_controls_loop(self):
        spec = g.controls_spec()[0]
        output = self.output(spec)
        output["answer"] = "invented"
        self.run_control(spec, output)
        with patch.object(g.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "neutral control failed"): g.controls()
            popen.assert_not_called()

    def test_missing_terminal_saved_as_spent_unknown(self):
        spec = g.controls_spec()[0]
        result = self.run_control(spec, missing=True)
        self.assertFalse(result["passed"])
        self.assertFalse(result["executionKnown"])
        self.assertEqual(result["requestCount"], 1)
        self.assertEqual(g.verify_unit(spec, self.build), result)

    def test_runtime_mismatch_is_error(self):
        result = self.run_control(g.controls_spec()[0], wrong_runtime=True)
        self.assertFalse(result["passed"])
        self.assertIsNotNone(result["validationError"])

    def test_native_refusal_is_error_not_successful_abstention(self):
        spec = g.controls_spec()[0]
        row = self.run_control(spec, refusal=True)
        self.assertFalse(row["passed"])
        self.assertTrue(row["executionKnown"])
        self.assertIsNone(row["output"])
        self.assertIsNotNone(row["validationError"])
        self.assertEqual(g.verify_unit(spec, self.build), row)

    def test_malformed_terminal_is_classified_without_repair(self):
        spec = g.controls_spec()[0]
        for raw in ("ANSWER_SUPPORT_RESULT []", "ANSWER_SUPPORT_RESULT not-json", ""):
            terminal, error = g.interpret(raw, spec, self.runtime)
            self.assertIsNone(terminal)
            self.assertIsNotNone(error)
        value = dict(schemaVersion=1, unit=spec["id"], syntheticOnly=True, status="ok", runtime=self.runtime,
                     nativeDeadlineSeconds=60, cancellationGraceSeconds=2)
        terminal, error = g.interpret("ANSWER_SUPPORT_RESULT " + json.dumps(value), spec, self.runtime)
        self.assertEqual(terminal, value)
        self.assertIsNotNone(error)

    def test_host_timeout_spends_request_stops_process_and_never_retries(self):
        spec = g.controls_spec()[0]
        process, state = MagicMock(), dict(stopped=False)
        process.poll.side_effect = lambda: 0 if state["stopped"] else None
        process.returncode = None
        def stopped(owned):
            self.assertIs(owned, process)
            state["stopped"] = True
            process.returncode = -15
        with patch.object(g.subprocess, "Popen", return_value=process), \
             patch.object(g, "stop_group", side_effect=stopped) as stop, \
             patch.object(g.time, "sleep"), patch.object(g.time, "monotonic", side_effect=[0, 76]):
            with self.assertRaises(TimeoutError): g.request_control(spec, self.build)
            stop.assert_called_once()
        row = g.verify_unit(spec, self.build)
        self.assertFalse(row["passed"])
        self.assertEqual(row["failure"]["type"], "TimeoutError")
        self.assertTrue(row["hostProcessExited"])
        self.assertEqual(row["requestCount"], 1)
        with patch.object(g.subprocess, "Popen") as popen:
            self.assertEqual(row, g.request_control(spec, self.build))
            popen.assert_not_called()

    def test_saved_error_and_request_count_are_recomputed(self):
        spec = g.controls_spec()[0]
        self.run_control(spec, missing=True)
        path = g.c.WORK / "generation-units" / (spec["id"] + ".json")
        original = g.c.load(path)
        for change in (dict(requestCount=2), dict(validationError=None)):
            value = copy.deepcopy(original)
            value["payload"].update(change)
            value["payloadSHA256"] = g.sha(value["payload"])
            path.write_bytes(g.c.encoded(value))
            with self.assertRaisesRegex(ValueError, "error/count/identity"):
                g.verify_unit(spec, self.build)

    def test_pause_before_dispatch_spends_nothing_new(self):
        with patch.object(g.c, "boundary", side_effect=g.c.Paused("test")):
            with self.assertRaises(g.c.Paused): g.request_control(g.controls_spec()[0], self.build)
        self.assertFalse((g.c.WORK / "generation-reservations").exists())

    def test_all_eight_verified_and_nine_cumulative(self):
        for spec in g.controls_spec(): self.run_control(spec)
        report = g.verify_controls()
        self.assertTrue(report["qualified"])
        self.assertEqual(report["cumulativeReservations"], 9)
        self.assertEqual(report["supportedAnswerLengths"], [8, 8])
        self.assertFalse(report["stageBAllowed"])

    def test_build_reserves_before_compile_and_rejects_source_drift(self):
        with patch.object(g.c, "WORK", g.c.WORK / "fresh"), \
             patch.object(g, "source_bindings", side_effect=[{"code": "before"}, {"code": "after"}]):
            (g.OLD_WORK / "generation-build.json").write_text("{}")
            def compiled(command):
                self.assertTrue((g.c.WORK / "generation-build-reserved.json").exists())
                g.BINARY.write_bytes(b"mock-only-not-executable")
                return "mocked"
            with patch.object(g, "compile_request", side_effect=compiled):
                with self.assertRaisesRegex(ValueError, "changed during compile"): g.build()
            self.assertFalse((g.c.WORK / "generation-build.json").exists())

    def test_unresolved_build_never_retried(self):
        with patch.object(g.c, "WORK", g.c.WORK / "fresh"):
            g.c.publish(g.c.WORK / "generation-build-reserved.json", {})
            with patch.object(g, "compile_request") as compile_request:
                with self.assertRaisesRegex(ValueError, "unresolved v2 build"): g.build()
                compile_request.assert_not_called()


if __name__ == "__main__": unittest.main()
