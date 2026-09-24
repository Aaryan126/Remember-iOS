#!/usr/bin/env python3
"""Bounded read-only sentence-model probe, with independent artifacts and bundle."""
import argparse
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('phone', ROOT/'scripts/ios27-phone-diagnostic/run.py')
phone = importlib.util.module_from_spec(spec); spec.loader.exec_module(phone)
c = phone.c
RUN = ROOT/'Evaluation/iOS27/sentence-diagnostic'
WORK = RUN/'build'
SCRIPT = Path(__file__).parent
BUNDLE = 'SimpleStudio.Remember.SentenceDiagnostic'
UNITS = ['snapshot-0', 'snapshot-1']


def resources():
    state = c.space()
    size = sum(p.stat().st_size for p in (ROOT/'Evaluation/iOS27').rglob('*') if p.is_file())
    c.require(size < 8*c.GIB, 'Experiment cap reached')
    return {'freeBytes': state['freeBytes'], 'allExperimentBytes': size}


def files():
    paths = list(SCRIPT.glob('*.py')) + list(SCRIPT.glob('*.swift'))
    paths += [c.SCRIPT/'project.pbxproj.template', phone.RUN/'checkpoint.json']
    paths += [p for p in WORK.rglob('*') if p.is_file() and
              ('Sources' in p.parts or 'Products' in p.parts or p.name == 'sentence-probe' or p.suffix == '.pbxproj')]
    return {str(p.relative_to(ROOT)): c.digest(p) for p in paths}


def build(device):
    c.require(device and not (RUN/'manifest.json').exists(), 'Missing device or already frozen')
    phone.verify(); resources()
    (WORK/'Sources').mkdir(parents=True, exist_ok=True)
    (WORK/'Resources').mkdir(exist_ok=True)
    shutil.copy2(SCRIPT/'SentenceProbe.swift', WORK/'Sources/SentenceProbe.swift')
    template = (c.SCRIPT/'project.pbxproj.template').read_text()
    team = re.search(r'DEVELOPMENT_TEAM = ([A-Z0-9]+);', (ROOT/'Remember/Remember.xcodeproj/project.pbxproj').read_text())
    c.require(team, 'Missing team')
    project = WORK/'SentenceProbe.xcodeproj'; project.mkdir(exist_ok=True)
    (project/'project.pbxproj').write_text(template.replace('__TEAM__',team[1])
        .replace('SimpleStudio.Remember.IOS27Compatibility', BUNDLE).replace('CompatibilityProbe','SentenceProbe')
        .replace('Remember Compatibility','Sentence Diagnostic'))
    commands = [
        ['xcrun','swiftc','-parse-as-library','-O','-module-cache-path',str(WORK/'module-cache'),
         str(WORK/'Sources/SentenceProbe.swift'),'-o',str(WORK/'sentence-probe')],
        ['xcodebuild','-project',str(project),'-scheme','SentenceProbe','-destination','generic/platform=iOS',
         '-derivedDataPath',str(WORK/'device-build'),'-disableAutomaticPackageResolution','-skipPackageUpdates','build','-quiet']]
    for args in commands:
        response = c.command(args,600)
        c.publish(RUN/f'build-attempts/{time.time_ns()}.json',{'command':args,'returnCode':response.returncode,
            'stdout':response.stdout,'stderr':response.stderr})
        c.require(response.returncode == 0, 'Build failed; inspect receipt')
    c.publish(RUN/'manifest.json',{'files':files(),'device':device,'units':UNITS,'platforms':['mac','phone'],
        'maximumRequestsPerPlatform':2,'assetRequests':False,'productionChanged':False})
    return {'builtAndFrozen':True}


def verify():
    phone.verify()
    c.require(files()==c.read(RUN/'manifest.json')['files'],'Frozen artifact changed')
    for path in (RUN/'units').glob('*/*.json'):
        row=c.read(path); raw=ROOT/row['rawPath']
        c.require(c.digest(raw)==row['rawSHA256'],'Raw output changed')
        c.require(c.parse_result(c.read(raw)['stdout'],path.stem)==row['result'],'Interpretation changed')
    return {'verified':True}


