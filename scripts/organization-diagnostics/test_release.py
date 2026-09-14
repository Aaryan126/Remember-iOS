import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import checkpoint as c
import finalize
import review_stories
import stories
from test_stories import fixture


class ReleaseTests(unittest.TestCase):
    def setup_fixture(self, root, findings=None):
        c.publish(root / "CONTRACT.md", {"test": "contract"})
        c.publish(root / "STORY_AUTHORING.md", {"test": "specification"})
        authored = []
        for index in range(1, 13):
            story = fixture()
            story["id"] = f"story-{index:02d}"
            authored.append(story)
            c.publish(root / f"stories/{story['id']}.json", story)
        review_stories.prepare()
        review = {"schemaVersion": 1, "reviewer": "alpha", "packetSHA256": c.digest(root / "packets/stories.json"),
                  "stories": [{"id": story["id"], "assignments": [
                      {"capture": item["id"], "memberships": item["memberships"], "rationale": "Synthetic unit-test expected assignment; not a real review."}
                      for item in story["captures"]], "findings": (findings or []) if story["id"] == "story-01" else []} for story in authored]}
        c.publish(root / "reviews/alpha-stories.json", review)
        review_stories.seal()
        c.publish(root / "story-adjudication.json", {"schemaVersion": 1, "reviewSHA256": c.digest(root / "reviews/alpha-stories.json"),
                                                     "decisions": [], "findings": [], "dependencyAdditions": []})

    def test_tampered_authored_membership_blocked_before_output(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(c, "DATA", Path(folder)):
            root = Path(folder)
            self.setup_fixture(root)
            path = root / "stories/story-01.json"
            modified = c.read(path)
            modified["captures"][3]["memberships"] = []
            path.write_text(json.dumps(modified))
            with self.assertRaises(ValueError):
                stories.build()
            self.assertFalse((root / "release").exists())

    def test_tampered_review_blocked_even_with_updated_adjudication_hash(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(c, "DATA", Path(folder)):
            root = Path(folder)
            self.setup_fixture(root)
            path = root / "reviews/alpha-stories.json"
            modified = c.read(path)
            modified["stories"][0]["assignments"][0]["rationale"] = "Changed supposedly sealed reviewer statement."
            path.write_text(json.dumps(modified))
            adjudication = c.read(root / "story-adjudication.json")
            adjudication["reviewSHA256"] = c.digest(path)
            (root / "story-adjudication.json").write_text(json.dumps(adjudication))
            with self.assertRaises(ValueError):
                stories.build()
            self.assertFalse((root / "release").exists())

    def test_duplicate_shuffle_fails_without_publishing_partial_release(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(c, "DATA", Path(folder)):
            root = Path(folder)
            self.setup_fixture(root)
            with patch.object(stories, "ordered", side_effect=lambda story, mode: story["events"]):
                with self.assertRaisesRegex(ValueError, "Shuffles must differ"):
                    stories.build()
            self.assertFalse((root / "release").exists())

    def test_unknown_story_amendment_rejected(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(c, "DATA", Path(folder)):
            root = Path(folder)
            self.setup_fixture(root)
            path = root / "story-adjudication.json"
            value = c.read(path)
            value["dependencyAdditions"] = [{"story": "missing", "event": "e01", "dependsOn": [], "rationale": "Unknown story may not be silently ignored."}]
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                finalize.validate_story_adjudication()

    def test_missing_seal_not_recreated_during_build(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(c, "DATA", Path(folder)):
            root = Path(folder)
            self.setup_fixture(root)
            path = root / "receipts/alpha-stories.json"
            path.unlink()
            with self.assertRaisesRegex(ValueError, "Missing existing"):
                stories.build()
            self.assertFalse(path.exists())
            self.assertFalse((root / "release").exists())

    def test_unresolved_blocker_prevents_release(self):
        finding = {"severity": "blocker", "eventIds": ["e14"], "captureIds": ["c02"],
                   "issue": "The correction lacks its required clarification evidence dependency.",
                   "suggestion": "Add the clarification event as a dependency before releasing this fixture."}
        with tempfile.TemporaryDirectory() as folder, patch.object(c, "DATA", Path(folder)):
            root = Path(folder)
            self.setup_fixture(root, [finding])
            with self.assertRaisesRegex(ValueError, "Unresolved story findings"):
                stories.build()
            path = root / "story-adjudication.json"
            value = c.read(path)
            value["findings"] = [{"story": "story-01", "index": 0, "disposition": "accepted-limitation",
                                   "rationale": "Attempt to waive a blocking causal correctness defect."}]
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "Unresolved blocker"):
                stories.build()
            self.assertFalse((root / "release").exists())

    def test_pair_summary_does_not_claim_accuracy(self):
        result = finalize.pair_results()
        self.assertIsNone(result["summary"]["accuracyEstimate"])
        self.assertFalse(result["summary"]["oldQualificationChanged"])
        self.assertFalse(result["summary"]["retrievalEvaluated"])
        self.assertEqual(len(result["pairs"]), 80)
        for counts in result["summary"]["finalRelationsByHistoricalStratum"].values():
            self.assertEqual(sum(counts.values()), 20)

    def test_pair_adjudication_cannot_omit_disagreement(self):
        original_read = c.read
        def missing_decision(path):
            value = original_read(path)
            if path == c.DATA / "pair-adjudication.json":
                value["decisions"] = value["decisions"][:-1]
            return value
        with patch.object(c, "read", side_effect=missing_decision):
            with self.assertRaisesRegex(ValueError, "every contextual disagreement"):
                finalize.pair_results()


if __name__ == "__main__":
    unittest.main()
