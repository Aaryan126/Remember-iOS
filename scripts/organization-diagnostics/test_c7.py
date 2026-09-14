import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import c2_common as c
import c7_run as run


def packet():
    return {"queryID": "q" + "a" * 24, "view": "pair", "pair": ["x", "y"],
            "sources": [{"id": "x", "text": "The orchard census has begun."},
                        {"id": "y", "text": "The orchard census continues."}]}


def output(verdict="same_project"):
    return {"verdict": verdict, "rationale": "Both concern the census.", "evidence": [] if verdict == "abstain" else
            [{"sourceID": s["id"], "quote": s["text"]} for s in packet()["sources"]]}


def raw(value=None):
    return {"returnCode": 0, "timedOut": False, "stdout": json.dumps({"status": "ok", "availability": "available",
            "output": value if value is not None else output()}), "stderr": ""}


def prediction(verdict="same_project"):
    return run.validate_output(packet(), output(verdict))


def labeled(verdict):
    return {"queryID": packet()["queryID"], "verdict": verdict, "family": "fixture",
            "partition": "diagnostic", "behavior": "fixture", "episode": "fixture"}


class NativeContractTests(unittest.TestCase):
    def test_valid_decision_and_abstention(self):
        for verdict in ("same_project", "separate_projects", "abstain"):
            result = run.interpret(packet(), raw(output(verdict)))
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["prediction"]["verdict"], verdict)

    def test_no_labels_or_view_in_request(self):
        p = packet()
        sent = json.loads(run.request(p)["packet"])
        self.assertEqual(set(sent), {"pair", "sources"})
        self.assertEqual(sent["sources"], p["sources"])
        p["gold"] = "same_project"
        with self.assertRaises(ValueError):
            run.request(p)

    def test_context_preserved_and_exact_dedup(self):
        p = packet()
        q = copy.deepcopy(p); q["queryID"] = "q" + "b" * 24; q["view"] = "context"
        self.assertEqual(run.context_key(p), run.context_key(q))
        q["sources"].append({"id": "z", "text": "A separate visible clarification."})
        self.assertNotEqual(run.context_key(p), run.context_key(q))
        self.assertEqual(len(json.loads(run.request(q)["packet"])["sources"]), 3)

    def test_no_silent_truncation(self):
        p = packet(); p["sources"][0]["text"] = "x" * 16_001
        with self.assertRaisesRegex(ValueError, "truncation"):
            run.request(p)

    def test_invented_quote_is_error_not_abstention(self):
        value = output(); value["evidence"][0]["quote"] = "Invented evidence"
        result = run.interpret(packet(), raw(value))
        self.assertEqual(result["errorKind"], "invalid-output")
        self.assertIsNone(result["prediction"])

    def test_invisible_source_and_one_sided_evidence_fail(self):
        for variant in ("invisible", "one-sided"):
            value = output()
            if variant == "invisible":
                value["evidence"][1]["sourceID"] = "z"
            else:
                value["evidence"] = value["evidence"][:1]
            self.assertEqual(run.interpret(packet(), raw(value))["status"], "error")

    def test_context_citations_do_not_replace_endpoint(self):
        p = packet(); p["view"] = "context"; p["sources"].append({"id": "z", "text": "Context."})
        value = output(); value["evidence"][1] = {"sourceID": "z", "quote": "Context."}
        with self.assertRaisesRegex(ValueError, "both queried"):
            run.validate_output(p, value)

    def test_malformed_outputs_are_errors(self):
        for value in ([], {}, {**output(), "verdict": "probably"}, {**output(), "rationale": ""},
                      {**output(), "extra": True}, {**output(), "evidence": [output()["evidence"][0]] * 5}):
            self.assertEqual(run.interpret(packet(), raw(value))["status"], "error")
        value = raw(); value["stdout"] = "not json"
        self.assertEqual(run.interpret(packet(), value)["status"], "error")

    def test_refusal_unavailability_and_crash_remain_errors(self):
        for state in ("unavailable", "error"):
            value = raw(); value["stdout"] = json.dumps({"status": state})
            self.assertEqual(run.interpret(packet(), value)["errorKind"], "model:" + state)
        value = raw(); value["returnCode"] = 1
        self.assertEqual(run.interpret(packet(), value)["errorKind"], "process")

    def test_timeout_is_saved_without_retry(self):
        with patch.object(run.subprocess, "run", side_effect=subprocess.TimeoutExpired("fixture", 60, output=b"partial")) as mocked:
            result = run.invoke(packet())
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(result["outcome"]["errorKind"], "timeout")
        self.assertEqual(result["raw"]["stdout"], "partial")


