#!/usr/bin/env python3
"""Authorized in-place typo-search installation using the verified signed build."""
import importlib.util
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("typo_install_checks", CODE / "check.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
checks = module.checks
deployment = checks.prior
deployment.CODE = CODE
deployment.WORK = checks.WORK
deployment.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-typos-device"
deployment.checks.verify = checks.verify


def verify_ready_build():
    deployment.configure()
    deployment.resources()
    deployment.d.verify_signed()
    checks.verify()
    ready = deployment.d.load(checks.WORK / "ready-to-install.json")
    if deployment.d.digest(checks.ROOT / ready["signedBuildReceipt"]) != ready["signedBuildReceiptSHA256"]:
        raise RuntimeError("Signed build differs from the reviewed candidate")
    prepared = deployment.d.load(deployment.RUN / "preparation.json")["sourceBindings"]
    for check in ready["sourceBoundChecks"].values():
        path = checks.ROOT / check["receipt"]
        if deployment.d.digest(path) != check["receiptSHA256"]:
            raise RuntimeError("Reviewed test receipt changed")
        receipt = deployment.d.load(path)
        if receipt["exitCode"] != 0:
            raise RuntimeError("Required simulator check failed")
        for name, expected in receipt["preparation"]["sourceBindings"].items():
            if prepared.get(name) != expected:
                raise RuntimeError("Simulator and signed source differ: " + name)


if __name__ == "__main__":
    allowed = {"resources", "backup", "inspect-backup", "install", "smoke",
               "post-backup", "compare", "launch", "finish"}
    if len(sys.argv) != 2 or sys.argv[1] not in allowed:
        raise SystemExit("Choose: " + ", ".join(sorted(allowed)))
    verify_ready_build()
    deployment.main()
