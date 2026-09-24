#!/usr/bin/env python3
"""Search-menu UI checks; retain completed deployment receipts and storage limits."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("search_options_deployment", CODE.parent / "unified-search/deploy.py")
prior = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prior
spec.loader.exec_module(prior)
ROOT = prior.ROOT
RUN = ROOT / "Evaluation/ProvenanceFirst/runs/search-options"
WORK = ROOT / "Evaluation/ProvenanceFirst/search-options"
RECEIPT = ROOT / "Evaluation/ProvenanceFirst/unified-search-deployment/checkpoint-stop.json"


def preserve():
    saved = prior.d.load(RECEIPT)
    for name, expected in saved["hashes"].items():
        target = RUN / "baseline" / name
        if not target.exists():
            if prior.d.digest(ROOT / name) != expected:
                raise ValueError("deployed input changed: " + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        if prior.d.digest(target) != expected:
            raise ValueError("invalid archive: " + name)
    target = WORK / "baseline.json"
    if not target.exists():
        prior.d.write(target, {"receiptSHA256": prior.d.digest(RECEIPT), "hashes": saved["hashes"]})
    print("Deployed checkpoint inputs preserved")


def verify():
    saved = prior.d.load(WORK / "baseline.json")
    if prior.d.digest(RECEIPT) != saved["receiptSHA256"]:
        raise ValueError("deployment receipt changed")
    for name, expected in saved["hashes"].items():
        if prior.d.digest(RUN / "baseline" / name) != expected:
            raise ValueError("archive changed: " + name)
    return {"archivedFilesVerified": len(saved["hashes"])}


def boundary(reservation=0):
    if (WORK / "PAUSE").exists():
        raise RuntimeError("Paused")
    return prior.resources(reservation)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preserve", "prepare", "unit", "ui", "resources"])
    action = parser.parse_args().action
    prior.configure()
    boundary()
    if action == "preserve": preserve(); return
    if action == "resources": print(json.dumps(boundary())); return
    runner = prior.d.guard
    runner.RUN, runner.WORK = RUN, WORK
    runner.CODE = CODE.parent / "unified-search"  # Reuse the fictional launcher.
    runner.PROJECT = RUN / "project"
    runner.BUILD = ROOT / "Evaluation/ProvenanceFirst/runs/unified-search/build"
    runner.verify_baseline, runner.boundary = verify, boundary
    if action == "prepare": runner.prepare(fixture=True)
    elif action == "unit": runner.execute("test", ["RememberTests/UnifiedMemorySearchTests", "RememberTests/SourceEvidenceBrowserTests"])
    else: runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests")


if __name__ == "__main__": main()
