from copy import deepcopy
import unittest
from unittest.mock import patch

import benchmark as b
import control as c


class FixtureBoundary(unittest.TestCase):
    def setUp(self):
        self.library = deepcopy(c.load(c.PF / "authored/development.json")["libraries"][0])
        for task in self.library["tasks"]:
            task["scope"] = "includeHistory" if task["mode"] == "historical" else "current"

    def test_observed_queries_strip_labels_keep_explicit_scope(self):
        packet = b.source_packet(self.library)
        for query in packet["queries"]:
            self.assertEqual(set(query), {"id", "atEvent", "question", "scope"})
        for event in packet["events"]:
            self.assertFalse(set(event) & {"gold", "dependsOn", "expectedState", "projects"})

    def test_native_queries_have_no_answer_labels(self):
        run = b.native_run(self.library)
        self.assertTrue(run["id"].startswith("history-"))
        for query in run["queries"]:
            self.assertEqual(set(query), {"id", "afterEvent", "scope", "limit"})
            self.assertEqual(query["limit"], 10000)

    def test_source_packet_does_not_mutate_author_fixture(self):
        prior = deepcopy(self.library)
        b.source_packet(self.library)
        b.native_run(self.library)
        self.assertEqual(self.library, prior)

    def test_archive_and_supersession_contract(self):
        # Minimal direct validator input; the independently tested legacy validator
        # is mocked only to exercise new history-specific guards in isolation.
        lib = {"id": "dev01", "events": [
            {"id":"e01", "sourceId":"s01", "kind":"capture"},
            {"id":"e02", "sourceId":"s01", "kind":"archive"}], "tasks": []}
        for index, mode in enumerate(("current", "historical", "overlap", "uncertain"), 1):
            lib["tasks"].append(dict(id=f"q{index}", mode=mode, answerable=mode!="uncertain",
                scope="includeHistory" if mode=="historical" else "current", atEvent="e02",
                expectedEvidence=[dict(sourceId="s01", revision=0)] if mode!="uncertain" else []))
        with patch.object(b, "validate_split"):
            b.validate_history_split({"libraries": [lib]})
            lib["id"] = "dev07"
            with self.assertRaisesRegex(ValueError, "superseded"): b.validate_history_split({"libraries": [lib]})
            lib["events"][1]["kind"] = "revise"
            b.validate_history_split({"libraries": [lib]})
            lib["tasks"][1]["scope"] = "current"
            with self.assertRaisesRegex(ValueError, "scope"): b.validate_history_split({"libraries": [lib]})


if __name__ == "__main__": unittest.main()
