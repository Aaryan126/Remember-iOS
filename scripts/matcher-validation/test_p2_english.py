import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import p2
import p2_common as c
import p2_data as data
import p2_english as english


class EnglishAmendmentTests(unittest.TestCase):
    def test_provider_only_changes_language_guard(self):
        source = (c.ROOT / "Remember/Remember/ProjectIntelligence.swift").read_text()
        body = english.english_provider(source)
        self.assertEqual(body.count("let language = NLLanguage.english"), 1)
        original = (english.OLD_EXTERNAL / "probe/ProductionEmbedding.swift").read_text()
        self.assertEqual(body.replace("let language = NLLanguage.english", english.LANGUAGE_GUARD), original)

    def test_missing_or_duplicate_guard_rejected(self):
        source = (c.ROOT / "Remember/Remember/ProjectIntelligence.swift").read_text()
        for replacement in ("", english.LANGUAGE_GUARD * 2):
            with self.assertRaisesRegex(ValueError, "exactly one"):
                english.english_provider(source.replace(english.LANGUAGE_GUARD, replacement))

    def test_scoped_overrides_restore_after_failure(self):
        old = (c.RUN, c.EXTERNAL, c.verify, data.probe, p2.run, p2.prepare)
        with self.assertRaises(RuntimeError):
            with english.adapted():
                self.assertEqual(c.RUN, english.NEW_RUN)
                self.assertEqual(c.EXTERNAL, english.NEW_EXTERNAL)
                self.assertIs(data.probe, english.probe)
                raise RuntimeError("fixture")
        self.assertEqual((c.RUN, c.EXTERNAL, c.verify, data.probe, p2.run, p2.prepare), old)

    def test_evaluation_stays_gated(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(english, "NEW_RUN", Path(folder)):
            with english.adapted(), self.assertRaisesRegex(ValueError, "evaluation forbidden"):
                c.split_data("evaluation")

    def records(self):
        value = {"status": "ok", "space": "apple-dual:en:fixture", "textSHA256": "fixture",
                 "contextual": [1.] + [0.] * 511, "sentence": [1.] + [0.] * 511}
        return {"a": value}

    def test_exact_parity_and_restoration(self):
        current = self.records()
        self.assertEqual(english.compare_embeddings(current, current)["exactlyUnchanged"], ["a"])
        previous = {"a": {"status": "unavailable", "textSHA256": "fixture"}}
        self.assertEqual(english.compare_embeddings(previous, current)["restored"], ["a"])

    def test_incomplete_or_changed_vectors_rejected(self):
        for change in ({"status": "unavailable"}, {"space": "apple-dual:nl:fixture"},
                       {"contextual": [0.] * 512}, {"sentence": [float("nan")] * 512},
                       {"textSHA256": "changed"}, {"sentence": [0., 1.] + [0.] * 510}):
            original = self.records()
            with self.subTest(change=list(change)), self.assertRaises(ValueError):
                english.compare_embeddings(original, {"a": original["a"] | change})

    def test_manifest_binds_amendment_and_original(self):
        with english.adapted():
            bindings = c.source_bindings()
        for suffix in ("p2_english.py", "test_p2_english.py", "P2_ENGLISH_AMENDMENT.md",
                       "runs/validation-01/manifest.json", "p2.py"):
            self.assertTrue(any(path.endswith(suffix) for path in bindings))

    def test_inventory_detects_changed_or_added_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            c.publish(root / "first.json", {"fixture": 1})
            before = english.inventory(root)
            c.publish(root / "second.json", {"fixture": 2})
            self.assertNotEqual(before, english.inventory(root))


if __name__ == "__main__":
    unittest.main()
