"""Deterministic answer-form tests; no Foundation Models requests."""
from copy import deepcopy
import unittest
import v2_policy as p


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.evidence=dict(sourceId='s1',revision=2,answerKey='gate',
                           quote='Gate code: PINE-84.',answerSpans=['PINE-84'])
        self.gold=dict(verdict='supported',answers=[self.evidence],missingEvidence=[])
        self.packet=dict(candidates=[dict(id='c1',sourceId='s1',revision=2,quote=self.evidence['quote'])])
        self.document=dict(split='development',author='/root/author',libraries=[dict(id='l1',tasks=[
            dict(id='q1',question='What is the gate code?',gold=self.gold)])])
        self.proposal=p.proposal(self.document,'corpus','packets')
        self.review=dict(split='development',reviewer='/root/reviewer',author='/root/author',
            inputSHA256='proposal',decisions=[dict(id=self.proposal['entries'][0]['id'],approve=True,
            reason='Exact gate code and qualifier retained.')],blockingIssues=[],limitations=['Agent review.'])
        self.addendum=p.reviewed_addendum(self.proposal,self.review,'proposal')

    def output(self,answer,**changes):
        result=dict(verdict='supported',answer=answer,evidence=[dict(candidateID='c1',quote=self.evidence['quote'])])
        result.update(changes)
        return result

    def assess(self,output,gold=None):
        return p.assess(output,self.packet,self.gold if gold is None else gold,'l1','q1',self.addendum)

    def test_compact_and_passage_separate(self):
        self.assertEqual(self.assess(self.output('PINE-84'))['answerForm'],'legacy')
        result=self.assess(self.output(self.evidence['quote']))
        self.assertTrue(result['correct'])
        self.assertFalse(result['legacyCompatible'])
        self.assertEqual(result['answerForm'],'reviewed_passage')

    def test_unapproved_substring_not_credited(self):
        self.assertFalse(self.assess(self.output('code: PINE-84'))['correct'])

    def test_rejected_form_preserves_legacy(self):
        self.review['decisions'][0]['approve']=False
        self.addendum=p.reviewed_addendum(self.proposal,self.review,'proposal')
        self.assertFalse(self.assess(self.output(self.evidence['quote']))['correct'])
        self.assertTrue(self.assess(self.output('PINE-84'))['correct'])

    def test_gold_is_not_mutated(self):
        before=deepcopy(self.gold)
        p.expanded_gold(self.gold,'l1','q1',self.addendum)
        self.assertEqual(self.gold,before)

    def test_retrieval_miss_not_repaired(self):
        missing=dict(verdict='not_established',answers=[],missingEvidence=[])
        self.assertEqual(p.expanded_gold(missing,'l1','q1',self.addendum),missing)
        self.assertFalse(self.assess(self.output('PINE-84'),missing)['correct'])

    def test_one_sided_conflict_packet_no_new_forms(self):
        self.assertEqual(p.expanded_gold(self.gold,'conflict-library','q1',self.addendum),self.gold)

    def test_wrong_source_or_revision(self):
        for key,value in [('sourceId','another-person'),('revision',1)]:
            with self.subTest(key=key):
                packet=deepcopy(self.packet)
                packet['candidates'][0][key]=value
                self.assertFalse(p.assess(self.output('PINE-84'),packet,self.gold,'l1','q1',self.addendum)['correct'])

    def test_unrelated_additional_citation(self):
        self.packet['candidates'].append(dict(id='c2',sourceId='other',revision=1,quote='Gate code: PINE-84.'))
        output=self.output('PINE-84')
        output['evidence'].append(dict(candidateID='c2',quote='Gate code: PINE-84.'))
        self.assertFalse(self.assess(output)['correct'])

    def test_equivalent_citation_different_surface(self):
        extra=dict(sourceId='s2',revision=1,answerKey='gate',quote='Use PINE-84 for entry.',answerSpans=['PINE-84'])
        self.gold['answers'].append(extra)
        self.proposal=p.proposal(self.document,'corpus','packets')
        self.review['decisions'].append(dict(id=self.proposal['entries'][1]['id'],approve=True,reason='Equivalent code.'))
        self.addendum=p.reviewed_addendum(self.proposal,self.review,'proposal')
        self.packet['candidates'].append(dict(id='c2',sourceId='s2',revision=1,quote=extra['quote']))
        output=self.output(self.evidence['quote'])
        output['evidence'].append(dict(candidateID='c2',quote=extra['quote']))
        self.assertTrue(self.assess(output)['correct'])

    def test_conflict_and_missing_not_supported(self):
        for state in ('conflicting','explicit_missing','not_established'):
            with self.subTest(state=state):
                gold=deepcopy(self.gold)
                gold['verdict']=state
                self.assertFalse(self.assess(self.output('PINE-84'),gold)['correct'])

    def test_negation_and_proposal_qualifiers(self):
        for quote,compact,wrong in [('Entry is not permitted.','not permitted','permitted'),
                                    ('Proposed gate code: PINE-84.','Proposed gate code: PINE-84.','PINE-84')]:
            with self.subTest(quote=quote):
                self.evidence.update(quote=quote,answerSpans=[compact])
                self.packet['candidates'][0]['quote']=quote
                self.proposal=p.proposal(self.document,'corpus','packets')
                self.addendum=p.reviewed_addendum(self.proposal,self.review,'proposal')
                self.assertFalse(self.assess(self.output(wrong))['correct'])

    def test_host_validation_no_repairs(self):
        cases=[self.output('x'*161),self.output(' PINE-84'),
               self.output('PINE-84',evidence=[dict(candidateID='unknown',quote=self.evidence['quote'])]),
               self.output('PINE-84',evidence=[dict(candidateID='c1',quote='Invented PINE-84 citation.')]),
               self.output('PINE-84',verdict='not_established')]
        for output in cases:
            with self.subTest(output=output),self.assertRaises(ValueError):self.assess(output)

    def test_review_binding_and_completeness(self):
        for field,value in [('reviewer','/root/author'),('inputSHA256','stale'),('decisions',[]),
                            ('blockingIssues',['Incorrect original label.']),('author','/root/other')]:
            with self.subTest(field=field):
                review=deepcopy(self.review);review[field]=value
                with self.assertRaises(ValueError):p.reviewed_addendum(self.proposal,review,'proposal')

    def test_duplicate_review_rejected(self):
        self.review['decisions']*=2
        with self.assertRaises(ValueError):p.reviewed_addendum(self.proposal,self.review,'proposal')

    def test_changed_proposal_rejected(self):
        self.proposal['entries'][0]['proposedAnswer']='Invented form'
        with self.assertRaises(ValueError):p.reviewed_addendum(self.proposal,self.review,'proposal')

    def test_injected_form_and_changed_legacy_rejected(self):
        for field,value in [('acceptedAnswers',['PINE-84','invented']),('legacyAnswers',['different'])]:
            with self.subTest(field=field):
                addendum=deepcopy(self.addendum);addendum['entries'][0][field]=value
                with self.assertRaises(ValueError):p.expanded_gold(self.gold,'l1','q1',addendum)


if __name__=='__main__':unittest.main()
