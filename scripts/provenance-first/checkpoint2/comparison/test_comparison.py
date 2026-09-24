"""Synthetic contract tests; native policy/search, no model inference or test labels."""
from copy import deepcopy
import unittest

from pc_native import Native, c
import pc_policy as p
import pc_metrics as m
import pc_runner as r


def capture(sid, text=None, eid=None):
    return {"id": eid or "e" + sid[1:], "kind": "capture", "sourceId": sid,
            "text": text or sid, "modality": "note", "locator": "Fixture"}


def memory(text, memberships, archived=False, revision=0, created=0):
    return dict(text=text, memberships=memberships, archived=archived, revision=revision,
                locator="Fixture", created=created, modality="note", pinned=False)


def score_table(scores):
    def score(a, b):
        return {"score": scores[b], "contextual": .5, "lexical": .5}
    return score


def label(projects, disposition="confirmed"):
    return {"memberships": projects, "disposition": disposition}


def synthetic_fixture():
    events = [capture("s01", "orchard budget"), capture("s02", "lantern budget"),
              capture("s03", "orchard invoice"), capture("s04", "unclear invoice")]
    labels = [["p1"], ["p2"], ["p1"], []]
    library = {"id": "synthetic", "projects": [{"id": "p1", "rootSourceId": "s01"},
               {"id": "p2", "rootSourceId": "s02"}], "events": [
               {**e, "gold": label(g, "confirmed" if g else "unresolved")} for e, g in zip(events, labels)], "tasks": []}
    return library, {"id": "synthetic", "order": "chronological", "events": events, "queries": []}


