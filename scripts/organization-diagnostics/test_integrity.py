import copy
import unittest

import integrity


class IntegrityTests(unittest.TestCase):
    def reports(self):
        libraries = [{"id": "library", "items": [{"id": "a"}, {"id": "b"}]}]
        row = {"id": "a--b", "first": "a", "second": "b", "library": "library", "relation": "same", "split": "evaluation", "score": .5}
        report = {"thresholds": {"baseline": .5, "hybrid": .5}, "predictions": {"baseline": [row], "hybrid": [copy.deepcopy(row)]}}
        return {"17": report}, libraries

    def test_report_id_split_probability_guards(self):
        reports, libraries = self.reports()
        integrity.validate_reports(reports, libraries)
        for field, bad in (("score", float("nan")), ("split", "train"), ("first", "other"), ("eligible", 1)):
            reports, libraries = self.reports()
            reports["17"]["predictions"]["hybrid"][0][field] = bad
            with self.assertRaises(ValueError):
                integrity.validate_reports(reports, libraries)
        reports, libraries = self.reports()
        reports["17"]["predictions"]["hybrid"] *= 2
        with self.assertRaises(ValueError):
            integrity.validate_reports(reports, libraries)

    def test_packet_injected_gold_or_text_changes_fail(self):
        original = {"pairs": [{"id": "r001", "text": "source evidence"}]}
        integrity.check_context(copy.deepcopy(original), original)
        for modified in ({"pairs": original["pairs"], "gold": "same"}, {"pairs": []}):
            with self.assertRaises(ValueError):
                integrity.check_context(modified, original)

    def test_saved_source_packets_reconstruct(self):
        self.assertTrue(integrity.verify()["sourceOnlyPacketsReconstructed"])


if __name__ == "__main__":
    unittest.main()
