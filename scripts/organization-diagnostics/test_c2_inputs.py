import copy
import hashlib
import unittest

import c2_inputs as c


def fixture():
    captures = [{"id": key, "memberships": projects} for key, projects in
                (("a", ["p1"]), ("b", ["p1"]), ("bridge", ["p1", "p2"]), ("target", []), ("z", ["p2"]))]
    events = [{"id": f"e-{item['id']}", "kind": "capture", "capture": item["id"], "dependsOn": []}
              for item in captures]
    events += [{"id": "revision", "kind": "revise", "target": "b", "dependsOn": ["e-b", "e-a"]},
               {"id": "correction", "kind": "correct", "target": "target",
                "dependsOn": ["revision", "e-target", "e-bridge", "e-z"]}]
    released = [{"id": event["id"], "kind": "capture", "source": {"id": event["capture"], "text": f"Text {event['capture']}", "modality": "note"}}
                for event in events[:5]]
    released += [{"id": "revision", "kind": "revise", "target": "b", "text": "Revised text b"},
                 {"id": "correction", "kind": "correct", "target": "target", "userRequestedProjects": ["p1", "p2"],
                  "reason": "Sensitive annotation omitted", "explicitUserAction": True}]
    return {"story": "synthetic", "order": "chronological", "events": released}, {"id": "synthetic", "captures": captures, "events": events}


class InputTests(unittest.TestCase):
    def test_transitive_lexical_single_project_anchors_and_projection(self):
        released, annotated = fixture()
        original = copy.deepcopy(released)
        result, audit = c.compile_stream(released, annotated)
        self.assertEqual(released, original)
        self.assertEqual(result["events"][-1], {"id": "correction", "kind": "correct", "target": "target", "targetAnchors": ["a", "z"]})
        self.assertEqual(audit[0]["eligibleAncestorCaptures"], ["a", "b"])
        self.assertEqual(audit[1]["eligibleAncestorCaptures"], ["z"])
        for event in result["events"]:
            self.assertNotIn("reason", event)
            self.assertNotIn("userRequestedProjects", event)

    def test_target_and_nondependency_sources_are_not_anchors(self):
        released, annotated = fixture()
        for item in annotated["captures"]:
            if item["id"] in {"a", "b"}:
                item["memberships"] = []
            elif item["id"] == "target":
                item["memberships"] = ["p1"]
        with self.assertRaisesRegex(ValueError, "No dependency anchor"):
            c.compile_stream(released, annotated)
        released, annotated = fixture()
        annotated["events"][-1]["dependsOn"] = ["e-target", "e-z", "e-bridge"]
        with self.assertRaisesRegex(ValueError, "No dependency anchor"):
            c.compile_stream(released, annotated)

    def test_dependency_order_and_cycles_fail(self):
        released, annotated = fixture()
        released["events"][-2], released["events"][-1] = released["events"][-1], released["events"][-2]
        with self.assertRaisesRegex(ValueError, "Dependency follows"):
            c.compile_stream(released, annotated)
        released, annotated = fixture()
        annotated["events"][0]["dependsOn"] = ["correction"]
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            c.compile_stream(released, annotated)

    def test_empty_correction_and_valid_shuffle(self):
        released, annotated = fixture()
        released["events"][-1]["userRequestedProjects"] = []
        result, audit = c.compile_stream(released, annotated)
        self.assertEqual(result["events"][-1]["targetAnchors"], [])
        self.assertEqual(audit, [])
        released, annotated = fixture()
        chronological, _ = c.compile_stream(released, annotated)
        released["order"] = "shuffle-1"
        released["events"][:5] = reversed(released["events"][:5])
        shuffled, _ = c.compile_stream(released, annotated)
        self.assertEqual(chronological["events"][-1], shuffled["events"][-1])

    def test_catalogue_all_cross_source_versions_and_deduplication(self):
        released, annotated = fixture()
        compiled, _ = c.compile_stream(released, annotated)
        result = c.catalogue([compiled, copy.deepcopy(compiled)])
        self.assertEqual(len(result["texts"]), 6)
        self.assertEqual(len(result["pairs"]), 14)
        digest = lambda value: hashlib.sha256(value.encode()).hexdigest()
        same_source = "--".join(sorted((digest("Text b"), digest("Revised text b"))))
        self.assertNotIn(same_source, result["pairs"])
        for other in ("a", "bridge", "target", "z"):
            cross_source = "--".join(sorted((digest(f"Text {other}"), digest("Revised text b"))))
            self.assertIn(cross_source, result["pairs"])
        self.assertEqual(result, c.catalogue([compiled]))

    def test_catalogue_no_cross_story_pairs_and_identical_text(self):
        source = lambda key, text: {"id": key, "kind": "capture", "source": {"id": key, "text": text, "modality": "note"}}
        streams = [{"story": "s1", "events": [source("a", "same"), source("b", "same")]},
                   {"story": "s2", "events": [source("a", "different")]}]
        result = c.catalogue(streams)
        self.assertEqual(len(result["texts"]), 2)
        self.assertEqual(len(result["pairs"]), 1)
        pair = next(iter(result["pairs"].values()))
        self.assertEqual(pair["first"], pair["second"])


if __name__ == "__main__":
    unittest.main()
