import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from organization_audio_diagnostic import distance, read, score, verify_binding, words, write_new


class AudioDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.inputs = {"schemaVersion": 1, "libraries": [{"id": "l", "split": "development", "items": [
            {"id": "audio", "kind": "audio", "referenceText": "one two three"},
            {"id": "image", "kind": "image", "referenceText": "not scored"}]}]}
        self.run = {"runID": "l-embedding-chronological-0", "libraryID": "l", "mode": "embedding",
                    "order": "chronological", "repeat": 0, "mediaMode": "extracted", "status": "completed",
                    "extractions": [{"itemID": "audio", "status": "completed", "text": "one four three"}]}
        self.results = {"schemaVersion": 1, "manifest": {"expectedRunIDs": [self.run["runID"]]}, "runs": [self.run]}

    def test_unicode_normalization_without_language_rewrites(self):
        self.assertEqual(words("CAFÉ, Straße! l'été twenty-one_42"), ["café", "strasse", "l", "été", "twenty", "one", "42"])
        self.assertNotEqual(words("café"), words("cafe"))
        self.assertNotEqual(words("twenty one"), words("21"))

    def test_word_edit_operations(self):
        self.assertEqual(distance([], []), 0)
        self.assertEqual(distance(["a", "b"], []), 2)
        self.assertEqual(distance([], ["a", "b"]), 2)
        self.assertEqual(distance(["a", "b", "c"], ["a", "x", "c"]), 1)
        self.assertEqual(distance(["a", "b"], ["b", "a"]), 2)

    def test_scores_audio_only_and_pools_edits(self):
        result = score(self.inputs, self.results)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["aggregate"]["corpusWordErrorRate"], 1 / 3)
        self.assertEqual(result["coverage"]["expectedAudioItems"], 1)

    def test_missing_failed_and_empty_remain_in_denominator(self):
        for state in ["missing_run", "failed_run", "missing_extraction", "failed_extraction", "empty"]:
            with self.subTest(state=state):
                results = copy.deepcopy(self.results)
                if state == "missing_run": results["runs"] = []
                elif state == "failed_run": results["runs"][0]["status"] = "timeout"
                elif state == "missing_extraction": results["runs"][0]["extractions"] = []
                elif state == "failed_extraction": results["runs"][0]["extractions"][0]["status"] = "blocked"
                else: results["runs"][0]["extractions"][0]["text"] = ""
                result = score(self.inputs, results)
                self.assertEqual(result["coverage"]["expectedAudioItems"], 1)
                self.assertEqual(result["aggregate"]["corpusWordErrorRate"], 1)

    def test_wer_can_exceed_one(self):
        self.run["extractions"][0]["text"] = "a b c d e f g"
        self.assertGreater(score(self.inputs, self.results)["items"][0]["wordErrorRate"], 1)

    def test_corpus_and_macro_weighting_are_distinct(self):
        self.inputs["libraries"][0]["items"].append({"id": "second", "kind": "audio", "referenceText": "a"})
        self.run["extractions"].append({"itemID": "second", "status": "completed", "text": "a"})
        result = score(self.inputs, self.results)
        self.assertEqual(result["aggregate"]["corpusWordErrorRate"], 1 / 4)
        self.assertEqual(result["aggregate"]["macroItemWordErrorRate"], 1 / 6)

    def test_duplicate_and_omitted_coverage_rejected(self):
        self.results["runs"].append(copy.deepcopy(self.run))
        with self.assertRaises(ValueError): score(self.inputs, self.results)
        self.results["runs"].pop()
        self.results["manifest"]["expectedRunIDs"] = []
        with self.assertRaises(ValueError): score(self.inputs, self.results)

    def test_hash_binding_and_refusal_to_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs, frozen, results = [root / name for name in ("inputs.json", "freeze.json", "results.json")]
            write_new(inputs, self.inputs)
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            write_new(frozen, {"schemaVersion": 1, "inputsSHA256": digest(inputs)})
            self.results["manifest"].update(inputsSHA256=digest(inputs), freezeSHA256=digest(frozen), mediaMode="extracted")
            write_new(results, self.results)
            verify_binding(inputs, frozen, results)
            archive = root / "results.json.gz"
            archive.write_bytes(gzip.compress(results.read_bytes(), mtime=0))
            self.assertEqual(read(archive), self.results)
            verify_binding(inputs, frozen, archive)
            with self.assertRaises(FileExistsError): write_new(inputs, {})
            inputs.write_text(json.dumps({**self.inputs, "changed": True}))
            with self.assertRaisesRegex(ValueError, "hash mismatch"): verify_binding(inputs, frozen, results)


if __name__ == "__main__":
    unittest.main()
