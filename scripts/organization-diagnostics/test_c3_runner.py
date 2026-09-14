import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import c2_common as c
import c3_run as runner
from c3_metrics import score_fixed
from c3_policy import NEW, POLICIES, fixed_trace, run_stream
from test_c3_policy import capture, pair, retrieve, THRESHOLDS


class RunnerTests(unittest.TestCase):
    def test_pause_resume_preserves_c2_globals_and_c3_saved_unit(self):
        original = c.RUN
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            with patch.object(runner, "RUN", run), patch.object(c, "space", return_value={}):
                c.unit(run / "saved.json", {"completed": 1})
                before = c.digest(run / "saved.json")
                runner.pause()
                with self.assertRaises(c.Paused):
                    with runner.worker():
                        runner.boundary("fixture")
                with runner.worker(resume=True):
                    runner.boundary("resumed")
                self.assertFalse((run / "control/pause-requested.json").exists())
                self.assertEqual(before, c.digest(run / "saved.json"))
                self.assertEqual(len(list((run / "resumptions").glob("*.json"))), 1)
                self.assertEqual(c.RUN, original)

    def test_score_fixed_complete_scorer_coverage_and_gold_alignment(self):
        stream = {"story": "s", "order": "o", "events": [capture(1, "Ocean first"), capture(2, "Ocean later"), capture(3, "Forest separate")]}
        trace = run_stream(stream, NEW, pair, retrieve, THRESHOLDS)
        fixed = fixed_trace(trace, pair, retrieve, THRESHOLDS)
        gold = {"story": "s", "order": "o", "prefixes": []}
        for event in trace["events"]:
            state = copy.deepcopy(event["expectedState"])
            for key in state:
                state[key]["memberships"] = ["p" if key in ("c1", "c2") else "q"]
            gold["prefixes"].append({"after": event["id"], "state": state})
        scored = score_fixed(fixed, gold, THRESHOLDS)
        for policy in POLICIES:
            self.assertEqual(scored["counts"][policy]["contexts"], 3)
            self.assertEqual(scored["counts"][policy]["wrongEvents"], 0)
            self.assertEqual(scored["counts"][policy]["missedEvents"], 0)
        for scorer in ("baseline", "17", "29", "41"):
            self.assertEqual(scored["pairClassification"][scorer], {"TP": 1, "TN": 2})
        fixed["contexts"][-1]["prior"]["c1"]["revision"] = 99
        with self.assertRaisesRegex(ValueError, "state mismatch"):
            score_fixed(fixed, gold, THRESHOLDS)

    def test_missing_prediction_inventory_and_runtime_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(runner, "RUN", Path(directory)), patch.object(c, "runtime", return_value={"test": 1}):
                c.publish(runner.RUN / "manifest.json", {"runtime": {"test": 2}, "sources": {}})
                with self.assertRaisesRegex(ValueError, "runtime changed"):
                    runner.verify_manifest()
            with patch.object(runner, "RUN", Path(directory)), patch.object(runner, "verify_manifest", return_value={}), \
                 patch.object(runner, "prediction_files", return_value=[Path(directory) / "one.json"]):
                c.publish(runner.RUN / "predictions-complete.json", {"manifestSHA256": c.digest(runner.RUN / "manifest.json"), "files": {}})
                with self.assertRaisesRegex(ValueError, "inventory"):
                    runner.verify_predictions()


if __name__ == "__main__":
    unittest.main()
