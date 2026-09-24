#!/usr/bin/env python3
"""Populated-search dismissal checks, preserving the installed spacing checkpoint."""
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
checks.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-dismissal"
checks.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-dismissal"
checks.RECEIPT = checks.ROOT / "Evaluation/ProvenanceFirst/search-spacing-deployment/checkpoint-stop.json"

if __name__ == "__main__":
    os.umask(0o077)
    action = sys.argv[1]
    checks.prior.configure()
    checks.boundary()
    if action == "preserve":
        # The compact-spacing follow-up already changed live inputs. Preserve
        # the verified installed bytes from its archive, not the working tree.
        checks.ROOT = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-compact/baseline"
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
        elif action == "motion":
            runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests/testClosingSearchPreservesScrolledLibraryAcrossRepeatedSessions")
        elif action == "ui":
            runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests")
        else:
            raise ValueError("Unknown action: " + action)
