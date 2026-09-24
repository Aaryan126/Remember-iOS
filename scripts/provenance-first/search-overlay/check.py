#!/usr/bin/env python3
"""Native overlay follow-up; preserve the installed dismissal checkpoint first."""
import importlib.util
import os
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("overlay_checks", CODE.parent / "search-options/check.py")
checks = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checks
spec.loader.exec_module(checks)
checks.CODE = CODE
checks.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-overlay"
checks.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-overlay"
checks.RECEIPT = checks.ROOT / "Evaluation/ProvenanceFirst/search-dismissal-deployment/checkpoint-stop.json"

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
        if action in {"motion", "motion-top", "ui"}:
            for name, expected in checks.prior.d.load(checks.RUN / "preparation.json")["sourceBindings"].items():
                if checks.prior.d.digest(checks.ROOT / name) != expected:
                    raise RuntimeError("Source changed; run prepare before testing: " + name)
        if action == "prepare":
            # First preparation needed a cold rebuild. Once its product and
            # module cache exist, use the runner's normal warm-test reservation.
            # The same 10 GiB floor and cumulative cap remain enforced throughout.
            warm = (runner.BUILD / "Build/Products/Debug-iphonesimulator/Remember.app/Remember").is_file()
            warm = warm and (runner.BUILD / "ModuleCache.noindex").is_dir()
            checks.boundary((256 if warm else 1536) * 1024**2)
            runner.prepare(fixture=True)
        elif action == "motion":
            runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests/testClosingSearchPreservesScrolledLibraryAcrossRepeatedSessions")
        elif action == "motion-top":
            runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests/testClosingSearchPreservesTopOfLibraryAcrossRepeatedSessions")
        elif action == "ui":
            runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests")
        else:
            raise ValueError("Unknown action: " + action)
