"""Approved development-first screen. Resume verifies and skips completed units."""
import argparse
import json
import sb_control as c
import sb_data as data
import sb_generation as generation
import sb_metrics as metrics


def freeze():
    data.prepare()
    tests=c.load(c.WORK/'tests.json')
    c.require(tests['status']=='passed','regressions must pass before freeze')
    c.require(tests['sourceHashes']=={str(p.relative_to(c.ROOT)):c.digest(p) for p in sorted(c.CODE.glob('*.py'))},
              'implementation changed after regression receipt')
    # No new binary or model configuration: bind the entire qualified v2 scope,
    # original inputs and new scheduler/reporting implementation before dispatch.
    paths=list(c.CODE.glob('*.py'))+[c.WORK/n for n in ('PROTOCOL.md','approval.json','tests.json','pause-proof.json')]
    paths+=list((c.WORK/'schedules').glob('*.json'))
    for root,manifest in [(c.previous.ROOT,c.previous.WORK/'frozen.json'),
                          (c.previous.ROOT,c.previous.previous.WORK/'frozen.json')]:
        paths.extend(root/name for name in c.load(manifest)['hashes'])
        paths.append(manifest)
    paths += [c.previous.WORK/'checkpoint-stop.json',c.previous.WORK/'generation-build.json',c.generation.BINARY]
    for split in data.SPLITS:
        paths += [data.old.c.WORK/'authored'/(split+'.json'),c.previous.WORK/'addenda'/(split+'.json')]
    for split in data.SPLITS:
        for spec in data.specs(split):generation.request(spec)
    c.publish(c.WORK/'frozen.json',dict(stage='B',developmentFirst=True,
        sourceFiles=sorted(str(p.relative_to(c.ROOT)) for p in c.CODE.glob('*.py')),
        hashes={str(p.relative_to(c.ROOT)):c.digest(p) for p in sorted(set(paths))}))


def result(split):
    c.verify_frozen()
    rows={spec['id']:generation.read(spec) for spec in data.specs(split)}
    c.require(all(r['executionKnown'] for r in rows.values()),'unknown executions require investigation')
    return metrics.evaluate(split,rows)


def decide(split):
    value=result(split)
    c.publish(c.WORK/'decisions'/(split+'.json'),value)
    return value


def verify_decision(split):
    saved=c.load(c.WORK/'decisions'/(split+'.json'))
    c.require(saved==result(split),'saved decision differs from raw replay')
    return saved


def run(split,maximum=None):
    c.require(maximum is None or type(maximum) is int and maximum>0,'invalid unit limit')
    c.verify_frozen()
    if (c.WORK/'decisions'/(split+'.json')).exists():return verify_decision(split)
    if split=='evaluation':c.require(verify_decision('development')['qualified'],'development gate failed')
    made=0
    for index,spec in enumerate(data.specs(split),1):
        c.boundary()
        existed=(c.WORK/'units'/(spec['id']+'.json')).exists()
        row=generation.dispatch(spec)
        c.require(row['executionKnown'],'unknown saved execution; investigation needed')
        if not existed:
            made+=1
            print(json.dumps(dict(split=split,completed=index,total=68,unit=spec['id'],
                                  executionStatus=row['terminal']['status'])),flush=True)
            if maximum is not None and made>=maximum:return dict(split=split,completed=index,boundedStop=True)
    return decide(split)


def audit():
    c.verify_prior();c.verify_frozen()
    results={}
    for split in data.SPLITS:
        c.require(data.specs(split)==data.schedule(split),'schedule differs from original cached eligible sources')
        if (c.WORK/'decisions'/(split+'.json')).exists():results[split]=verify_decision(split)
    prior,reserved=generation.reservations()
    units=list((c.WORK/'units').glob('*.json'))
    c.require(len(units)==len(reserved),'unresolved attempt, no completed audit')
    expected={s['id'] for split in results for s in data.specs(split)}
    c.require({p.stem for p in units}=={p.stem for p in reserved}==expected,'unscored/unknown units in final audit')
    c.require(len(reserved)<=c.NEW_LIMIT and len(prior)+len(reserved)<=c.GLOBAL_LIMIT,'request budget violation')
    if any(p.stem.startswith('evaluation-') for p in reserved):
        c.require(results.get('development',{}).get('qualified') is True,'evaluation started without passed dev')
    return dict(priorPreserved=True,requests=len(reserved),cumulativeRequests=len(prior)+len(reserved),
        splitDecisions={s:dict(qualified=r['qualified'],gates=r['gates']) for s,r in results.items()},
        resources=c.previous.resources(),appIntegrationAllowed=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','freeze','verify','run','audit','pause','status'))
    parser.add_argument('--split',choices=data.SPLITS,default='development')
    parser.add_argument('--max-units',type=int)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.command=='pause':
        c.atomic(c.checked(c.WORK/'pause.request.json'),dict(reason='user-request'))
        print('Pause requested; wait for owned-process exit and worker stopped confirmation.');return
    if args.command=='status':
        print(json.dumps(dict(worker=c.load(c.WORK/'worker.json') if (c.WORK/'worker.json').exists() else None,
            pauseRequested=(c.WORK/'pause.request.json').exists(),
            completed=len(list((c.WORK/'units').glob('*.json'))))));return
    try:
        with c.worker(resume=args.resume):
            if args.command=='prepare':value=data.prepare()
            elif args.command=='freeze':value=freeze()
            elif args.command=='verify':c.verify_frozen();value=dict(verified=True)
            elif args.command=='audit':value=audit();c.publish(c.WORK/'audit.json',value)
            else:value=run(args.split,args.max_units)
        print(json.dumps(dict(command=args.command,workerStopped=True,
            result={k:v for k,v in value.items() if k not in {'hashes','metrics','legacyMetrics','baselines'}} if value else None)))
    except c.Paused as error:print(json.dumps(dict(status='paused',reason=str(error),workerStopped=True)))


if __name__=='__main__':main()
