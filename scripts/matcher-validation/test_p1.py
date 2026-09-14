import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import p1
import p1_history
from prepare import read, publish


def fixture():
    groups = [["catalog"]] * 5 + [["dispatch"]] * 5 + [["audit"]] * 4
    groups += [["catalog"], ["dispatch"], ["audit"], ["catalog", "dispatch"], ["catalog"], []]
    return {"id": "unit01a", "split": "train", "storyFamily": "unit01", "templateFamily": "unit-template",
            "threads": ["catalog", "dispatch", "audit"],
            "threadDescriptions": {"catalog": "Catalog stock", "dispatch": "Send stock", "audit": "Review accounts"},
            "relatedThreads": [["catalog", "dispatch"]], "challenges": ["bridge"],
            "items": [{"id": f"unit01a-i{index+1:02d}", "text": f"Original source number {index}. Its evidence has unique detail {index * 7}.",
                       "modality": ["note", "image", "voice"][index % 3], "memberships": members, "rationale": "Unit fixture, not benchmark content."}
                      for index, members in enumerate(groups)],
            "historyChecks": {"bridge": {"item": "unit01a-i18", "threads": ["catalog", "dispatch"]},
                              "revision": {"earlier": "unit01a-i01", "later": "unit01a-i05", "thread": "catalog"},
                              "rename": {"thread": "catalog", "from": "Catalog stock", "to": "Stock listing", "evidenceItem": "unit01a-i19"},
                              "undo": {"item": "unit01a-i02", "wrongThread": "audit", "reason": "Hypothetical incorrect assignment"}}}


class P1Tests(unittest.TestCase):
    def test_assignment_freeze(self):
        assigned = p1.assignment()
        self.assertEqual(len(assigned), 48)
        self.assertEqual(len({f["id"] for f in assigned.values()}), 24)

    def test_valid_library(self):
        lib = fixture()
        _, _, report = p1.validate_library(lib, {"id": "unit01", "split": "train", "libraries": ["unit01a", "unit01b"]})
        self.assertEqual(report["pairs"], 190)

    def test_history_chronology_and_membership(self):
        for field in ("earlier", "thread"):
            lib = fixture()
            lib["historyChecks"]["revision"][field] = "unit01a-i20" if field == "earlier" else "audit"
            with self.subTest(field=field), self.assertRaises(ValueError):
                p1.validate_history(lib)

    def test_history_preserves_both_revisions_and_bridge(self):
        history = p1_history.build(fixture())
        self.assertEqual(len(history["expected"]["memberships"]), 20)
        self.assertEqual(history["expected"]["memberships"]["unit01a-i18"], ["catalog", "dispatch"])
        self.assertEqual(history["expected"]["memberships"]["unit01a-i02"], ["catalog"])
        self.assertEqual(history["expected"]["threadNames"]["catalog"], "Stock listing")
        self.assertEqual(len(history["expected"]["revisions"]), 1)

    def test_invalid_history_undo_rejected(self):
        events = [{"type": "insert", "source": "x", "memberships": ["a"]},
                  {"type": "hypothetical-link", "source": "x", "thread": "b"}]
        with self.assertRaisesRegex(ValueError, "unfinished"):
            p1_history.replay(events, {"a": "A", "b": "B"})
        with self.assertRaisesRegex(ValueError, "does not match"):
            p1_history.replay(events + [{"type": "undo-link", "source": "x", "thread": "a"}], {"a": "A", "b": "B"})

    def test_unknown_history_operation_rejected(self):
        with self.assertRaises(ValueError):
            p1_history.replay([{"type": "merge"}], {})

    def test_sampling_is_deterministic_and_label_free(self):
        lib = fixture()
        sample = p1.pair_sample(lib)
        self.assertEqual(len(sample), 12)
        self.assertEqual(len({r["id"] for r in sample}), 12)
        for item in lib["items"]:
            item["memberships"], item["rationale"] = [], "Changed proposed labels"
        self.assertEqual(p1.pair_sample(lib), sample)
        self.assertEqual(set(sample[0]["first"]), {"id", "text", "modality"})

    def pair_review(self):
        packet = {"author": "author_a", "reviewer": "author_c", "pairs": p1.pair_sample(fixture())}
        review = {"author": "author_a", "reviewer": "author_c", "phase": "pair-first", "packetSHA256": "bound",
                  "pairs": [{"id": p["id"], "relation": "uncertain", "sufficiency": "needs-context", "evidence": "Only a test fixture"} for p in packet["pairs"]]}
        return packet, review

    def test_pair_review_requires_every_pair_and_correct_reviewer(self):
        packet, review = self.pair_review()
        p1.validate_pair_review(review, packet, "bound")
        for key, value in (("reviewer", "author_a"), ("packetSHA256", "wrong"), ("phase", "context")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                p1.validate_pair_review(review | {key: value}, packet, "bound")
        with self.assertRaises(ValueError):
            p1.validate_pair_review(review | {"pairs": review["pairs"][:-1]}, packet, "bound")

    def test_duplicate_review_does_not_cover_missing_pair(self):
        packet, review = self.pair_review()
        review["pairs"][-1] = review["pairs"][0]
        with self.assertRaises(ValueError):
            p1.validate_pair_review(review, packet, "bound")

    def test_context_requires_all_memberships(self):
        lib = fixture()
        packet = {"author": "author_a", "reviewer": "author_c", "libraries": [lib]}
        reviewed = {"id": lib["id"], "assignments": [{"id": i["id"], "memberships": i["memberships"], "reason": "Fixture"} for i in lib["items"]],
                    "relatedThreads": lib["relatedThreads"], "historyVerdict": "supported", "historyEvidence": "Fixture evidence"}
        review = {"author": "author_a", "reviewer": "author_c", "phase": "context", "packetSHA256": "bound", "libraries": [reviewed]}
        p1.validate_context_review(review, packet, "bound")
        reviewed["assignments"].pop()
        with self.assertRaises(ValueError):
            p1.validate_context_review(review, packet, "bound")

    def test_context_unavailable_until_pair_review_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            lib = fixture()
            publish(data / "authoring/unit01a.json", lib)
            with patch.object(p1, "DATA", data), patch.object(p1, "RUN", data / "run"), \
                 patch.object(p1, "capacity"), patch.object(p1, "author_libraries", return_value=[lib]):
                p1.project("author_a")
                with self.assertRaises(FileNotFoundError):
                    p1.seal_pairs("author_a")
                self.assertFalse((data / "run/packets/author_a-context.json").exists())
                packet_path = data / "run/packets/author_a-pairs.json"
                packet = read(packet_path)
                _, review = self.pair_review()
                review["packetSHA256"] = p1.digest(packet_path)
                publish(data / "reviews/author_c-pairs.json", review)
                p1.seal_pairs("author_a")
                context = read(data / "run/packets/author_a-context.json")
                self.assertNotIn("memberships", context["libraries"][0]["items"][0])
                self.assertNotIn("relatedThreads", context["libraries"][0])
                self.assertTrue((data / "run/receipts/author_a-pair-review.json").exists())


if __name__ == "__main__":
    unittest.main()
