#!/usr/bin/env python3
"""Auditable performance-only continuation of the frozen Stage 2 runner."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

import screening2_common as common
import screening2 as original
from stage5 import Tee


ATTEMPT = "fast-scan-attempt-01"
SOURCES = ("screening2_runtime.py", "test_screening2_runtime.py")
PLAN = common.SCREENING / "RUNTIME_CONTINUATION.md"
MODULES = ("screening2_common", "screening2", "screening2_data", "screening2_models",
           "screening2_neural", "screening2_report", "audit_screening2")


def logical_bytes(folder: Path) -> int:
    """Match Path.rglob/file-size semantics without repeated Path/stat work.

    Directory links are not traversed; file links are counted as in the original.
    No cache is used: additions, deletions and changed file sizes are seen afresh.
    Enumeration/stat errors propagate rather than undercounting storage silently.
    """
    if not folder.is_dir():
        return 0
    total = 0
    pending = [os.fspath(folder)]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    pending.append(entry.path)
                elif entry.is_file():
                    total += entry.stat().st_size
    return total


def capacity_snapshot(planned: int = 2 * 1024**2) -> dict:
    common.require(isinstance(planned, int) and planned >= 0, "invalid planned storage")
    used = logical_bytes(common.SCREENING) + logical_bytes(common.WORKSPACE / "screening")
    free = shutil.disk_usage(common.WORKSPACE).free
    return {"usedBytes": used, "freeBytes": free, "plannedBytes": planned,
            "storageCapBytes": 4 * common.GIB, "freeReserveBytes": 10 * common.GIB,
            "withinCap": used + planned <= 4 * common.GIB,
            "withinReserve": free - planned >= 10 * common.GIB}


class StorageGuard:
    def __init__(self, run: Path):
        self.run = run

    def __call__(self, planned: int = 2 * 1024**2) -> bool:
        measurement = capacity_snapshot(planned)
        okay = measurement["withinCap"] and measurement["withinReserve"]
        if not okay:
            # Keep the exact failing measurement, before model teardown frees RAM/swap.
            common.save(self.run / "runtime-continuations" / ATTEMPT / "storage-pauses" /
                        f"{time.time_ns()}.json", {"at": common.now(), **measurement})
        return okay


@contextmanager
def installed_guard(guard):
    """Explicitly replace only storage guard aliases, never training/eval code.

    Legacy modules use import-star aliases. Load the finite module set first so
    each alias is accounted for, including when tests have already imported them.
    """
    modules = [importlib.import_module(name) for name in MODULES]
    previous = common.capacity
    replacements = []
    for module in modules:
        if hasattr(module, "capacity"):
            common.require(module.capacity is previous, "unexpected storage guard override")
            replacements.append((module, module.capacity))
    try:
        for module, _ in replacements:
            module.capacity = guard
        yield
    finally:
        for module, value in replacements:
            module.capacity = value


def folder_for(run: Path) -> Path:
    folder = run / "runtime-continuations" / ATTEMPT
    common.require(not folder.is_symlink() and not folder.parent.is_symlink(),
                   "continuation symlink rejected")
    return folder


def source_bindings() -> dict:
    paths = [common.HERE / name for name in SOURCES] + [PLAN]
    return {str(path.relative_to(common.ROOT)): common.sha(path) for path in paths}


def preserved_files(run: Path) -> dict:
    excluded = ("logs/", "control/", "runtime-continuations/")
    return {name: digest for name, digest in common.files_in(run).items()
            if name != "worker.lock" and not name.startswith(excluded)}


def benchmark() -> dict:
    samples = []
    for _ in range(3):
        start = time.monotonic()
        baseline = common.logical_bytes(common.SCREENING) + common.logical_bytes(common.WORKSPACE / "screening")
        original_seconds = time.monotonic() - start
        start = time.monotonic()
        optimized = logical_bytes(common.SCREENING) + logical_bytes(common.WORKSPACE / "screening")
        optimized_seconds = time.monotonic() - start
        common.require(baseline == optimized, "live byte-count parity failed; keep worker stopped")
        samples.append({"bytes": baseline, "originalSeconds": original_seconds,
                        "optimizedSeconds": optimized_seconds})
    return {"at": common.now(), "passed": True, "samples": samples,
            "note": "Fresh complete scans; no caching or reduced safety-check frequency."}


def prepare(run: Path, external: Path) -> dict:
    original.verify(run, external)
    common.require(not (run / "complete.json").exists(), "cannot amend a completed experiment")
    folder = folder_for(run)
    if (folder / "manifest.json").exists():
        return verify(run, external)
    common.require(common.capacity(32 * 1024**2), "insufficient continuation preparation space")
    comparison = benchmark()
    evidence = preserved_files(run)
    exports = {name: digest for name, digest in common.files_in(external).items()
               if name.startswith("models/")}
    common.require(bool(exports), "expected existing lossless model exports")
    recovery = common.recovery_receipts(run)[-1]
    common.require(common.sha(external / recovery["file"]) == recovery["SHA256"], "recovery changed")
    for name in SOURCES:
        destination = folder / "source-snapshots" / name
        if destination.exists():
            common.require(common.sha(destination) == common.sha(common.HERE / name), "partial snapshot changed")
        else:
            common.publish_bytes(destination, (common.HERE / name).read_bytes())
    report = folder / "benchmark.json"
    if not report.exists():
        common.save(report, comparison)
    manifest = {"schemaVersion": 1, "attempt": ATTEMPT, "at": common.now(),
                "authorization": "user: Okay u can carry on as you feel is best, after performance-only fix proposal",
                "originalManifestSHA256": common.sha(run / "manifest.json"),
                "sourceBindings": source_bindings(), "preservedEvidence": evidence,
                "preservedModelExports": exports, "startingRecovery": recovery,
                "benchmarkSHA256": common.sha(report),
                "scope": "fresh folder enumeration and exact storage-pause telemetry only",
                "modelDataEvaluationSettingsChanged": False, "testAccess": False,
                "storageCapBytes": 4 * common.GIB, "freeReserveBytes": 10 * common.GIB}
    common.save(folder / "manifest.json", manifest)
    return {"prepared": True, "continuation": ATTEMPT, "benchmark": comparison}


def verify(run: Path, external: Path) -> dict:
    result = original.verify(run, external)
    folder = folder_for(run)
    record = common.read(folder / "manifest.json")
    common.require(record["sourceBindings"] == source_bindings(), "continuation source freeze changed")
    common.require(record["originalManifestSHA256"] == common.sha(run / "manifest.json"), "original manifest changed")
    common.require(record["storageCapBytes"] == 4 * common.GIB and
                   record["freeReserveBytes"] == 10 * common.GIB and
                   record["modelDataEvaluationSettingsChanged"] is False, "continuation scope changed")
    common.verify_files(folder / "source-snapshots", {name: common.sha(common.HERE / name) for name in SOURCES})
    common.verify_files(run, record["preservedEvidence"])
    common.verify_files(external, record["preservedModelExports"])
    common.require(common.sha(folder / "benchmark.json") == record["benchmarkSHA256"], "benchmark changed")
    return result | {"continuationVerified": True, "continuation": ATTEMPT,
                     "continuationManifestSHA256": common.sha(folder / "manifest.json")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run", "pause", "verify"))
    parser.add_argument("--run", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--pause-after-steps", type=int)
    args = parser.parse_args()
    run, external = common.paths(args.run)
    common.setup()
    if args.action == "pause":
        print(json.dumps({"status": common.request_pause(run)}))
        return
    handle = common.lock(run)
    stdout, stderr = sys.stdout, sys.stderr
    log = None
    try:
        if args.action == "prepare":
            print(json.dumps(prepare(run, external)))
            return
        check = verify(run, external)
        if args.action == "verify" or check["complete"]:
            print(json.dumps(check))
            return
        common.require(args.resume, "continuation requires explicit --resume")
        if args.pause_after_steps is not None:
            common.require(args.pause_after_steps > 0, "pause steps must be positive")
        (run / "logs").mkdir(exist_ok=True)
        log = (run / "logs" / f"runtime-{time.time_ns()}.log").open("x")
        sys.stdout, sys.stderr = Tee(stdout, log), Tee(stderr, log)
        print(json.dumps({"phase": "runtime-continuation", **check}), flush=True)
        with installed_guard(StorageGuard(run)):
            original.execute(run, external, resume=True, pause_after_steps=args.pause_after_steps)
        # Read-only verification covers both the legacy freeze and this supplement.
        print(json.dumps(verify(run, external)), flush=True)
    except common.Paused as error:
        print(json.dumps({"status": "paused", "phase": str(error), "safeToCloseLaptop": True}), flush=True)
    except Exception as error:
        common.save(run / "failures" / f"{time.time_ns()}.json",
                    {"at": common.now(), "type": type(error).__name__, "error": str(error),
                     "runtimeContinuation": ATTEMPT})
        raise
    finally:
        handle.close()
        sys.stdout, sys.stderr = stdout, stderr
        if log:
            log.close()


if __name__ == "__main__":
    main()
