"""Two bounded units: no-model watchdog control, then one identical generation request."""
import importlib.util
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('base',ROOT/'scripts/ios27-evaluation/run.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
c.RUN=ROOT/'Evaluation/iOS27/generation-trace';c.WORK=c.RUN/'build'
c.BUNDLE='SimpleStudio.Remember.GenerationTrace'
c.UNITS=['watchdog-control','generation']
SCRIPT=Path(__file__).parent
TEMPLATE=ROOT/'scripts/ios27-evaluation/project.pbxproj.template'

def sources():
    paths=list(SCRIPT.glob('*.py'))+list(SCRIPT.glob('*.swift'))+[TEMPLATE,
        ROOT/'scripts/ios27-evaluation/run.py',ROOT/'Evaluation/iOS27/readiness/closure.json']
    return {str(p.relative_to(ROOT)):c.digest(p) for p in paths}

def space():
    free=shutil.disk_usage(ROOT).free
    size=sum(p.stat().st_size for p in (ROOT/'Evaluation/iOS27').rglob('*') if p.is_file())
    c.require(free>=10*c.GIB and size<8*c.GIB,'Experiment storage limits reached')
    return {'freeBytes':free,'experimentBytes':size}

def prepare():
    space();c.require(not c.WORK.exists(),'Preserve existing preparation')
    c.require(c.read(ROOT/'Evaluation/iOS27/readiness/closure.json')['safeToClose'],'Prior attempt not closed')
    source=c.WORK/'Sources';source.mkdir(parents=True)
    (c.WORK/'Resources').mkdir()
    shutil.copy2(SCRIPT/'GenerationProbe.swift',source/'GenerationProbe.swift')
    team=re.search(r'DEVELOPMENT_TEAM = ([A-Z0-9]+);',(ROOT/'Remember/Remember.xcodeproj/project.pbxproj').read_text())[1]
    project=c.WORK/'CompatibilityProbe.xcodeproj';project.mkdir()
    (project/'project.pbxproj').write_text(TEMPLATE.read_text().replace('__TEAM__',team)
        .replace('SimpleStudio.Remember.IOS27Compatibility',c.BUNDLE).replace('Remember Compatibility','Generation Trace'))
    c.publish(c.RUN/'protocol.json',{'units':c.UNITS,'maximumModelRequests':1,'syntheticOnly':True,
        'generationDeadlineSeconds':60,'cancellationGraceSeconds':2,'controlDeadlineSeconds':2,
        'prewarmUsed':False,'samePromptAndSchemaAsPrior':True,'stage2Started':False,'productionChanged':False})
    return {'prepared':True}

base_build=c.build
def build(platform):
    c.require(platform=='phone','This diagnostic targets only the physical phone')
    return base_build(platform)

def freeze():
    app=c.WORK/'device-build/Build/Products/Debug-iphoneos/CompatibilityProbe.app'
    c.require((app/'CompatibilityProbe').exists(),'Missing phone build')
    generated=list((c.WORK/'Sources').glob('*.swift'))+[c.WORK/'CompatibilityProbe.xcodeproj/project.pbxproj']
    c.publish(c.RUN/'manifest.json',{'sources':sources(),'protocolSHA256':c.digest(c.RUN/'protocol.json'),
        'generated':{str(p.relative_to(c.RUN)):c.digest(p) for p in generated},
        'phoneFiles':{str(p.relative_to(c.RUN)):c.digest(p) for p in app.rglob('*') if p.is_file()},
        'units':c.UNITS,'stage2Started':False})

def verify():
    manifest=c.read(c.RUN/'manifest.json')
    c.require(manifest['sources']==sources(),'Frozen sources changed')
    c.require(manifest['protocolSHA256']==c.digest(c.RUN/'protocol.json'),'Protocol changed')
    for name,sha in {**manifest['generated'],**manifest['phoneFiles']}.items():
        c.require(c.digest(c.RUN/name)==sha,'Frozen artifact changed')
    for path in (c.RUN/'units').glob('*/*.json'):
        row=c.read(path);raw=c.RUN/row['rawPath']
        c.require(c.digest(raw)==row['rawSHA256'],'Raw evidence changed')
        c.require(c.parse_result(c.read(raw)['stdout'],path.stem)==row['result'],'Parsed result changed')
    return {'verified':True}

def check_result(result,unit):
    c.require(result['status']=='ok' and result['result']['passed'],'Saved diagnostic failure; stop without retry')
    row=result['result']
    if unit=='watchdog-control':
        c.require(row['watchdogControl'] and row['deadlineFired'],'Watchdog was not exercised')
    else:
        c.require(not row['watchdogControl'] and not row['deadlineFired'] and row['code']=='ORBIT-27','Generation not successful')

c.sources=sources;c.space=space;c.prepare=prepare;c.build=build;c.freeze=freeze;c.verify=verify;c.check_result=check_result
if __name__=='__main__':
    c.signal.signal(c.signal.SIGINT,c.stop_signal);c.signal.signal(c.signal.SIGTERM,c.stop_signal)
    try:c.main()
    except InterruptedError:
        print(c.json.dumps({'paused':True,'safeToClose':c.safe_to_close()}));raise SystemExit(75)
    except (ValueError,OSError,c.subprocess.SubprocessError) as error:
        print(c.json.dumps({'error':str(error),'stage2Started':False}));raise SystemExit(1)
