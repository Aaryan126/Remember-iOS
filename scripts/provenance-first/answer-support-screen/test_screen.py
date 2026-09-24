"""Deterministic screen tests using frozen fixtures and mocked process outputs."""
from contextlib import ExitStack
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock,patch
import sb_control as c
import sb_data as d
import sb_generation as g
import sb_metrics as m
import sb_runner as runner


def oracle_units(split):
    tasks={(lib['id'],t['id']):t for lib in d.libraries(split) for t in lib['tasks']}
    result={}
    for spec in d.specs(split):
        gold=m.p.packet_gold(tasks[(spec['library'],spec['question'])]['gold'],spec['packet'])
        targets=gold['missingEvidence'] if gold['verdict']=='explicit_missing' else gold['answers']
        references=[]
        for evidence in targets:
            candidate=next(r for r in spec['packet']['candidates'] if r['sourceId']==evidence['sourceId']
                           and r['revision']==evidence['revision'] and evidence['quote'] in r['quote'])
            reference=dict(candidateID=candidate['id'],quote=evidence['quote'])
            if reference not in references:references.append(reference)
        output=dict(verdict=gold['verdict'],answer=targets[0]['answerSpans'][0] if gold['verdict']=='supported' else '',
                    evidence=references[:3])
        result[spec['id']]=dict(id=spec['id'],failure=None,validationError=None,
                              terminal=dict(status='ok',output=output,elapsedSeconds=1,peakResidentBytes=1024))
    return result


