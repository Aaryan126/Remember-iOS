"""One isolated phone test batch, with saved reservation/results and a pause boundary."""
import argparse
import importlib.util
from pathlib import Path

s=importlib.util.spec_from_file_location('prepare',Path(__file__).with_name('prepare.py'))
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
c=p.c;c.RUN=p.RUN


def verify():
    manifest=c.read(p.RUN/'manifest.json')
    for name,sha in manifest['sources'].items():c.require(c.digest(p.ROOT/name)==sha,'Source changed: '+name)
    for name,sha in manifest['generated'].items():c.require(c.digest(p.RUN/name)==sha,'Generated source changed: '+name)
    for name,sha in manifest['dependencyFiles'].items():c.require(c.digest(p.WORK/name)==sha,'Dependency changed: '+name)
    retry=c.read(p.RUN/'signing-retry.json')
    for name,sha in retry['generated'].items():c.require(c.digest(p.RUN/name)==sha,'Signing project changed')
    c.require(c.digest(Path(__file__).with_name('retry_signing.py'))==retry['launcherSHA256'],'Signing launcher changed')
    app=p.WORK/'derived/Build/Products/Debug-iphoneos/Remember.app'
    receipt=p.RUN/'test-inputs.json'
    value={'sourceManifestSHA256':c.digest(p.RUN/'manifest.json'),'signingSHA256':c.digest(p.RUN/'signing-retry.json'),
        'runnerSHA256':c.digest(__file__),'files':{str(file.relative_to(p.RUN)):c.digest(file) for file in app.rglob('*') if file.is_file()}}
    c.require(value['files'],'Missing signed test app')
    c.publish(receipt,value)
    identity=c.command(['/usr/libexec/PlistBuddy','-c','Print CFBundleIdentifier',str(app/'Info.plist')])
    c.require(identity.stdout.strip()=='SimpleStudio.Remember.Stage1Safety','Unsafe target bundle')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['run','verify','pause','status']);parser.add_argument('--device')
    args=parser.parse_args()
    if args.action=='pause':
        if not (p.RUN/'pause.request.json').exists():c.publish(p.RUN/'pause.request.json',{'pauseRequested':True})
        print(c.json.dumps({'safeToClose':not c.active()}));return
    if args.action=='status':
        print(c.json.dumps({'safeToClose':not c.active(),'resultSaved':(p.RUN/'test-result.json').exists()}));return
    with c.lock():
        verify()
        if args.action=='verify':print('{"verified":true}');return
        if (p.RUN/'test-result.json').exists():
            print(c.json.dumps({'saved':True,'returnCode':c.read(p.RUN/'test-result.json')['returnCode']}));return
        c.require(not (p.RUN/'pause.request.json').exists(),'Paused before test batch')
        c.require(args.device,'Connected device required')
        c.require(not (p.RUN/'test-reserved.json').exists(),'Unresolved test attempt; inspect result bundle, never blindly rerun')
        command=['xcodebuild','-xctestrun',str(p.WORK/'derived/Build/Products/Safeguards_iphoneos27.0-arm64.xctestrun'),
            '-destination','id='+args.device,'-parallel-testing-enabled','NO',
            '-resultBundlePath',str(p.WORK/'phone-tests.xcresult'),'test-without-building','-quiet']
        c.publish(p.RUN/'test-reserved.json',{'command':command,'inputSHA256':c.digest(p.RUN/'test-inputs.json')})
        result=c.command(command,600)
        c.publish(p.RUN/'test-result.json',{'returnCode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        print(result.stdout[-5000:]);print(result.stderr[-5000:])
        c.require(result.returncode==0,'Tests failed; saved result bundle')


if __name__=='__main__':main()
