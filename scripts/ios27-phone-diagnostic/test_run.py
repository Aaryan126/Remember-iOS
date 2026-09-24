import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('phone', Path(__file__).with_name('run.py'))
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)


class PhoneTests(unittest.TestCase):
    def test_scope(self):
        self.assertEqual(len(d.UNITS), 33)
        self.assertEqual(len(set(d.UNITS)), 33)
        self.assertNotIn('generation', d.UNITS)

    def test_numeric_failure_is_observation_not_pass(self):
        row = {'status':'ok','result':{'passed':False}}
        d.check_native(row, 'parity-00')
        self.assertFalse(row['result']['passed'])

    def test_native_error_stops(self):
        with self.assertRaises(ValueError): d.check_native({'status':'error'}, 'embedding-00')

    def test_embedding_mismatch_stops(self):
        with self.assertRaises(ValueError):
            d.check_native({'status':'ok','result':{'compatible':False}}, 'embedding-00')

    def test_unresolved_device_work_not_safe(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(d,'RUN',Path(temp)), patch.object(d.c,'safe_to_close',return_value=True):
            d.c.publish(d.RUN/'attempts/parity-01/reserved.json', {})
            self.assertFalse(d.safe_to_close())
            d.c.publish(d.RUN/'units/parity-01.json', {})
            self.assertTrue(d.safe_to_close())

    def test_no_blind_retry(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(d,'RUN',Path(temp)), patch.object(d,'verify'), patch.object(d,'boundary'), patch.object(d,'UNITS',['parity-01']), patch.object(d.c,'command') as command:
            d.c.publish(d.RUN/'manifest.json', {'device':'fictional-device'})
            d.c.publish(d.RUN/'attempts/parity-01/reserved.json', {})
            with self.assertRaises(ValueError): d.run(0)
            command.assert_not_called()

    def test_replay_skips_completed_inference(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(d,'RUN',Path(temp)), patch.object(d,'verify'), patch.object(d,'boundary'), patch.object(d,'UNITS',['parity-01']), patch.object(d.c,'command') as command:
            d.c.publish(d.RUN/'manifest.json', {'device':'fictional-device'})
            d.c.publish(d.RUN/'units/parity-01.json', {'result':{'status':'ok','result':{'passed':False}}})
            self.assertEqual(d.run(0), {'savedThisRun':0})
            command.assert_not_called()

    def test_incomplete_not_summarized(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(d,'RUN',Path(temp)), patch.object(d,'verify'):
            with self.assertRaises(ValueError): d.evaluate()


if __name__ == '__main__': unittest.main()
