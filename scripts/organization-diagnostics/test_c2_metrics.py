import copy
import unittest

import c2_metrics as m
from test_c2_policy import capture, pair, run


def gold_for(trace, assignments):
    prefixes = []
    for event, labels in zip(trace["events"], assignments):
        state = copy.deepcopy(event["expectedState"])
        for source_id, projects in labels.items():
            state[source_id]["memberships"] = projects
        prefixes.append({"after": event["id"], "state": state})
    return {"story": trace["story"], "order": trace["order"], "prefixes": prefixes}


class MetricTests(unittest.TestCase):
    def test_known_pair_false_and_missed_attachment_counts(self):
        trace = run([capture("a"), capture("b"), capture("c")], {("b", "a"): pair(1)}, "hybrid-strongest-17")
        gold = gold_for(trace, [{"a": ["p1"]}, {"a": ["p1"], "b": ["p2"]},
                                {"a": ["p1"], "b": ["p2"], "c": ["p1"]}])
        result = m.score_trace(trace, gold)
        self.assertEqual(result["counts"]["falseAttachmentEvents"], 1)
        self.assertEqual(result["counts"]["missedAttachmentEvents"], 1)
        self.assertEqual(result["rates"]["falseAttachments"]["denominator"], 2)
        self.assertEqual(result["rates"]["missedAttachments"]["denominator"], 1)
        self.assertEqual(result["final"]["pairs"]["falsePositive"], 1)
        self.assertEqual(result["final"]["pairs"]["falseNegative"], 1)
        self.assertEqual(result["final"]["structure"]["projectClusterCounts"], {"p1": 2, "p2": 1})
        self.assertEqual(result["final"]["structure"]["mixedClusters"]["numerator"], 1)
        self.assertEqual(result["rates"]["retrievalSharedCoverage"]["value"], 1)

    def test_bridge_is_not_transitive_and_is_not_itself_mixing(self):
        events = [capture("a"), capture("b"), capture("bridge"),
                  {"id": "bridge-links", "kind": "correct", "target": "bridge", "targetAnchors": ["a", "b"]}]
        trace = run(events)
        labels = [{"a": ["p1"]}, {"a": ["p1"], "b": ["p2"]}]
        labels.extend([{**labels[-1], "bridge": ["p1", "p2"]}] * 2)
        result = m.score_trace(trace, gold_for(trace, labels))
        self.assertEqual(result["final"]["pairs"]["truePositive"], 2)
        self.assertEqual(result["final"]["pairs"]["trueNegative"], 1)
        self.assertEqual(result["final"]["pairs"]["precision"]["value"], 1)
        self.assertEqual(result["final"]["structure"]["mixedClusters"]["numerator"], 0)
        # Literal occupied runtime clusters are reported even when occupancy comes
        # from a valid bridge; this diagnostic is not an equivalence-class score.
        self.assertEqual(result["final"]["structure"]["projectClusterCounts"], {"p1": 2, "p2": 2})

    def test_uncertain_truth_never_becomes_negative(self):
        trace = run([capture("a"), capture("unknown"), capture("b")],
                    {("unknown", "a"): pair(1), ("b", "a"): pair(1)}, "hybrid-strongest-17")
        labels = [{"a": ["p1"]}, {"a": ["p1"], "unknown": []}, {"a": ["p1"], "unknown": [], "b": ["p1"]}]
        result = m.score_trace(trace, gold_for(trace, labels))
        self.assertEqual(result["counts"]["falseAttachmentEvents"], 0)
        self.assertEqual(result["counts"]["uncertainCaptureEvents"], 1)
        self.assertEqual(result["counts"]["uncertainCaptureJoinedEvents"], 1)
        self.assertEqual(result["final"]["pairs"]["knownPairs"], 1)
        self.assertEqual(result["final"]["pairs"]["uncertainJoinedPairs"], 2)

    def test_correction_recovery_uses_current_truth_and_archive_filter(self):
        events = [capture("a"), capture("b"), capture("c"),
                  {"id": "correct-c", "kind": "correct", "target": "c", "targetAnchors": ["b"]},
                  {"id": "archive-b", "kind": "archive", "target": "b"},
                  {"id": "revise-c", "kind": "revise", "target": "c", "text": "A corrected measurement"},
                  {"id": "restore-b", "kind": "restore", "target": "b"}]
        trace = run(events, {("c", "a"): pair(1)}, "hybrid-strongest-17")
        stable = {"a": ["p1"], "b": ["p2"], "c": ["p2"]}
        labels = [{"a": ["p1"]}, {"a": ["p1"], "b": ["p2"]}, {**stable, "c": []}] + [stable] * 4
        result = m.score_trace(trace, gold_for(trace, labels))
        self.assertEqual(result["counts"]["correctionErrorsBefore"], 2)
        self.assertEqual(result["counts"]["correctionErrorsAfter"], 0)
        self.assertEqual(result["prefixes"][4]["pairs"]["knownPairs"], 1)
        self.assertEqual(result["prefixes"][5]["pairs"], result["prefixes"][4]["pairs"])
        self.assertEqual(result["final"]["pairs"]["knownPairs"], 3)

    def test_alignment_and_observed_state_failures(self):
        trace = run([capture("a")])
        gold = gold_for(trace, [{"a": ["p1"]}])
        for field, value in (("order", "shuffle-2"), ("story", "another-story")):
            changed = {**gold, field: value}
            with self.assertRaisesRegex(ValueError, "story/order"):
                m.score_trace(trace, changed)
        changed = copy.deepcopy(gold)
        changed["prefixes"][0]["state"]["a"]["revision"] = 1
        with self.assertRaisesRegex(ValueError, "observed state"):
            m.score_trace(trace, changed)

    def test_macro_undefined_and_reference_coverage(self):
        trace = run([capture("a"), capture("b")], policy="production-embedding-reference",
                    reference=lambda source, clusters: {"selected": sorted(clusters)[:1]})
        result = m.score_trace(trace, gold_for(trace, [{"a": ["p1"]}, {"a": ["p1"], "b": ["p1"]}]))
        self.assertIsNone(result["prefixes"][0]["pairs"]["precision"]["value"])
        self.assertEqual(result["macroPrefix"]["precision"]["denominator"], 1)
        self.assertEqual(result["macroPrefix"]["precision"]["value"], 1)
        self.assertIsNone(result["rates"]["retrievalSharedCoverage"]["value"])


if __name__ == "__main__":
    unittest.main()
