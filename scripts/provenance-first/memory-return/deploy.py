#!/usr/bin/env python3
"""Authorized memory-return installation with existing preservation safeguards."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("return_install_checks", CODE / "check.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
checks = module.checks
deployment = checks.prior
deployment.CODE = CODE
deployment.WORK = checks.WORK
deployment.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/memory-return-device"
deployment.checks.verify = checks.verify


def verified_suite(suite, count):
    prepared = deployment.d.load(deployment.RUN / "preparation.json")["sourceBindings"]
    for path in sorted(checks.RUN.glob("[0-9]*.json"), reverse=True):
        result = deployment.d.load(path)
        if (result.get("exitCode") != 0
                or "-only-testing:" + suite not in result.get("command", [])
                or any(prepared.get(name) != expected for name, expected
                       in result["preparation"]["sourceBindings"].items())):
            continue
        summary = json.loads(subprocess.check_output([
            "xcrun", "xcresulttool", "get", "test-results", "summary",
            "--path", str(path.with_suffix(".xcresult")), "--compact"]))
        if (summary["result"] == "Passed" and summary["passedTests"] == count
                and summary["totalTestCount"] == count and not summary["skippedTests"]):
            return {"receipt": str(path.relative_to(checks.ROOT)),
                    "receiptSHA256": deployment.d.digest(path), "passed": count}
    raise RuntimeError("Missing source-matched passing suite: " + suite)


def verify_ready():
    deployment.d.verify_signed()
    ready = deployment.d.load(checks.WORK / "ready-to-install.json")
    if deployment.d.digest(deployment.RUN / "signed-build.json") != ready["signedBuildReceiptSHA256"]:
        raise RuntimeError("Signed build differs from verified candidate")
    prepared = deployment.d.load(deployment.RUN / "preparation.json")["sourceBindings"]
    for check in ready["sourceBoundChecks"].values():
        path = checks.ROOT / check["receipt"]
        if deployment.d.digest(path) != check["receiptSHA256"]:
            raise RuntimeError("Verified test receipt changed")
        result = deployment.d.load(path)
        if result["exitCode"] != 0 or any(prepared.get(name) != expected for name, expected
                in result["preparation"]["sourceBindings"].items()):
            raise RuntimeError("Simulator and signed sources differ")


if __name__ == "__main__":
    allowed = {"resources", "prepare", "build", "ready", "refresh-smoke", "refresh-installation", "backup", "inspect-backup",
               "install", "smoke", "post-backup", "compare", "launch", "finish"}
    if len(sys.argv) != 2 or sys.argv[1] not in allowed:
        raise SystemExit("Choose: " + ", ".join(sorted(allowed)))
    action = sys.argv[1]
    deployment.configure()
    deployment.resources()
    checks.verify()
    if action == "refresh-smoke":
        verify_ready()
        deployment.d.refresh_smoke()
        (checks.WORK / "ready-to-install.json").rename(
            deployment.RUN / ("ready-before-smoke-" + str(time.time_ns()) + ".json"))
    elif action == "refresh-installation":
        deployment.d.verify_signed()
        previous = sorted(deployment.RUN.glob("preparation-before-smoke-*.json"))[-1]
        if deployment.d.load(previous)["sourceBindings"] != deployment.d.load(deployment.RUN / "preparation.json")["sourceBindings"]:
            raise RuntimeError("App sources changed during harness refresh")
        archive = deployment.RUN / ("installation-before-smoke-" + str(time.time_ns()))
        archive.mkdir()
        for name in ["installation.json", "backup-approved.json", "launch-approved.json"]:
            (deployment.RUN / name).rename(archive / name)
        deployment.d.write(archive / "reason.json", {
            "reason": "Harness rebuild re-signed unchanged app sources; fresh backup and install required",
            "appSourceBindingsUnchanged": True})
        print("Prior installation preserved; fresh backup and installation required")
    elif action == "build":
        deployment.d.xcode("build-for-testing")
    elif action == "ready":
        deployment.d.verify_signed()
        if (deployment.RUN / "installation.json").exists():
            installation = deployment.d.load(deployment.RUN / "installation.json")
            archived = next((p for p in deployment.RUN.glob("signed-build-before-smoke-*.json")
                             if deployment.d.digest(p) == installation["signedBuildSHA256"]), None)
            if archived is None or deployment.d.load(archived)["products"] != deployment.d.signed_products():
                raise RuntimeError("Installed app products changed during harness rebuild")
            deployment.d.write(deployment.RUN / "harness-product-verification.json", {
                "installedSignedBuildReceipt": str(archived.relative_to(checks.ROOT)),
                "normalAppAndExtensionUnchanged": True})
        deployment.d.write(checks.WORK / "ready-to-install.json", {
            "signedBuildReceiptSHA256": deployment.d.digest(deployment.RUN / "signed-build.json"),
            "sourceBoundChecks": {
                "ui": verified_suite("RememberUITests/MemoryReturnUITests", 6)}})
        print("Signed build and final simulator checks verified")
    else:
        if action not in {"resources", "prepare"}:
            verify_ready()
        deployment.main()
