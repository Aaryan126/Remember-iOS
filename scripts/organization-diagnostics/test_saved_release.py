import hashlib
import unittest

import checkpoint as c


class SavedReleaseTests(unittest.TestCase):
    def test_all_saved_prefixes_observe_only_prior_events(self):
        prefix_count = 0
        for index in range(1, 13):
            identifier = f"story-{index:02d}"
            story = c.read(c.DATA / f"release/gold/{identifier}-adjudicated.json")
            events = {event["id"]: event for event in story["events"]}
            final_states = []
            for mode in ("chronological", "shuffle-1", "shuffle-2"):
                inputs = c.read(c.DATA / f"release/inputs/{identifier}-{mode}.json")["events"]
                gold = c.read(c.DATA / f"release/gold/{identifier}-{mode}.json")["prefixes"]
                self.assertEqual(len(inputs), len(gold))
                seen, captured, texts = set(), set(), {}
                for source, expected in zip(inputs, gold):
                    event = events[source["id"]]
                    self.assertLessEqual(set(event["dependsOn"]), seen)
                    self.assertEqual(source["id"], expected["after"])
                    if source["kind"] == "capture":
                        self.assertEqual(set(source["source"]), {"id", "text", "modality"})
                        captured.add(source["source"]["id"])
                        texts[source["source"]["id"]] = source["source"]["text"]
                    elif source["kind"] == "revise":
                        texts[source["target"]] = source["text"]
                    self.assertEqual(set(expected["state"]), captured)
                    for item, text in texts.items():
                        self.assertEqual(expected["state"][item]["textSHA256"], hashlib.sha256(text.encode()).hexdigest())
                    seen.add(source["id"])
                    prefix_count += 1
                final_states.append(gold[-1]["state"])
            self.assertEqual(final_states[0], final_states[1])
            self.assertEqual(final_states[1], final_states[2])
        self.assertEqual(prefix_count, 579)

    def test_specific_ambiguity_and_partial_link_cases(self):
        def states(story):
            return {row["after"]: row["state"] for row in c.read(c.DATA / f"release/gold/{story}-chronological.json")["prefixes"]}
        focus = states("story-11")
        self.assertEqual(focus["e08"]["c03"]["memberships"], [])
        self.assertEqual(focus["e11"]["c03"]["memberships"], ["p1"])
        permission = states("story-08")
        self.assertEqual(permission["e03"]["c03"]["memberships"], ["p1"])
        self.assertEqual(permission["e07"]["c03"]["memberships"], ["p1", "p2"])
        unresolved = states("story-09")
        self.assertEqual(unresolved["e15"]["c04"]["memberships"], [])

    def test_reviewed_dependency_fixes_hold_in_every_order(self):
        for story, earlier, later in (("story-04", "e01", "e02"), ("story-06", "e06", "e08"), ("story-12", "e04", "e05")):
            for mode in ("chronological", "shuffle-1", "shuffle-2"):
                sequence = [event["id"] for event in c.read(c.DATA / f"release/inputs/{story}-{mode}.json")["events"]]
                self.assertLess(sequence.index(earlier), sequence.index(later))


if __name__ == "__main__":
    unittest.main()
