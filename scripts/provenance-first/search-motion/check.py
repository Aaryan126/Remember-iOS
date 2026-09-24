#!/usr/bin/env python3
"""Separate native-search motion follow-up; preserve the prior installed checkpoint."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("search_motion_checks", CODE.parent / "search-options/check.py")
checks = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checks
spec.loader.exec_module(checks)
checks.CODE = CODE
checks.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-motion"
checks.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-motion"
checks.RECEIPT = checks.ROOT / "Evaluation/ProvenanceFirst/search-transition-deployment/checkpoint-stop.json"

if __name__ == "__main__":
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preserve", "prepare", "unit", "ui", "regression", "resources"])
    action = parser.parse_args().action
    checks.prior.configure()
    checks.boundary()
    if action == "preserve": checks.preserve()
    elif action == "resources": print(json.dumps(checks.boundary()))
    else:
        runner = checks.prior.d.guard
        runner.RUN, runner.WORK = checks.RUN, checks.WORK
        runner.CODE = CODE.parent / "search-transition"
        runner.PROJECT = checks.RUN / "project"
        runner.BUILD = checks.ROOT / "Evaluation/ProvenanceFirst/runs/unified-search/build"
        runner.verify_baseline, runner.boundary = checks.verify, checks.boundary
        if action == "prepare": runner.prepare(fixture=True)
        elif action == "unit": runner.execute("test", ["RememberTests/UnifiedMemorySearchTests", "RememberTests/SourceEvidenceBrowserTests"])
        elif action == "regression": runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests/testClosingSearchPreservesScrolledLibraryAcrossRepeatedSessions")
        else: runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests")
