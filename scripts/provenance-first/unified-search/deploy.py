#!/usr/bin/env python3
"""Approved unified-search deployment, reusing frozen backup/signing safeguards."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("unified_search_checks", CODE / "check.py")
checks = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checks
spec.loader.exec_module(checks)
d = checks.deployment
ROOT = checks.ROOT
WORK = ROOT / "Evaluation/ProvenanceFirst/unified-search-deployment"
RUN = ROOT / "Evaluation/ProvenanceFirst/runs/unified-search-deployment"
APPROVAL = WORK / "resource-amendment-32.json"


def resources(reservation=0):
    if (WORK / "PAUSE").exists():
        raise RuntimeError("Deployment paused")
    snapshot = d.guard.resource_snapshot()
    if snapshot["freeBytes"] - reservation < 10 * d.GIB:
        raise RuntimeError("10 GiB free reserve would be exceeded")
    if snapshot["conservativeGrowthBytes"] + reservation > 32 * d.GIB:
        raise RuntimeError("32 GiB cumulative ceiling would be exceeded")
    return snapshot


def configure():
    d.CODE, d.WORK, d.RUN = CODE, WORK, RUN
    d.PROJECT, d.BUILD = RUN / "project", RUN / "build"
    d.APP = d.BUILD / "Build/Products/Debug-iphoneos/Remember.app"
    d.guard.CAP = 32 * d.GIB
    d.guard.RESOURCE_APPROVAL = APPROVAL
    d.resources = resources
    # Validate the archived prior deployment rather than rewriting old receipts
    # to match the newly integrated UI.
    d.verify_old = checks.verify


def build():
    d.verify_sources()
    # Reuse precompiled SDK modules from the earlier signed iPhone build. Products
    # and receipts live in this checkpoint; older signed products stay untouched.
    cache = ROOT / "Evaluation/ProvenanceFirst/runs/main-app-deployment/build/ModuleCache.noindex"
    if not cache.is_dir():
        raise RuntimeError("Prior device module cache missing; reassess build reservation")
    command = ["xcodebuild", "-project", str(d.PROJECT / "Remember.xcodeproj"),
        "-scheme", "Remember", "-configuration", "Debug", "-destination", "platform=iOS,id=" + d.PHONE,
        "-derivedDataPath", str(d.BUILD), "-disableAutomaticPackageResolution", "-skipPackageUpdates",
        "-parallel-testing-enabled", "NO", "-collect-test-diagnostics", "never",
        "COMPILER_INDEX_STORE_ENABLE=NO", "DEBUG_INFORMATION_FORMAT=dwarf", "SWIFT_EMIT_LOC_STRINGS=NO",
        "CODE_SIGNING_ALLOWED=YES", "DEVELOPMENT_TEAM=" + d.TEAM,
        "CLANG_MODULE_CACHE_PATH=" + str(cache), "SWIFT_MODULE_CACHE_PATH=" + str(cache),
        "-only-testing:RememberUITests/MainAppSmokeTests", "-allowProvisioningUpdates", "build-for-testing"]
    operation = d.run(command, "signed-main-app-build", reservation=768 * 1024**2, timeout=1200)
    d.write(RUN / "signed-build.json", {"operation": operation, "products": d.signed_products(),
        "preparationSHA256": d.digest(RUN / "preparation.json")})
    print(json.dumps({"signedMainAppBuildPassed": True, "operation": operation}))


def finish():
    d.verify_signed()
    d.require_backup()
    preserved = d.load(RUN / "preservation.json")
    if not all(preserved[key] for key in ["sqliteIntegrityOK", "allOriginalBytesUnchanged",
            "allMemoryRowsUnchanged", "historicalEventsUnchanged"]):
        raise RuntimeError("Preservation gate failed")
    suites = sorted(RUN.glob("smoke-*.xcresult"))
    if not suites:
        raise RuntimeError("No phone smoke result")
    import subprocess
    summary = json.loads(subprocess.check_output(["xcrun", "xcresulttool", "get", "test-results",
        "summary", "--path", str(suites[-1]), "--compact"]))
    if summary["result"] != "Passed" or summary["passedTests"] != 1 or summary["skippedTests"] or summary["failedTests"]:
        raise RuntimeError("Phone smoke gate failed")
    installation = d.load(RUN / "installation.json")
    if installation["uninstalled"] or installation["after"]["bundleIdentifier"] != d.BUNDLE:
        raise RuntimeError("Installed identity mismatch")
    paths = set(CODE.glob("*.py")) | set(CODE.glob("*.swift")) | set(WORK.glob("*.md"))
    paths.update([APPROVAL, ROOT / "docs/unified-memory-search.md", ROOT / "docs/provenance-first.md"])
    paths.update(ROOT / name for name in d.load(RUN / "preparation.json")["sourceBindings"])
    paths.update(RUN.glob("*.json"))
    paths.update((RUN / "operations").glob("*.json"))
    for key in ["backup", "postSnapshot"]:
        paths.add(ROOT / preserved[key] / "verified.json")
    d.write(WORK / "checkpoint-stop.json", {"complete": True, "stopForReview": True,
        "previous": checks.verify(), "resources": resources(), "smokeSummary": summary,
        "preservation": preserved, "uninstalled": False,
        "hashes": {str(p.relative_to(ROOT)): d.digest(p) for p in sorted(paths)}})
    print(json.dumps({"complete": True, "installed": d.BUNDLE, "stopForReview": True}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["resources", "prepare", "build", "backup", "inspect-backup",
        "install", "smoke", "post-backup", "compare", "launch", "finish"])
    action = parser.parse_args().action
    os.umask(0o077)
    configure()
    RUN.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (RUN / "worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        resources()
        if action == "resources": print(json.dumps(resources()))
        elif action == "prepare": d.prepare()
        elif action == "build": build()
        elif action == "backup": d.backup("backup")
        elif action == "inspect-backup": d.inspect_backup()
        elif action == "install":
            # Preserve headroom for a full post-install snapshot before installing.
            resources(600 * 1024**2)
            d.install()
        elif action == "smoke": d.xcode("test-without-building")
        elif action == "post-backup": d.backup("post-install")
        elif action == "compare": d.compare_after()
        elif action == "launch":
            d.verify_signed()
            d.require_backup()
            if not (RUN / "launch-approved.json").exists():
                raise RuntimeError("Launch preflight missing")
            d.run(["xcrun", "devicectl", "device", "process", "launch", "--device", d.PHONE,
                   d.BUNDLE, "--timeout", "60", "--quiet"], "open-updated-app", timeout=90)
            print("Updated Remember opened")
        else: finish()


if __name__ == "__main__":
    main()
