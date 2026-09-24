"""Frozen cached packets and label-free request scheduling; never reruns retrieval."""
from copy import deepcopy
import sb_control as c
import as_fixtures as fixtures
import as_runner as old
import as_policy as policy
import v2_policy as forms

SPLITS=('development','evaluation')
REPEAT_CATEGORIES=('current_a','archived','explicit_missing','conflict')


def document(split):
    c.require(split in SPLITS,'unknown split')
    return c.load(old.c.WORK/'authored'/(split+'.json'))


def schedule(split):
    rows=[]
    libraries=sorted(document(split)['libraries'],key=lambda lib:lib['id'])
    for lib in libraries:
        packets=old.packets(lib['id'])
        eligible_states=fixtures.prefixes(lib)
        for task in sorted(lib['tasks'],key=lambda task:task['id']):
            packet=packets[task['id']]
            eligible=fixtures.eligible(task,eligible_states)
            for row in packet['candidates']:
                c.require((row['sourceId'],row['revision']) in eligible and
                    row['quote'] in eligible[(row['sourceId'],row['revision'])],'cached source not eligible')
            c.generation.old.model_packet(packet)
            rows.append(dict(id=f"{split}-{lib['id']}-{task['id']}",split=split,
                library=lib['id'],question=task['id'],repeatOf=None,packet=packet))
    for lib,category in zip(libraries,REPEAT_CATEGORIES):
        task=next(t for t in lib['tasks'] if t['category']==category)
        source=next(r for r in rows if r['library']==lib['id'] and r['question']==task['id'])
        rows.append(dict(source,id=source['id']+'-repeat',repeatOf=source['id']))
    c.require(len(rows)==68 and len({r['id'] for r in rows})==68,'split schedule count')
    return rows


def prepare():
    for split in SPLITS:
        c.boundary()
        c.publish(c.WORK/'schedules'/(split+'.json'),schedule(split))


def specs(split):
    c.require(split in SPLITS,'unknown split')
    return c.load(c.WORK/'schedules'/(split+'.json'))


def libraries(split,expanded=True):
    libraries=deepcopy(document(split)['libraries'])
    if expanded:
        addendum=c.load(c.previous.WORK/'addenda'/(split+'.json'))
        for lib in libraries:
            for task in lib['tasks']:
                task['gold']=forms.expanded_gold(task['gold'],lib['id'],task['id'],addendum)
    return libraries


def baselines(split):
    rows=[]
    for lib in libraries(split):
        cached={row['id']:row for row in c.previous.previous.read_unit(
            old.c.RUN/'retrieval'/(lib['id']+'.json'),old.corpus_binding())}
        for task in lib['tasks']:
            row=cached[task['id']]
            selected=[source for source in row['allScores'] if source['id'] in row['scoreOnlyDiagnostic']]
            expected=old.ranking_policy.predict(dict(scoped=row['allScores']),dict(family='B',minScore=.5,margin=.1,limit=1))
            c.require([r['id'] for r in selected]==[r['id'] for r in expected],'R1 cached diagnostic changed')
            c.require({r['id'] for r in selected}<={r['id'] for r in row['candidates']},'R1 outside common B0 packet')
            answerable=task['gold']['verdict']=='supported'
            hit=answerable and any(policy.in_packet(e,dict(candidates=selected)) for e in task['gold']['answers'])
            available=answerable and policy.packet_gold(task['gold'],row)['verdict']=='supported'
            rows.append(dict(library=lib['id'],question=task['id'],category=task['category'],answerable=answerable,
                sourceListAvailable=True,sourceCount=len(row['candidates']),retrievedSupport=available,
                r1Asserted=bool(selected),r1Correct=hit,selectedIDs=[r['id'] for r in selected]))
    total=sum(r['answerable'] for r in rows)
    count=sum(r['r1Asserted'] for r in rows)
    correct=sum(r['r1Correct'] for r in rows)
    return dict(R0=dict(queries=len(rows),retrievedSupport=sum(r['retrievedSupport'] for r in rows),
                       answerable=total,assertions=0,precision=None,sourceListsAvailable=len(rows)),
        R1=dict(assertions=count,correctSelections=correct,answerable=total,
                precision=correct/count if count else None,recall=correct/total if total else None,
                falseSupport=sum(r['r1Asserted'] and not r['answerable'] for r in rows),exactAnswerAccuracy=None),rows=rows)
