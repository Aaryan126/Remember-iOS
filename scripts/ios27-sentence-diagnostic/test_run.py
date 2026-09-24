import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

s=importlib.util.spec_from_file_location('sentence',Path(__file__).with_name('run.py'))
d=importlib.util.module_from_spec(s); s.loader.exec_module(d)


class SentenceTests(unittest.TestCase):
    def test_bounded_scope(self):
        self.assertEqual(d.UNITS,['snapshot-0','snapshot-1'])
        self.assertNotEqual(d.BUNDLE,d.c.BUNDLE)

    def test_invalid_unit(self):
        with patch.object(d,'verify'),patch.object(d,'resources'):
            with self.assertRaises(ValueError): d.run('phone','generation')

    def test_replay_skips_inference(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(d,'RUN',Path(temp)),patch.object(d,'verify'),patch.object(d,'resources'),patch.object(d.c,'command') as command:
            d.c.publish(d.RUN/'units/phone/snapshot-0.json',{})
            self.assertFalse(d.run('phone','snapshot-0')['newInference'])
            command.assert_not_called()

    def test_unknown_attempt_not_retried(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(d,'RUN',Path(temp)),patch.object(d,'verify'),patch.object(d,'resources'),patch.object(d.c,'command') as command:
            d.c.publish(d.RUN/'attempts/phone/snapshot-0/reserved.json',{})
            with self.assertRaises(ValueError): d.run('phone','snapshot-0')
            command.assert_not_called()

    def test_failure_does_not_save_success(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(d,'RUN',Path(temp)),patch.object(d,'verify'),patch.object(d,'resources'),patch.object(d.c,'command',side_effect=d.subprocess.TimeoutExpired('probe',60)):
            with self.assertRaises(ValueError): d.run('mac','snapshot-0')
            self.assertTrue((d.RUN/'attempts/mac/snapshot-0/raw.json').exists())
            self.assertFalse((d.RUN/'units/mac/snapshot-0.json').exists())


if __name__=='__main__': unittest.main()
