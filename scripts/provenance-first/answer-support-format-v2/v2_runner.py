"""Only the approved v2 preparation and eight neutral checks; no benchmark dispatch."""
import argparse
import json
import v2_control as c
import v2_policy as p
import as_fixtures as fixtures


def prepare():
    for document in fixtures.documents():
        c.boundary()
        split=document['split']
        source=c.previous.WORK/'authored'/(split+'.json')
        labels=c.previous.WORK/'packet-labels'/(split+'.json')
        c.publish(c.WORK/'proposals'/(split+'.json'),p.proposal(document,c.digest(source),c.digest(labels)))


def addenda():
    for document in fixtures.documents():
        split=document['split']
        path=c.WORK/'proposals'/(split+'.json')
        proposed=c.load(path)
        c.require(proposed==p.proposal(document,c.digest(c.previous.WORK/'authored'/(split+'.json')),
                                      c.digest(c.previous.WORK/'packet-labels'/(split+'.json'))),'proposal no longer matches frozen corpus')
        review=c.load(c.WORK/'reviews'/(split+'.json'))
        c.publish(c.WORK/'addenda'/(split+'.json'),p.reviewed_addendum(proposed,review,c.digest(path)))


def freeze():
    import v2_generation as g
    addenda()
    g.verify_build()
    paths=list(c.CODE.glob('*.py'))
    paths += [c.WORK/name for name in ('REVIEW.md','APPROVAL.md','REVIEW-FORMAT.md','approval.json',
                                     'tests.json','pause-proof.json')]
    for folder in ('proposals','reviews','addenda'):
        paths+=list((c.WORK/folder).glob('*.json'))
    # Generation preparation exposes a receipt binding its binary, generated
    # schema description, prompt, fresh controls, source and runtime identities.
    paths += [c.WORK/'generation-build.json']
    value=dict(stage='v2 preparation and controls',stageBAllowed=False,
               hashes={str(path.relative_to(c.ROOT)):c.digest(path) for path in sorted(paths)},
               sourceFiles=sorted(str(path.relative_to(c.ROOT)) for path in c.CODE.glob('*.py')))
    c.publish(c.WORK/'frozen.json',value)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','addenda','build','freeze','verify','controls','pause','status'))
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--max-units',type=int)
    args=parser.parse_args()
    if args.command=='pause':
        c.atomic(c.checked(c.WORK/'pause.request.json'),dict(reason='user-request'))
        print('Pause requested; wait for worker/owned-process confirmation.');return
    if args.command=='status':
        print(json.dumps(dict(worker=c.load(c.WORK/'worker.json') if (c.WORK/'worker.json').exists() else None,
                              paused=(c.WORK/'pause.request.json').exists(),stageBAllowed=False)));return
    try:
        with c.worker(resume=args.resume):
            if args.command=='prepare':prepare()
            elif args.command=='addenda':addenda()
            elif args.command=='freeze':freeze()
            elif args.command=='verify':c.verify_frozen()
            else:
                import v2_generation as g
                if args.command=='build':g.build()
                else:g.controls(maximum=args.max_units)
        print(json.dumps(dict(command=args.command,status='complete',workerStopped=True,stageBAllowed=False)))
    except c.Paused as error:print(json.dumps(dict(status='paused',reason=str(error),workerStopped=True)))


if __name__=='__main__':main()
