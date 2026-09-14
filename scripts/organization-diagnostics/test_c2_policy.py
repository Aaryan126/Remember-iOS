import copy
import hashlib
import unittest

import c2_policy as p


THRESHOLDS = {"baseline": 0.5, "hybrids": {seed: 0.5 for seed in p.SEEDS}}


def capture(source_id, text=None):
    return {"id": f"capture-{source_id}", "kind": "capture",
            "source": {"id": source_id, "text": text or f"Synthetic source {source_id}", "modality": "note"}}


def pair(score=0.0, eligible=True):
    return {"baseline": {"score": score, "eligible": eligible},
            "hybrid": {seed: score for seed in p.SEEDS}}


def stream(events, order="chronological"):
    return {"story": "synthetic", "order": order, "events": events}


def run(events, scores=None, policy="hybrid-corroborated-17", retrieval=None, reference=None):
    return p.run_stream(stream(events), policy,
                        lambda source, member: (scores or {}).get((source["id"], member["id"]), pair()),
                        retrieval or (lambda source, member: {"contextual": None, "lexical": 0}),
                        THRESHOLDS, reference)


class PolicyTests(unittest.TestCase):
    def test_eight_variants_and_missing_scores_abstain(self):
        self.assertEqual(len(set(p.POLICY_IDS)), 8)
        for policy in p.POLICY_IDS[1:]:
            result = run([capture("a"), capture("b")], {("b", "a"): {}}, policy)
            self.assertEqual(result["events"][-1]["decision"]["action"], "new")
            self.assertEqual(result["events"][-1]["decision"]["retrievedIDs"], ["a"])

    def test_baseline_eligibility_is_required(self):
        result = run([capture("a"), capture("b")], {("b", "a"): pair(1, False)}, "simple-baseline-strongest")
        self.assertEqual(result["events"][-1]["decision"]["action"], "new")

    def test_two_qualifying_threads_propose_without_merge(self):
        result = run([capture("a"), capture("b"), capture("c")],
                     {("c", "a"): pair(1), ("c", "b"): pair(1)})
        decision = result["events"][-1]["decision"]
        self.assertEqual(decision["action"], "proposal")
        self.assertEqual(decision["qualifyingThreadIDs"], ["t:a", "t:b"])
        self.assertEqual(result["events"][-1]["expectedState"]["c"]["memberships"], ["t:c"])

    def test_singleton_and_two_member_quorum(self):
        scores = {("b", "a"): pair(1), ("c", "a"): pair(1)}
        result = run([capture("a"), capture("b"), capture("c")], scores)
        self.assertEqual(result["events"][1]["decision"]["action"], "attach")
        last = result["events"][-1]["decision"]
        self.assertEqual(last["action"], "new")
        self.assertEqual(last["candidateEvidence"][0]["requiredSupport"], 2)
        scores[("c", "b")] = pair(1)
        self.assertEqual(run([capture("a"), capture("b"), capture("c")], scores)["events"][-1]["decision"]["action"], "attach")

    def test_three_member_quorum_two_of_three(self):
        scores = {(incoming, prior): pair(1) for incoming, prior in (("b", "a"), ("c", "a"), ("c", "b"), ("d", "a"), ("d", "c"))}
        result = run([capture(key) for key in "abcd"], scores)
        evidence = result["events"][-1]["decision"]["candidateEvidence"][0]
        self.assertEqual(evidence["testedMemberIDs"], ["a", "b", "c"])
        self.assertEqual(evidence["supportingMemberIDs"], ["a", "c"])
        self.assertTrue(evidence["qualifies"])

    def test_quorum_uses_retrieved_rank_not_score_cherry_picking(self):
        events = [capture("a")]
        for source_id in "bcd":
            events.extend([capture(source_id), {"id": f"correct-{source_id}", "kind": "correct", "target": source_id, "targetAnchors": ["a"]}])
        events.append(capture("z"))
        scores = {("z", "c"): pair(1), ("z", "d"): pair(1)}
        result = run(events, scores)
        evidence = result["events"][-1]["decision"]["candidateEvidence"][0]
        self.assertEqual(evidence["testedMemberIDs"], ["a", "b", "c"])
        self.assertFalse(evidence["qualifies"])
        strongest = run(events, scores, "hybrid-strongest-17")
        self.assertEqual(strongest["events"][-1]["decision"]["action"], "attach")

    def test_insufficient_retrieved_members_cannot_pass(self):
        events = [capture("a"), capture("z"), {"id": "join", "kind": "correct", "target": "z", "targetAnchors": ["a"]}]
        events.extend(capture(key) for key in "bcde")
        events.append(capture("new"))
        result = run(events, {("new", "a"): pair(1)})
        evidence = next(item for item in result["events"][-1]["decision"]["candidateEvidence"] if item["threadID"] == "t:a")
        self.assertEqual(evidence["activeMemberIDs"], ["a", "z"])
        self.assertEqual(evidence["retrievedMemberIDs"], ["a"])
        self.assertFalse(evidence["qualifies"])

    def test_retrieval_union_zero_lexical_and_stable_ties(self):
        events = [capture(f"s{index}") for index in range(10)] + [capture("z")]
        retrieval = lambda source, member: {"contextual": int(member["id"][1:]), "lexical": 0}
        result = run(events, retrieval=retrieval)
        decision = result["events"][-1]["decision"]
        self.assertEqual(set(decision["retrievedIDs"]), {f"s{index}" for index in range(10)})
        self.assertEqual(decision["retrievedIDs"][:2], ["s0", "s9"])
        self.assertAlmostEqual(decision["retrieval"][0]["rrf"], 1 / 61)
        for policy in p.POLICY_IDS[1:]:
            self.assertEqual(run(events, policy=policy, retrieval=retrieval)["events"][-1]["decision"]["retrievedIDs"], decision["retrievedIDs"])

    def test_correction_anchor_bridge_archive_revision_and_restore(self):
        events = [capture("a"), capture("b"), capture("c"),
                  {"id": "archive-a", "kind": "archive", "target": "a"},
                  {"id": "correct-c", "kind": "correct", "target": "c", "targetAnchors": ["a", "b"]},
                  {"id": "revise-c", "kind": "revise", "target": "c", "text": "Revised visible text"},
                  capture("d"), {"id": "restore-a", "kind": "restore", "target": "a"}]
        observed = []
        result = p.run_stream(stream(events), "hybrid-strongest-17", lambda source, member: observed.append(member) or pair(),
                              lambda source, member: {"contextual": None, "lexical": 0}, THRESHOLDS)
        self.assertEqual(result["events"][2]["expectedState"]["c"]["memberships"], ["t:c"])
        revised = result["events"][5]["expectedState"]["c"]
        self.assertEqual(revised["memberships"], ["t:a", "t:b"])
        self.assertEqual(revised["revision"], 1)
        self.assertEqual(revised["textSHA256"], hashlib.sha256(b"Revised visible text").hexdigest())
        self.assertEqual(result["events"][6]["decision"]["retrievedIDs"], ["b", "c"])
        self.assertTrue(any(item["id"] == "c" and item["text"] == "Revised visible text" for item in observed))
        self.assertFalse(result["events"][-1]["expectedState"]["a"]["archived"])

    def test_order_controls_and_nonmutation(self):
        first, second = stream([capture("a"), capture("b")]), stream([capture("b"), capture("a")], "shuffle-1")
        original = copy.deepcopy(first)
        callback = lambda source, member: pair(1)
        retrieval = lambda source, member: {"contextual": None, "lexical": 0}
        left = p.run_stream(first, "hybrid-strongest-17", callback, retrieval, THRESHOLDS)
        right = p.run_stream(second, "hybrid-strongest-17", callback, retrieval, THRESHOLDS)
        self.assertEqual(first, original)
        self.assertEqual(left, p.run_stream(first, "hybrid-strongest-17", callback, retrieval, THRESHOLDS))
        self.assertEqual(left["events"][-1]["expectedState"]["a"]["memberships"], ["t:a"])
        self.assertEqual(right["events"][-1]["expectedState"]["a"]["memberships"], ["t:b"])

    def test_reference_callback_and_invalid_selection(self):
        callback = lambda source, clusters: {"selected": sorted(clusters)[:1], "details": {"source": source["id"]}}
        result = run([capture("a"), capture("b")], policy=p.POLICY_IDS[0], reference=callback)
        self.assertEqual(result["events"][-1]["decision"]["selected"], ["t:a"])
        self.assertEqual(result["events"][-1]["decision"]["details"],
                         {"selected": ["t:a"], "details": {"source": "b"}})
        with self.assertRaisesRegex(ValueError, "Invalid reference"):
            run([capture("a")], policy=p.POLICY_IDS[0], reference=lambda *_: {"selected": ["missing"]})

    def test_invalid_events_and_scores_fail_closed(self):
        invalid = [capture("a"), {"id": "bad", "kind": "correct", "target": "a", "targetAnchors": ["future"]}]
        with self.assertRaisesRegex(ValueError, "anchors"):
            run(invalid)
        with self.assertRaisesRegex(ValueError, "contextual"):
            run([capture("a"), capture("b")], retrieval=lambda *_: {"contextual": float("nan"), "lexical": 0})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            run([capture("a"), capture("a")])


if __name__ == "__main__":
    unittest.main()