class MetricTests(unittest.TestCase):
    def test_schedules_have_fixed_repeats_and_no_mutation(self):
        for split in d.SPLITS:
            rows=d.schedule(split)
            self.assertEqual(len(rows),68)
            self.assertEqual(rows,d.specs(split))
            for spec in rows[-4:]:
                original=next(r for r in rows if r['id']==spec['repeatOf'])
                self.assertEqual(original['packet'],spec['packet'])

    def test_prompt_has_no_labels_answers_scores_or_category(self):
        spec=deepcopy(d.specs('development')[0])
        spec['packet'].update(gold='SENTINEL',category='SENTINEL',allScores='SENTINEL')
        value=g.request(spec)
        self.assertNotIn('SENTINEL',json.dumps(value))
        self.assertEqual(value['instructions'],c.generation.instructions())
        self.assertEqual(set(json.loads(value['packet'])),{'question','scope','candidates'})

    def test_no_truncation_or_historical_leakage(self):
        for change in [dict(quote='a'*801),dict(isArchived=True),dict(isCurrentVersion=False)]:
            spec=deepcopy(d.specs('development')[0]);spec['packet']['scope']='current'
            spec['packet']['candidates'][0].update(change)
            with self.assertRaises(ValueError):g.request(spec)

    def test_oracle_scores_retrieval_misses_and_preserves_denominators(self):
        units=oracle_units('development');before=deepcopy(units)
        result=m.evaluate('development',units)
        self.assertEqual(result['metrics']['queries'],64)
        self.assertEqual(result['metrics']['correctAnswers'],30)
        self.assertEqual(result['metrics']['answerable'],32)
        self.assertEqual(result['metrics']['retrievedSupport'],30)
        self.assertTrue(result['qualified'])
        self.assertEqual(units,before)

    def test_empty_answers_do_not_qualify(self):
        units=oracle_units('development')
        for row in units.values():row['terminal']['output']=dict(verdict='not_established',answer='',evidence=[])
        result=m.evaluate('development',units)
        self.assertFalse(result['qualified']);self.assertEqual(result['metrics']['correctAnswers'],0)
        self.assertFalse(result['gates']['coverage']);self.assertFalse(result['gates']['precision'])

    def test_validation_error_keeps_raw_false_support_and_source_list(self):
        units=oracle_units('development')
        target=next(spec for spec in d.specs('development') if spec['repeatOf'] is None
                    and units[spec['id']]['terminal']['output']['verdict']=='explicit_missing')
        units[target['id']]['terminal']['output']=dict(verdict='supported',answer='invented',
            evidence=[dict(candidateID='unknown',quote='invented')])
        result=m.evaluate('development',units)
        self.assertEqual(result['metrics']['errors'],1)
        self.assertEqual(result['metrics']['rawFalseSupport'],1)
        self.assertEqual(result['metrics']['falseSupport'],0)
        self.assertEqual(result['sourceListsAvailable'],64)

    def test_native_error_cannot_be_successful_abstention(self):
        units=oracle_units('development');key=d.specs('development')[0]['id']
        units[key]['terminal']['status']='error'
        result=m.evaluate('development',units)
        self.assertEqual(result['metrics']['errors'],1)
        self.assertEqual(result['metrics']['correctAnswers'],29)
        self.assertEqual(result['metrics']['queries'],64)

    def test_repeat_mismatch_fails_gate(self):
        units=oracle_units('development');key=d.specs('development')[-1]['id']
        units[key]['terminal']['output']=dict(verdict='not_established',answer='',evidence=[])
        result=m.evaluate('development',units)
        self.assertFalse(result['gates']['repeats']);self.assertFalse(result['qualified'])

    def test_incomplete_split_cannot_decide(self):
        units=oracle_units('development');units.pop(next(iter(units)))
        with self.assertRaisesRegex(ValueError,'incomplete'):m.evaluate('development',units)

    def test_cluster_intervals_deterministic_and_undefined_safe(self):
        rows=[dict(library=str(i),goldVerdict='supported',verdict=None,correct=False) for i in range(8)]
        first=m.bootstrap(rows,draws=20)
        self.assertEqual(first,m.bootstrap(rows,draws=20))
        self.assertEqual(first['intervals']['precision']['validDraws'],0)
        self.assertIsNone(first['intervals']['precision']['low'])
        self.assertEqual(first['intervals']['recall']['high'],0)

    def test_baseline_is_source_selection_not_answer_accuracy(self):
        value=d.baselines('development')
        self.assertEqual(value['R0']['retrievedSupport'],30)
        self.assertIsNone(value['R0']['precision'])
        self.assertEqual(value['R1']['correctSelections'],20)
        self.assertEqual(value['R1']['assertions'],30)
        self.assertIsNone(value['R1']['exactAnswerAccuracy'])


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        root=Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        self.spec=deepcopy(d.specs('development')[0])
        self.stack.enter_context(patch.object(c,'WORK',root/'work'))
        self.stack.enter_context(patch.object(c,'RUN',root/'run'))
        self.stack.enter_context(patch.object(c,'verify_frozen',return_value={}))
        self.stack.enter_context(patch.object(c,'boundary',return_value={}))
        self.stack.enter_context(patch.object(d,'specs',return_value=[self.spec]))
        self.stack.enter_context(patch.object(g,'reservations',return_value=([Path(str(i)) for i in range(9)],[])))
        c.publish(c.WORK/'frozen.json',dict(mock=True))
        self.runtime=g.request(self.spec)['expectedRuntime']

    def output(self):
        return dict(verdict='not_established',answer='',evidence=[])

    def launch(self,missing=False,refusal=False):
        process=MagicMock();process.poll.return_value=process.returncode=0
        terminal=dict(schemaVersion=1,unit=self.spec['id'],syntheticOnly=True,
            status='error' if refusal else 'ok',output=None if refusal else self.output(),runtime=self.runtime,
            nativeDeadlineSeconds=60,cancellationGraceSeconds=2)
        def spawn(*args,**kwargs):
            kwargs['stdout'].write(('no terminal\n' if missing else 'ANSWER_SUPPORT_RESULT '+json.dumps(terminal)+'\n').encode())
            return process
        return spawn

    def dispatch(self,**kwargs):
        with patch.object(g.subprocess,'Popen',side_effect=self.launch(**kwargs)):return g.dispatch(self.spec)

    def test_success_reserves_tenth_lifetime_call(self):
        row=self.dispatch()
        reservation=c.load(c.WORK/'reservations'/(self.spec['id']+'.json'))
        self.assertEqual(reservation['cumulativeRequests'],10)
        self.assertTrue(row['executionKnown']);self.assertTrue(row['hostProcessExited'])

    def test_resume_skips_and_preserves_saved_units(self):
        first=self.dispatch();path=c.WORK/'units'/(self.spec['id']+'.json');mtime=path.stat().st_mtime_ns
        with patch.object(g.subprocess,'Popen') as spawn:self.assertEqual(first,g.dispatch(self.spec));spawn.assert_not_called()
        self.assertEqual(path.stat().st_mtime_ns,mtime)

    def test_unknown_execution_spent_not_retried(self):
        with self.assertRaisesRegex(ValueError,'unknown execution'):self.dispatch(missing=True)
        self.assertFalse(g.read(self.spec)['executionKnown'])
        with patch.object(g.subprocess,'Popen') as spawn:
            self.assertFalse(g.dispatch(self.spec)['executionKnown']);spawn.assert_not_called()

    def test_unresolved_reservation_never_retried(self):
        c.publish(c.WORK/'reservations'/(self.spec['id']+'.json'),{})
        with patch.object(g.subprocess,'Popen') as spawn:
            with self.assertRaisesRegex(ValueError,'unresolved'):g.dispatch(self.spec)
            spawn.assert_not_called()

    def test_known_refusal_saved_as_error(self):
        row=self.dispatch(refusal=True)
        self.assertEqual(row['terminal']['status'],'error');self.assertIsNotNone(row['validationError'])
        self.assertEqual(row,g.read(self.spec))

    def test_raw_tamper_detected(self):
        self.dispatch();raw=c.RUN/'raw'/(self.spec['id']+'.log');raw.write_text('tampered')
        with self.assertRaisesRegex(ValueError,'changed'):g.read(self.spec)

    def test_pause_before_dispatch_spends_nothing(self):
        with patch.object(c,'boundary',side_effect=c.Paused()):
            with self.assertRaises(c.Paused):g.dispatch(self.spec)
        self.assertFalse((c.WORK/'reservations').exists())

    def test_cumulative_budget(self):
        with patch.object(g,'reservations',return_value=([Path(str(i)) for i in range(9)],[Path(str(i)) for i in range(136)])):
            with self.assertRaisesRegex(ValueError,'budget'):g.dispatch(self.spec)

    def test_split_budget(self):
        with patch.object(g,'reservations',return_value=([Path(str(i)) for i in range(9)],
                [Path('development-'+str(i)+'.json') for i in range(68)])):
            with self.assertRaisesRegex(ValueError,'split request'):g.dispatch(self.spec)

    def test_modified_or_out_of_order_packet_rejected(self):
        changed=deepcopy(self.spec);changed['packet']['question']='changed'
        with self.assertRaisesRegex(ValueError,'frozen schedule'):g.dispatch(changed)
        preceding=dict(self.spec,id='preceding')
        with patch.object(d,'specs',return_value=[preceding,self.spec]):
            with self.assertRaisesRegex(ValueError,'out-of-order'):g.dispatch(self.spec)

    def test_evaluation_forbidden_on_failed_development(self):
        self.spec['split']='evaluation'
        with patch.object(runner,'verify_decision',return_value=dict(qualified=False)),patch.object(g.subprocess,'Popen') as spawn:
            with self.assertRaisesRegex(ValueError,'evaluation forbidden'):g.dispatch(self.spec)
            spawn.assert_not_called()

    def test_decision_recomputed_not_trusted(self):
        c.publish(c.WORK/'decisions/development.json',dict(qualified=True))
        with patch.object(runner,'result',return_value=dict(qualified=False)):
            with self.assertRaisesRegex(ValueError,'differs'):runner.verify_decision('development')

    def test_host_timeout_stops_process_and_saves_attempt(self):
        process=MagicMock();state=dict(stopped=False)
        process.poll.side_effect=lambda:0 if state['stopped'] else None
        process.returncode=None
        def stop(owned):state['stopped']=True;process.returncode=-15
        with patch.object(g.subprocess,'Popen',return_value=process),patch.object(g.g,'stop_group',side_effect=stop),\
             patch.object(g.time,'sleep'),patch.object(g.time,'monotonic',side_effect=[0,76]):
            with self.assertRaises(TimeoutError):g.dispatch(self.spec)
        row=g.read(self.spec)
        self.assertTrue(row['hostProcessExited']);self.assertFalse(row['executionKnown'])
        self.assertEqual(row['requestCount'],1)

    def test_pause_in_flight_saves_spent_attempt_and_stops_process(self):
        process=MagicMock();state=dict(stopped=False)
        process.poll.side_effect=lambda:0 if state['stopped'] else None
        process.returncode=None
        def stop(owned):state['stopped']=True;process.returncode=-15
        with patch.object(g.subprocess,'Popen',return_value=process),patch.object(g.g,'stop_group',side_effect=stop),\
             patch.object(g.time,'sleep'),patch.object(c,'boundary',side_effect=[{},c.Paused('test')]):
            with self.assertRaises(c.Paused):g.dispatch(self.spec)
        row=g.read(self.spec)
        self.assertTrue(row['hostProcessExited']);self.assertEqual(row['requestCount'],1)
        self.assertEqual(row['failure']['type'],'Paused')


if __name__=='__main__':unittest.main()
