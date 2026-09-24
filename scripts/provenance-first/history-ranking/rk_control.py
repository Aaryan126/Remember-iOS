"""Independent checkpoint-2 control; checkpoint-1 artifacts remain immutable."""
from contextlib import contextmanager
import fcntl
import importlib.util
import os
from pathlib import Path
import signal
import sys
import time

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE.parent / "history"))
import control as history
import benchmark

ROOT, PF = history.ROOT, history.PF
WORK = history.WORK / "checkpoint2"
RUN = PF / "runs/history-ranking"
load, require, digest, encoded = history.load, history.require, history.digest, history.encoded
atomic = history.previous.atomic
_paused = False


class ResourceBlocked(RuntimeError): pass


def resources():
    try: return history.resources()
    except ValueError as error: raise ResourceBlocked(str(error)) from error


def checked(path):
    path = Path(path).absolute()
    require(path.resolve() == path and any(path.is_relative_to(root) and path != root for root in (WORK, RUN)),
            "ranking output escapes isolated workspace or contains symlink")
    return path


def publish(path, value):
    path = checked(path)
    if path.exists(): require(path.read_bytes() == encoded(value), f"immutable ranking artifact changed: {path}")
    else: atomic(path, value)


def verify_prior():
    benchmark.verify()
    record = load(history.WORK / "checkpoint1-complete.json")
    require(record["checkpoint1Complete"] and not record["rankingMeasured"], "coverage prerequisite incomplete")
    for name, expected in record["hashes"].items():
        require(digest(history.WORK / name) == expected, f"checkpoint-1 artifact changed: {name}")


class Paused(Exception): pass


def boundary():
    if _paused or (WORK / "pause.request.json").exists(): raise Paused("ranking saved-unit boundary")
    return resources()


@contextmanager
def worker(resume=False):
    global _paused
    WORK.mkdir(parents=True, exist_ok=True)
    with checked(WORK / "worker.lock").open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_prior()
        marker = WORK / "pause.request.json"
        if resume and marker.exists(): marker.rename(WORK / f"pause-resumed-{time.time_ns()}.json")
        _paused = False
        def requested(signum, frame):
            global _paused
            _paused = True
        old = {sig: signal.signal(sig, requested) for sig in (signal.SIGINT, signal.SIGTERM)}
        atomic(checked(WORK / "worker.json"), dict(pid=os.getpid(), running=True))
        try:
            boundary()
            yield
        finally:
            atomic(checked(WORK / "worker.json"), dict(pid=os.getpid(), running=False))
            for sig, handler in old.items(): signal.signal(sig, handler)


def unit(path, value, binding):
    import hashlib
    publish(path, dict(bindingSHA256=binding, payload=value,
                       payloadSHA256=hashlib.sha256(encoded(value)).hexdigest()))


def read_unit(path, binding):
    import hashlib
    value = load(path)
    require(set(value) == {"bindingSHA256", "payload", "payloadSHA256"}, "invalid unit envelope")
    require(value["bindingSHA256"] == binding
            and value["payloadSHA256"] == hashlib.sha256(encoded(value["payload"])).hexdigest(), "cache identity mismatch")
    return value["payload"]
