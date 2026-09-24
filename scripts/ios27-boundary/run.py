"""Separate frozen threshold-near diagnostic; preserves original experiments."""
import importlib.util
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('precision',ROOT/'scripts/ios27-precision/run.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
c=p.c
c.RUN=ROOT/'Evaluation/iOS27/boundary';c.WORK=c.RUN/'build/native'
c.BUNDLE='SimpleStudio.Remember.BoundaryComparison'
c.UNITS=[f'{precision}-{i:02}' for i in range(24) for precision in ['fp16','fp32']]
base_sources=c.sources;base_prepare=c.prepare


def sources():
    result=base_sources()
    paths=list(Path(__file__).parent.glob('*.py'))
    paths += [c.RUN/'selection.json',c.RUN/'reference-inputs.json',c.RUN/'parity-inputs.json']
    paths += sorted((c.RUN/'references').glob('*.json'))
    for path in paths:result[str(path.relative_to(ROOT))]=c.digest(path)
    return result


def prepare():
    result=base_prepare()
    shutil.copy2(c.RUN/'parity-inputs.json',c.WORK/'Resources/parity-inputs.json')
    return result


def check_result(result,unit):
    c.require(result['status']=='ok','Native failure: '+unit)
    c.require(result['result']['tokenParity'],'Tokenizer mismatch: '+unit)
    # Collect this preregistered small diagnostic even if a decision changes; never promote on failure.


c.sources=sources;c.prepare=prepare;c.check_result=check_result
if __name__=='__main__':
    c.signal.signal(c.signal.SIGINT,c.stop_signal);c.signal.signal(c.signal.SIGTERM,c.stop_signal)
    try:c.main()
    except InterruptedError:
        print(c.json.dumps({'paused':True,'safeToClose':c.safe_to_close()}));raise SystemExit(75)
    except (ValueError,OSError,c.subprocess.SubprocessError) as error:
        print(c.json.dumps({'error':str(error),'stage2Started':False}));raise SystemExit(1)
