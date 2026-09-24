#!/usr/bin/env python3
"""Typo-search verification and signed build preparation; never installs on a phone."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("typo_search_checks", CODE.parent / "search-options/check.py")
checks = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checks
spec.loader.exec_module(checks)
checks.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-typos"
checks.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-typos"
checks.RECEIPT = checks.ROOT / "Evaluation/ProvenanceFirst/search-opening-deployment/checkpoint-stop.json"


def native_check(benchmark=False):
    checks.boundary(256 * 1024**2)
    app = checks.ROOT / "Remember/Remember"
    sources = [app / "SearchTextMatcher.swift"]
    label = "benchmark" if benchmark else "source-regression"
    if benchmark:
        sources.append(CODE / "Benchmark.swift")
    else:
        spec = importlib.util.spec_from_file_location("source_regression_support", CODE.parent / "source-browser/check.py")
        foundation = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foundation)
        support = checks.RUN / "ProductionSupport.swift"
        support.write_text(foundation.support())
        sources += [support, app / "SourceEvidenceSearch.swift", app / "SourceEvidenceStoreAdapter.swift",
                    CODE.parent / "source-browser/SourceEvidenceTests.swift"]
    binary = checks.RUN / label
    command = ["xcrun", "swiftc", "-O", "-swift-version", "5", "-default-isolation", "MainActor",
               "-strict-concurrency=complete", "-warnings-as-errors", "-parse-as-library",
               *map(str, sources), "-o", str(binary)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    receipt = {"command": command, "sources": {str(p.relative_to(checks.ROOT)): checks.prior.d.digest(p) for p in sources},
               "buildExitCode": result.returncode, "buildOutput": result.stdout + result.stderr}
    if result.returncode == 0:
        run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=180)
        receipt.update(exitCode=run.returncode, stdout=run.stdout, stderr=run.stderr)
    (checks.RUN / (label + ".json")).write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))
    checks.boundary()
    raise SystemExit(result.returncode or receipt.get("exitCode", 1))


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["resources", "preserve", "prepare", "unit", "ui",
                                         "native", "benchmark", "prepare-device", "build-device"])
    action = parser.parse_args().action
    checks.prior.configure()
    checks.boundary()
    if action == "resources":
        print(json.dumps(checks.boundary()))
        return
    if action == "preserve":
        checks.preserve()
        return
    if action in {"native", "benchmark"}:
        native_check(benchmark=action == "benchmark")
    if action in {"prepare-device", "build-device"}:
        deployment = checks.prior
        deployment.WORK = checks.ROOT / "Evaluation/ProvenanceFirst/search-typos"
        deployment.RUN = checks.ROOT / "Evaluation/ProvenanceFirst/runs/search-typos-device"
        deployment.CODE = CODE.parent / "search-handoff"
        deployment.checks.verify = checks.verify
        deployment.configure()
        deployment.RUN.mkdir(parents=True, exist_ok=True)
        if action == "prepare-device":
            deployment.resources(1536 * 1024**2)
            deployment.d.prepare()
        else:
            # The older shared device cache was cleaned up. Use this build's own
            # cache and the existing larger cold-build reservation instead.
            deployment.d.xcode("build-for-testing")
        return
    runner = checks.prior.d.guard
    runner.RUN, runner.WORK = checks.RUN, checks.WORK
    runner.CODE = CODE.parent / "search-transition"  # Existing fictional library; no cloud/startup.
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
    suites = ["RememberTests/SearchTextMatcherTests", "RememberTests/UnifiedMemorySearchTests",
              "RememberTests/SourceEvidenceBrowserTests", "RememberTests/RememberTests",
              "RememberTests/VideoIndexingTests", "RememberTests/SearchResultsHandoffTests"]
    runner.execute("test", suites if action == "unit" else "RememberUITests/UnifiedMemorySearchUITests")


if __name__ == "__main__":
    main()
