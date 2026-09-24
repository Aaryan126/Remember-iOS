"""Durable, isolated checkpoint-2 control; no writes to frozen or legacy runs."""
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import os
from pathlib import Path
import signal
import sys
import time

CODE = Path(__file__).resolve().parent
ROOT = CODE.parents[2]
PF = ROOT / "Evaluation/ProvenanceFirst"
WORK = PF / "checkpoint2"
EXTERNAL = Path("/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1")
P2 = ROOT / "Evaluation/MatcherValidation/runs/validation-02"
sys.path.insert(0, str(CODE.parent))
import fixtures

spec = importlib.util.spec_from_file_location("pf_checkpoint1", CODE.parent / "checkpoint.py")
pf1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf1)
read, require, encoded = fixtures.load, fixtures.require, fixtures.encoded
_paused = False


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def publish(path, value):
    path = Path(path)
    require(path.resolve().is_relative_to(WORK.resolve()), "output escapes checkpoint 2")
    if path.exists():
        require(path.read_bytes() == encoded(value), f"immutable artifact changed: {path}")
    else:
        pf1.atomic(path, value)


def unit(path, value, binding):
    publish(path, {"bindingSHA256": binding, "payload": value,
                   "payloadSHA256": text_hash(encoded(value).decode())})


def read_unit(path, binding):
    data = read(path)
    require(set(data) == {"bindingSHA256", "payload", "payloadSHA256"}, "invalid receipt schema")
    require(data["bindingSHA256"] == binding, "receipt binding mismatch")
    require(data["payloadSHA256"] == text_hash(encoded(data["payload"]).decode()), "receipt tampered")
    return data["payload"]


class Paused(Exception):
    pass


def boundary():
    if _paused or (WORK / "pause.request.json").exists():
        raise Paused("saved unit boundary")
    return pf1.resource_check()


def verify_saved_preflight():
    manifest = WORK / "runs/preflight/binding.json"
    if not manifest.exists():
        return
    for name, expected in read(manifest)["hashes"].items():
        require(digest(Path(name)) == expected, f"preflight binding changed: {name}")
    binding = digest(manifest)
    for folder in ("embeddings", "neural"):
        for path in (manifest.parent / folder).glob("*.json"):
            require(path.resolve().is_relative_to(WORK.resolve()), "receipt path escape")
            read_unit(path, binding)


@contextmanager
def worker(resume=False):
    global _paused
    WORK.mkdir(parents=True, exist_ok=True)
    with (WORK / "worker.lock").open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_saved_preflight()
        marker = WORK / "pause.request.json"
        if resume and marker.exists():
            (WORK / "runs").mkdir(parents=True, exist_ok=True)
            os.replace(marker, WORK / f"runs/pause-{time.time_ns()}.json")
        _paused = False
        def pause_signal(signum, frame):
            global _paused
            _paused = True
        previous = {sig: signal.signal(sig, pause_signal) for sig in (signal.SIGINT, signal.SIGTERM)}
        pf1.atomic(WORK / "worker.json", {"pid": os.getpid(), "running": True})
        try:
            yield
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
            pf1.atomic(WORK / "worker.json", {"pid": os.getpid(), "running": False})
            fcntl.flock(stream, fcntl.LOCK_UN)


def log(**fields):
    import json
    print(json.dumps(fields, sort_keys=True), flush=True)
