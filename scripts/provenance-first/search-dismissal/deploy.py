#!/usr/bin/env python3
"""Search dismissal and compact spacing deployment with verified phone backups."""
import importlib.util
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("dismissal_checks", CODE / "check.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
checks = module.checks
deployment = checks.prior
deployment.CODE = CODE
deployment.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-dismissal-deployment"
deployment.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-dismissal-deployment"
deployment.checks.verify = checks.verify

if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        deployment.configure()
        deployment.resources(1536 * 1024**2)
        tested = deployment.d.load(checks.RUN / "preparation.json")
        for name, expected in tested["sourceBindings"].items():
            if deployment.d.digest(checks.ROOT / name) != expected:
                raise RuntimeError("Source changed since simulator verification: " + name)
    elif sys.argv[1:] == ["build"] and not (deployment.RUN / "preparation.json").exists():
        raise SystemExit("Run prepare successfully before building.")
    deployment.main()
