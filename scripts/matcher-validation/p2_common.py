"""Isolated P2 authority, storage accounting and immutable recovery evidence."""
from __future__ import annotations

import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time

from prepare import ROOT, DATA, read, publish, require
import p1_release

LEGACY = ROOT / "scripts/matcher-feasibility"
sys.path.insert(0, str(LEGACY))
from stage3_common import WORKSPACE
from stage5_common import save_state, load_state
from screening2_runtime import logical_bytes

RUN = DATA / "runs/validation-01"
EXTERNAL = WORKSPACE / "validation/validation-01"
RELEASE = DATA / "releases/v1"
GIB = 1024 ** 3
MIB = 1024 ** 2
requested = False


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


class Paused(Exception):
    pass


def setup():
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    def handler(*_):
        global requested
        requested = True
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def log(phase, **values):
    print(json.dumps({"phase": phase, **values}, allow_nan=False), flush=True)


def capacity(planned=2 * MIB):
    require(isinstance(planned, int) and planned >= 0, "invalid planned bytes")
    used = logical_bytes(DATA) + logical_bytes(Path(__file__).parent) + logical_bytes(EXTERNAL.parent)
    free = shutil.disk_usage(WORKSPACE).free
    return {"usedBytes": used, "freeBytes": free, "plannedBytes": planned,
            "withinCap": used + planned <= 4 * GIB, "withinReserve": free - planned >= 10 * GIB}


def check_space(planned=2 * MIB):
    snapshot = capacity(planned)
    require(snapshot["withinCap"] and snapshot["withinReserve"], "storage limit: " + json.dumps(snapshot))
    return snapshot


def wants_pause():
    return requested or (RUN / "control/pause.json").exists()


def boundary(phase, planned=2 * MIB):
    if wants_pause():
        publish(RUN / "pauses" / f"{time.time_ns()}.json", {"phase": phase, "atNS": time.time_ns()})
        raise Paused(phase)
    check_space(planned)


def pause():
    require((RUN / "manifest.json").exists(), "P2 not prepared")
    if not (RUN / "control/pause.json").exists():
        publish(RUN / "control/pause.json", {"atNS": time.time_ns(), "reason": "user"})


def resume_control():
    marker = RUN / "control/pause.json"
    if marker.exists():
        target = RUN / "control" / f"resumed-{time.time_ns()}.json"
        os.rename(marker, target)


def lock():
    for folder in (RUN, EXTERNAL):
        require(not folder.is_symlink() and not folder.parent.is_symlink(), "run symlink rejected")
        folder.mkdir(parents=True, exist_ok=True)
    handle = (RUN / "worker.lock").open("a")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BaseException:
        handle.close()
        raise
    return handle


def source_bindings():
    own = [Path(__file__).parent / name for name in
           ("p2_common.py", "p2_data.py", "p2_train.py", "p2_models.py", "p2.py", "test_p2.py", "P2EmbeddingProbe.swift")]
    # Bind reused helpers transitively without editing any previous experiment.
    old = sorted(LEGACY.glob("*.py"))
    return {str(p.relative_to(ROOT)): digest(p) for p in own + old +
            [ROOT / "Remember/Remember/ProjectIntelligence.swift", DATA / "P2_PROTOCOL.md"]}


def environment():
    return {d.metadata["Name"].lower(): d.version for d in importlib.metadata.distributions()}


def verify():
    p1_release.verify()
    manifest = read(RUN / "manifest.json")
    require(manifest["sources"] == source_bindings(), "P2 frozen implementation changed")
    require(manifest["environment"] == environment(), "P2 environment changed")
    require(manifest["p1SHA256"] == digest(DATA / "runs/p1-01/complete.json"), "P1 changed")
    for relative, expected in manifest["assets"].items():
        require(digest(WORKSPACE / relative) == expected, "local model asset changed")
    return manifest


def split_data(split):
    require(split in ("train", "calibration", "evaluation"), "unknown split")
    if split == "evaluation":
        verify_selection()
    document = read(RELEASE / f"inputs-{split}.json")
    gold = read(RELEASE / f"gold-{split}.json")["pairs"]
    ids = read(RELEASE / "splits.json")["libraries"][split]
    require(sorted(l["id"] for l in document["libraries"]) == ids, "input split mismatch")
    require(len(gold) == len(ids) * 190 and all(r["split"] == split and r["library"] in ids for r in gold), "gold split mismatch")
    return document["libraries"], gold


