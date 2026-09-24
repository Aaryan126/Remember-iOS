"""One-shot regression receipt. No model calls."""
import re
import subprocess
import sb_control as c


def main():
    with c.worker():
        c.require(not (c.WORK/'tests.json').exists(),'tests receipt already saved')
        commands=[s['command'] for s in c.load(c.previous.WORK/'tests.json')['suites']]
        commands.append(['python3','-B','-m','unittest','discover','-s',str(c.CODE.relative_to(c.ROOT)),'-p','test_*.py'])
        rows=[]
        for command in commands:
            c.boundary()
            result=subprocess.run(command,cwd=c.ROOT,capture_output=True,text=True,timeout=60)
            count=re.search(r'Ran (\d+) tests?',result.stderr)
            rows.append(dict(command=command,exitCode=result.returncode,count=int(count[1]) if count else 0,
                             stdout=result.stdout,stderr=result.stderr))
            if result.returncode:break
        passed=len(rows)==len(commands) and all(row['exitCode']==0 and row['count'] for row in rows)
        receipt=dict(status='passed' if passed else 'failed',testCount=sum(r['count'] for r in rows),suites=rows,
            sourceHashes={str(p.relative_to(c.ROOT)):c.digest(p) for p in sorted(c.CODE.glob('*.py'))})
        c.publish(c.WORK/'tests.json',receipt)
        c.require(passed,'regression failure; inspect tests.json')
        print('Passed',receipt['testCount'],'tests; no model requests.')


if __name__=='__main__':main()
