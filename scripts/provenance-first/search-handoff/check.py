#!/usr/bin/env python3
"""Frozen-results handoff checks; preserve the installed overlay checkpoint."""
import importlib.util
import os
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("handoff_checks", CODE.parent / "search-options/check.py")
checks = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checks
spec.loader.exec_module(checks)
checks.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-handoff"
checks.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-handoff"
checks.RECEIPT = checks.ROOT / "Evaluation/ProvenanceFirst/search-overlay-deployment/checkpoint-stop.json"

if __name__ == "__main__":
    os.umask(0o077)
    action = sys.argv[1]
    checks.prior.configure()
    checks.boundary()
    if action == "preserve":
        checks.preserve()
    elif action == "resources":
        print(checks.boundary())
    else:
        runner = checks.prior.d.guard
        runner.RUN, runner.WORK = checks.RUN, checks.WORK
        runner.CODE = CODE
        runner.PROJECT = checks.RUN / "project"
        runner.BUILD = checks.ROOT / "Evaluation/ProvenanceFirst/runs/unified-search/build"
        runner.verify_baseline, runner.boundary = checks.verify, checks.boundary
        if action == "prepare":
            warm = (runner.BUILD / "ModuleCache.noindex").is_dir()
            checks.boundary((256 if warm else 1536) * 1024**2)
            runner.prepare(fixture=True)
        else:
            for name, expected in checks.prior.d.load(checks.RUN / "preparation.json")["sourceBindings"].items():
                if checks.prior.d.digest(checks.ROOT / name) != expected:
                    raise RuntimeError("Source changed; prepare first: " + name)
            suites = {
                "motion": "RememberUITests/UnifiedMemorySearchUITests/testClosingSearchPreservesScrolledLibraryAcrossRepeatedSessions",
                "motion-top": "RememberUITests/UnifiedMemorySearchUITests/testClosingSearchPreservesTopOfLibraryAcrossRepeatedSessions",
                "ui": "RememberUITests/UnifiedMemorySearchUITests",
                "unit": "RememberTests/SearchResultsHandoffTests",
            }
            runner.execute("test", suites[action])