class CombinationTests(unittest.TestCase):
    def test_explicit_conflict_overrides_both_modes(self):
        local = {"status": "ok", "prediction": prediction("separate_projects")}
        for mode in ("veto", "confirm"):
            self.assertEqual(run.combine(prediction(), local, mode)["prediction"]["verdict"], "separate_projects")

    def test_confirmation_requires_both_same(self):
        for legacy in ("same_project", "abstain"):
            for local in ("same_project", "abstain"):
                result = run.combine(prediction(legacy), {"status": "ok", "prediction": prediction(local)}, "confirm")
                self.assertEqual(result["prediction"]["verdict"], "same_project" if legacy == local == "same_project" else "abstain")

    def test_veto_preserves_legacy_on_uncertainty(self):
        result = run.combine(prediction(), {"status": "ok", "prediction": prediction("abstain")}, "veto")
        self.assertEqual(result["prediction"]["verdict"], "same_project")

    def test_errors_do_not_silently_fall_back(self):
        for mode in ("veto", "confirm"):
            result = run.combine(prediction(), {"status": "error", "errorKind": "timeout", "prediction": None}, mode)
            self.assertEqual(result["status"], "error")
            self.assertIsNone(result["prediction"])


class MetricsTests(unittest.TestCase):
    def test_errors_stay_in_denominators(self):
        rows = [{"queryID": packet()["queryID"], "status": "error", "errorKind": "timeout", "prediction": None}]
        for target in ("same_project", "separate_projects", "abstain"):
            result = run.metrics([packet()], [labeled(target)], rows)["all"]
            self.assertEqual(result["errorRate"]["value"], 1)
            self.assertEqual(result["correctness"]["value"], 0)
            self.assertEqual(result["counts"]["abstained"], 0)
            self.assertIsNone(result["samePrecision"]["value"])

    def test_unsupported_assertions_reduce_precision(self):
        result = run.metrics([packet()], [labeled("abstain")], [{"queryID": packet()["queryID"], "status": "ok", "prediction": prediction()}])["all"]
        self.assertEqual(result["samePrecision"]["value"], 0)
        self.assertEqual(result["unsupportedAssertionRate"]["value"], 1)

    def test_missing_and_duplicate_predictions_fail(self):
        row = {"queryID": packet()["queryID"], "status": "ok", "prediction": prediction()}
        for rows in ([], [row, row]):
            with self.assertRaisesRegex(ValueError, "inventory"):
                run.metrics([packet()], [labeled("same_project")], rows)

    def test_gate_requires_every_condition_and_defined_rates(self):
        values = {"conflictPrecision": .90, "conflictRecall": .80, "sameRecall": .75,
                  "unsupportedAssertionRate": .10, "errorRate": .05}
        data = {"view:context": {k: {"value": v} for k, v in values.items()}}
        self.assertTrue(run.exploration_gate(data)["passed"])
        for key in values:
            altered = copy.deepcopy(data); altered["view:context"][key]["value"] = None
            self.assertFalse(run.exploration_gate(altered)["passed"])


class RecoveryTests(unittest.TestCase):
    def test_pause_resume_ack(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(run, "RUN", Path(directory)), patch.object(c, "space", return_value={}):
            self.assertFalse(run.pause()["safeToClose"])
            with run.worker():
                with self.assertRaises(c.Paused):
                    run.boundary("fixture")
            with run.worker(resume=True):
                run.boundary("resumed")

    def test_saved_unit_resume_and_timestamp_proof(self):
        p = packet(); key = run.context_key(p)
        with tempfile.TemporaryDirectory() as directory, patch.object(run, "RUN", Path(directory)), \
             patch.object(run, "verify_manifest"), patch.object(run, "boundary"), patch.object(run, "invoke") as invoke:
            root = Path(directory)
            c.publish(root / "catalogue.json", {"contexts": {key: p}, "mapping": {p["queryID"]: key}})
            c.publish(root / "manifest.json", {})
            c.unit(root / f"units/{key}.json", {"fixture": True})
            run.proof_before()
            self.assertTrue(run.predict()["outcomesComplete"])
            invoke.assert_not_called()
            self.assertTrue(run.proof_after()["resumeVerified"])

    def test_three_errors_save_before_pause(self):
        contexts = {}
        for i in range(3):
            p = packet(); p["sources"][0]["text"] += str(i)
            contexts[run.context_key(p)] = p
        error = {"raw": {"elapsedSeconds": 0}, "outcome": {"status": "error", "errorKind": "fixture", "prediction": None}}
        with tempfile.TemporaryDirectory() as directory, patch.object(run, "RUN", Path(directory)), \
             patch.object(run, "verify_manifest"), patch.object(c, "space", return_value={}), \
             patch.object(run, "invoke", return_value=error), patch.object(c, "log"):
            c.publish(Path(directory) / "catalogue.json", {"contexts": contexts})
            with self.assertRaises(c.Paused):
                run.predict()
            self.assertEqual(len(list((Path(directory) / "units").glob("*.json"))), 3)
            self.assertTrue((Path(directory) / "control/pause-requested.json").exists())


if __name__ == "__main__":
    unittest.main()