def verify_selection():
    path = RUN / "selection.json"
    require(path.exists(), "evaluation forbidden before all model/threshold choices are frozen")
    selection = read(path)
    require(selection["manifestSHA256"] == digest(RUN / "manifest.json"), "selection manifest changed")
    require(set(selection["hybrids"]) == {"17", "29", "41"}, "all seeds must be frozen")
    expected = {"baseline.json", "tfidf.json", "hybrid-17.json", "hybrid-29.json", "hybrid-41.json", "representations.json"}
    require(set(selection["artifacts"]) == expected, "selection artifact inventory incomplete")
    expected_weights = {f"models/seed-{seed}-{fold}.pt.gz" for seed in (17,29,41) for fold in (0,1,2,"final")}
    require(set(selection["weights"]) == expected_weights, "selection weight inventory incomplete")
    for relative, expected in selection["artifacts"].items():
        target = (RUN / relative).resolve()
        require(target.is_relative_to(RUN.resolve()) and digest(target) == expected, "selected artifact changed")
    for relative, expected in selection["weights"].items():
        target = (EXTERNAL / relative).resolve()
        require(target.is_relative_to(EXTERNAL.resolve()) and digest(target) == expected, "selected weights changed")
    representations = read(RUN / "representations.json")
    for relative, expected in representations["run"].items():
        target = (RUN / relative).resolve()
        require(target.is_relative_to(RUN.resolve()) and digest(target) == expected, "training/calibration representation changed")
    for relative, expected in representations["external"].items():
        target = (EXTERNAL / relative).resolve()
        require(target.is_relative_to(EXTERNAL.resolve()) and digest(target) == expected, "token representation changed")
    baseline = read(RUN / "baseline.json")["selection"]
    require(selection["baseline"] == (baseline["threshold"] if baseline else None), "baseline threshold differs from calibration choice")
    for seed in (17,29,41):
        selected = read(RUN / f"hybrid-{seed}.json")["selection"]
        require(selection["hybrids"][str(seed)] == (selected["threshold"] if selected else None), "hybrid threshold differs from calibration choice")
    return selection


def recoveries():
    return [read(p) for p in sorted((RUN / "recovery").glob("*.json"))]


def latest_recovery(task):
    matches = [r for r in recoveries() if r["task"] == task and (EXTERNAL / r["file"]).exists()]
    return matches[-1] if matches else None


def rotate_recovery():
    receipts = recoveries()
    if len(receipts) <= 2:
        return
    kept = receipts[-2:]
    for r in kept:
        require(digest(EXTERNAL / r["file"]) == r["SHA256"], "cannot rotate before verifying two newest states")
    for old in receipts[:-2]:
        path = EXTERNAL / old["file"]
        event = RUN / "retention" / f"{old['stamp']}.json"
        require(path.parent == EXTERNAL / "recovery" and not path.is_symlink(), "unsafe recovery target")
        if not path.exists():
            require(event.exists(), "missing recovery without retention receipt")
            continue
        require(digest(path) == old["SHA256"], "superseded recovery changed")
        if event.exists():
            require(read(event)["removed"] == old, "retention receipt differs")
        else:
            publish(event, {"removed": old, "kept": kept, "authority": "approved P2 latest-two recovery plan"})
        path.unlink()
        log("recovery-retention", removed=old["file"], retainedStates=2)


def save_recovery(task, payload):
    previous = latest_recovery(task)
    if previous and previous["position"] == payload["position"]:
        require(digest(EXTERNAL / previous["file"]) == previous["SHA256"], "latest recovery changed")
        return previous
    # Three full FP32 parameter-sized arrays conservatively cover AdamW state.
    estimate = sum(v.numel() * v.element_size() for v in payload["model"].values()) * 3 + 16 * MIB
    check_space(estimate)
    stamp = time.time_ns()
    path = EXTERNAL / "recovery" / f"{stamp}.pt.gz"
    save_state(path, payload)
    record = {"stamp": stamp, "task": task, "file": str(path.relative_to(EXTERNAL)),
              "SHA256": digest(path), "bytes": path.stat().st_size, "position": payload["position"]}
    # A successful reload, not merely a hash of unreadable bytes, precedes retention.
    restored = load_state(path, record["SHA256"])
    require(restored["position"] == payload["position"] and restored["fingerprint"] == payload["fingerprint"], "recovery reload mismatch")
    del restored
    publish(RUN / "recovery" / f"{stamp}.json", record)
    rotate_recovery()
    log("checkpoint", task=task, **payload["position"], bytes=record["bytes"])
    return record
