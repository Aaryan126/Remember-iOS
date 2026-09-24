#!/usr/bin/env python3
"""Isolated SciPy compatibility override; original environment and failure untouched."""
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Evaluation/iOS27/precision/build/python-overrides'))
s=importlib.util.spec_from_file_location('export',Path(__file__).with_name('export.py'))
e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
e.RUN=ROOT/'Evaluation/iOS27/precision/export-fp32'
if __name__=='__main__':
    with e.c.lock():
        import scipy, scipy.sparse, coremltools
        e.c.publish(e.RUN/'environment-override.json',{'scipyVersion':scipy.__version__,
            'scipyPath':scipy.__file__,'coremltoolsVersion':coremltools.__version__,
            'launcherSHA256':e.c.digest(__file__),'historicalEnvironmentModified':False})
        e.main()
