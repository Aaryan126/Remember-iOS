"""Final phone availability and one fictional generation smoke check, not quality testing."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('recovery',ROOT/'scripts/ios27-embedding-recovery-v2/run.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
c=r.c
c.RUN=ROOT/'Evaluation/iOS27/readiness';c.WORK=c.RUN/'build'
c.BUNDLE='SimpleStudio.Remember.Stage1Readiness'
c.UNITS=['environment','generation']
base_sources=c.sources
def sources():
    result=base_sources();result[str(Path(__file__).relative_to(ROOT))]=c.digest(__file__);return result
def space():
    free=c.shutil.disk_usage(ROOT).free
    size=sum(p.stat().st_size for p in (ROOT/'Evaluation/iOS27').rglob('*') if p.is_file())
    c.require(free>=10*c.GIB and size<8*c.GIB,'Experiment storage limits reached')
    return {'freeBytes':free,'experimentBytes':size}
c.sources=sources;c.space=space
if __name__=='__main__':
    c.signal.signal(c.signal.SIGINT,c.stop_signal);c.signal.signal(c.signal.SIGTERM,c.stop_signal)
    try:c.main()
    except InterruptedError:
        print(c.json.dumps({'paused':True,'safeToClose':c.safe_to_close()}));raise SystemExit(75)
    except (ValueError,OSError,c.subprocess.SubprocessError) as error:
        print(c.json.dumps({'error':str(error),'stage2Started':False}));raise SystemExit(1)
