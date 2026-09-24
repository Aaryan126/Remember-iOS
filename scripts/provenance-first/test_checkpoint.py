from contextlib import ExitStack
import fcntl
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import checkpoint as cp
from fixtures import InvalidFixture, encoded, load, sha
from test_fixtures import sample_split


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.work = self.root / "Evaluation/ProvenanceFirst"
        self.work.mkdir(parents=True)
        self.code = self.root / "scripts/provenance-first"
        self.code.mkdir(parents=True)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in (("ROOT", self.root), ("CODE", self.code)):
            self.stack.enter_context(patch.object(cp, name, value))
        self.stack.enter_context(patch.object(cp, "resource_check", return_value={"test": True}))
        for name in ("CONTRACT.md", "FORMAT.md", "PLAN.md", "METRICS.md"):
            (self.work / name).write_text("Synthetic test instructions.")
        for split in ("development", "evaluation"):
            document = sample_split(split)
            path = self.work / "authored" / (split + ".json")
            cp.atomic(path, document)
            review = {"reviewer": "independent-test-reviewer", "author": "/root/pf_author_dev" if split == "development" else "/root/pf_author_eval",
                      "split": split, "inputSHA256": sha(path.read_bytes()), "crossLibraryIssues": [],
                      "libraries": [{"id": lib["id"], "verdict": "pass", "issues": []} for lib in document["libraries"]]}
            cp.atomic(self.work / "reviews" / (split + ".json"), review)
        cp.freeze(self.work)

    def test_pause_resume_does_not_recompute(self):
        cp.run(self.work, maximum=1)
        path = self.work / "units/dev01/receipt.json"
        before = (path.read_bytes(), path.stat().st_mtime_ns)
        self.assertEqual(load(self.work / "status.json")["status"], "paused")
        cp.run(self.work)
        self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))
        self.assertEqual(len(cp.verify_units(self.work)), 24)
        self.assertEqual(len(load(self.work / "runs/checkpoint1/input.json")["runs"]), 24)

    def test_pause_before_first_unit(self):
        cp.atomic(self.work / "pause.request.json", {"requested": True})
        cp.run(self.work)
        self.assertEqual(cp.verify_units(self.work), [])
        cp.run(self.work, maximum=1, resume=True)
        self.assertEqual(cp.verify_units(self.work), ["dev01"])

    def test_corrupt_output_rejected(self):
        cp.run(self.work, maximum=1)
        cp.atomic(self.work / "units/dev01/relationships.json", [])
        with self.assertRaisesRegex(InvalidFixture, "corrupt resumed"):
            cp.verify_units(self.work)
        with self.assertRaisesRegex(InvalidFixture, "corrupt resumed"):
            cp.run(self.work)

    def test_empty_receipt_output_set_rejected(self):
        cp.run(self.work, maximum=1)
        path = self.work / "units/dev01/receipt.json"
        value = load(path)
        value["outputs"] = {}
        cp.atomic(path, value)
        with self.assertRaisesRegex(InvalidFixture, "output set"):
            cp.run(self.work)

    def test_wrong_receipt_library_rejected(self):
        cp.run(self.work, maximum=1)
        path = self.work / "units/dev01/receipt.json"
        value = load(path)
        value["libraryId"] = "dev02"
        cp.atomic(path, value)
        with self.assertRaisesRegex(InvalidFixture, "library mismatch"):
            cp.verify_units(self.work)

    def test_changed_frozen_input_rejected(self):
        (self.work / "CONTRACT.md").write_text("Changed after freeze.")
        with self.assertRaisesRegex(InvalidFixture, "hashes changed"):
            cp.run(self.work)

    def test_stale_review_rejected(self):
        path = self.work / "reviews/evaluation.json"
        review = load(path)
        review["inputSHA256"] = "bad"
        cp.atomic(path, review)
        with self.assertRaisesRegex(InvalidFixture, "stale"):
            cp.reviewed(self.work)

    def test_author_cannot_review_own_split(self):
        path = self.work / "reviews/development.json"
        review = load(path)
        review["reviewer"] = review["author"]
        cp.atomic(path, review)
        with self.assertRaisesRegex(InvalidFixture, "independent"):
            cp.reviewed(self.work)

    def test_resume_does_not_clear_pause_if_hashes_invalid(self):
        marker = self.work / "pause.request.json"
        cp.atomic(marker, {"requested": True})
        (self.work / "FORMAT.md").write_text("Changed")
        with self.assertRaises(InvalidFixture):
            cp.run(self.work, resume=True)
        self.assertTrue(marker.exists())

    def test_concurrent_resume_cannot_cancel_pause(self):
        marker = self.work / "pause.request.json"
        cp.atomic(marker, {"requested": True})
        with (self.work / "worker.lock").open("a+") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError, "already running"):
                cp.run(self.work, resume=True)
            self.assertTrue(marker.exists())

    def test_status_never_claims_global_safe_from_compiler_only(self):
        self.assertFalse(cp.status(self.work)["safeToClose"])

    def test_native_verification_requires_complete_compilation(self):
        cp.run(self.work, maximum=1)
        with self.assertRaisesRegex(InvalidFixture, "incomplete"):
            cp.verify_native(self.work)


if __name__ == "__main__":
    unittest.main()
