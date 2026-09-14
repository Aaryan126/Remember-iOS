"""Isolated, stage-gated matcher screening with immutable receipts."""
from __future__ import annotations

import fcntl
import os
from pathlib import Path
import re
import shutil
import signal
import time

from experiment import ROOT, DATA, read, save, sha, require, validate_inputs, validate_labels, pair_rows
from stage3_common import WORKSPACE, now, files_in, verify_files

HERE = Path(__file__).resolve().parent
SCREENING = ROOT / "Evaluation/MatcherScreening"
RELEASE = DATA / "releases/v1"
BASELINE = DATA / "runs/stage-2-attempt-01"
NEURAL = DATA / "runs/stage-5-attempt-01"
SOURCES = ["screening.py", "screening_common.py", "screening_config.py", "screening_ablation.py",
           "screening_review.py", "screening_sanity.py", "screening_diagnostics.py",
           "audit_screening.py", "test_screening.py"]
pause_signal = False
GIB = 1024**3


class Paused(Exception):
    pass


def locations(value):
    run = Path(value).resolve()
    require(run.parent == (SCREENING / "runs").resolve()
            and re.fullmatch(r"audit-attempt-\d+", run.name), "unscoped screening audit run")
    external = WORKSPACE / "screening" / run.name
    require(not external.is_symlink(), "external run cannot be a symlink")
    return run, external


def stage_guard(stage):
    require(stage == "audit", "Screening Stage 2 is not authorized or implemented by Stage 1; stop for user review")


def load_split(split):
    require(split in ("train", "development"), "screening cannot open the heldout test split")
    inputs = read(RELEASE / f"inputs-{split}.json")
    labels = read(RELEASE / f"labels-{split}.json")
    validate_inputs(inputs, complete=False)
    validate_labels(inputs, labels)
    require(all(lib["split"] == split for lib in inputs["libraries"]), "mixed split")
    return inputs, labels


def gold(split):
    inputs, labels = load_split(split)
    lookup = {lib["id"]: lib for lib in labels["libraries"]}
    return [dict(row, id=row["first"] + "--" + row["second"], library=lib["id"])
            for lib in inputs["libraries"] for row in pair_rows(lib, lookup[lib["id"]])]


def setup():
    def request(*_):
        global pause_signal
        pause_signal = True
    signal.signal(signal.SIGINT, request)
    signal.signal(signal.SIGTERM, request)
    for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        os.environ[name] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"


def wants_pause(run):
    return pause_signal or (run / "control/pause-requested.json").exists()


def request_pause(run, reason="user"):
    require((run / "manifest.json").exists(), "run not initialized")
    if (run / "complete.json").exists():
        return "already_complete_and_stopped"
    path = run / "control/pause-requested.json"
    if not path.exists():
        save(path, {"at": now(), "reason": reason})
    return "pause_requested_wait_for_confirmation"


def logical_bytes(folder):
    return sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()) if folder.exists() else 0


def space_ok(free, used, planned):
    return free - planned >= 10 * GIB and used + planned <= 4 * GIB


def capacity(run, external, planned=2*1024**2):
    # Include other screening attempts; the allowance is not reset per retry.
    used = logical_bytes(SCREENING) + logical_bytes(WORKSPACE / "screening")
    return space_ok(shutil.disk_usage(WORKSPACE).free, used, planned)


def boundary(run, external, phase, planned=2*1024**2):
    if not wants_pause(run) and not capacity(run, external, planned):
        request_pause(run, "storage_budget")
    if wants_pause(run):
        save(run / "pauses" / f"{time.time_ns()}.json",
             {"at": now(), "phase": phase, "safeToCloseLaptop": True})
        raise Paused(phase)


def lock(run):
    run.mkdir(parents=True, exist_ok=True)
    handle = (run / "worker.lock").open("a")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        handle.close()
        raise
    return handle


def bindings():
    names = SOURCES + ["experiment.py", "stage2.py", "stage2_metrics.py", "stage3_common.py",
                       "stage5_common.py", "stage5_train.py", "stage5_data.py", "audit_stage5.py"]
    paths = [HERE / name for name in names]
    paths += [RELEASE / f"{kind}-{split}.json" for split in ("train", "development") for kind in ("inputs", "labels")]
    paths += [BASELINE / "complete.json", NEURAL / "complete.json", DATA / "environment.lock.txt",
              DATA / "model-manifest.json", SCREENING / "PLAN.md"]
    return {str(path.relative_to(ROOT)): sha(path) for path in paths}


def initialize(run, external):
    from screening_config import folds, trials
    current = bindings()
    path = run / "manifest.json"
    if path.exists():
        require(read(path)["bindings"] == current, "frozen screening source/input changed; preserve and create a new attempt")
        require(read(run / "folds.json") == folds(), "fold plan changed")
        require(read(run / "stage2-trials.json") == trials(), "proposed trials changed")
        require(all(sha(run/"source-snapshots"/name)==sha(HERE/name) for name in SOURCES), "source snapshot changed")
        return read(path)
    require(capacity(run, external, 64*1024**2), "insufficient screening storage allowance")
    external.mkdir(parents=True, exist_ok=True)
    result = {"schemaVersion": 1, "stage": "audit", "createdAt": now(), "bindings": current,
              "authorization": "user: Implement the two-stage plan; Stage 1 only until checkpoint review",
              "stage2Authorized": False, "testAccess": False, "phone": False,
              "stopAfterStage": True, "additionalStorageCapBytes": 4*GIB, "freeReserveBytes": 10*GIB,
              "newRecoveryRetention": "user selected two latest active-trial states; final models and all receipts retained; old feasibility untouched"}
    for target,value in ((run/"folds.json",folds()),(run/"stage2-trials.json",trials())):
        if target.exists(): require(read(target)==value,"partial initialization configuration changed")
        else: save(target,value)
    for name in SOURCES:
        from environment import publish_bytes
        target = run/"source-snapshots"/name
        if target.exists(): require(sha(target)==sha(HERE/name),"partial source snapshot changed")
        else: publish_bytes(target, (HERE / name).read_bytes())
    save(path, result)
    return result


def validate_fold(fold):
    groups = [set(fold[name]) for name in ("fit", "calibration", "evaluation")]
    require(list(map(len, groups)) == [9, 3, 6], "invalid fold sizes")
    require(all(not a & b for i, a in enumerate(groups) for b in groups[i+1:]), "library leakage")
    require(set.union(*groups) == {f"mf{i:02}" for i in range(1,19)}, "wrong fold coverage")


def roll_recovery(run, external, receipts):
    """Only superseded recovery blobs in this new run; never candidate weights."""
    receipts = sorted(receipts, key=lambda row: row["stamp"])
    if len(receipts) < 3:
        return
    for row in receipts[-2:]:
        require(sha(external / row["file"]) == row["SHA256"], "latest recovery corrupted; refuse rotation")
    for row in receipts[:-2]:
        original = external / row["file"]
        require(not any(p.is_symlink() for p in (external, external/"recovery", external/"recovery/sanity", original)), "symlink recovery target")
        file = original.resolve()
        root = (external / "recovery/sanity").resolve()
        require(file.parent == root and file.name.endswith(".pt.gz"), "unsafe recovery rotation target")
        event = run / "retention" / f"{row['stamp']}.json"
        if not file.exists():
            require(event.exists(), "unrecorded missing recovery")
            continue
        require(sha(file) == row["SHA256"], "superseded recovery changed")
        if not event.exists():
            save(event, {"at": now(), "file": row["file"], "SHA256": row["SHA256"],
                         "authorization": "selected rolling retention for new experiment", "bytes": row["bytes"]})
        file.unlink()
