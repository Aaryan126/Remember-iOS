import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('ios27_runner', Path(__file__).with_name('run.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.override = patch.object(r, 'RUN', self.root)
        self.override.start()

    def tearDown(self):
        self.override.stop()
        self.directory.cleanup()

    def test_immutable_checkpoint(self):
        p = self.root/'unit.json'
        r.publish(p, {'a': 1})
        before = (p.stat().st_mtime_ns, r.digest(p))
        r.publish(p, {'a': 1})
        self.assertEqual(before, (p.stat().st_mtime_ns, r.digest(p)))
        with self.assertRaises(ValueError): r.publish(p, {'a': 2})

    def test_non_finite_refused(self):
        with self.assertRaises(ValueError): r.publish(self.root/'bad.json', {'a': float('nan')})

    def test_exact_native_identity(self):
        value = {'schemaVersion': 1, 'unit': 'environment', 'syntheticOnly': True, 'status': 'ok'}
        line = 'IOS27_RESULT ' + json.dumps(value)
        self.assertEqual(r.parse_result(line, 'environment'), value)
        for text, unit in [(line, 'parity-00'), (line + '\n' + line, 'environment'), ('noise', 'environment')]:
            with self.assertRaises(ValueError): r.parse_result(text, unit)

    def test_schema_and_synthetic_boundary(self):
        for field, value in [('syntheticOnly', False), ('schemaVersion', 2), ('status', 'unknown')]:
            result = {'schemaVersion': 1, 'unit': 'environment', 'syntheticOnly': True, 'status': 'ok'}
            result[field] = value
            with self.assertRaises(ValueError): r.parse_result('IOS27_RESULT ' + json.dumps(result), 'environment')

    def test_lock_exclusive(self):
        with r.lock():
            self.assertTrue(r.active())
            self.assertFalse(r.safe_to_close())
        self.assertFalse(r.active())

    def test_pause_boundary(self):
        r.publish(self.root/'pause.request.json', {})
        with patch.object(r, 'space', return_value={}):
            with self.assertRaises(InterruptedError): r.boundary()

    def test_resource_reserve(self):
        with patch.object(r.shutil, 'disk_usage') as usage:
            usage.return_value.free = r.GIB
            with self.assertRaises(ValueError): r.space()

    def test_errors_are_not_passes(self):
        for unit, result in [('environment', {'status': 'error'}),
                             ('parity-00', {'status': 'ok', 'result': {'passed': False}}),
                             ('embedding-00', {'status': 'ok', 'result': {'compatible': False}})]:
            with self.assertRaises(ValueError): r.check_result(result, unit)

    def test_device_disconnect_is_not_safe_completion(self):
        r.publish(self.root/'attempts/phone/environment/reserved.json', {})
        self.assertFalse(r.safe_to_close())

    def test_completed_replay_does_not_execute(self):
        for unit in r.UNITS:
            value = {'status': 'ok', 'result': {'passed': True, 'compatible': True, 'decisionUnchanged': True}}
            r.publish(self.root/f'units/mac/{unit}.json', {'result': value})
        r.publish(self.root/'manifest.json', {})
        with patch.object(r, 'verify'), patch.object(r, 'space'), patch.object(r, 'command') as command:
            self.assertEqual(r.run('mac', None, 0)['savedThisRun'], 0)
            command.assert_not_called()

    def test_unknown_attempt_not_retried(self):
        r.publish(self.root/'manifest.json', {})
        r.publish(self.root/'attempts/mac/environment/reserved.json', {})
        with patch.object(r, 'verify'), patch.object(r, 'space'), patch.object(r, 'command') as command:
            with self.assertRaises(ValueError): r.run('mac', None, 0)
            command.assert_not_called()

    def test_failed_result_cannot_be_skipped_on_resume(self):
        r.publish(self.root/'manifest.json', {})
        r.publish(self.root/'units/mac/environment.json', {'result': {'status': 'error'}})
        with patch.object(r, 'verify'), patch.object(r, 'space'), patch.object(r, 'command') as command:
            with self.assertRaises(ValueError): r.run('mac', None, 0)
            command.assert_not_called()


if __name__ == '__main__':
    unittest.main()