class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = Native()

    def decide(self, memories, scores, variant="A", threshold=p.THRESHOLDS[0], automatic=True):
        return p.decision("new", memories, score_table(scores), self.native, variant, threshold, automatic)

    def test_empty_reference_matches_native(self):
        self.assertEqual(self.decide({}, {})["selected"], [])

    def test_singleton_support_matches_native(self):
        value = self.decide({"s01": memory("a", ["s01"])}, {"a": p.THRESHOLDS[0]})
        self.assertEqual(value["selected"], ["s01"])
        self.assertEqual(value["support"]["s01"][0]["revision"], 0)

    def test_below_threshold_abstains(self):
        self.assertEqual(self.decide({"s01": memory("a", ["s01"])}, {"a": .98})["selected"], [])

    def test_multiple_projects_abstain(self):
        memories = {"s01": memory("a", ["s01"]), "s02": memory("b", ["s02"])}
        self.assertEqual(len(self.decide(memories, {"a": 1, "b": 1})["qualifying"]), 2)
        self.assertEqual(self.decide(memories, {"a": 1, "b": 1})["selected"], [])

    def test_two_member_corroboration(self):
        memories = {"s01": memory("a", ["s01"]), "s02": memory("b", ["s01"])}
        self.assertEqual(self.decide(memories, {"a": 1, "b": .5})["selected"], [])
        self.assertEqual(self.decide(memories, {"a": 1, "b": 1})["selected"], ["s01"])

    def test_archived_sources_not_scored(self):
        self.assertEqual(self.decide({"s01": memory("not scored", ["s01"], True)}, {})["retrieved"], [])

    def test_only_first_three_supports_considered(self):
        ids = p.ordered([f"s{i:02}" for i in range(1, 5)])
        memories = {sid: memory(sid, ["s01"]) for sid in ids}
        scores = {sid: 1 if i >= 2 else .5 for i, sid in enumerate(ids)}
        self.assertEqual(self.decide(memories, scores)["selected"], [])

    def test_channel_ties_match_native_top_five(self):
        ids = [f"s{i:02}" for i in range(1, 9)]
        value = self.decide({sid: memory(sid, [sid]) for sid in ids}, {sid: .5 for sid in ids})
        self.assertEqual(value["retrieved"], p.ordered(ids)[:5])

    def test_c_requires_exclusive_support(self):
        # A has two supporting records for s01. C must not count the shared
        # record as independent exclusive corroboration for that project.
        memories = {"s01": memory("a", ["s01"]), "s02": memory("b", ["s02"]),
                    "s03": memory("shared", p.ordered(["s01", "s02"]))}
        scores = {"a": 1, "b": .5, "shared": 1}
        self.assertEqual(self.decide(memories, scores)["selected"], ["s01"])
        result = self.decide(memories, scores, "C")
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["proposals"], ["s01"])

    def test_exclusive_filter_must_not_resolve_ambiguity(self):
        memories = {"s01": memory("a", ["s01"]), "s02": memory("b", ["s01"]),
                    "s03": memory("shared", p.ordered(["s01", "s02"]))}
        value = self.decide(memories, {"a": 1, "b": 1, "shared": 1}, "C")
        self.assertEqual(len(value["qualifying"]), 2)
        self.assertEqual(value["selected"], [])

    def test_suggestions_only_retains_proposal_without_mutation(self):
        memories = {"s01": memory("a", ["s01"])}
        old = deepcopy(memories)
        value = self.decide(memories, {"a": 1}, "C", automatic=False)
        self.assertEqual(value["selected"], [])
        self.assertEqual(value["proposals"], ["s01"])
        self.assertEqual(memories, old)

    def test_nonfinite_and_out_of_range_scores_rejected(self):
        for invalid in (float("nan"), float("inf"), 1.01, -.1):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.decide({"s01": memory("a", ["s01"])}, {"a": invalid})

    def test_correction_is_literal_root_not_roots_current_membership(self):
        memories = {}
        p.apply(memories, capture("s01"), [])
        p.apply(memories, capture("s02"), ["s01"])
        p.apply(memories, capture("s03"), [])
        p.apply(memories, dict(id="e04", kind="correct", sourceId="s03", reason="user chose", assignedProjectRoots=["s02"]))
        self.assertEqual(memories["s03"]["memberships"], ["s02"])
        self.assertTrue(memories["s03"]["pinned"])

    def test_revision_archive_restore_keep_pin_and_membership(self):
        memories = {"s01": memory("old", ["s01"])}
        p.apply(memories, dict(id="e02", kind="correct", sourceId="s01", reason="user", assignedProjectRoots=["s01"]))
        p.apply(memories, dict(id="e03", kind="revise", sourceId="s01", text="new", locator="Updated"))
        for i, kind in enumerate(("archive", "restore"), 4):
            p.apply(memories, dict(id=f"e{i:02}", kind=kind, sourceId="s01"))
        self.assertEqual(memories["s01"]["memberships"], ["s01"])
        self.assertTrue(memories["s01"]["pinned"])
        self.assertEqual(memories["s01"]["revision"], 1)

    def test_future_targets_rejected(self):
        for e, selected in ((capture("s01"), ["s02"]),
                            (dict(id="e01", kind="restore", sourceId="s01"), None)):
            with self.assertRaises(ValueError): p.apply({}, e, selected)

    def test_hidden_fields_rejected(self):
        for hidden in ("gold", "dependsOn", "projectTitle", "rationale"):
            with self.subTest(hidden=hidden), self.assertRaises(ValueError):
                p.apply({}, {**capture("s01"), hidden: {}}, [])

    def test_future_text_does_not_enter_prefix_scores(self):
        _, stream = synthetic_fixture()
        seen = []
        def score(a, b):
            seen.append((a, b))
            return dict(contextual=.5, lexical=.5, score=.5)
        trace = p.run_stream(stream, score, self.native, "A", p.THRESHOLDS[0])
        self.assertEqual(len(seen), 6)
        self.assertEqual(set(trace["events"][0]["state"]), {"s01"})
        self.assertNotIn(("orchard budget", "unclear invoice"), seen)
        self.assertEqual(p.ledger_run(trace)["events"][0]["expectedState"]["localc01"]["memberships"], ["t:c01"])


class SearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.native = Native()

    def recover(self, question, memories, native=None):
        return p.recover(dict(id="q01", atEvent="e01", question=question), memories, native or self.native)

    def test_native_diacritic_and_case_normalization(self):
        value = self.recover("CAFE", {"s01": memory("Café meeting", ["s01"])})
        self.assertEqual(value["confirmed"][0]["score"], 1)

    def test_native_newer_tie_and_source_deduplication(self):
        memories = {"s01": memory("budget " * 400, ["s01"], created=1),
                    "s02": memory("budget", ["s02"], created=2)}
        value = self.recover("budget", memories)
        self.assertEqual(value["river"], "s02")
        self.assertEqual(len(value["combined"]), 2)

    def test_native_chunk_locator_traceable(self):
        text = "padding " * 180 + "uniquequartz"
        result = self.recover("uniquequartz", {"s01": memory(text, ["s01"])})
        hit = result["confirmed"][0]
        self.assertGreater(hit["ordinal"], 0)
        self.assertIn(hit["quote"], text)
        self.assertEqual(hit["locator"], f"Fixture, part {hit['ordinal']+1}")

    def test_confirmed_and_outside_lists_separate(self):
        memories = {f"s{i:02}": memory("budget", ["s01"] if i in (1, 2, 7) else [f"s{i:02}"], created=i)
                    for i in range(1, 8)}
        value = self.recover("budget", memories)
        self.assertEqual(value["river"], "s01")
        self.assertEqual([h["sourceId"] for h in value["confirmed"]], ["s07", "s02", "s01"])
        self.assertEqual([h["sourceId"] for h in value["suggested"]], ["s06", "s05", "s04"])
        self.assertEqual([h["sourceId"] for h in value["combined"]], ["s07", "s06", "s05"])

    def test_no_answer_and_archives(self):
        value = self.recover("budget", {"s01": memory("budget", ["s01"], archived=True)})
        self.assertEqual(value["combined"], [])
        self.assertIsNone(value["river"])

    def test_stale_duplicate_fabricated_and_wrong_locator_hits_rejected(self):
        memories = {"s01": memory("budget", ["s01"], revision=1)}
        hit = dict(sourceId="s01", revision=1, quote="budget", locator="Fixture", ordinal=0, score=1)
        for hits in ([{**hit, "revision": 0}], [hit, hit], [{**hit, "quote": "fabricated"}], [{**hit, "locator": "elsewhere"}]):
            with self.subTest(hits=hits), self.assertRaises(ValueError):
                self.recover("budget", memories, lambda request: {"hits": hits})

    def test_query_annotations_rejected(self):
        with self.assertRaises(ValueError):
            p.recover(dict(id="q01", atEvent="e01", question="budget", mode="current"), {}, self.native)


class MetricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.native = Native()

    def report(self, query=None, expected=None, answerable=True, automatic=False):
        library, stream = synthetic_fixture()
        if query:
            stream["queries"] = [dict(id="q01", atEvent="e04", question=query)]
            library["tasks"] = [dict(id="q01", mode="current", answerable=answerable,
                                     expectedEvidence=expected or [])]
        trace = p.run_stream(stream, score_table({e["text"]: 1 for e in stream["events"]}),
                             self.native, "C", p.THRESHOLDS[0], automatic)
        return m.evaluate([trace], [library], "C"), library, trace

    def test_singletons_are_not_credited_as_automatic_resolution(self):
        report, _, _ = self.report()
        self.assertEqual(report["automaticEdges"], 0)
        self.assertIsNone(report["precision"])
        self.assertEqual(report["exactMembershipSets"], 3)  # two roots + unresolved, not s03
        self.assertEqual(report["finalStates"][0]["additionalFragments"]["p1"], 1)

    def test_wrong_and_unresolved_edges_are_errors(self):
        report, _, _ = self.report(automatic=True)
        self.assertEqual(report["automaticEdges"], 3)
        self.assertEqual(report["correctEdges"], 1)
        self.assertEqual(report["wrongEdges"], 2)
        self.assertEqual(report["unsupportedRate"], 1)

    def test_unanswerable_only_macro_is_undefined(self):
        report, _, _ = self.report(query="budget", answerable=False)
        self.assertIsNone(report["queries"]["libraryMacroRecallAt3"])
        self.assertEqual(report["queries"]["unanswerableWithReturns"], 1)
        self.assertEqual(report["queries"]["precisionAt3"], 0)

    def test_empty_return_answerable_recall_zero(self):
        report, _, _ = self.report(query="unfindable", expected=[dict(sourceId="s01", revision=0)])
        self.assertEqual(report["queries"]["libraryMacroRecallAt3"], 0)
        self.assertIsNone(report["queries"]["precisionAt3"])
        self.assertEqual(report["queries"]["resultCountDistribution"]["0"], 1)

    def test_unique_evidence_denominator_and_outside_precision(self):
        gold = [dict(sourceId="s01", revision=0), dict(sourceId="s01", revision=0)]
        report, _, _ = self.report(query="budget", expected=gold)
        self.assertEqual(report["queries"]["returned"], 2)
        self.assertEqual(report["queries"]["precisionAt3"], .5)
        self.assertEqual(report["queries"]["pooledRecallAt3"], 1)
        self.assertEqual(report["queries"]["suggestionPrecisionAt3"], 1)

    def test_old_revision_not_credited_for_current(self):
        report, _, _ = self.report(query="budget", expected=[dict(sourceId="s01", revision=1)])
        self.assertEqual(report["queries"]["oldRevisionTasks"], 1)
        self.assertEqual(report["queries"]["oldRevisionTaskRecall"], 0)

    def test_b_has_exactly_a_placements(self):
        _, library, trace = self.report(query="budget", expected=[dict(sourceId="s01", revision=0)])
        a, b = (m.evaluate([trace], [library], variant) for variant in ("A", "B"))
        self.assertEqual(a["edges"], b["edges"])
        self.assertEqual(a["queries"]["pooledRecallAt3"], 0)
        self.assertEqual(b["queries"]["pooledRecallAt3"], 1)

    def test_threshold_gates_coverage_then_stricter_tie(self):
        def report(n, precision): return dict(automaticEdges=n, precision=precision)
        self.assertFalse(m.choose([(t, report(19, 1)) for t in p.THRESHOLDS])["automatic"])
        self.assertFalse(m.choose([(t, report(100, .949)) for t in p.THRESHOLDS])["automatic"])
        self.assertEqual(m.choose([(t, report(20, .95)) for t in p.THRESHOLDS])["threshold"], .995)
        self.assertEqual(m.choose([(p.THRESHOLDS[0], report(25, .96)), (.995, report(20, 1))])["threshold"], p.THRESHOLDS[0])

    def test_retention_uses_exact_edge_identity(self):
        report, _, _ = self.report(automatic=True)
        candidate = deepcopy(report)
        candidate["edges"] = [{**e, "key": [*e["key"][:-1], "different"]} for e in report["edges"]]
        result = m.gates(report, candidate)
        self.assertEqual(result["retention"], 0)
        self.assertFalse(result["automaticPointTargetsMet"])


class CompilationTests(unittest.TestCase):
    def test_development_streams_are_allowlisted_and_prefix_only(self):
        libraries = c.read(c.PF / "authored/development.json")["libraries"]
        for library in libraries:
            chronological, alternate = r.streams_for(library)
            self.assertEqual(len(chronological["queries"]), 4)
            self.assertEqual(alternate["queries"], [])
            self.assertEqual({e["id"] for e in chronological["events"]}, {e["id"] for e in alternate["events"]})
            for event in chronological["events"] + alternate["events"]: p.validate_event(event)
            self.assertEqual({e["id"] for e in chronological["queries"]}, {e["id"] for e in library["tasks"]})

    def test_catalogue_deduplicates_text_and_includes_versions(self):
        stream = dict(id="synthetic", order="chronological", queries=[], events=[capture("s01", "a"),
               capture("s02", "b"), dict(id="e03", kind="revise", sourceId="s01", text="c", locator="Revision")])
        catalog = r.catalogue([stream, stream])
        self.assertEqual(set(catalog["texts"].values()), {"a", "b", "c"})
        self.assertEqual(len(catalog["pairs"]), 2)

    def test_prediction_settings_are_fixed(self):
        self.assertEqual(r.settings("Coff"), ("C", p.THRESHOLDS[0], False))
        self.assertEqual(r.settings("C2"), ("C", .995, True))
        with self.assertRaises(ValueError): r.settings("C3")


if __name__ == "__main__": unittest.main()
