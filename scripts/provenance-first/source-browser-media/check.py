#!/usr/bin/env python3
"""Bounded media follow-up reusing the frozen integration runner."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

CODE = Path(__file__).resolve().parent
ROOT = CODE.parents[2]
spec = importlib.util.spec_from_file_location("source_browser_ui_runner", CODE.parent / "source-browser-ui/check.py")
previous = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = previous
spec.loader.exec_module(previous)

OLD_WORK = previous.WORK
OLD_RUN = previous.RUN
WORK = ROOT / "Evaluation/ProvenanceFirst/source-browser-media"
RUN = ROOT / "Evaluation/ProvenanceFirst/runs/source-browser-media"
RECEIPT = OLD_WORK / "checkpoint-stop.json"
RESOURCE_APPROVAL = WORK / "resource-amendment-28.json"
ORIGINAL_ACCOUNTING = previous.accounting


def accounting(free, initial, scoped, external, reservation=0):
    # Reuse the frozen guard, including whole-Mac decline and reservations. Only
    # its approved ceiling and diagnostic wording change in this follow-up.
    try:
        return ORIGINAL_ACCOUNTING(free, initial, scoped, external, reservation)
    except SystemExit as error:
        if str(error) == "26 GiB growth cap reached; preserve original baseline and stop":
            raise SystemExit("28 GiB growth cap reached; preserve original baseline and stop") from None
        raise


def configure_resources():
    previous.CAP = 28 * previous.GIB
    previous.RESOURCE_APPROVAL = RESOURCE_APPROVAL
    previous.accounting = accounting


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    previous.boundary()
    previous.verify_baseline()
    saved = json.loads(RECEIPT.read_text())
    if not saved["complete"] or not saved["stopForReview"]:
        raise ValueError("previous checkpoint is not complete")
    for name, expected in saved["hashes"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("previous input already changed: " + name)
    for name in saved["hashes"]:
        target = WORK / "baseline" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and digest(target) != saved["hashes"][name]:
            raise ValueError("do not overwrite historical archive")
        if not target.exists():
            shutil.copy2(ROOT / name, target)
    path = WORK / "baseline.json"
    with path.open("x") as stream:
        json.dump({"receiptSHA256": digest(RECEIPT), "hashes": saved["hashes"]}, stream, indent=2)
        stream.write("\n")
    print(verify())


def verify():
    saved = json.loads((WORK / "baseline.json").read_text())
    if digest(RECEIPT) != saved["receiptSHA256"]:
        raise ValueError("prior completion receipt changed")
    if saved["hashes"] != json.loads(RECEIPT.read_text())["hashes"]:
        raise ValueError("archive manifest differs from prior receipt")
    for name, expected in saved["hashes"].items():
        if digest(WORK / "baseline" / name) != expected:
            raise ValueError("archived input changed: " + name)
        # App source may evolve; old research/tooling/results remain frozen.
        if not name.startswith("Remember/") and name != "docs/provenance-first.md":
            if digest(ROOT / name) != expected:
                raise ValueError("historical artifact changed: " + name)
    return {"previousReceiptSHA256": saved["receiptSHA256"], "archivedFilesVerified": len(saved["hashes"])}


def configure():
    configure_resources()
    previous.WORK = WORK
    previous.RUN = RUN
    previous.PROJECT = RUN / "project"
    previous.BUILD = RUN / "build"
    previous.CODE = CODE
    previous.verify_baseline = verify
    # Historical files remain unchanged; this process uses the new scoped approval.


def prepare_media():
    assets = RUN / "fixtures"
    assets.mkdir(parents=True, exist_ok=True)
    commands = {
        "photo.png": ["-f", "lavfi", "-i", "color=c=0x366A94:s=480x320", "-frames:v", "1", "-update", "1"],
        "silence.wav": ["-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "60", "-c:a", "pcm_s16le"],
        "brief.wav": ["-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "0.3", "-c:a", "pcm_s16le"],
        "motion.mp4": ["-f", "lavfi", "-i", "testsrc2=size=320x180:rate=12", "-t", "15", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an"],
    }
    for name, arguments in commands.items():
        path = assets / name
        if not path.exists():
            subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n", *arguments, str(path)],
                           check=True, timeout=60)
        previous.copy_file(path, previous.PROJECT / "Remember" / name)
    path = RUN / "preparation.json"
    receipt = json.loads(path.read_text())
    receipt["fictionalMedia"] = {name: digest(assets / name) for name in commands}
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


def checkpoint(args):
    baseline = verify()
    resources = previous.boundary()
    artifacts = set(CODE.glob("*.py")) | set(WORK.glob("*.md"))
    artifacts.update([CODE / "FixtureApp.swift", WORK / "baseline.json", ROOT / "docs/provenance-first.md"])
    artifacts.add(RESOURCE_APPROVAL)
    summaries = {}
    runs = {}
    for role, count in [("unit", 29), ("ui", 10), ("phone", 10), ("build", None)]:
        run_id = getattr(args, role + "_run")
        if not run_id or not re.fullmatch(r"[0-9]+", run_id):
            raise ValueError("provide all successful run IDs")
        path = RUN / (run_id + ".json")
        receipt = json.loads(path.read_text())
        if receipt["exitCode"] != 0: raise ValueError("failed run: " + role)
        for name, expected in receipt["preparation"]["sourceBindings"].items():
            if digest(ROOT / name) != expected: raise ValueError("source changed since " + role + ": " + name)
            artifacts.add(ROOT / name)
        if role == "build":
            if receipt["preparation"]["fixtureLauncher"] or receipt["command"][-1] != "build":
                raise ValueError("production-entrypoint build required")
        else:
            if not receipt["preparation"]["fixtureLauncher"] or receipt["preparation"]["fixtureLauncherSHA256"] != digest(CODE / "FixtureApp.swift"):
                raise ValueError("current fictional launcher required: " + role)
            expected_media = {path.name: digest(path) for path in (RUN / "fixtures").iterdir() if path.is_file()}
            if receipt["preparation"].get("fictionalMedia") != expected_media:
                raise ValueError("fictional media changed since " + role)
            summary = json.loads(subprocess.check_output(["xcrun", "xcresulttool", "get", "test-results", "summary",
                "--path", str(RUN / (run_id + ".xcresult")), "--compact"]))
            if summary["result"] != "Passed" or summary["passedTests"] != count or summary["totalTestCount"] != count or summary["skippedTests"]:
                raise ValueError("unexpected suite result: " + role)
            summaries[role] = summary
        if role == "phone" and f"platform=iOS,id={previous.PHONE}" not in receipt["command"]:
            raise ValueError("physical result required")
        runs[role] = run_id
        artifacts.update([path, RUN / (run_id + ".log")])
    signed = RUN / "phone-build.json"
    if json.loads(signed.read_text())["products"] != previous.phone_products():
        raise ValueError("signed products changed")
    artifacts.add(signed)
    artifacts.update((RUN / "fixtures").glob("*"))
    for folder in RUN.glob("*-review-*"):
        artifacts.update(folder.glob("*.png")); artifacts.update(folder.glob("*.json"))
    record = {"complete": True, "stopForReview": True, "previous": baseline, "resources": resources,
        "runs": runs, "summaries": summaries,
        "hashes": {str(path.relative_to(ROOT)): digest(path) for path in sorted(artifacts)}}
    with (WORK / "checkpoint-stop.json").open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True); stream.write("\n")
    print(json.dumps({"complete": True, "stopForReview": True, "filesBound": len(artifacts)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["snapshot", "verify", "resources", "prepare", "prepare-fixture",
        "build", "test-unit", "test-ui", "test-previews", "build-phone", "test-phone", "save-hold", "checkpoint"])
    for name in ["unit", "ui", "phone", "build"]: parser.add_argument("--" + name + "-run")
    args = parser.parse_args()
    if args.action == "verify":
        print(json.dumps(verify())); return
    if args.action == "resources":
        configure_resources()
        print(json.dumps(previous.resource_snapshot())); return
    with (WORK / "worker.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == "snapshot":
            snapshot(); return
        configure()
        if args.action == "checkpoint": checkpoint(args); return
        if args.action.startswith("prepare"):
            previous.prepare(fixture=args.action == "prepare-fixture")
            if args.action == "prepare-fixture": prepare_media()
        elif args.action == "build": previous.execute("build")
        elif args.action == "test-unit": previous.execute("test", [
            "RememberTests/SourceEvidenceBrowserTests", "RememberTests/ThreadPresentationTests",
            "RememberTests/AppearanceTests", "RememberTests/VideoRiverTests"])
        elif args.action == "build-phone": previous.execute("build-for-testing", ["RememberUITests/SourceEvidenceMediaUITests", "RememberUITests/SourceEvidenceUITests"], phone=True)
        elif args.action == "test-phone": previous.execute("test-without-building", ["RememberUITests/SourceEvidenceMediaUITests", "RememberUITests/SourceEvidenceUITests"], phone=True)
        elif args.action == "test-ui": previous.execute("test", ["RememberUITests/SourceEvidenceMediaUITests", "RememberUITests/SourceEvidenceUITests"])
        elif args.action == "test-previews": previous.execute("test", ["RememberUITests/SourceEvidenceMediaUITests/testImageOriginalAndQuickLookReturn", "RememberUITests/SourceEvidenceMediaUITests/testTextOriginalAndCurrentRiverRoundTrip"])
        elif args.action == "save-hold": previous.save_hold()


if __name__ == "__main__": main()
