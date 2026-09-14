import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import checkpoint as c


class CheckpointTests(unittest.TestCase):
    def reports(self):
        rows = []
        for index, (relation, score) in enumerate((("related", .9), ("same", .1),
                                                  ("same", .9), ("unrelated", .1),
                                                  ("uncertain", .9))):
            rows.append({"id": str(index), "first": "a", "second": str(index), "library": "l",
                         "relation": relation, "score": score, "split": "evaluation"})
        return {seed: {"predictions": {"hybrid": copy.deepcopy(rows)}, "thresholds": {"hybrid": .5}}
                for seed in ("17", "29", "41")}

    def test_distinct_all_seed_sampling_and_stability(self):
        reports = self.reports()
        reports["29"]["predictions"]["hybrid"][0]["score"] = .1
        selected, counts = c.select(reports, count=1)
        self.assertEqual([r["stratum"] for r in selected], ["FP", "FN", "TP", "TN"])
        self.assertEqual(len({r["originalPair"] for r in selected}), 4)
        self.assertEqual(selected[0]["outcomes"]["29"], "TN")
        self.assertEqual(counts["TN"], 1)
        for report in reports.values():
            report["predictions"]["hybrid"].reverse()
        self.assertEqual((selected, counts), c.select(reports, count=1))

    def test_missing_strata_or_inconsistent_gold_fails(self):
        reports = self.reports()
        with self.assertRaisesRegex(ValueError, "Insufficient"):
            c.select(reports, count=2)
        reports["29"]["predictions"]["hybrid"][0]["relation"] = "same"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            c.select(reports, count=1)

    def test_boundary_and_eligibility(self):
        row = {"relation": "same", "score": .5}
        self.assertEqual(c.outcome(row, .5), "TP")
        self.assertEqual(c.outcome(row | {"eligible": False}, .5), "FN")
        self.assertEqual(c.outcome(row | {"score": None}, .5), "FN")
        self.assertIsNone(c.outcome(row | {"relation": "uncertain"}, .5))

    def test_atomic_publication_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "receipt.json"
            c.publish(path, {"a": 1})
            original = path.read_bytes()
            c.publish(path, {"a": 1})
            with self.assertRaises(ValueError):
                c.publish(path, {"a": 2})
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual([p.name for p in path.parent.iterdir()], ["receipt.json"])

    def test_review_validation_and_missing_context_gate(self):
        packet = {"pairs": [{"id": "r001"}]}
        review = {"schemaVersion": 1, "reviewer": "alpha", "phase": "pair", "packetSHA256": "test",
                  "judgments": [{"id": "r001", "relation": "same", "pairSufficient": True,
                                 "rationale": "The two captures identify the same continuing undertaking."}]}
        c.validate_review(review, packet, "alpha", "pair")
        with self.assertRaises(ValueError):
            c.validate_review(review | {"judgments": []}, packet, "alpha", "pair")
        review["judgments"][0]["relation"] = "uncertain"
        with self.assertRaises(ValueError):
            c.validate_review(review, packet, "alpha", "pair")
        with tempfile.TemporaryDirectory() as folder, patch.object(c, "DATA", Path(folder)):
            with self.assertRaisesRegex(ValueError, "Both pair reviews"):
                c.verify_pair_seals()

    def test_frozen_pair_packet_has_only_source_fields(self):
        packet = c.read(c.DATA / "packets/pairs.json")
        self.assertEqual(set(packet), {"schemaVersion", "phase", "pairs"})
        self.assertEqual(len(packet["pairs"]), 80)
        for row in packet["pairs"]:
            self.assertEqual(set(row), {"id", "first", "second"})
            for side in ("first", "second"):
                self.assertEqual(set(row[side]), {"id", "text", "modality"})


if __name__ == "__main__":
    unittest.main()
