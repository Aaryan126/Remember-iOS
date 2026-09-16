import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('diagnostic',Path(__file__).with_name('diagnose.py'))
d=importlib.util.module_from_spec(spec); spec.loader.exec_module(d)


class DiagnosticTests(unittest.TestCase):
    def test_stable_sigmoid(self):
        self.assertEqual(d.sigmoid(0), .5)
        self.assertEqual(d.sigmoid(1000), 1)
        self.assertEqual(d.sigmoid(-1000), 0)

    def test_independent_combiner(self):
        model={'intercept':0,'mean':[0,0],'scale':[1,1],'coefficient':[0,1]}
        self.assertAlmostEqual(d.combined([42], .8, model), .8)

    def test_neural_boundary_is_clamped(self):
        model={'intercept':0,'mean':[0],'scale':[1],'coefficient':[1]}
        self.assertAlmostEqual(d.combined([],0,model),1e-6)
        self.assertAlmostEqual(d.combined([],1,model),1-1e-6)

    def test_plan_is_bounded(self):
        self.assertEqual(len(d.KEYS),18)
        self.assertEqual(len(set(d.KEYS)),18)
        self.assertNotIn('generation',d.KEYS)

    def test_pause_stops_before_work(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(d,'RUN',Path(temp)), patch.object(d,'resources'):
            d.c.publish(Path(temp)/'pause.request.json',{})
            with self.assertRaises(InterruptedError): d.boundary()

    def test_unknown_attempt_not_retried(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(d,'RUN',Path(temp)), patch.object(d,'verify'), patch.object(d,'boundary'), patch.object(d.c,'command') as command:
            d.c.publish(Path(temp)/'units/parity-00.json',{})
            d.c.publish(Path(temp)/'attempts/parity-01/reserved.json',{})
            with self.assertRaises(ValueError): d.run(0)
            command.assert_not_called()

    def test_complete_run_replay_no_inference(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(d,'RUN',Path(temp)), patch.object(d,'verify'), patch.object(d,'boundary'), patch.object(d.c,'command') as command:
            for key in d.KEYS: d.c.publish(Path(temp)/f'units/{key}.json',{})
            self.assertEqual(d.run(0)['savedThisRun'],0)
            command.assert_not_called()

    def test_incomplete_results_not_passed(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(d,'RUN',Path(temp)), patch.object(d,'verify'):
            with self.assertRaises(ValueError): d.evaluate()


if __name__=='__main__': unittest.main()
