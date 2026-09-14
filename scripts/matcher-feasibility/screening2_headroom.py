#!/usr/bin/env python3
"""Authorized temporary checkpoint headroom; frozen statistical code is reused."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import sys
import time

import screening2_runtime as runtime

common = runtime.common
original = runtime.original
ATTEMPT = "checkpoint-headroom-attempt-01"
SOURCES = ("screening2_headroom.py", "test_screening2_headroom.py")
PLAN = common.SCREENING / "CHECKPOINT_HEADROOM.md"
TEMPORARY_CAP = 9 * common.GIB // 2
FINAL_CAP = 4 * common.GIB
FREE_RESERVE = 10 * common.GIB


def folder_for(run):
    folder = run / "runtime-continuations" / ATTEMPT
    common.require(not folder.is_symlink() and not folder.parent.is_symlink(), "headroom symlink rejected")
    return folder


def source_bindings():
    return {str(p.relative_to(common.ROOT)): common.sha(p)
            for p in [common.HERE / name for name in SOURCES] + [PLAN]}


class StorageGuard:
    def __init__(self, run):
        self.run = run
        self.finalizing = False

    def measurement(self, planned=2 * 1024**2):
        record = runtime.capacity_snapshot(planned)
        cap = FINAL_CAP if self.finalizing else TEMPORARY_CAP
        return record | {"storageCapBytes": cap, "finalStorageTargetBytes": FINAL_CAP,
                         "finalizing": self.finalizing,
                         "withinCap": record["usedBytes"] + planned <= cap}

    def __call__(self, planned=2 * 1024**2):
        record = self.measurement(planned)
        okay = record["withinCap"] and record["withinReserve"]
        if not okay:
            common.save(folder_for(self.run) / "storage-pauses" / f"{time.time_ns()}.json",
                        {"at": common.now(), **record})
        return okay


@contextmanager
def installed_policy(guard):
    # The sole extra boundary hook restores the final 4 GiB cap before auditing.
    # No fitting, prediction, threshold, selection or audit function is replaced.
    previous = original.boundary

    def boundary(run, phase, planned=2 * 1024**2):
        if phase == "final-audit":
            guard.finalizing = True
        previous(run, phase, planned)
        if phase == "final-audit":
            common.save(folder_for(run) / "final-storage-checks" / f"{time.time_ns()}.json",
                        {"at": common.now(), **guard.measurement(planned)})

    with runtime.installed_guard(guard):
        original.boundary = boundary
        try:
            yield
        finally:
            original.boundary = previous


def prepare(run, external):
    runtime.verify(run, external)
    common.require(not (run / "complete.json").exists(), "cannot amend completed experiment")
    folder = folder_for(run)
    if (folder / "manifest.json").exists():
        return verify(run, external)
    common.require(StorageGuard(run)(32 * 1024**2), "insufficient preparation headroom")
    evidence = runtime.preserved_files(run)
    prior_folder = runtime.folder_for(run)
    prior_files = common.files_in(prior_folder)
    exports = {k: v for k, v in common.files_in(external).items() if k.startswith("models/")}
    recovery = common.recovery_receipts(run)[-1]
    common.require(common.sha(external / recovery["file"]) == recovery["SHA256"], "recovery changed")
    for name in SOURCES:
        target = folder / "source-snapshots" / name
        if target.exists():
            common.require(common.sha(target) == common.sha(common.HERE / name), "partial snapshot changed")
        else:
            common.publish_bytes(target, (common.HERE / name).read_bytes())
    common.save(folder / "manifest.json", {
        "schemaVersion": 1, "attempt": ATTEMPT, "at": common.now(),
        "authorization": "user explicitly approved temporary 4.5 GiB; final target 4 GiB and free reserve 10 GiB unchanged",
        "sourceBindings": source_bindings(), "preservedEvidence": evidence,
        "priorContinuationFiles": prior_files, "preservedModelExports": exports,
        "startingRecovery": recovery, "temporaryCapBytes": TEMPORARY_CAP,
        "finalCapBytes": FINAL_CAP, "freeReserveBytes": FREE_RESERVE,
        "modelDataEvaluationSettingsChanged": False, "testAccess": False,
        "retention": "unchanged latest-two Stage2 recoveries; permanent evidence retained"})
    return {"prepared": True, "continuation": ATTEMPT}


def verify(run, external):
    result = runtime.verify(run, external)
    folder = folder_for(run)
    record = common.read(folder / "manifest.json")
    common.require(record["sourceBindings"] == source_bindings(), "headroom source freeze changed")
    common.require((record["temporaryCapBytes"], record["finalCapBytes"], record["freeReserveBytes"])
                   == (TEMPORARY_CAP, FINAL_CAP, FREE_RESERVE), "headroom limits changed")
    common.require(record["modelDataEvaluationSettingsChanged"] is False and record["testAccess"] is False,
                   "headroom scope changed")
    common.verify_files(folder / "source-snapshots", {n: common.sha(common.HERE / n) for n in SOURCES})
    common.verify_files(run, record["preservedEvidence"])
    common.verify_files(runtime.folder_for(run), record["priorContinuationFiles"])
    common.verify_files(external, record["preservedModelExports"])
    if result["complete"]:
        checks = list((folder / "final-storage-checks").glob("*.json"))
        common.require(bool(checks), "missing final storage check")
        for path in checks:
            check = common.read(path)
            common.require(check["finalizing"] and check["storageCapBytes"] == FINAL_CAP
                           and check["withinCap"] and check["withinReserve"], "final storage gate failed")
        used = runtime.logical_bytes(common.SCREENING) + runtime.logical_bytes(common.WORKSPACE / "screening")
        common.require(used <= FINAL_CAP, "retained screening assets exceed final cap")
    return result | {"headroomVerified": True, "headroomManifestSHA256": common.sha(folder / "manifest.json")}


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
    stdout, stderr, log = sys.stdout, sys.stderr, None
    try:
        if args.action == "prepare":
            print(json.dumps(prepare(run, external)))
            return
        check = verify(run, external)
        if args.action == "verify" or check["complete"]:
            print(json.dumps(check))
            return
        common.require(args.resume, "headroom continuation requires --resume")
        common.require(args.pause_after_steps is None or args.pause_after_steps > 0, "invalid pause steps")
        (run / "logs").mkdir(exist_ok=True)
        log = (run / "logs" / f"headroom-{time.time_ns()}.log").open("x")
        sys.stdout, sys.stderr = runtime.Tee(stdout, log), runtime.Tee(stderr, log)
        print(json.dumps({"phase": "headroom-continuation", **check}), flush=True)
        with installed_policy(StorageGuard(run)):
            original.execute(run, external, resume=True, pause_after_steps=args.pause_after_steps)
        print(json.dumps(verify(run, external)), flush=True)
    except common.Paused as error:
        print(json.dumps({"status": "paused", "phase": str(error), "safeToCloseLaptop": True}), flush=True)
    except Exception as error:
        common.save(run / "failures" / f"{time.time_ns()}.json",
                    {"at": common.now(), "type": type(error).__name__, "error": str(error), "headroomContinuation": ATTEMPT})
        raise
    finally:
        handle.close()
        sys.stdout, sys.stderr = stdout, stderr
        if log:
            log.close()


if __name__ == "__main__":
    main()
