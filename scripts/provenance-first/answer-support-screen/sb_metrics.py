"""Offline frozen metrics; model transport never imports or reads these labels."""
from collections import Counter
import random
import statistics
import sb_control as c
import sb_data as data
import as_policy as p


def bootstrap(rows,draws=2000,seed=20260919):
    clusters={key:[r for r in rows if r['library']==key] for key in sorted({r['library'] for r in rows})}
    rng=random.Random(seed)
    values={k:[] for k in ('precision','recall','falseSupportRate')}
    keys=list(clusters)
    for _ in range(draws):
        sampled=[r for key in rng.choices(keys,k=len(keys)) for r in clusters[key]]
        supported=[r for r in sampled if r['goldVerdict']=='supported']
        negative=[r for r in sampled if r['goldVerdict']!='supported']
        assertions=[r for r in sampled if r['verdict']=='supported']
        correct=sum(r['correct'] for r in assertions)
        for name,num,den in [('precision',correct,len(assertions)),('recall',correct,len(supported)),
                            ('falseSupportRate',sum(r['verdict']=='supported' for r in negative),len(negative))]:
            if den:values[name].append(num/den)
    result={}
    for name,samples in values.items():
        samples.sort()
        def percentile(q):
            if not samples:return None
            position=(len(samples)-1)*q
            left=int(position);right=min(left+1,len(samples)-1)
            return samples[left]+(samples[right]-samples[left])*(position-left)
        result[name]=dict(low=percentile(.025),high=percentile(.975),validDraws=len(samples))
    return dict(method='library-cluster percentile',draws=draws,seed=seed,clusters=len(keys),intervals=result)


def summary(values):
    return dict(count=len(values),minimum=min(values) if values else None,
                median=statistics.median(values) if values else None,maximum=max(values) if values else None)


def evaluate(split,units):
    specs=data.specs(split)
    c.require(set(units)=={s['id'] for s in specs},'incomplete split, no gate decision')
    primary=[s for s in specs if s['repeatOf'] is None]
    packets={lib['id']:{} for lib in data.libraries(split)}
    responses={key:{} for key in packets}
    for spec in primary:
        row=units[spec['id']]
        terminal=row['terminal']
        response=terminal if terminal is not None else dict(status='error',output=None)
        if row['failure'] is not None:response=dict(response,status='error')
        packets[spec['library']][spec['question']]=spec['packet']
        responses[spec['library']][spec['question']]=response
    libraries=data.libraries(split)
    metrics=p.metrics(libraries,packets,responses)
    legacy=p.metrics(data.libraries(split,expanded=False),packets,responses)
    legacy_rows={(r['library'],r['id']):r for r in legacy['rows']}
    tasks={(lib['id'],t['id']):t for lib in libraries for t in lib['tasks']}
    spec_by_key={(s['library'],s['question']):s for s in primary}
    raw_counts=Counter();raw_assertions=raw_correct=raw_errors=0
    lengths=[];legacy_correct=passage_correct=0
    for row in metrics['rows']:
        key=(row['library'],row['id']);spec=spec_by_key[key];unit=units[spec['id']]
        output=unit['terminal'].get('output') if unit['terminal'] else None
        row.update(question=spec['packet']['question'],output=output,legacyCompatible=legacy_rows[key]['correct'],
                   answerForm=None,answerCharacters=None)
        if isinstance(output,dict):
            verdict=output.get('verdict')
            raw_counts[verdict if isinstance(verdict,str) else 'invalid']+=1
            if verdict=='supported':raw_assertions+=1
            try:
                validated=p.validate_output(output,spec['packet'])
                raw_correct+=verdict=='supported' and p.semantic_correct(validated,tasks[key]['gold'])
            except (ValueError,KeyError,TypeError):raw_errors+=1
        else:raw_counts['missing_output']+=1;raw_errors+=1
        if row['verdict']=='supported':
            row['answerCharacters']=len(output['answer']);lengths.append(len(output['answer']))
            if row['correct']:
                row['answerForm']='legacy' if row['legacyCompatible'] else 'reviewed_passage'
                legacy_correct+=row['legacyCompatible'];passage_correct+=not row['legacyCompatible']
    repeat_rows=[]
    for spec in specs:
        if spec['repeatOf']:
            original=units[spec['repeatOf']];repeat=units[spec['id']]
            valid=all(u['failure'] is None and u['validationError'] is None and u['terminal'] is not None
                      and u['terminal']['status']=='ok' for u in (original,repeat))
            match=valid and original['terminal']['output']==repeat['terminal']['output']
            repeat_rows.append(dict(id=spec['id'],original=spec['repeatOf'],matched=match))
    # Only successfully host-validated output is emitted. Candidate eligibility
    # is checked in the frozen schedule and again in the final full-input audit.
    emitted_invalid=0
    for row in metrics['rows']:
        if row['verdict'] is not None:
            spec=spec_by_key[(row['library'],row['id'])]
            try:p.validate_output(row['output'],spec['packet'])
            except (ValueError,KeyError,TypeError):emitted_invalid+=1
    integrity=emitted_invalid==0 and all(row['sourceListPreserved'] for row in metrics['rows'])
    gates=p.gates(metrics,integrity,len(repeat_rows)==4 and all(r['matched'] for r in repeat_rows))
    by_category={};by_library={}
    for field,destination in [('category',by_category),('library',by_library)]:
        for key in sorted({r[field] for r in metrics['rows']}):
            rows=[r for r in metrics['rows'] if r[field]==key]
            destination[key]=dict(queries=len(rows),correctStatesAndEvidence=sum(r['correct'] for r in rows),
                correctAnswers=sum(r['correct'] and r['verdict']=='supported' for r in rows),
                errors=sum(r['error'] is not None for r in rows))
    terminals=[units[s['id']]['terminal'] for s in primary if units[s['id']]['terminal'] is not None]
    return dict(split=split,qualified=all(gates.values()),gates=gates,metrics=metrics,
        legacyMetrics={k:v for k,v in legacy.items() if k!='rows'},baselines=data.baselines(split),
        raw=dict(verdictCounts=dict(raw_counts),assertions=raw_assertions,strictCorrectAnswers=raw_correct,
                 strictPrecision=raw_correct/raw_assertions if raw_assertions else None,
                 falseSupport=metrics['rawFalseSupport'],unscorableOrInvalid=raw_errors),
        answerForms=dict(legacyCompatibleCorrect=legacy_correct,reviewedPassageCorrect=passage_correct,
                         validSupportedLengths=summary(lengths)),
        repeats=repeat_rows,byCategory=by_category,byLibrary=by_library,uncertainty=bootstrap(metrics['rows']),
        nativeElapsedSeconds=summary([t['elapsedSeconds'] for t in terminals if 'elapsedSeconds' in t]),
        probeOnlyPeakResidentBytes=summary([t['peakResidentBytes'] for t in terminals if 'peakResidentBytes' in t]),
        sourceListsAvailable=len(primary),emittedInvalidCitations=emitted_invalid,appIntegrationAllowed=False)
