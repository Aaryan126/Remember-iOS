#!/usr/bin/env python3
"""Separate transition regression receipts; preserve the installed menu checkpoint."""
import importlib.util
import argparse
import json
import os
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("search_transition_checks", CODE.parent / "search-options/check.py")
checks = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checks
spec.loader.exec_module(checks)
checks.CODE = CODE
checks.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-transition"
checks.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-transition"
checks.RECEIPT = checks.ROOT / "Evaluation/ProvenanceFirst/search-options-deployment/checkpoint-stop.json"

if __name__ == "__main__":
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preserve", "prepare", "unit", "ui", "regression", "resources"])
    action = parser.parse_args().action
    checks.prior.configure()
    checks.boundary()
    if action == "preserve":
        checks.preserve()
    elif action == "resources":
        print(json.dumps(checks.boundary()))
    else:
        runner = checks.prior.d.guard
        runner.RUN, runner.WORK, runner.CODE = checks.RUN, checks.WORK, CODE
        runner.PROJECT = checks.RUN / "project"
        runner.BUILD = checks.ROOT / "Evaluation/ProvenanceFirst/runs/unified-search/build"
        runner.verify_baseline, runner.boundary = checks.verify, checks.boundary
        if action == "prepare":
            runner.prepare(fixture=True)
        elif action == "unit":
            runner.execute("test", ["RememberTests/UnifiedMemorySearchTests", "RememberTests/SourceEvidenceBrowserTests"])
        elif action == "regression":
            runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests/testClosingSearchPreservesScrolledLibraryAcrossRepeatedSessions")
        else:
            runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests")
