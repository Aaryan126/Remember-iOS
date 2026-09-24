import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run as q


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.packet = q.old.packets()[0]
        self.prediction = q.prediction(self.packet, True)
        self.output = {k: self.prediction[k] for k in ('verdict', 'evidence')}
        self.output['rationale'] = 'Fictional validation fixture.'

    def test_schedule_unique_and_bounded(self):
        units = q.schedule()
        self.assertEqual(len(units), 288)
        self.assertEqual(len(set(units)), 288)
        self.assertEqual(sum(not u.startswith('control-') for u in units), 232)
        self.assertLessEqual(232+q.PRIOR_REQUESTS, q.CAP)

    def test_pilot_uses_primary_requests(self):
        self.assertEqual(q.schedule()[56:60], ['c7-000', 'boundary-000', 'boundary-001', 'c7-001'])
        self.assertTrue(all('repeat' not in u for u in q.schedule()[56:64]))

    def test_input_inventory_and_repeat_identity(self):
        data = q.inputs()
        self.assertEqual(len(data['requests']), 232)
        self.assertEqual(len(data['controls']), 56)
        self.assertEqual(set(q.schedule()), set(data['requests']) | set(data['controls']))
        for reviewer in q.REVIEWERS:
            for i in q.REPEATS:
                self.assertEqual(data['requests'][f'{reviewer}-{i:03}'], data['requests'][f'repeat-{reviewer}-{i:03}'])

    def test_no_gold_in_visible_payload(self):
        for row in q.inputs()['requests'].values():
            payload = q.c.json.loads(row['packet'])
            self.assertEqual(set(payload), {'pair', 'sources'})
            self.assertEqual(set(row), {'packet', 'instructions', 'context', 'reviewer'})
            self.assertLessEqual(len(row['packet']), 16000)

    def test_old_prompt_exact(self):
        self.assertEqual(q.inputs()['requests']['c7-000']['instructions'], q.old.PROMPT.read_text())

    def test_valid_prediction(self):
        native = {'status': 'ok', 'result': {'output': self.output}}
        self.assertEqual(q.interpretation(self.packet, native)['prediction'], self.prediction)

    def test_invalid_quote_is_error_not_abstention(self):
        self.output['evidence'][0]['quote'] = 'Not a verbatim source quotation.'
        result = q.interpretation(self.packet, {'status': 'ok', 'result': {'output': self.output}})
        self.assertEqual(result['status'], 'error')
        self.assertIsNone(result['prediction'])

    def test_decisive_requires_both_queried_sources(self):
        self.output['evidence'] = self.output['evidence'][:1]
        self.assertEqual(q.interpretation(self.packet, {'status': 'ok', 'result': {'output': self.output}})['status'], 'error')

    def test_native_error_stays_error(self):
        self.assertEqual(q.interpretation(self.packet, {'status': 'error'})['errorKind'], 'native')

    def test_extra_output_keys_rejected(self):
        self.output['confidence'] = 1.0
        self.assertEqual(q.interpretation(self.packet, {'status': 'ok', 'result': {'output': self.output}})['status'], 'error')

    def test_combiner_does_not_hide_error(self):
        error = {'status': 'error', 'errorKind': 'invalid-output', 'prediction': None}
        for mode in ('veto', 'confirm'):
            self.assertEqual(q.old.combine(self.prediction, error, mode), error)

    def test_gate_requires_all_conditions_and_net_fixes(self):
        context = {k: {'value': 1.0} for k in ('samePrecision', 'sameRecall', 'conflictPrecision', 'conflictRecall')}
        context.update({k: {'value': 0.0} for k in ('errorRate', 'unsupportedAssertionRate')})
        delta = {'context': {'fixed': 2, 'damaged': 1}}
        self.assertTrue(q.gate({'view:context': context}, delta)['passed'])
        delta['context']['damaged'] = 2
        self.assertFalse(q.gate({'view:context': context}, delta)['passed'])
        delta['context']['damaged'] = 1
        context['samePrecision']['value'] = .94
        self.assertFalse(q.gate({'view:context': context}, delta)['passed'])
        context['samePrecision']['value'] = None
        self.assertFalse(q.gate({'view:context': context}, delta)['passed'])

    def test_error_is_damage_not_fix(self):
        row = {'queryID': self.packet['queryID'], 'status': 'ok', 'prediction': self.prediction}
        bad = {'queryID': row['queryID'], 'status': 'error', 'prediction': None, 'errorKind': 'test'}
        delta = q.changes([self.packet], [{'queryID': row['queryID'], 'verdict': 'same_project'}], [row], [bad])
        self.assertEqual(delta[self.packet['view']]['damaged'], 1)
        self.assertEqual(delta[self.packet['view']]['fixed'], 0)

    def test_pause_and_unresolved_attempt_safety(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(q.c, 'RUN', Path(tmp)):
            q.c.publish(Path(tmp)/'attempts/phone/c7-000/reserved.json', {'unit': 'c7-000'})
            self.assertFalse(q.c.safe_to_close())
            q.c.publish(Path(tmp)/'units/phone/c7-000.json', {'status': 'error'})
            self.assertTrue(q.c.safe_to_close())
            q.c.publish(Path(tmp)/'pause.request.json', {})
            with self.assertRaises(InterruptedError):
                q.c.boundary()

    def test_three_invalid_outputs_stop(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(q.c, 'RUN', Path(tmp)):
            units = q.schedule()[56:59]
            for unit in units:
                request = q.inputs()['requests'][unit]
                native = {'status': 'ok', 'result': {k: request[k] for k in ('context', 'reviewer')}}
                q.c.publish(Path(tmp)/f'units/phone/{unit}.json', {'result': native})
            with self.assertRaisesRegex(ValueError, 'Three consecutive'):
                q.check_result(native, units[-1])

    def test_publication_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'unit.json'
            q.c.publish(path, {'answer': 1})
            before = path.stat().st_mtime_ns
            q.c.publish(path, {'answer': 1})
            self.assertEqual(path.stat().st_mtime_ns, before)
            with self.assertRaises(ValueError):
                q.c.publish(path, {'answer': 2})


if __name__ == '__main__':
    unittest.main()
