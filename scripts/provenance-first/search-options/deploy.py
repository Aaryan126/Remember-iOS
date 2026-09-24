#!/usr/bin/env python3
"""Same controlled phone-update workflow, separate products/backup/receipts."""
import importlib.util
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("search_menu_checks", CODE / "check.py")
checks = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checks
spec.loader.exec_module(checks)
deployment = checks.prior
deployment.CODE = CODE
deployment.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-options-deployment"
deployment.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-options-deployment"
deployment.checks.verify = checks.verify

if __name__ == "__main__":
    # Reserve a conservative full build+two-backup allowance before starting this
    # refinement's deployment. Keep the previously approved cap and free reserve.
    if sys.argv[1:] == ["prepare"]:
        deployment.configure()
        deployment.resources(1536 * 1024**2)
    elif sys.argv[1:] == ["build"] and not (deployment.RUN / "preparation.json").exists():
        raise SystemExit("Deployment preparation has not completed; resolve its storage hold and run prepare first.")
    deployment.main()
