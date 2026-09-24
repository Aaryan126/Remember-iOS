#!/usr/bin/env python3
"""Isolated unified-search checks; no Git writes or personal-device access."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

CODE = Path(__file__).resolve().parent
ROOT = CODE.parents[2]
WORK = ROOT / "Evaluation/ProvenanceFirst/unified-search"
RUN = ROOT / "Evaluation/ProvenanceFirst/runs/unified-search"
spec = importlib.util.spec_from_file_location("unified_deployment_guard", CODE.parent / "main-app-deployment/deploy.py")
deployment = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = deployment
spec.loader.exec_module(deployment)


def archive():
    deployment.resources()
    receipt = ROOT / "Evaluation/ProvenanceFirst/main-app-deployment/checkpoint-stop.json"
    saved = json.loads(receipt.read_text())
    if not saved["complete"] or not saved["stopForReview"]:
        raise ValueError("previous deployment is incomplete")
    for name, expected in saved["hashes"].items():
        source = ROOT / name
        target = WORK / "baseline" / name
        if target.exists():
            if deployment.digest(target) != expected:
                raise ValueError("archived baseline changed: " + name)
        else:
            if deployment.digest(source) != expected:
                raise ValueError("checkpoint input already changed: " + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    target = WORK / "baseline.json"
    if not target.exists():
        deployment.write(target, {"receiptSHA256": deployment.digest(receipt), "hashes": saved["hashes"]})
    print("Preserved", len(saved["hashes"]), "deployment input bindings")


def verify():
    saved = json.loads((WORK / "baseline.json").read_text())
    receipt = ROOT / "Evaluation/ProvenanceFirst/main-app-deployment/checkpoint-stop.json"
    if deployment.digest(receipt) != saved["receiptSHA256"]:
        raise ValueError("historical receipt changed")
    for name, expected in saved["hashes"].items():
        if deployment.digest(WORK / "baseline" / name) != expected:
            raise ValueError("historical source archive changed: " + name)
    return {"archivedFilesVerified": len(saved["hashes"])}


def boundary(reservation=0):
    if (WORK / "PAUSE").exists():
        raise SystemExit("Unified-search checks paused; no further unit dispatched")
    return deployment.resources(reservation)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["archive", "resources", "prepare", "prepare-ui", "unit", "ui", "build"])
    action = parser.parse_args().action
    if action == "archive":
        archive()
        return
    if action == "resources":
        print(json.dumps(deployment.resources()))
        return
    runner = deployment.guard
    runner.WORK, runner.RUN, runner.CODE = WORK, RUN, CODE
    runner.PROJECT, runner.BUILD = RUN / "project", RUN / "build"
    runner.verify_baseline = verify
    runner.boundary = boundary
    if (WORK / "PAUSE").exists():
        raise SystemExit("Paused")
    if action in {"prepare", "prepare-ui"}:
        runner.prepare(fixture=action == "prepare-ui")
    elif action == "unit":
        runner.execute("test", ["RememberTests/SourceEvidenceBrowserTests", "RememberTests/UnifiedMemorySearchTests"])
    elif action == "ui":
        runner.execute("test", "RememberUITests/UnifiedMemorySearchUITests")
    else:
        runner.execute("build")


if __name__ == "__main__":
    main()
