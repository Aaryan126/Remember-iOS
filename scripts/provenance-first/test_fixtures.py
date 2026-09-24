from copy import deepcopy
import unittest

from fixtures import (InvalidFixture, alternate_events, compile_library, observed_inputs, observed_packet,
                      relationship_records, validate_library, validate_pair, validate_split)


def sample_library(identifier="dev01"):
    events = []
    def event(kind, source, memberships, disposition="confirmed", related=None, **extra):
        eid = f"e{len(events)+1:02d}"
        events.append({"id": eid, "kind": kind, "sourceId": source,
                       "dependsOn": [e["id"] for e in events],
                       "gold": {"memberships": memberships, "disposition": disposition,
                                "relatedProjects": related or [], "rationale": "Test-only declared oracle.", "evidence": []}, **extra})
        if kind == "capture" and disposition in {"confirmed", "related"}:
            events[-1]["gold"]["evidence"] = [{"sourceId": source, "revision": 0, "quote": extra["text"]}]
    event("capture", "s01", ["p1"], text=f"{identifier} project Alpha deadline Monday.", modality="note", locator="text")
    event("capture", "s02", ["p2"], text=f"{identifier} project Beta separately commissioned.", modality="pdf", locator="page 1")
    event("capture", "s03", ["p1", "p2"], text=f"{identifier} rota explicitly covers Alpha and Beta.", modality="photo", locator="image")
    event("capture", "s04", [], "unresolved", text=f"{identifier} that deadline changed.", modality="voice", locator="00:01")
    event("capture", "s05", [], "related", ["p1"], text=f"{identifier} unrelated-job template useful for Alpha.", modality="link", locator="paragraph 1")
    event("correct", "s04", ["p2"], assignments=["p2"], reason="User assigns the memo to Beta.")
    event("revise", "s01", ["p1"], text=f"{identifier} project Alpha deadline now Friday, replacing Monday.", locator="text")
    event("archive", "s03", ["p1", "p2"])
    event("restore", "s03", ["p1", "p2"])
    event("capture", "s06", [], "independent", text=f"{identifier} grocery list unrelated to work.", modality="note", locator="text")
    event("capture", "s07", ["p1"], text=f"{identifier} Alpha launch tasks.", modality="note", locator="text")
    event("revise", "s07", ["p1"], text=f"{identifier} Alpha launch tasks revised.", locator="text")
    tasks = []
    for index, (mode, at, source, revision, quote) in enumerate([
        ("current", "e07", "s01", 1, "deadline now Friday"),
        ("historical", "e07", "s01", 0, "deadline Monday"),
        ("overlap", "e09", "s03", 0, "covers Alpha and Beta"),
        ("uncertain", "e04", None, None, None)], 1):
        tasks.append({"id": f"q{index}", "atEvent": at, "mode": mode,
                      "question": f"Test evidence task {index}?", "answerable": source is not None,
                      "expectedEvidence": [] if source is None else [{"sourceId": source, "revision": revision, "quote": quote}],
                      "rationale": "Synthetic validator test, not benchmark data."})
    return {"id": identifier, "family": identifier + "-unit-test", "description": "Not evaluation data.",
            "projects": [{"id": "p1", "rootSourceId": "s01", "title": "Alpha"}, {"id": "p2", "rootSourceId": "s02", "title": "Beta"}],
            "events": events, "tasks": tasks}


