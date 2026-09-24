"""Reviewed answer-form addendum. No model input, inference or changes to v1 gold."""
from copy import deepcopy
import v2_control as c
import as_policy as original


def proposal(document,corpus_hash,packet_labels_hash):
    entries=[]
    for lib in document['libraries']:
        for task in lib['tasks']:
            if task['gold']['verdict']!='supported':continue
            for index,evidence in enumerate(task['gold']['answers']):
                entries.append(dict(id=f"{lib['id']}:{task['id']}:{evidence['sourceId']}:r{evidence['revision']}:{index}",
                    library=lib['id'],question=task['id'],sourceId=evidence['sourceId'],revision=evidence['revision'],
                    answerKey=evidence['answerKey'],questionText=task['question'],supportQuote=evidence['quote'],
                    legacyAnswers=deepcopy(evidence['answerSpans']),proposedAnswer=evidence['quote']))
    return dict(schemaVersion=2,split=document['split'],author=document['author'],
                corpusSHA256=corpus_hash,packetLabelsSHA256=packet_labels_hash,entries=entries)


def reviewed_addendum(proposed,review,proposal_hash):
    c.require(set(review)=={'split','reviewer','author','inputSHA256','decisions','blockingIssues','limitations'},'review schema')
    c.require(review['split']==proposed['split'] and review['author']==proposed['author']
              and isinstance(review['reviewer'],str) and review['reviewer'].startswith('/root/')
              and review['reviewer']!=proposed['author'] and review['inputSHA256']==proposal_hash,'review not independent or stale')
    c.require(review['blockingIssues']==[] and isinstance(review['limitations'],list),'blocking label issue')
    decisions=review['decisions']
    c.require(isinstance(decisions,list) and all(set(d)=={'id','approve','reason'} for d in decisions),'decision schema')
    by_id={d['id']:d for d in decisions}
    c.require(len(by_id)==len(decisions)==len(proposed['entries'])
              and set(by_id)=={e['id'] for e in proposed['entries']},'incomplete/duplicate review')
    entries=[]
    for e in proposed['entries']:
        d=by_id[e['id']]
        c.require(type(d['approve']) is bool and isinstance(d['reason'],str) and d['reason'].strip(),'invalid review decision')
        c.require(e['proposedAnswer']==e['supportQuote'] and 1<=len(e['proposedAnswer'])<=160,'answer proposal changed')
        forms=list(e['legacyAnswers'])
        if d['approve'] and e['proposedAnswer'] not in forms:forms.append(e['proposedAnswer'])
        entries.append(dict(e,passageApproved=d['approve'],reason=d['reason'],acceptedAnswers=forms))
    return dict(schemaVersion=2,split=proposed['split'],corpusSHA256=proposed['corpusSHA256'],
                packetLabelsSHA256=proposed['packetLabelsSHA256'],proposalSHA256=proposal_hash,
                reviewer=review['reviewer'],entries=entries)


def expanded_gold(gold,library_id,question_id,addendum):
    result=deepcopy(gold)
    entries=[e for e in addendum['entries'] if e['library']==library_id and e['question']==question_id]
    # A retrieval miss must stay non-answering. Conversely, a conflict with only
    # one side retrieved can have supported packet gold without a corpus-level
    # supported addendum. Neither situation grants new answer forms.
    if gold['verdict']!='supported' or not entries:
        return result
    # Packet gold can be a subset of corpus evidence. Match each retained source
    # annotation exactly; never add missing evidence to make a retrieval miss pass.
    for evidence in result['answers']:
        matches=[e for e in entries if e['sourceId']==evidence['sourceId'] and e['revision']==evidence['revision']
                 and e['answerKey']==evidence['answerKey'] and e['supportQuote']==evidence['quote']]
        c.require(len(matches)==1,'addendum evidence binding absent/ambiguous')
        entry=matches[0]
        c.require(entry['legacyAnswers']==evidence['answerSpans'],'legacy answer forms changed')
        allowed=list(evidence['answerSpans'])
        if entry['passageApproved'] and evidence['quote'] not in allowed:allowed.append(evidence['quote'])
        c.require(entry['acceptedAnswers']==allowed,'unreviewed answer form injected')
        evidence['answerSpans']=allowed
    return result


def assess(output,packet,gold,library_id,question_id,addendum):
    validated=original.validate_output(output,packet)
    expanded=expanded_gold(gold,library_id,question_id,addendum)
    correct=original.semantic_correct(validated,expanded)
    legacy=original.semantic_correct(validated,gold)
    return dict(correct=correct,legacyCompatible=legacy,
                answerForm=('legacy' if legacy else 'reviewed_passage') if correct and output['verdict']=='supported' else None,
                answerCharacters=len(output['answer']) if output['verdict']=='supported' else None)
