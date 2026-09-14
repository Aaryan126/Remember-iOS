import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pilot as p


def packet():
    return {"queryID": "q" + "a" * 24, "view": "pair", "pair": ["x", "y"],
        "sources": [{"id": "x", "text": "The orchard census begins."}, {"id": "y", "text": "The same orchard census continues."}]}


def response():
    output = {"verdict": "same_project", "rationale": "Both concern the census.",
        "evidence": [{"sourceID": s["id"], "quote": s["text"]} for s in packet()["sources"]]}
    return {"httpStatus": 200, "elapsedSeconds": 1,
        "body": {"model": p.MODEL, "service_tier": "default", "store": False, "status": "completed",
            "usage": {"input_tokens": 1000, "output_tokens": 500, "input_tokens_details": {"cached_tokens": 0}},
            "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(output)}]}]}}


class PilotTests(unittest.TestCase):
    def test_request_boundaries_and_no_gold(self):
        request = p.request(packet())
        self.assertEqual(request["model"], p.MODEL)
        self.assertFalse(request["store"])
        self.assertEqual(request["tools"], [])
        self.assertEqual(request["max_output_tokens"], 2000)
        self.assertEqual(set(json.loads(request["input"])), {"pair", "sources"})
        dirty = packet(); dirty["gold"] = "same_project"
        with self.assertRaises(ValueError): p.request(dirty)

    def test_no_truncation(self):
        dirty = packet(); dirty["sources"][0]["text"] = "z" * 5000
        with self.assertRaises(ValueError): p.request(dirty)

    def test_corpus_fits_and_deduplicates(self):
        data = p.historical.catalogue()
        self.assertEqual(len(data["contexts"]), 112)
        self.assertEqual(len(data["mapping"]), 160)
        for item in data["contexts"].values():
            self.assertEqual(len(json.loads(p.request(item)["input"])["sources"]), len(item["sources"]))

    def test_valid_response(self):
        self.assertEqual(p.interpret(packet(), response())["prediction"]["verdict"], "same_project")

    def test_invalid_quotes_are_errors(self):
        value = response()
        content = value["body"]["output"][0]["content"][0]
        output = json.loads(content["text"]); output["evidence"][0]["quote"] = "Invented evidence"
        content["text"] = json.dumps(output)
        self.assertEqual(p.interpret(packet(), value)["status"], "error")

    def test_incomplete_refusal_and_model_tier_mismatch(self):
        for key, value in (("status", "incomplete"), ("model", "gpt-5.5"), ("service_tier", "priority"), ("store", True)):
            result = response(); result["body"][key] = value
            self.assertEqual(p.interpret(packet(), result)["status"], "error")
        result = response(); result["body"]["output"][0]["content"] = [{"type": "refusal", "refusal": "No"}]
        self.assertEqual(p.interpret(packet(), result)["status"], "error")

    def test_budget_includes_reasoning_once_and_cached_discount(self):
        body = response()["body"]
        body["usage"]["output_tokens_details"] = {"reasoning_tokens": 400}
        self.assertEqual(p.usage_cost(body), 10_000_000)
        body["usage"]["input_tokens_details"]["cached_tokens"] = 500
        self.assertEqual(p.usage_cost(body), 8_875_000)
        body["usage"]["output_tokens"] = 2001
        with self.assertRaises(ValueError): p.usage_cost(body)

    def test_usage_rejects_missing_negative_and_boolean(self):
        self.assertIsNone(p.usage_cost({}))
        for value in (-1, True, "100", None):
            body = response()["body"]; body["usage"]["input_tokens"] = value
            with self.assertRaises(ValueError): p.usage_cost(body)

    def test_reservation_prevents_overspend_and_unknown_is_not_free(self):
        with tempfile.TemporaryDirectory(prefix="cloud-pilot-test-") as directory, patch.object(p, "RUN", Path(directory)):
            p.reserve("first", {"test": True})
            self.assertEqual(p.budget()["accountedNanoUSD"], p.RESERVE_NANO)
            self.assertEqual(p.budget()["unresolvedCalls"], 1)
            with patch.object(p, "CAP_NANO", p.RESERVE_NANO):
                with self.assertRaises(ValueError): p.reserve("second", {})
            with patch.object(p, "MAX_CALLS", 1):
                with self.assertRaises(ValueError): p.reserve("second", {})

    def test_resume_uses_saved_response_without_network_or_rewrite(self):
        with tempfile.TemporaryDirectory(prefix="cloud-pilot-test-") as directory, patch.object(p, "RUN", Path(directory)), \
             patch.object(p, "verify"), patch.object(p, "boundary"), patch.object(p, "transport") as network:
            key = p.historical.context_key(packet())
            p.c.publish(p.RUN / "manifest.json", {"test": True})
            p.c.publish(p.RUN / "catalogue.json", {"contexts": {key: packet()}, "mapping": {}})
            reserved = p.reserve(key, p.request(packet()))
            wire = response(); p.c.unit(reserved / "result.json", {"wire": wire, "outcome": p.interpret(packet(), wire)})
            p.predict()
            path = p.RUN / f"units/{key}.json"; before = (p.c.digest(path), path.stat().st_mtime_ns)
            p.predict()
            self.assertEqual((p.c.digest(path), path.stat().st_mtime_ns), before)
            network.assert_not_called()

    def test_interrupted_request_is_error_never_resent(self):
        with tempfile.TemporaryDirectory(prefix="cloud-pilot-test-") as directory, patch.object(p, "RUN", Path(directory)), \
             patch.object(p, "verify"), patch.object(p, "boundary"), patch.object(p, "transport") as network:
            key = p.historical.context_key(packet())
            p.c.publish(p.RUN / "manifest.json", {"test": True})
            p.c.publish(p.RUN / "catalogue.json", {"contexts": {key: packet()}, "mapping": {}})
            p.reserve(key, p.request(packet()))
            p.predict()
            outcome = p.c.read_unit(p.RUN / f"units/{key}.json")["outcome"]
            self.assertEqual(outcome["errorKind"], "interrupted-unknown-billing")
            self.assertEqual(p.budget()["accountedNanoUSD"], p.RESERVE_NANO)
            network.assert_not_called()

    def test_pause_boundary(self):
        with tempfile.TemporaryDirectory(prefix="cloud-pilot-test-") as directory, patch.object(p, "RUN", Path(directory)):
            p.c.publish(p.RUN / "pause.request", {"test": True})
            with self.assertRaises(p.c.Paused): p.boundary()

    def test_immutable_receipts(self):
        with tempfile.TemporaryDirectory(prefix="cloud-pilot-test-") as directory:
            path = Path(directory) / "one.json"
            p.c.publish(path, {"a": 1}); p.c.publish(path, {"a": 1})
            with self.assertRaises(ValueError): p.c.publish(path, {"a": 2})

    def test_confirmation_does_not_invent_positive_matches(self):
        cloud = p.interpret(packet(), response())
        legacy = {"queryID": packet()["queryID"], "verdict": "abstain", "evidence": []}
        self.assertEqual(p.historical.combine(legacy, cloud, "confirm")["prediction"]["verdict"], "abstain")
        self.assertEqual(p.historical.combine(legacy, cloud, "veto")["prediction"]["verdict"], "abstain")


if __name__ == "__main__":
    unittest.main()
