import copy
import itertools
import unittest

import p1_release
from prepare import DATA, read, validate_corpus
from test_p1 import fixture


class ReleaseTests(unittest.TestCase):
    def reviews(self, lib):
        reviewed = {"id": lib["id"], "assignments": [{"id": i["id"], "memberships": list(i["memberships"]), "reason": "Independent fixture reason"} for i in lib["items"]],
                    "relatedThreads": lib["relatedThreads"], "historyVerdict": "supported", "historyEvidence": "Supported fixture"}
        return [{"libraries": [reviewed]}]

    def test_consensus_has_no_issues(self):
        lib = fixture()
        self.assertEqual(p1_release.collect_issues([lib], self.reviews(lib), [{"pairs": []}]), [])

    def test_membership_disagreement_is_recorded_not_applied(self):
        lib = fixture()
        review = self.reviews(lib)
        review[0]["libraries"][0]["assignments"][0]["memberships"] = ["dispatch"]
        issues = p1_release.collect_issues([lib], review, [{"pairs": []}])
        self.assertEqual(len(issues), 1)
        self.assertEqual(lib["items"][0]["memberships"], ["catalog"])
        decision = {"reviewer": "root-adjudicator", "method": "Read visible evidence", "decisions":
                    [{"id": issues[0]["id"], "resolution": "accept-reviewer", "reason": "Fixture explicit correction"}]}
        final, _ = p1_release.apply_decisions([lib], issues, decision)
        self.assertEqual(final[0]["items"][0]["memberships"], ["dispatch"])
        self.assertEqual(lib["items"][0]["memberships"], ["catalog"])

    def test_pair_insufficiency_is_an_issue_even_if_label_agrees(self):
        lib = fixture()
        pairs = [{"pairs": [{"id": "unit01a-i01--unit01a-i02", "relation": "same",
                              "sufficiency": "needs-context", "evidence": "Fixture needs another source"}]}]
        issues = p1_release.collect_issues([lib], self.reviews(lib), pairs)
        self.assertEqual(len(issues), 1)
        decision = {"reviewer": "root-adjudicator", "method": "Read evidence", "decisions":
                    [{"id": issues[0]["id"], "resolution": "pair-uncertain", "reason": "Insufficient pair-only evidence"}]}
        final, overrides = p1_release.apply_decisions([lib], issues, decision)
        self.assertEqual(final, [lib])
        self.assertEqual(overrides["unit01a-i01--unit01a-i02"]["relation"], "uncertain")

    def test_missing_and_duplicate_adjudications_rejected(self):
        issues = [{"id": "x", "kind": "pair", "library": "unit01a"}, {"id": "y", "kind": "pair", "library": "unit01a"}]
        for decisions in ([], [{"id": "x"}, {"id": "x"}]):
            with self.assertRaisesRegex(ValueError, "unresolved"):
                p1_release.apply_decisions([fixture()], issues, {"reviewer": "root-adjudicator", "method": "test", "decisions": decisions})

    def test_unknown_resolution_rejected(self):
        with self.assertRaises(ValueError):
            p1_release.apply_decisions([fixture()], [{"id": "x", "kind": "pair", "library": "unit01a"}],
                                      {"reviewer": "root-adjudicator", "method": "test",
                                       "decisions": [{"id": "x", "resolution": "trust-majority", "reason": "test"}]})

    def test_explicit_link_adjudication_and_context_pair(self):
        lib = fixture()
        issues = [{"id": "links:unit01a", "kind": "links", "library": "unit01a"},
                  {"id": "pair:unit", "kind": "pair", "library": "unit01a"}]
        decision = {"reviewer": "root-adjudicator", "method": "Explicit source review", "decisions": [
            {"id": "links:unit01a", "resolution": "set-links", "relatedThreads": [], "reason": "No link in fixture variation"},
            {"id": "pair:unit", "resolution": "use-context-gold", "reason": "Derive from adjudicated links"}]}
        final, overrides = p1_release.apply_decisions([lib], issues, decision)
        self.assertEqual(final[0]["relatedThreads"], [])
        self.assertEqual(overrides, {})
        self.assertEqual(lib["relatedThreads"], [["catalog", "dispatch"]])

    def test_relation_links_are_not_transitive(self):
        links = {frozenset(("a", "b")), frozenset(("b", "c"))}
        self.assertEqual(p1_release.relation(["a"], ["c"], links), "unrelated")
        self.assertEqual(p1_release.relation(["a", "b"], ["c"], links), "related")
        self.assertEqual(p1_release.relation(["a", "b"], ["b", "c"], links), "same")
        self.assertEqual(p1_release.relation([], ["b"], links), "uncertain")

    def test_additional_consensus_correction_is_separate_and_nonmutating(self):
        lib = fixture()
        correction = {"library": lib["id"], "before": lib["relatedThreads"], "relatedThreads": [],
                      "resolution": "set-links", "reason": "Root found no supporting shared material in fixture variation"}
        adjudication = {"reviewer": "root-adjudicator", "method": "Explicit review", "decisions": [],
                        "additionalLinkDecisions": [correction]}
        final, _ = p1_release.apply_decisions([lib], [], adjudication)
        self.assertEqual(final[0]["relatedThreads"], [])
        self.assertEqual(lib["relatedThreads"], [["catalog", "dispatch"]])
        final[0]["relatedThreads"].append(["catalog", "dispatch"])
        self.assertEqual(correction["relatedThreads"], [])

    def test_additional_corrections_reject_bad_bindings_and_links(self):
        lib = fixture()
        correction = {"library": lib["id"], "before": lib["relatedThreads"], "relatedThreads": [],
                      "resolution": "set-links", "reason": "Explicit fixture evidence"}
        base = {"reviewer": "root-adjudicator", "method": "Explicit review", "decisions": []}
        for change in ({"library": "unknown"}, {"before": []}, {"reason": " "}, {"resolution": "vote"},
                       {"relatedThreads": [["catalog", "unknown"]]}, {"relatedThreads": [["catalog", "catalog"]]},
                       {"relatedThreads": [["catalog", "dispatch"], ["dispatch", "catalog"]]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                p1_release.apply_decisions([lib], [], base | {"additionalLinkDecisions": [correction | change]})
        with self.assertRaises(ValueError):
            p1_release.apply_decisions([lib], [], base | {"additionalLinkDecisions": [correction, correction]})
        issue = {"id": "links:" + lib["id"], "kind": "links", "library": lib["id"]}
        with self.assertRaises(ValueError):
            p1_release.apply_decisions([lib], [issue], base | {"decisions": [{"id": issue["id"], "resolution": "retain-author", "reason": "test"}],
                                                            "additionalLinkDecisions": [correction]})

    def test_membership_changes_trigger_fresh_pair_disposition(self):
        original = fixture()
        final = copy.deepcopy(original)
        final["items"][0]["memberships"] = ["dispatch"]
        reviews = [{"pairs": [{"id": "unit01a-i01--unit01a-i02", "relation": "same", "sufficiency": "sufficient", "evidence": "Originally same"}]}]
        required = p1_release.final_pair_requirements([original], [final], reviews, [])
        self.assertEqual(len(required), 1)
        self.assertEqual(required[0]["contextRelation"], "related")
        with self.assertRaisesRegex(ValueError, "explicit final"):
            p1_release.resolve_final_pairs(required, [], {})
        decided = [{"id": required[0]["id"], "resolution": "use-context-gold", "reason": "Checked final distinct objectives"}]
        self.assertEqual(p1_release.resolve_final_pairs(required, decided, {}), {})

    def test_changed_pair_is_rechecked_even_when_reviewer_agrees(self):
        original = fixture()
        final = copy.deepcopy(original)
        final["relatedThreads"] = []
        reviews = [{"pairs": [{"id": "unit01a-i01--unit01a-i06", "relation": "unrelated", "sufficiency": "sufficient", "evidence": "Different objectives"}]}]
        required = p1_release.final_pair_requirements([original], [final], reviews, [{"id": "pair:unit01a-i01--unit01a-i06"}])
        self.assertEqual(len(required), 1)
        self.assertEqual(required[0]["before"], "related")
        self.assertEqual(required[0]["contextRelation"], "unrelated")

    def test_final_pair_uncertainty_retains_context_memberships(self):
        required = [{"id": "pair:p", "pair": "p"}]
        decision = [{"id": "pair:p", "resolution": "pair-uncertain", "reason": "Insufficient pair-only evidence"}]
        self.assertEqual(p1_release.resolve_final_pairs(required, decision, {})["p"]["relation"], "uncertain")

    def gold(self):
        lib = fixture()
        policy = read(DATA / "contract.json") | {"requiredSplits": {"train": 1}, "librariesPerStoryFamily": 1}
        _, gold, _ = validate_corpus({"schemaVersion": 1, "purpose": "qualification-release", "libraries": [lib]}, policy, release=True)
        return lib, gold["pairs"]

    def test_independent_expansion_matches_projection(self):
        lib, gold = self.gold()
        self.assertEqual(p1_release.independent_pair_audit([lib], gold, {})["checkedPairs"], 190)
        key = gold[0]["id"]
        gold[0]["relation"] = "uncertain"
        self.assertTrue(p1_release.independent_pair_audit([lib], gold, {key: {"relation": "uncertain"}})["passed"])

    def test_audit_rejects_wrong_or_missing_gold(self):
        lib, gold = self.gold()
        for candidate in (gold[:-1], [gold[0]] + gold, [gold[0] | {"relation": "unrelated"}] + gold[1:]):
            with self.assertRaisesRegex(ValueError, "audit failed"):
                p1_release.independent_pair_audit([lib], candidate, {})


if __name__ == "__main__":
    unittest.main()
