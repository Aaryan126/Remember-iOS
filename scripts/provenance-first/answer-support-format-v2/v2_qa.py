"""Deterministic regression and read-only control audit; never dispatch a model."""
import argparse
import re
import subprocess
import v2_control as c
import v2_generation as g
import v2_runner as runner
import v2_policy as policy
from copy import deepcopy


def tests():
    c.require(not (c.WORK/'tests.json').exists(),'test receipt already exists')
    commands=[row['command'] for row in c.load(c.previous.WORK/'tests.json')['suites']]
    commands.append(['python3','-B','-m','unittest','discover','-s',str(c.CODE.relative_to(c.ROOT)),'-p','test_*.py'])
    rows=[]
    for command in commands:
        c.boundary()
        result=subprocess.run(command,cwd=c.ROOT,capture_output=True,text=True,timeout=60)
        count=re.search(r'Ran (\d+) tests?',result.stderr)
        rows.append(dict(command=command,exitCode=result.returncode,count=int(count[1]) if count else 0,
                         stdout=result.stdout,stderr=result.stderr))
        if result.returncode:break
    passed=len(rows)==len(commands) and all(row['exitCode']==0 and row['count']>0 for row in rows)
    receipt=dict(status='passed' if passed else 'failed',testCount=sum(row['count'] for row in rows),suites=rows,
                 sourceHashes={str(path.relative_to(c.ROOT)):c.digest(path) for path in sorted(c.CODE.glob('*.py'))})
    c.publish(c.WORK/'tests.json',receipt)
    c.require(passed,'regression suite failed; inspect tests.json')
    return receipt


def audit():
    c.verify_prior()
    frozen=c.verify_frozen()
    build=g.verify_build()
    runner.addenda()
    gold_records=0
    for document in runner.fixtures.documents():
        split=document['split']
        addendum=c.load(c.WORK/'addenda'/(split+'.json'))
        for collection in (document,c.load(c.previous.WORK/'packet-labels'/(split+'.json'))):
            for library in collection['libraries']:
                for task in library['tasks']:
                    original=deepcopy(task['gold'])
                    expanded=policy.expanded_gold(original,library['id'],task['id'],addendum)
                    c.require(task['gold']==original,'gold mutated')
                    for before,after in zip(original['answers'],expanded['answers']):
                        c.require(set(before['answerSpans'])<=set(after['answerSpans']),'legacy form lost')
                        after['answerSpans']=before['answerSpans']
                    c.require(expanded==original,'non-format gold changed')
                    gold_records+=1
    tests=c.load(c.WORK/'tests.json')
    c.require(tests['status']=='passed','test qualification missing')
    for name,expected in tests['sourceHashes'].items():
        c.require(c.digest(c.ROOT/name)==expected,'source changed after tests: '+name)
    prior,reserved=g.reservations()
    rows=[]
    failed=False
    for spec in g.controls_spec():
        path=c.WORK/'generation-units'/(spec['id']+'.json')
        if not path.exists():break
        c.require(not failed,'request after failed control')
        row=g.verify_unit(spec,build)
        failed=not row['passed']
        rows.append(row)
    unit_files=list((c.WORK/'generation-units').glob('*.json'))
    c.require(len(unit_files)==len(rows),'out-of-order or unknown unit')
    c.require(len(reserved)==len(rows),'unresolved reservation requires investigation')
    c.require(len(prior)==1 and len(reserved)<=8 and len(prior)+len(reserved)<=145,'request count violation')
    return dict(priorPreserved=True,frozenSHA256=c.digest(c.WORK/'frozen.json'),
        stageBAllowed=frozen['stageBAllowed'],requests=len(rows),passed=sum(r['passed'] for r in rows),
        qualified=len(rows)==8 and not failed,cumulativeRequests=len(prior)+len(reserved),
        tests=tests['testCount'],goldRecordsChecked=gold_records,resources=c.resources(),
        ownedProcessesExited=all(r['hostProcessExited'] for r in rows))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('tests','audit'))
    args=parser.parse_args()
    with c.worker():
        result=tests() if args.command=='tests' else audit()
        if args.command=='audit':c.publish(c.WORK/'audit.json',result)
    print(c.encoded(result).decode())


if __name__=='__main__':main()
