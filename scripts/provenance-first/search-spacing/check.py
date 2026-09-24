#!/usr/bin/env python3
"""Search header layout checks, preserving the installed motion checkpoint."""
import importlib.util
import os
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("search_spacing_checks", CODE.parent / "search-motion/check.py")
motion = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = motion
spec.loader.exec_module(motion)
checks = motion.checks
checks.CODE = CODE
checks.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-spacing"
checks.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-spacing"
checks.RECEIPT = checks.ROOT / "Evaluation/ProvenanceFirst/search-motion-deployment/checkpoint-stop.json"

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
        runner.CODE = CODE.parent / "search-transition"
        runner.PROJECT = checks.RUN / "project"
        runner.BUILD = checks.ROOT / "Evaluation/ProvenanceFirst/runs/unified-search/build"
        runner.verify_baseline, runner.boundary = checks.verify, checks.boundary
        if action == "prepare":
            runner.prepare(fixture=True)
        elif action == "layout":
            runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests/testSearchHeaderAlignmentAndBalancedSpacing")
        elif action == "ui":
            runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests")
        else:
            raise ValueError("Unknown action: " + action)
