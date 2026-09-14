import copy
import unittest

import stories as s


def fixture():
    captures = [{"id": f"c{i:02d}", "modality": "note" if i % 2 else "image",
                 "text": f"Independent documented capture number {i} for its specified commission.",
                 "memberships": [f"p{(i - 1) % 3 + 1}"],
                 "rationale": "An explicitly identified continuing commission determines membership."}
                for i in range(1, 13)]
    events = [{"id": f"e{i:02d}", "kind": "capture", "capture": f"c{i:02d}", "dependsOn": []}
              for i in range(1, 13)]
    events += [
        {"id": "e13", "kind": "revise", "target": "c01", "text": "Corrected measurement for the same commission.", "dependsOn": ["e01"]},
        {"id": "e14", "kind": "correct", "target": "c02", "memberships": ["p3"],
         "reason": "Explicit user correction identifying the separate third commission.", "dependsOn": ["e02", "e03"]},
        {"id": "e15", "kind": "archive", "target": "c01", "dependsOn": ["e13"]},
        {"id": "e16", "kind": "restore", "target": "c01", "dependsOn": ["e15"]}]
    return {"schemaVersion": 1, "id": "story-test", "title": "Independent commissions",
            "threads": [{"id": f"p{i}", "title": f"Commission {i}", "scope": f"Distinct fictional commission {i}."} for i in range(1, 4)],
            "captures": captures, "events": events, "challenges": ["revision"], "authorNotes": "Unit fixture only."}


class StoryTests(unittest.TestCase):
    def test_valid_orders_have_equal_final_state(self):
        story = s.validate(fixture())
        finals, orders = [], []
        for mode in ("chronological", "shuffle-1", "shuffle-2"):
            events = s.ordered(story, mode)
            self.assertEqual(events, s.ordered(story, mode))
            _, prefixes = s.project(story, events)
            self.assertEqual(len(prefixes), 16)
            finals.append(prefixes[-1]["state"])
            orders.append(tuple(e["id"] for e in events))
        self.assertEqual(len(set(orders)), 3)
        self.assertEqual(finals[0], finals[1])
        self.assertEqual(finals[1], finals[2])
        self.assertEqual(finals[0]["c02"]["memberships"], ["p3"])
        self.assertEqual(finals[0]["c01"]["revision"], 1)

    def test_prefixes_do_not_leak_later_corrections(self):
        story = s.validate(fixture())
        inputs, prefixes = s.project(story, story["events"])
        self.assertEqual(set(prefixes[0]["state"]), {"c01"})
        self.assertEqual(prefixes[12]["state"]["c02"]["memberships"], ["p2"])
        self.assertEqual(prefixes[13]["state"]["c02"]["memberships"], ["p3"])
        self.assertTrue(prefixes[14]["state"]["c01"]["archived"])
        self.assertFalse(prefixes[15]["state"]["c01"]["archived"])
        for event in inputs[:12]:
            self.assertEqual(set(event["source"]), {"id", "modality", "text"})
        self.assertTrue(inputs[13]["explicitUserAction"])
        self.assertNotIn("memberships", inputs[13])

    def test_forward_and_missing_dependencies_fail(self):
        story = fixture()
        story["events"][0]["dependsOn"] = ["e02"]
        with self.assertRaises(ValueError):
            s.validate(story)
        story = fixture()
        story["events"][12]["dependsOn"] = []
        with self.assertRaisesRegex(ValueError, "target dependency"):
            s.validate(story)
        story = fixture()
        story["events"][14]["dependsOn"] = ["e01"]
        with self.assertRaisesRegex(ValueError, "chain"):
            s.validate(story)

    def test_correction_requires_project_evidence_dependency(self):
        story = fixture()
        story["events"][13]["dependsOn"] = ["e02"]
        with self.assertRaisesRegex(ValueError, "target project evidence"):
            s.validate(story)

    def test_invalid_restore_and_unknown_membership_fail(self):
        story = fixture()
        story["events"][14]["kind"] = "restore"
        with self.assertRaises(ValueError):
            s.validate(story)
        story = fixture()
        story["captures"][0]["memberships"] = ["not-a-project"]
        with self.assertRaises(ValueError):
            s.validate(story)

    def test_duplicate_capture_and_event_fail(self):
        story = fixture()
        story["events"][1]["capture"] = "c01"
        with self.assertRaises(ValueError):
            s.validate(story)
        story = fixture()
        story["events"][1]["id"] = "e01"
        with self.assertRaises(ValueError):
            s.validate(story)

    def test_reordered_dependency_violation_and_cycles_fail(self):
        story = fixture()
        with self.assertRaises(ValueError):
            s.project(story, list(reversed(story["events"])))
        story["events"][0]["dependsOn"] = ["e01"]
        with self.assertRaises(ValueError):
            s.ordered(story, "shuffle-1")

    def test_amendments_preserve_authorship_and_fail_on_changed_source(self):
        story = fixture()
        original = copy.deepcopy(story)
        amendment = {"decisions": [{"story": "story-test", "capture": "c04", "authored": ["p1"],
                                     "final": [], "rationale": "The initial capture does not identify its project sufficiently."}],
                     "dependencyAdditions": [{"story": "story-test", "event": "e13", "dependsOn": ["e02"]}]}
        updated = s.apply_adjudication(story, amendment)
        self.assertEqual(story, original)
        self.assertEqual(updated["captures"][3]["memberships"], [])
        self.assertEqual(updated["events"][12]["dependsOn"], ["e01", "e02"])
        amendment["decisions"][0]["authored"] = ["p2"]
        with self.assertRaises(ValueError):
            s.apply_adjudication(story, amendment)


if __name__ == "__main__":
    unittest.main()
