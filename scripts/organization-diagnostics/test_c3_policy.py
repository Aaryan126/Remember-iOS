import copy
import unittest

from c2_policy import run_stream as legacy
from c3_policy import NEW, POLICIES, decide, run_stream, fixed_trace, contexts
from c3_metrics import capture_counts, score_fixed

THRESHOLDS = {"baseline": .8, "hybrids": {seed: .8 for seed in ("17", "29", "41")}}


def pair(a, b):
    score = .95 if a["text"].split()[0] == b["text"].split()[0] else .1
    return {"baseline": {"score": score, "eligible": True}, "hybrid": {seed: score for seed in ("17", "29", "41")}}


def retrieve(a, b):
    return {"contextual": pair(a, b)["baseline"]["score"], "lexical": .5}


def capture(n, text):
    return {"id": f"e{n}", "kind": "capture", "source": {"id": f"c{n}", "text": text, "modality": "note"}}


def memory(text, groups, archived=False):
    return {"text": text, "modality": "note", "memberships": groups, "archived": archived, "revision": 0}


class PolicyTests(unittest.TestCase):
    def test_all_old_policies_match_full_stream(self):
        stream = {"story": "s", "order": "chronological", "events": [capture(1, "Ocean initial"),
            capture(2, "Ocean later"), capture(3, "Forest independent"),
            {"id": "e4", "kind": "revise", "target": "c1", "text": "Ocean revised"},
            {"id": "e5", "kind": "correct", "target": "c2", "targetAnchors": ["c3"]},
            {"id": "e6", "kind": "archive", "target": "c3"},
            {"id": "e7", "kind": "restore", "target": "c3"}, capture(8, "Ocean final")]}
        before = copy.deepcopy(stream)
        for policy in POLICIES:
            if policy != NEW:
                actual = run_stream(stream, policy, pair, retrieve, THRESHOLDS)
                expected = legacy(stream, policy, pair, retrieve, THRESHOLDS)
                expected["id"] = actual["id"]
                self.assertEqual(actual, expected)
        self.assertEqual(before, stream)

    def test_baseline_corrob_requires_eligibility_and_small_thread_quorum(self):
        source = {"id": "new", "text": "Ocean new", "modality": "note", "revision": 0}
        memories = {"a": memory("Ocean a", ["t"]), "b": memory("Forest b", ["t"])}
        self.assertEqual(decide(source, memories, NEW, pair, retrieve, THRESHOLDS)["action"], "new")
        memories.pop("b")
        self.assertEqual(decide(source, memories, NEW, pair, retrieve, THRESHOLDS)["selected"], ["t"])
        def ineligible(a, b):
            value = pair(a, b); value["baseline"]["eligible"] = False
            return value
        self.assertEqual(decide(source, memories, NEW, ineligible, retrieve, THRESHOLDS)["action"], "new")

    def test_top_three_quorum_and_multiple_threads_propose(self):
        source = {"id": "n", "text": "Ocean new", "modality": "note", "revision": 0}
        memories = {"a": memory("Ocean a", ["t"]), "b": memory("Ocean b", ["t"]), "c": memory("Forest c", ["t"])}
        result = decide(source, memories, NEW, pair, retrieve, THRESHOLDS)
        self.assertEqual(result["selected"], ["t"])
        self.assertEqual(result["candidateEvidence"][0]["requiredSupport"], 2)
        memories["d"] = memory("Ocean d", ["u"])
        self.assertEqual(decide(source, memories, NEW, pair, retrieve, THRESHOLDS)["action"], "proposal")

    def test_fixed_context_uses_anchor_not_counterfactual_future(self):
        stream = {"story": "s", "order": "o", "events": [capture(1, "Ocean first"), capture(2, "Forest other"),
            {"id": "e3", "kind": "revise", "target": "c1", "text": "Forest revised"}, capture(4, "Forest current")]}
        anchor = run_stream(stream, NEW, pair, retrieve, THRESHOLDS)
        before = copy.deepcopy(anchor)
        observed = list(contexts(anchor))
        self.assertEqual(observed[1][2]["c1"]["text"], "Ocean first")
        self.assertEqual(observed[2][2]["c1"]["text"], "Forest revised")
        fixed = fixed_trace(anchor, pair, retrieve, THRESHOLDS)
        self.assertEqual(len(fixed["contexts"]), 3)
        self.assertTrue(all(set(row["decisions"]) == set(POLICIES) for row in fixed["contexts"]))
        self.assertEqual(anchor, before)
        anchor["events"][0]["expectedState"]["c1"]["textSHA256"] = "corrupt"
        with self.assertRaisesRegex(ValueError, "reconstruction"):
            list(contexts(anchor))

    def test_invalid_policy_mutation_and_duplicate_event(self):
        stream = {"story": "s", "order": "o", "events": [capture(1, "Ocean"), capture(1, "Ocean")]}
        with self.assertRaises(ValueError):
            run_stream(stream, NEW, pair, retrieve, THRESHOLDS)
        with self.assertRaises(ValueError):
            run_stream(stream, "not-a-policy", pair, retrieve, THRESHOLDS)


class MetricTests(unittest.TestCase):
    def fixture(self):
        context = {"sourceID": "n", "prior": {"a": {"memberships": ["t"], "archived": False},
                                                "b": {"memberships": ["t"], "archived": False}}}
        truth = {"n": {"memberships": ["p"]}, "a": {"memberships": ["p"]}, "b": {"memberships": ["q"]}}
        decision = {"selected": ["t"], "action": "attach", "candidateEvidence": [
            {"threadID": "t", "activeMemberIDs": ["a", "b"], "supportingMemberIDs": ["a"]}]}
        return context, decision, truth

    def test_direct_versus_inherited_and_uncertain_support(self):
        context, decision, truth = self.fixture()
        counts, details = capture_counts(context, decision, truth)
        self.assertEqual(counts["wrongEvents"], 1)
        self.assertEqual(counts["inheritedOrNontransitive"], 1)
        self.assertEqual(details["wrongIDs"], ["b"])
        decision["candidateEvidence"][0]["supportingMemberIDs"] = ["b"]
        self.assertEqual(capture_counts(context, decision, truth)[0]["directDisjointSupport"], 1)
        truth["a"]["memberships"] = []
        decision["candidateEvidence"][0]["supportingMemberIDs"] = ["a"]
        self.assertEqual(capture_counts(context, decision, truth)[0]["uncertainSupport"], 1)

    def test_safe_complete_candidate_and_bridge_proposal_flags(self):
        context, decision, truth = self.fixture()
        truth["n"]["memberships"] = ["p", "q"]
        decision["action"], decision["selected"] = "proposal", []
        counts, _ = capture_counts(context, decision, truth)
        self.assertEqual(counts["missedPairs"], 2)
        self.assertEqual(counts["missedViaProposal"], 1)
        self.assertEqual(counts["missedBridgeEvents"], 1)
        self.assertEqual(counts["missedWithSafeCompleteCandidate"], 1)
        decision["candidateEvidence"] = []
        self.assertEqual(capture_counts(context, decision, truth)[0]["missedWithoutSafeCompleteCandidate"], 1)

    def test_uncertain_target_and_archived_predecessor_excluded(self):
        context, decision, truth = self.fixture()
        truth["n"]["memberships"] = []
        context["prior"]["b"]["archived"] = True
        counts, _ = capture_counts(context, decision, truth)
        self.assertEqual(counts["eligibleWrongEvents"], 0)
        self.assertEqual(counts["uncertainJoinedPairs"], 1)


if __name__ == "__main__":
    unittest.main()
