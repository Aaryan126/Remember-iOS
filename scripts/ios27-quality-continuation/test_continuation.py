from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run as r


class ContinuationTests(unittest.TestCase):
    def test_exception_is_never_native(self):
        with self.assertRaisesRegex(ValueError, 'not a native'):
            r.native(r.EXCEPTION)

    def test_transport_disposition_is_error_not_abstention(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r, 'RUN', Path(tmp)):
            r.c.publish(r.RUN/'disposition.json', {'status': 'error', 'errorKind': 'transport-unknown-execution', 'prediction': None})
            value = r.outcome(r.q.old.packets()[0], r.EXCEPTION)
            self.assertEqual(value, {'status': 'error', 'errorKind': 'transport-unknown-execution', 'prediction': None})

    def test_original_checkpoint_is_unchanged(self):
        r.historical_verify()

    def test_remaining_schedule_has_no_retries(self):
        remaining = [u for u in r.q.schedule() if not r.completed(u)]
        self.assertNotIn(r.EXCEPTION, remaining)
        self.assertTrue(all(not u.startswith('control-') for u in remaining))
        self.assertTrue(all(not (r.ORIGINAL/f'units/phone/{u}.json').exists() for u in remaining))

    def test_unknown_attempt_counts_in_budget(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r, 'RUN', Path(tmp)):
            self.assertEqual(r.attempt_count(), 11)
            r.c.publish(r.RUN/'attempts/boundary-004/reserved.json', {})
            self.assertEqual(r.attempt_count(), 12)

    def test_unresolved_continuation_prevents_safe_shutdown_claim(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r, 'RUN', Path(tmp)), patch.object(r.c, 'active', return_value=False):
            self.assertTrue(r.safe_to_close())
            r.c.publish(r.RUN/'attempts/boundary-004/reserved.json', {})
            self.assertFalse(r.safe_to_close())
            r.c.publish(r.RUN/'units/boundary-004.json', {})
            self.assertTrue(r.safe_to_close())

    def test_pause_before_inference(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(r, 'RUN', Path(tmp)), patch.object(r.q, 'space'):
            r.c.publish(r.RUN/'pause.request.json', {})
            with self.assertRaises(InterruptedError):
                r.boundary()

    def test_incomplete_screen_cannot_pass(self):
        with patch.object(r, 'verify'), patch.object(r, 'completed', return_value=False):
            with self.assertRaisesRegex(ValueError, 'Incomplete'):
                r.evaluate()

    def test_full_evaluator_keeps_transport_error_in_denominator(self):
        controls = r.q.inputs()['controls']
        def fake_native(unit):
            if unit in controls:
                return {'status': 'ok', 'result': {'key': controls[unit]['key'], 'scores': {'fp16': {'accepted': False}, 'fp32': {'accepted': False}}}}
            return {'status': 'ok', 'result': {'output': {'verdict': 'abstain', 'evidence': [], 'rationale': 'Synthetic evaluator test.'}, 'generationSeconds': 1.0}}
        with tempfile.TemporaryDirectory() as tmp, patch.object(r, 'RUN', Path(tmp)), patch.object(r, 'verify'), \
                patch.object(r, 'completed', return_value=True), patch.object(r, 'native', side_effect=fake_native):
            r.c.publish(r.RUN/'disposition.json', {'status': 'error', 'errorKind': 'transport-unknown-execution', 'prediction': None})
            result = r.evaluate()
            self.assertFalse(any(result['gates'].values()))
            summary = r.c.read(r.RUN/'summary.json')
            counts = summary['adjudicated']['metrics']['c7']['all']['counts']
            self.assertEqual(counts['queries'], 160)
            self.assertGreaterEqual(counts['errors'], 1)
            self.assertEqual(summary['generationSeconds']['c7']['count'], 111)
            self.assertEqual(len(list((r.RUN/'predictions').glob('*.json'))), 15)

    def test_native_error_stops(self):
        with patch.object(r.q, 'schedule', return_value=['boundary-004']), patch.object(r, 'completed', return_value=True), \
                patch.object(r, 'native', return_value={'status': 'error'}):
            with self.assertRaisesRegex(ValueError, 'Native failure'):
                r.check_stops()

    def test_three_invalid_outputs_stop(self):
        units = ['boundary-004', 'boundary-005', 'c7-005']
        def fake_native(unit):
            request = r.q.inputs()['requests'][unit]
            return {'status': 'ok', 'result': {k: request[k] for k in ('context', 'reviewer')}}
        with patch.object(r.q, 'schedule', return_value=units), patch.object(r, 'completed', return_value=True), \
                patch.object(r, 'native', side_effect=fake_native):
            with self.assertRaisesRegex(ValueError, 'Three consecutive'):
                r.check_stops()


if __name__ == '__main__':
    unittest.main()
