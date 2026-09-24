#!/usr/bin/env python3
"""Deploy the traced search fix only after full UI validation and fresh backup."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("overlay_deploy_checks", CODE / "check.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
checks = module.checks
deployment = checks.prior
deployment.CODE = CODE
deployment.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-overlay-deployment"
deployment.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-overlay-deployment"
deployment.checks.verify = checks.verify

def verified_ui():
    tested = deployment.d.load(checks.RUN / "preparation.json")
    for name, expected in tested["sourceBindings"].items():
        if deployment.d.digest(checks.ROOT / name) != expected:
            raise RuntimeError("Source changed since simulator preparation: " + name)
    for path in sorted(checks.RUN.glob("[0-9]*.json"), reverse=True):
        result = deployment.d.load(path)
        command = result.get("command", [])
        if (result.get("exitCode") != 0 or not command or command[-1] != "test"
                or "-only-testing:RememberUITests/UnifiedMemorySearchUITests" not in command
                or result["preparation"]["sourceBindings"] != tested["sourceBindings"]):
            continue
        summary = json.loads(subprocess.check_output(["xcrun", "xcresulttool", "get", "test-results", "summary",
            "--path", str(path.with_suffix(".xcresult")), "--compact"]))
        if (summary["result"] == "Passed" and summary["passedTests"] == 11
                and summary["totalTestCount"] == 11 and not summary["skippedTests"]):
            return {"receipt": str(path.relative_to(checks.ROOT)),
                    "receiptSHA256": deployment.d.digest(path), "summary": summary}
    raise RuntimeError("A source-matched 11/11 simulator UI pass is required")

if __name__ == "__main__":
    action = sys.argv[1:]
    if action == ["archive-install-attempt"]:
        import fcntl
        deployment.configure()
        with (deployment.RUN / "worker.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            deployment.resources()
            deployment.d.verify_signed()
            names = ["installation.json", "backup-approved.json", "launch-approved.json"]
            if not all((deployment.RUN / name).is_file() for name in names):
                raise RuntimeError("Previous install and backup receipts are required")
            archive = deployment.RUN / "install-before-harness-correction"
            archive.mkdir()
            deployment.d.write(archive / "reason.json", {
                "reason": "Harness rebuild changed signed app bytes; require fresh backup and explicit reinstall",
                "receipts": {name: deployment.d.digest(deployment.RUN / name) for name in names}})
            for name in names:
                (deployment.RUN / name).rename(archive / name)
        print("Previous receipts retained; fresh backup/preflight/reinstall required")
        raise SystemExit(0)
    elif action == ["refresh-smoke"]:
        import fcntl
        deployment.configure()
        with (deployment.RUN / "worker.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            deployment.resources()
            deployment.d.refresh_smoke()
        raise SystemExit(0)
    elif action == ["prepare"]:
        deployment.configure()
        deployment.resources(1536 * 1024**2)
        result = verified_ui()
        deployment.RUN.mkdir(parents=True, exist_ok=True)
        deployment.d.write(deployment.RUN / "simulator-verification.json", result)
    elif action == ["build"] and not (deployment.RUN / "preparation.json").exists():
        raise SystemExit("Run prepare successfully before building")
    deployment.main()
