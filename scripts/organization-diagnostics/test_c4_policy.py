import copy
import math
import unittest

from c2_policy import _snapshot
from c3_policy import run_stream
from c4_policy import propose, fixed_stream, apply_proposal, signature, shared
from c4_metrics import review, score_stream, aggregate
from test_c3_policy import THRESHOLDS, memory, pair, retrieve, capture


def state(*rows):
    return {key: memory(text, groups) for key, text, groups in rows}


def candidates(values, scorer="17", protected=(), callback=pair):
    return propose(values, protected, scorer, callback, THRESHOLDS)["proposals"]


def custom(scores):
    def callback(a, b):
        score = scores.get(tuple(sorted((a["id"], b["id"]))), .1)
        return {"baseline": {"score": score, "eligible": True}, "hybrid": {s: score for s in ("17", "29", "41")}}
    return callback


class ProposalTests(unittest.TestCase):
    def test_fragment_merge_and_add_are_proposals_only(self):
        values = state(("a", "Ocean a", ["t"]), ("b", "Ocean b", ["u"]))
        original = copy.deepcopy(values)
        proposals = candidates(values)
        self.assertEqual({p["kind"] for p in proposals}, {"add", "merge"})
        for p in proposals:
            after = apply_proposal(_snapshot(values), p, [])
            self.assertTrue(shared(after, "a", "b"))
        self.assertEqual(values, original)

    def test_split_disconnected_components(self):
        values = state(("a", "Ocean a", ["t"]), ("b", "Ocean b", ["t"]), ("c", "Forest c", ["t"]))
        proposals = candidates(values)
        p = next(p for p in proposals if p["kind"] == "split")
        after = apply_proposal(_snapshot(values), p, [])
        self.assertTrue(shared(after, "a", "b"))
        self.assertFalse(shared(after, "a", "c"))

    def test_false_positive_bridge_prevents_component_split(self):
        values = state(("a", "a", ["t"]), ("b", "b", ["t"]), ("c", "c", ["t"]))
        callback = custom({("a", "b"): .95, ("b", "c"): .95})
        self.assertFalse(any(p["kind"] == "split" for p in candidates(values, callback=callback)))

    def test_bridge_adds_without_merging_independent_topics(self):
        values = state(("a", "a", ["t"]), ("b", "b", ["u"]), ("c", "c", ["t"]))
        callback = custom({("a", "c"): .95, ("b", "c"): .95})
        proposals = candidates(values, callback=callback)
        self.assertFalse(any(p["kind"] == "merge" for p in proposals))
        p = next(p for p in proposals if p["kind"] == "add")
        after = apply_proposal(_snapshot(values), p, [])
        self.assertTrue(shared(after, "a", "c"))
        self.assertTrue(shared(after, "b", "c"))
        self.assertFalse(shared(after, "a", "b"))

    def test_reassign_requires_rejected_existing_peer(self):
        values = state(("a", "Ocean a", ["t"]), ("b", "Forest b", ["t"]), ("c", "Forest c", ["u"]))
        p = next(p for p in candidates(values) if p["kind"] == "reassign")
        self.assertEqual(p["assignments"], {"b": ["u"]})
        after = apply_proposal(_snapshot(values), p, [])
        self.assertFalse(shared(after, "a", "b"))
        self.assertTrue(shared(after, "b", "c"))

    def test_unknown_scores_do_not_justify_split_or_move(self):
        values = state(("a", "a", ["t"]), ("b", "b", ["t"]), ("c", "c", ["u"]))
        callback = custom({("a", "b"): None, ("b", "c"): .95})
        self.assertFalse(any(p["kind"] in ("split", "reassign") for p in candidates(values, callback=callback)))

    def test_baseline_eligibility_and_nonfinite_scores(self):
        values = state(("a", "Ocean a", ["t"]), ("b", "Ocean b", ["u"]))
        def callback(a, b):
            value = pair(a, b)
            value["baseline"]["eligible"] = False
            return value
        self.assertEqual(candidates(values, scorer="baseline", callback=callback), [])
        with self.assertRaises(ValueError):
            candidates(values, callback=custom({("a", "b"): math.nan}))

    def test_protected_relationship_guard_not_just_assignment_guard(self):
        values = state(("a", "Ocean a", ["t"]), ("b", "Forest b", ["t"]))
        self.assertEqual(candidates(values, protected=["a"]), [])
        snapshot = _snapshot(values)
        p = {"beforeSHA256": signature(snapshot), "assignments": {"b": ["u"]}}
        with self.assertRaisesRegex(ValueError, "relationship"):
            apply_proposal(snapshot, p, ["a"])

    def test_archived_sources_are_neither_evidence_nor_mutation_targets(self):
        values = state(("a", "Ocean a", ["t"]), ("b", "Ocean b", ["u"]), ("c", "Ocean c", ["t"]))
        values["c"]["archived"] = True
        seen = []
        def callback(a, b):
            seen.extend([a["id"], b["id"]])
            return pair(a, b)
        proposals = candidates(values, callback=callback)
        self.assertFalse(any(p["kind"] == "merge" for p in proposals))
        for p in proposals:
            after = apply_proposal(_snapshot(values), p, [])
            self.assertEqual(after["c"], _snapshot(values)["c"])
            for key in ("a", "b"):
                self.assertEqual(shared(after, key, "c"), shared(values, key, "c"))
        self.assertNotIn("c", seen)

    def test_atomic_stale_rejection_and_noop(self):
        values = state(("a", "Ocean a", ["t"]), ("b", "Ocean b", ["u"]))
        p = candidates(values)[0]
        snapshot = _snapshot(values)
        snapshot["a"]["revision"] = 1
        old = copy.deepcopy(snapshot)
        with self.assertRaisesRegex(ValueError, "Stale"):
            apply_proposal(snapshot, p, [])
        self.assertEqual(snapshot, old)
        p = {"beforeSHA256": signature(snapshot), "assignments": {"b": ["another-singleton"]}}
        with self.assertRaisesRegex(ValueError, "No changed"):
            apply_proposal(snapshot, p, [])

    def test_budget_determinism_and_no_input_mutation(self):
        values = state(*[(str(i), "Ocean " + str(i), [str(i)]) for i in range(6)])
        first = propose(values, [], "17", pair, THRESHOLDS)
        second = propose(dict(reversed(list(values.items()))), [], "17", pair, THRESHOLDS)
        self.assertEqual(first, second)
        self.assertLessEqual(len(first["proposals"]), 4)
        self.assertEqual(first["eligibleByKind"]["merge"], 15)
        self.assertEqual(len({p["kind"] for p in first["proposals"]}), len(first["proposals"]))

    def test_fixed_revisions_pins_and_no_future_state_feedback(self):
        stream = {"story": "s", "order": "o", "events": [capture(1, "Ocean first"), capture(2, "Forest other"),
            {"id": "e3", "kind": "revise", "target": "c1", "text": "Forest edited"},
            {"id": "e4", "kind": "correct", "target": "c2", "targetAnchors": ["c1"]}]}
        trace = run_stream(stream, "hybrid-corroborated-17", pair, retrieve, THRESHOLDS)
        seen = []
        def callback(a, b):
            seen.append((a["text"], b["text"]))
            return pair(a, b)
        result = fixed_stream(trace, callback, THRESHOLDS)
        self.assertEqual(result["prefixes"][-1]["protected"], ["c2"])
        self.assertTrue(any("Ocean first" in row for row in seen))
        self.assertTrue(any("Forest edited" in row for row in seen))
        self.assertEqual([p["state"] for p in result["prefixes"]], [e["expectedState"] for e in trace["events"]])


