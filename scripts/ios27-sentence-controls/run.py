#!/usr/bin/env python3
"""Separate, frozen call-order controls; reuses the existing transport/build harness."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT/'scripts/ios27-sentence-diagnostic/run.py'
spec = importlib.util.spec_from_file_location('sentence_harness', PARENT)
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
original_files = h.files
h.SCRIPT = Path(__file__).parent
h.RUN = ROOT/'Evaluation/iOS27/sentence-controls'
h.WORK = h.RUN/'build'
h.BUNDLE = 'SimpleStudio.Remember.SentenceControls'
h.UNITS = ['default-only','revision-first']


def files():
    result = original_files()
    result[str(PARENT.relative_to(ROOT))] = h.c.digest(PARENT)
    return result


# The shared harness freezes this variant's source, bundle, binary and unit list.
h.files = files

if __name__ == '__main__':
    try: h.main()
    except (ValueError, OSError, h.subprocess.SubprocessError) as error:
        print(h.c.json.dumps({'error': str(error)})); raise SystemExit(1)
