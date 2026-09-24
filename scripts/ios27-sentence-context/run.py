#!/usr/bin/env python3
"""Compare actor/main execution without modifying production or old checkpoints."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=load('harness',ROOT/'scripts/ios27-sentence-diagnostic/run.py')
r=load('recovery',ROOT/'scripts/ios27-embedding-recovery/run.py')
h.phone.verify=r.verify_history
original_files=h.files
h.SCRIPT=Path(__file__).parent
h.RUN=ROOT/'Evaluation/iOS27/sentence-context'
h.WORK=h.RUN/'build'
h.BUNDLE='SimpleStudio.Remember.SentenceContext'
h.UNITS=['actor-first','main-first']
def files():
    result=original_files()
    for path in [ROOT/'scripts/ios27-sentence-diagnostic/run.py',ROOT/'scripts/ios27-embedding-recovery/run.py',ROOT/'Remember/Remember/ProjectIntelligence.swift']:
        result[str(path.relative_to(ROOT))]=h.c.digest(path)
    return result
h.files=files
if __name__=='__main__':
    try:h.main()
    except (ValueError,OSError,h.subprocess.SubprocessError) as error:
        print(h.c.json.dumps({'error':str(error)}));raise SystemExit(1)
