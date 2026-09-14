import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import stage3_common as common
import stage3
from stage3_parity import comparison, summarize, fixture_requests
from stage3_build import phone_inputs


class Stage3Tests(unittest.TestCase):
    def test_nonfinite_conversion_rejected(self):
        for value in (float("nan"), float("inf")):
            with self.assertRaisesRegex(ValueError, "nonfinite"):
                comparison([[value, .3, .3]], [[.4, .3, .3]])

    def test_wrong_output_shape_rejected(self):
        with self.assertRaisesRegex(ValueError, "shape"):
            comparison([.4, .3, .3], [[.4, .3, .3]])

    def test_invalid_probability_mass_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid probability"):
            comparison([[.8, .3, .3]], [[.4, .3, .3]])

    def test_class_flip_detected_despite_small_delta(self):
        result = comparison([[.499, .501, 0]], [[.501, .499, 0]])
        self.assertFalse(result["classAgreement"])
        self.assertLess(result["maxProbabilityDifference"], .01)

    def test_99_percent_agreement_gate(self):
        rows = [{"maxProbabilityDifference": .001, "classAgreement": i != 0} for i in range(100)]
        self.assertTrue(summarize(rows)["passed"])
        rows[1]["classAgreement"] = False
        self.assertFalse(summarize(rows)["passed"])

    def test_maximum_delta_not_average(self):
        rows = [{"maxProbabilityDifference": 0, "classAgreement": True} for _ in range(99)]
        rows.append({"maxProbabilityDifference": .011, "classAgreement": True})
        self.assertFalse(summarize(rows)["passed"])

    def test_empty_parity_cannot_pass(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            summarize([])

    def test_fp16_attention_mask_regression(self):
        with np.errstate(over="ignore", invalid="ignore"):
            unsafe = np.array([0, 1], dtype=np.float16) * np.float16(np.finfo(np.float32).min)
        safe = np.array([0, 1], dtype=np.float16) * np.float16(-10000)
        self.assertFalse(np.isfinite(unsafe).all())
        self.assertTrue(np.isfinite(safe).all())

    def fixture_document(self):
        return {"fixtures": [{"id": f"fixture-{i}", "first": "A", "second": "B",
                              "gold": "same", "probabilities": [.8, .1, .1], "sourceIDs": ["private"]} for i in range(104)]}

    def test_phone_projection_removes_gold_and_predictions(self):
        projected = phone_inputs(self.fixture_document())
        self.assertEqual(set(projected), {"schemaVersion", "fixtures"})
        self.assertTrue(all(set(f) == {"id", "first", "second"} for f in projected["fixtures"]))

    def test_phone_projection_rejects_path_traversal(self):
        document = self.fixture_document()
        document["fixtures"][0]["id"] = "../bad"
        with self.assertRaisesRegex(ValueError, "unsafe"):
            phone_inputs(document)

    def test_phone_projection_requires_complete_unique_coverage(self):
        document = self.fixture_document()
        document["fixtures"][0]["id"] = document["fixtures"][1]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            phone_inputs(document)

    def test_all_reference_directions_and_lengths_covered(self):
        requests = fixture_requests()
        self.assertEqual(len(requests), 416)
        self.assertEqual(len({r["id"] for r in requests}), 416)
        self.assertEqual({r["length"] for r in requests}, {256, 512})

    def test_pause_saves_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            common.save(run / "manifest.json", {"stage": 3})
            stage3.request_pause(run)
            with self.assertRaises(common.Paused):
                common.boundary(run, "after-conversion")
            records = list((run / "pauses").glob("*.json"))
            self.assertEqual(common.read(records[0])["phase"], "after-conversion")

    def test_completed_run_pause_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            common.save(run / "manifest.json", {"stage": 3})
            common.save(run / "complete.json", {"stage": 3})
            self.assertEqual(stage3.request_pause(run), "already_complete_and_stopped")
            self.assertFalse((run / "control/pause-requested.json").exists())

    def test_integrity_rejects_changes_and_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            common.save(root / "fixture.json", {"value": 1})
            values = common.files_in(root)
            common.verify_files(root, values)
            values["fixture.json"] = "bad"
            with self.assertRaisesRegex(ValueError, "mismatch"):
                common.verify_files(root, values)
            with self.assertRaisesRegex(ValueError, "mismatch"):
                common.verify_files(root, {"../secret": "bad"})


class NativeTokenizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.executable = Path(cls.temporary.name) / "TokenizerProbe"
        result = subprocess.run(["xcrun", "swiftc", "-parse-as-library", "-O", str(common.HERE / "MatcherTokenizer.swift"),
                                 str(common.HERE / "Stage3TokenizerProbe.swift"), "-o", str(cls.executable)], capture_output=True, text=True)
        if result.returncode:
            cls.temporary.cleanup()
            raise AssertionError(result.stderr)
        manifest = common.read(common.DATA / "model-manifest.json")
        cls.vocabulary = common.WORKSPACE / manifest["workspaceRelativeDirectory"] / "vocab.txt"

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def tokens(self, first, second, length=256):
        request = {"id": "unit", "first": first, "second": second, "length": length}
        result = subprocess.run([str(self.executable), str(self.vocabulary)], input=json.dumps(request) + "\n",
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)["inputs"]

    def test_empty_second_is_single_sequence(self):
        result = self.tokens("", "")
        self.assertEqual(result["input_ids"][0][:4], [101, 102, 0, 0])
        self.assertEqual(sum(result["attention_mask"][0]), 2)

    def test_whitespace_second_remains_pair(self):
        result = self.tokens("", " ")
        self.assertEqual(result["input_ids"][0][:4], [101, 102, 102, 0])
        self.assertEqual(result["token_type_ids"][0][:4], [0, 0, 1, 0])

    def test_longest_first_preserves_original_length_order(self):
        a = self.tokens("alpha " * 800, "beta " * 700)
        b = self.tokens("alpha " * 700, "beta " * 800)
        self.assertEqual(sum(a["token_type_ids"][0]), 127)
        self.assertEqual(sum(b["token_type_ids"][0]), 128)

    def test_equal_length_truncation_tie(self):
        result = self.tokens("alpha " * 700, "beta " * 700)
        self.assertEqual(sum(result["token_type_ids"][0]), 128)

    def test_literal_special_tokens_not_lowercased(self):
        result = self.tokens("[CLS][MASK]", "")
        self.assertEqual(result["input_ids"][0][:4], [101, 101, 103, 102])

    def test_canonical_accents_match(self):
        self.assertEqual(self.tokens("Café façade", ""), self.tokens("Cafe\u0301 facade", ""))

    def test_overlong_word_is_one_unknown(self):
        result = self.tokens("x" * 101, "")
        self.assertEqual(result["input_ids"][0][:3], [101, 100, 102])


if __name__ == "__main__":
    unittest.main()
