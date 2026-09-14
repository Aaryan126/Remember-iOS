import copy
import tempfile
import unittest
from pathlib import Path

from stage4_report import distribution, validate_timing
from stage4 import merge_export, run_path


class Stage4Tests(unittest.TestCase):
    def test_nearest_rank(self):
        self.assertEqual(distribution(list(range(1, 101)))["p95"], 95)
        self.assertEqual(distribution([4, 2])["median"], 3)

    def test_reject_missing_or_invalid_timings(self):
        for values in [[], [float("nan")], [float("inf")], [-1]]:
            with self.assertRaises(Exception): distribution(values)

    def test_complete_shortlist(self):
        fixtures = [{"id": str(i)} for i in range(104)]
        value = {"index": 10, "length": 256, "passes": 20, "fullShortlistSeconds": .7,
                 "tokenizationSeconds": .1, "modelPredictionSeconds": .5,
                 "pairs": [{"fixtureID": str((100+i) % 104), "averagedProbabilities": [.1, .2, .7]} for i in range(10)]}
        validate_timing(value, 256, 10, fixtures)
        for key, wrong in [("passes", 10), ("length", 512), ("index", 0), ("fullShortlistSeconds", .4), ("pairs", [])]:
            invalid = copy.deepcopy(value); invalid[key] = wrong
            with self.assertRaises(Exception): validate_timing(invalid, 256, 10, fixtures)
        invalid = copy.deepcopy(value); invalid["pairs"][0]["fixtureID"] = "wrong"
        with self.assertRaises(Exception): validate_timing(invalid, 256, 10, fixtures)
        invalid = copy.deepcopy(value); invalid["pairs"][0]["averagedProbabilities"] = [float("nan"), 0, 0]
        with self.assertRaises(Exception): validate_timing(invalid, 256, 10, fixtures)

    def test_resume_merge_keeps_exact_bytes_and_rejects_changed_records(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root / "source"; target = root / "target"
            source.mkdir(); (source / "one.json").write_bytes(b'{"v": 1}\n')
            merge_export(source, target)
            merge_export(source, target)
            self.assertEqual((target / "one.json").read_bytes(), b'{"v": 1}\n')
            (source / "one.json").write_bytes(b'{"v": 2}\n')
            with self.assertRaises(Exception): merge_export(source, target)
            self.assertEqual((target / "one.json").read_bytes(), b'{"v": 1}\n')

    def test_reject_broad_run_path(self):
        for value in ["/", "/tmp/stage-4-attempt-01", "Evaluation/MatcherFeasibility/runs/../stage-4-attempt-01"]:
            with self.assertRaises(Exception): run_path(value)


if __name__ == "__main__": unittest.main()
