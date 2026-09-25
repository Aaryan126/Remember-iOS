#!/usr/bin/env python3
"""Library control transition simulator checks."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("memory_return_checks", CODE.parent / "search-options/check.py")
checks = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checks
spec.loader.exec_module(checks)
checks.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/memory-controls-motion"
checks.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/memory-controls-motion"
checks.RECEIPT = checks.ROOT / "Evaluation/ProvenanceFirst/memory-return/checkpoint-stop.json"


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preserve", "resources", "prepare", "unit", "ui", "status-ui", "return-ui", "photo-ui", "regressions"])
    action = parser.parse_args().action
    checks.prior.configure()
    checks.boundary()
    if action == "preserve":
        checks.preserve()
        return
    if action == "resources":
        print(json.dumps(checks.boundary()))
        return
    runner = checks.prior.d.guard
    runner.RUN, runner.WORK = checks.RUN, checks.WORK
    runner.CODE = CODE.parent / "memory-return"
    runner.PROJECT = checks.RUN / "project"
    runner.BUILD = checks.ROOT / "Evaluation/ProvenanceFirst/runs/unified-search/build"
    runner.verify_baseline, runner.boundary = checks.verify, checks.boundary
    if action == "prepare":
        checks.boundary(512 * 1024**2)
        runner.prepare(fixture=True)
        return
    for name, expected in checks.prior.d.load(checks.RUN / "preparation.json")["sourceBindings"].items():
        if checks.prior.d.digest(checks.ROOT / name) != expected:
            raise RuntimeError("Source changed; prepare first: " + name)
    suites = {
        "photo-ui": "RememberUITests/MemoryReturnUITests/testPhotoBackAndInteractiveCancellationRestoreLibraryControls",
        "return-ui": "RememberUITests/MemoryReturnUITests",
        "regressions": ["RememberUITests/MemoryReturnUITests",
                        "RememberUITests/UnifiedMemorySearchUITests/testClosingSearchPreservesTopOfLibraryAcrossRepeatedSessions",
                        "RememberUITests/UnifiedMemorySearchUITests/testClosingSearchPreservesScrolledLibraryAcrossRepeatedSessions"],
        "unit": ["RememberTests/UnifiedMemorySearchTests", "RememberTests/SourceEvidenceBrowserTests",
                 "RememberTests/SearchResultsHandoffTests"],
        "ui": "RememberUITests/UnifiedMemorySearchUITests",
        "status-ui": ["RememberUITests/UnifiedMemorySearchUITests/testEmptySearchStatusIsCenteredBelowHeader",
                      "RememberUITests/UnifiedMemorySearchUITests/testLoadingUsesSamePositionAsEmptyMessage",
                      "RememberUITests/UnifiedMemorySearchUITests/testFailedSavedSearchKeepsErrorAndRetry"],
    }
    runner.execute("test", suites[action])


if __name__ == "__main__":
    main()