def save(platform, unit, raw):
    result=c.parse_result(c.read(raw)['stdout'],unit)
    c.publish(RUN/f'units/{platform}/{unit}.json',{'result':result,
        'rawPath':str(raw.relative_to(ROOT)),'rawSHA256':c.digest(raw)})
    return result


def run(platform, unit):
    verify(); resources()
    c.require(unit in UNITS,'Invalid unit')
    if (RUN/'units'/platform/f'{unit}.json').exists(): return {'alreadySaved':True,'newInference':False}
    attempt=RUN/f'attempts/{platform}/{unit}'
    c.require(not (attempt/'reserved.json').exists(),'Unresolved attempt; collect before retry')
    c.publish(attempt/'reserved.json',{'startedUnix':time.time(),'unit':unit})
    args=[str(WORK/'sentence-probe'),'--unit',unit]
    if platform=='phone':
        args=['xcrun','devicectl','device','process','launch','--device',c.read(RUN/'manifest.json')['device'],
              '--console','--timeout','45',BUNDLE,'--unit',unit]
    try:
        response=c.command(args,60)
        wire={'stdout':response.stdout,'stderr':response.stderr,'returnCode':response.returncode}
    except subprocess.TimeoutExpired: wire={'timeout':True}
    raw=attempt/'raw.json'; c.publish(raw,wire)
    c.require(wire.get('returnCode')==0,'Process failure saved; recover without rerunning')
    return save(platform,unit,raw)


def collect(unit):
    verify(); c.require(unit in UNITS,'Invalid unit')
    attempt=RUN/f'attempts/phone/{unit}'
    c.require((attempt/'reserved.json').exists() and not (RUN/f'units/phone/{unit}.json').exists(),'No unresolved request')
    recovered=attempt/f'recovered-{time.time_ns()}.json'
    response=c.command(['xcrun','devicectl','device','copy','from','--device',c.read(RUN/'manifest.json')['device'],
        '--source',f'Documents/unit-{unit}.json','--destination',str(recovered),'--domain-type','appDataContainer',
        '--domain-identifier',BUNDLE],45)
    c.require(response.returncode==0 and recovered.exists(),'Checkpoint unavailable')
    result=c.parse_result('IOS27_RESULT '+c.json.dumps(c.read(recovered)),unit)
    raw=attempt/f'collected-{time.time_ns()}.json'
    c.publish(raw,{'stdout':'IOS27_RESULT '+c.json.dumps(result),'collectedWithoutInference':True})
    return save('phone',unit,raw)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['build','install','run','collect','verify','status'])
    parser.add_argument('--device'); parser.add_argument('--platform',choices=['mac','phone'],default='phone')
    parser.add_argument('--unit',choices=UNITS)
    args=parser.parse_args()
    if args.action=='status':
        unresolved=[str(p.relative_to(RUN)) for p in (RUN/'attempts/phone').glob('*/reserved.json')
                    if not (RUN/f'units/phone/{p.parent.name}.json').exists()]
        result={'safeToClose':not c.active() and not unresolved,'unresolved':unresolved}
    else:
        with c.lock():
            if args.action=='build': result=build(args.device)
            elif args.action=='verify': result=verify()
            elif args.action=='collect': result=collect(args.unit)
            elif args.action=='run': result=run(args.platform,args.unit)
            else:
                verify(); resources()
                response=c.command(['xcrun','devicectl','device','install','app','--device',c.read(RUN/'manifest.json')['device'],
                    str(WORK/'device-build/Build/Products/Debug-iphoneos/SentenceProbe.app')],120)
                c.publish(RUN/f'installations/{time.time_ns()}.json',{'returnCode':response.returncode,'stdout':response.stdout,'stderr':response.stderr})
                c.require(response.returncode==0,'Install failed')
                result={'installed':BUNDLE}
    print(c.json.dumps(result))


if __name__=='__main__':
    try: main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        print(c.json.dumps({'error':str(error)})); raise SystemExit(1)
