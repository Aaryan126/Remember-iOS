"""Close only the timed-out isolated probe; never fabricate a native result or retry."""
import argparse
import importlib.util
from pathlib import Path
import re
import time

s=importlib.util.spec_from_file_location('runner',Path(__file__).with_name('run.py'))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
c=r.c

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--device',required=True);args=parser.parse_args()
    c.require(not c.active(),'Host worker still active')
    c.verify()
    raw=c.RUN/'attempts/phone/generation/raw.json'
    c.require(c.read(raw).get('returnCode')==2 and 'timeout' in c.read(raw).get('stderr','').lower(),'Not the expected timed-out attempt')
    installations=list((c.RUN/'installations').glob('*.json'));c.require(len(installations)==1,'Ambiguous installation')
    saved=c.read(installations[0])['stdout']
    c.require('bundleID: '+c.BUNDLE in saved,'Wrong installed bundle')
    match=re.search(r'installationURL: file://([^\n]+)',saved);c.require(match,'Missing installed path')
    executable=match[1]+'CompatibilityProbe'
    def processes():
        result=c.command(['xcrun','devicectl','device','info','processes','--device',args.device],30)
        c.require(result.returncode==0,'Cannot verify process state')
        return [line.strip() for line in result.stdout.splitlines() if executable in line]
    before=processes();c.require(len(before)<=1,'Ambiguous target process')
    if before:
        pid=before[0].split()[0];c.require(pid.isdigit(),'Invalid process ID')
        # Resolve the current app identity independently before terminating the exact process.
        app=c.command(['xcrun','devicectl','device','info','apps','--device',args.device,'--bundle-id',c.BUNDLE,'--json-output','-'],30)
        c.require(app.returncode==0 and match[1] in app.stdout,'Installed identity mismatch')
        c.publish(c.RUN/'closure-reserved.json',{'bundle':c.BUNDLE,'process':before[0],'rawSHA256':c.digest(raw),'scriptSHA256':c.digest(__file__)})
        result=c.command(['xcrun','devicectl','device','process','terminate','--device',args.device,'--pid',pid],30)
        c.publish(c.RUN/'termination.json',{'returnCode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        c.require(result.returncode==0,'Termination failed')
    time.sleep(1)
    after=processes();c.require(not after,'Probe still active; not safe to close')
    c.publish(c.RUN/'closure.json',{'unit':'generation','outcome':'host-timeout-probe-terminated',
        'nativeResultAvailable':False,'generationPassed':False,'newInference':False,'safeToClose':True,
        'matchingProcessesAfter':after,'rawSHA256':c.digest(raw),'scriptSHA256':c.digest(__file__),
        'retryPolicy':'No automatic resume/retry; preserve reservation and use a separately reviewed diagnostic'})
    print('{"generationPassed":false,"safeToClose":true,"probeTerminated":true}')

if __name__=='__main__':main()