class ReviewTests(unittest.TestCase):
    def fixture(self):
        values = state(("a", "Ocean a", ["t"]), ("b", "Ocean b", ["u"]))
        snapshot = _snapshot(values)
        gold = copy.deepcopy(snapshot)
        gold["a"]["memberships"], gold["b"]["memberships"] = ["p"], ["p"]
        return values, snapshot, gold

    def test_beneficial_harmful_uncertain_are_distinct(self):
        values, snapshot, gold = self.fixture()
        p = candidates(values)[0]
        self.assertEqual(review(snapshot, p, [], gold)["label"], "beneficial")
        gold["b"]["memberships"] = ["q"]
        self.assertEqual(review(snapshot, p, [], gold)["label"], "harmful")
        gold["b"]["memberships"] = []
        self.assertEqual(review(snapshot, p, [], gold)["label"], "indeterminate")

    def test_harm_is_not_cancelled_by_more_repairs(self):
        values = state(("a", "Ocean a", ["t"]), ("b", "Ocean b", ["t"]), ("c", "Forest c", ["t"]))
        snapshot = _snapshot(values)
        gold = copy.deepcopy(snapshot)
        gold["a"]["memberships"] = ["p"]
        gold["b"]["memberships"] = ["q"]
        gold["c"]["memberships"] = ["p"]
        p = next(p for p in candidates(values) if p["kind"] == "split")
        result = review(snapshot, p, [], gold)
        self.assertEqual(result["label"], "harmful")
        self.assertTrue(result["repairedPairs"] and result["introducedPairs"])

    def test_explicit_single_acceptance_and_no_gold_feedback(self):
        values, snapshot, gold = self.fixture()
        unit = {"anchor": "a", "story": "s", "order": "o", "prefixes": [{"after": "e", "state": snapshot,
            "protected": [], "scorers": {s: propose(values, [], s, pair, THRESHOLDS) for s in ("baseline", "17", "29", "41")}}]}
        original = copy.deepcopy(unit)
        result = score_stream(unit, {"story": "s", "order": "o", "prefixes": [{"after": "e", "state": gold}]})
        row = result["prefixes"][0]["scorers"]["17"]
        self.assertEqual(row["acceptance"]["decision"], "explicit-accept")
        self.assertEqual(row["after"]["pairs"]["falseNegative"], 0)
        self.assertEqual(unit, original)
        summary = aggregate([result], "17")
        self.assertEqual(summary["counts"]["accepted"], 1)
        self.assertEqual(summary["counts"]["beneficial"], 2)

    def test_reject_all_on_unknown_and_validate_identity(self):
        values, snapshot, gold = self.fixture()
        gold["b"]["memberships"] = []
        unit = {"anchor": "a", "story": "s", "order": "o", "prefixes": [{"after": "e", "state": snapshot,
            "protected": [], "scorers": {s: propose(values, [], s, pair, THRESHOLDS) for s in ("baseline", "17", "29", "41")}}]}
        truth = {"story": "s", "order": "o", "prefixes": [{"after": "e", "state": gold}]}
        result = score_stream(unit, truth)
        self.assertEqual(result["prefixes"][0]["scorers"]["17"]["acceptance"]["decision"], "reject-all")
        self.assertEqual(aggregate([result], "17")["beneficialProposalRate"], 0)
        truth["order"] = "wrong"
        with self.assertRaises(ValueError):
            score_stream(unit, truth)


if __name__ == "__main__":
    unittest.main()