def sample_split(split):
    prefix = "dev" if split == "development" else "eval"
    return {"schemaVersion": 1, "split": split, "libraries": [sample_library(f"{prefix}{i:02d}") for i in range(1, 13)]}


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.library = sample_library()

    def test_valid_lifecycle(self):
        prefixes = validate_library(self.library)
        self.assertEqual(prefixes["e04"][0]["s04"]["memberships"], [])
        self.assertEqual(prefixes["e06"][0]["s04"]["memberships"], ["p2"])

    def test_exact_future_quote_rejected(self):
        self.library["events"][3]["gold"]["evidence"] = [{"sourceId": "s01", "revision": 1, "quote": "Friday"}]
        with self.assertRaisesRegex(InvalidFixture, "future"):
            validate_library(self.library)

    def test_fabricated_quote_rejected(self):
        self.library["tasks"][0]["expectedEvidence"][0]["quote"] = "Tuesday"
        with self.assertRaisesRegex(InvalidFixture, "quotation"):
            validate_library(self.library)

    def test_implicit_reassignment_rejected(self):
        self.library["events"][6]["gold"]["memberships"] = ["p2"]
        with self.assertRaisesRegex(InvalidFixture, "implicit reassignment"):
            validate_library(self.library)

    def test_current_cannot_cite_old_revision(self):
        self.library["tasks"][1]["mode"] = "current"
        with self.assertRaisesRegex(InvalidFixture, "stale"):
            validate_library(self.library)

    def test_current_cannot_cite_archived_source(self):
        self.library["tasks"][2]["atEvent"] = "e08"
        with self.assertRaisesRegex(InvalidFixture, "archived"):
            validate_library(self.library)

    def test_dependency_enforced(self):
        self.library["events"][5]["dependsOn"] = []
        with self.assertRaisesRegex(InvalidFixture, "dependency"):
            validate_library(self.library)

    def test_unknown_project_rejected(self):
        self.library["events"][2]["gold"]["memberships"].append("p9")
        with self.assertRaisesRegex(InvalidFixture, "references"):
            validate_library(self.library)

    def test_archive_does_not_revise_source(self):
        compiled = compile_library(self.library)
        self.assertEqual(compiled["events"][7]["expectedState"]["localc03"]["revision"], 0)
        self.assertEqual(compiled["events"][7]["expectedState"]["localc03"]["memberships"], ["t:c01", "t:c02"])

    def test_unresolved_retains_singleton_not_project(self):
        compiled = compile_library(self.library)
        self.assertEqual(compiled["events"][3]["assignments"], ["t:c04"])
        self.assertEqual(compiled["events"][5]["assignments"], ["t:c02"])

    def test_source_only_export_has_no_gold(self):
        observed = observed_inputs(self.library)
        self.assertNotIn("projects", observed)
        for event in observed["events"]:
            self.assertNotIn("gold", event)
            self.assertNotIn("dependsOn", event)
        self.assertEqual(observed["events"][5]["assignedProjectRoots"], ["s02"])
        self.assertEqual(set(observed["queries"][0]), {"id", "atEvent", "question"})

    def test_proposals_do_not_mutate_ledger(self):
        records = relationship_records(self.library)
        self.assertEqual(records[4]["status"], "suggested")
        self.assertTrue(all(not r["mutatesProduction"] for r in records))

    def test_prefix_packet_has_no_future_or_labels(self):
        packet = observed_packet(self.library, "e04", "q4")
        self.assertEqual(len(packet["events"]), 4)
        self.assertNotIn("queries", packet)
        self.assertNotIn("expectedEvidence", str(packet))
        self.assertNotIn("assignments", str(packet))
        self.assertNotIn("dependsOn", str(packet))

    def test_query_cannot_bypass_prefix(self):
        with self.assertRaisesRegex(InvalidFixture, "prefix"):
            observed_packet(self.library, "e03", "q4")

    def test_empty_supported_evidence_rejected(self):
        self.library["events"][0]["gold"]["evidence"] = []
        with self.assertRaisesRegex(InvalidFixture, "needs source evidence"):
            validate_library(self.library)

    def test_correction_authority_survives_later_event(self):
        self.library["events"][11] = {"id": "e12", "kind": "archive", "sourceId": "s04",
                                       "gold": deepcopy(self.library["events"][5]["gold"]),
                                       "dependsOn": ["e11"]}
        validate_library(self.library)
        record = relationship_records(self.library)[-1]
        self.assertEqual(record["authority"], "explicit-user-correction")
        self.assertEqual(record["correctionEventId"], "e06")

    def test_deterministic_compilation(self):
        self.assertEqual(compile_library(self.library), compile_library(deepcopy(self.library)))

    def test_alternate_respects_dependencies(self):
        events = [{"id": "e01", "dependsOn": []}, {"id": "e02", "dependsOn": []}, {"id": "e03", "dependsOn": ["e01"]}]
        self.assertEqual([e["id"] for e in alternate_events(events)], ["e02", "e01", "e03"])

    def test_split_sizes_and_no_exact_leakage(self):
        a, b = sample_split("development"), sample_split("evaluation")
        validate_pair(a, b)
        b["libraries"][0]["events"][0]["text"] = a["libraries"][0]["events"][0]["text"]
        b["libraries"][0]["events"][0]["gold"]["evidence"][0]["quote"] = a["libraries"][0]["events"][0]["text"]
        with self.assertRaisesRegex(InvalidFixture, "leakage"):
            validate_pair(a, b)

    def test_same_family_across_splits_rejected(self):
        a, b = sample_split("development"), sample_split("evaluation")
        b["libraries"][0]["family"] = a["libraries"][0]["family"]
        with self.assertRaisesRegex(InvalidFixture, "family leakage"):
            validate_pair(a, b)

    def test_incomplete_split_rejected(self):
        document = sample_split("development")
        document["libraries"].pop()
        with self.assertRaises(InvalidFixture):
            validate_split(document)


if __name__ == "__main__":
    unittest.main()
