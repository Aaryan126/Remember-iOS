#!/usr/bin/env python3
"""Deploy the handoff fix using existing signing, backup and preservation gates."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("handoff_deploy_checks", CODE / "check.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
checks = module.checks
deployment = checks.prior
deployment.CODE = CODE
deployment.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-handoff-deployment"
deployment.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-handoff-deployment"
deployment.checks.verify = checks.verify


def verified_suite(suite, count):
    tested = deployment.d.load(checks.RUN / "preparation.json")
    for name, expected in tested["sourceBindings"].items():
        if deployment.d.digest(checks.ROOT / name) != expected:
            raise RuntimeError("Source changed since preparation: " + name)
    for path in sorted(checks.RUN.glob("[0-9]*.json"), reverse=True):
        result = deployment.d.load(path)
        command = result.get("command", [])
        if (result.get("exitCode") != 0 or not command or command[-1] != "test"
                or "-only-testing:" + suite not in command
                or result["preparation"]["sourceBindings"] != tested["sourceBindings"]):
            continue
        summary = json.loads(subprocess.check_output([
            "xcrun", "xcresulttool", "get", "test-results", "summary",
            "--path", str(path.with_suffix(".xcresult")), "--compact"]))
        if (summary["result"] == "Passed" and summary["passedTests"] == count
                and summary["totalTestCount"] == count and not summary["skippedTests"]):
            return {"receipt": str(path.relative_to(checks.ROOT)),
                    "receiptSHA256": deployment.d.digest(path), "summary": summary}
    raise RuntimeError("Missing source-matched passing suite: " + suite)


if __name__ == "__main__":
    action = sys.argv[1:]
    if action == ["archive-uninstalled-build"]:
        import fcntl
        import time
        deployment.configure()
        with (deployment.RUN / "worker.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            deployment.resources()
            if (deployment.RUN / "installation.json").exists():
                raise RuntimeError("Do not refresh an installed checkpoint")
            names = ["project", "preparation.json", "signed-build.json", "simulator-verification.json"]
            if not all((deployment.RUN / name).exists() for name in names):
                raise RuntimeError("Complete uninstalled build required")
            archive = deployment.RUN / ("uninstalled-build-" + str(time.time_ns()))
            archive.mkdir()
            deployment.d.write(archive / "reason.json", {
                "reason": "Explicit main-actor callback types; revalidate source and rebuild before install",
                "receipts": {name: deployment.d.digest(deployment.RUN / name)
                             for name in names if name.endswith(".json")}})
            for name in names:
                (deployment.RUN / name).rename(archive / name)
        print("Previous source and receipts retained; source-matched prepare/build required")
        raise SystemExit(0)
    elif action == ["prepare"]:
        deployment.configure()
        deployment.resources(1536 * 1024**2)
        result = {"ui": verified_suite("RememberUITests/UnifiedMemorySearchUITests", 11),
                  "unit": verified_suite("RememberTests/SearchResultsHandoffTests", 6)}
        deployment.RUN.mkdir(parents=True, exist_ok=True)
        deployment.d.write(deployment.RUN / "simulator-verification.json", result)
    elif action == ["build"] and not (deployment.RUN / "preparation.json").exists():
        raise SystemExit("Prepare successfully before building")
    deployment.main()
