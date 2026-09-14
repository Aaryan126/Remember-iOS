"""C2 isolated artifact/worker control. No Git operations or legacy-run mutations."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import platform
import sys
import time

import checkpoint

ROOT = checkpoint.ROOT
DATA = checkpoint.DATA
RUN = DATA / "runs/c2-01"
CURATED = DATA / "c2"
P2 = ROOT / "Evaluation/MatcherValidation/runs/validation-02"
WORKSPACE = Path("/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1")
EXTERNAL = WORKSPACE / "validation/validation-02"
LEGACY = ROOT / "scripts/matcher-feasibility"
require, read, publish = checkpoint.require, checkpoint.read, checkpoint.publish
_pause_signal = False


class Paused(Exception):
    pass


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def pair_key(a, b):
    return "--".join(sorted((text_sha(a), text_sha(b))))


def log(phase, **fields):
    print(json.dumps({"phase": phase, **fields}, sort_keys=True), flush=True)


def space(planned=0):
    stats = os.statvfs(ROOT)
    free = stats.f_bavail * stats.f_frsize
    allocated = sum(p.stat().st_blocks * 512 for root in (DATA, ROOT / "scripts/organization-diagnostics")
                    for p in root.rglob("*") if p.is_file())
    require(free - planned >= 10 * 1024**3, "10 GiB reserve would be violated; pause and request space")
    # Reserve space for the isolated simulator's incremental files outside RUN.
    # The ledger coordinator measures that delta separately and must keep it <=1 GiB.
    simulator_reserve = 1024**3
    require(allocated + planned + simulator_reserve <= 4 * 1024**3, "4 GiB diagnostic cap would be violated")
    return {"freeBytes": free, "allocatedBytes": allocated, "plannedBytes": planned,
            "simulatorReservedBytes": simulator_reserve}


def request_pause():
    path = RUN / "control/pause-requested.json"
    if not path.exists():
        publish(path, {"requestedAt": datetime.now(timezone.utc).isoformat()})
    # The independent ledger harness uses its own boundary signal when running.
    ledger = RUN / "ledger/results"
    if ledger.is_dir():
        marker = ledger / "pause.request"
        marker.touch(exist_ok=True)
    return {"pauseRequested": True, "safeToClose": False}


def boundary(phase, planned=0):
    space(planned)
    if _pause_signal or (RUN / "control/pause-requested.json").exists():
        publish(RUN / f"pauses/{time.time_ns()}.json", {"phase": phase, "state": "saved-boundary"})
        raise Paused(phase)


@contextmanager
def worker(resume=False):
    global _pause_signal
    RUN.mkdir(parents=True, exist_ok=True)
    with (RUN / "worker.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another C2 worker is active; do not launch a duplicate") from error
        marker = RUN / "control/pause-requested.json"
        if resume and marker.exists():
            publish(RUN / f"resumptions/{time.time_ns()}.json", {"pauseRequestSHA256": digest(marker)})
            marker.unlink()  # Only this runner's recorded request marker, never user data.
        ledger_marker = RUN / "ledger/results/pause.request"
        if resume and ledger_marker.exists():
            publish(RUN / f"resumptions/{time.time_ns()}-ledger.json", {"pauseRequestSHA256": digest(ledger_marker)})
            ledger_marker.unlink()
        _pause_signal = False
        previous = {}
        def stop(signum, frame):
            global _pause_signal
            _pause_signal = True
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous[sig] = signal.signal(sig, stop)
        try:
            yield
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
            fcntl.flock(lock, fcntl.LOCK_UN)


def verify_bindings():
    manifest = read(RUN / "manifest.json")
    for relative, expected in manifest["sources"].items():
        path = (ROOT / relative).resolve()
        require(path.is_relative_to(ROOT) and digest(path) == expected, "Frozen C2 source changed: " + relative)
    for relative, expected in manifest["external"].items():
        path = (WORKSPACE / relative).resolve()
        require(path.is_relative_to(WORKSPACE) and digest(path) == expected, "Frozen C2 asset changed: " + relative)
    require(manifest["runtime"] == runtime(), "Frozen Python/package/platform runtime changed")
    return manifest


def runtime():
    return {"python": sys.version, "platform": platform.platform(),
            "packages": {name: importlib.metadata.version(name) for name in
                         ("torch", "transformers", "numpy", "scikit-learn", "tokenizers")}}


def unit(path, payload):
    """Self-checksummed, immutable work unit; validated before a resume skips it."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    publish(path, {"payload": payload, "payloadSHA256": hashlib.sha256(encoded).hexdigest()})


def read_unit(path):
    saved = read(path)
    encoded = json.dumps(saved["payload"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    require(saved["payloadSHA256"] == hashlib.sha256(encoded).hexdigest(), "Work-unit checksum mismatch: " + str(path))
    return saved["payload"]
