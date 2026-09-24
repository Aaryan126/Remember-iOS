#!/usr/bin/env python3
"""Isolated paired-precision checks; frozen production weights/thresholds unchanged."""
import importlib.util
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('recovery',ROOT/'scripts/ios27-embedding-recovery-v2/run.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
c=r.c
c.RUN=ROOT/'Evaluation/iOS27/precision'
c.WORK=c.RUN/'build/native'
c.BUNDLE='SimpleStudio.Remember.PrecisionComparison'
c.UNITS=[f'{precision}-{i:02}' for i in range(16) for precision in ['fp16','fp32']]
SCRIPT=Path(__file__).parent
EXPORT=c.RUN/'export-fp32'
base_sources=c.sources; base_prepare=c.prepare; base_build=c.build; base_verify=c.verify


def sources():
    result=base_sources()
    paths=list(SCRIPT.glob('*.py'))+list(SCRIPT.glob('*.swift'))+list(SCRIPT.glob('*.txt'))
    paths += [EXPORT/'export-inputs.json',EXPORT/'export-result.json',EXPORT/'environment-override.json',EXPORT/'pytorch-reference.json']
    for path in paths: result[str(path.relative_to(ROOT))]=c.digest(path)
    return result


def verify_export():
    saved=c.read(EXPORT/'export-result.json')
    for path,value in saved['files'].items(): c.require(c.digest(EXPORT/path)==value,'FP32 package changed')
    for path,value in c.read(EXPORT/'export-inputs.json')['bindings'].items():
        c.require(c.digest(path)==value,'Original export input changed')


def space():
    free=shutil.disk_usage(ROOT).free
    size=sum(p.stat().st_size for p in (ROOT/'Evaluation/iOS27').rglob('*') if p.is_file())
    c.require(free>=10*c.GIB and size<8*c.GIB,'Experiment storage limits reached')
    return {'freeBytes':free,'experimentBytes':size}


def prepare():
    verify_export()
    c.publish(c.RUN/'pre-change.json',c.read(ROOT/'Evaluation/iOS27/embedding-recovery/pre-change.json'))
    result=base_prepare()
    shutil.copy2(SCRIPT/'PrecisionProbe.swift',c.WORK/'Sources/CompatibilityProbe.swift')
    shutil.copytree(EXPORT/'models/D3MatcherFP32.mlpackage',c.WORK/'Resources/MatcherAssets/D3MatcherFP32.mlpackage',dirs_exist_ok=True)
    return result


def build(platform):
    result=base_build(platform)
    if platform=='mac':
        dest=c.WORK/'Resources/MatcherAssets'
        c.require(not (dest/'D3MatcherFP32.mlmodelc').exists(),'FP32 already compiled; preserve artifact')
        response=c.command(['xcrun','coremlcompiler','compile',str(dest/'D3MatcherFP32.mlpackage'),str(dest)],120)
        c.publish(c.RUN/f'build-attempts/{c.time.time_ns()}-fp32.json',{'returnCode':response.returncode,'stdout':response.stdout,'stderr':response.stderr})
        c.require(response.returncode==0,'FP32 compilation failed')
    return result


def verify():
    verify_export()
    return base_verify()


def check_result(result,unit):
    c.require(result['status']=='ok','Native error saved: '+unit)
    row=result['result']
    c.require(row['tokenParity'] and row['fixedDecisionUnchanged'] and row['freshDecisionUnchanged'],
              'Decision or tokenizer regression; stop and review')
    # Numeric failures remain visible; this diagnostic does not turn them into passes.


c.sources=sources;c.space=space;c.prepare=prepare;c.build=build;c.verify=verify;c.check_result=check_result
if __name__=='__main__':
    c.signal.signal(c.signal.SIGINT,c.stop_signal);c.signal.signal(c.signal.SIGTERM,c.stop_signal)
    try:c.main()
    except InterruptedError:
        print(c.json.dumps({'paused':True,'safeToClose':c.safe_to_close()}));raise SystemExit(75)
    except (ValueError,OSError,c.subprocess.SubprocessError) as error:
        print(c.json.dumps({'error':str(error),'stage2Started':False}));raise SystemExit(1)
