#!/usr/bin/env python3
"""Opening synchronization update; reuse backup/signing/preservation safeguards."""
import importlib.util
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("opening_handoff_deployment", CODE.parent / "search-handoff/deploy.py")
handoff = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = handoff
spec.loader.exec_module(handoff)
deployment = handoff.deployment
deployment.WORK = handoff.checks.ROOT / "Evaluation/ProvenanceFirst/search-opening-deployment"
deployment.RUN = handoff.checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-opening-deployment"

if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        deployment.configure()
        deployment.resources(1536 * 1024**2)
        result = {"ui": handoff.verified_suite("RememberUITests/UnifiedMemorySearchUITests", 11),
                  "unit": handoff.verified_suite("RememberTests/SearchResultsHandoffTests", 6)}
        deployment.RUN.mkdir(parents=True, exist_ok=True)
        deployment.d.write(deployment.RUN / "simulator-verification.json", result)
    elif sys.argv[1:] == ["finish"]:
        deployment.configure()
        deployment.resources()
        deployment.d.write(deployment.RUN / "entrypoints.json", {
            str(path.relative_to(handoff.checks.ROOT)): deployment.d.digest(path)
            for path in CODE.glob("*.py")})
    deployment.main()
