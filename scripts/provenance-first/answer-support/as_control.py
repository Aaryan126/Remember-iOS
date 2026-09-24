"""Scoped Stage A control; preserves earlier controllers and original accounting."""
from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import signal
import sys
import time

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE.parent / "history-ranking"))
import rk_runner as prior
import rk_control as ranking

ROOT, PF = ranking.ROOT, ranking.PF
WORK, RUN = PF / "answer-support", PF / "runs/answer-support"
load, require, digest, encoded = ranking.load, ranking.require, ranking.digest, ranking.encoded
atomic = ranking.atomic
GIB, CAP, RESERVE = 1024**3, 19*1024**3, 10*1024**3
_paused = False


def checked(path):
    path = Path(path).absolute()
    require(path.resolve() == path and any(path != p and path.is_relative_to(p) for p in (WORK, RUN)),
            "answer-support output escaped isolated scope or contains symlink")
    return path


def publish(path, value):
    path = checked(path)
    if path.exists(): require(path.read_bytes() == encoded(value), f"immutable artifact changed: {path}")
    else: atomic(path, value)


def accounting(free, initial, scoped, external):
    require(all(type(v) is int and v >= 0 for v in (free, initial, scoped, external)), "invalid accounting")
    growth = max(scoped+external, max(0, initial-free))
    require(free >= RESERVE, "free reserve below 10 GiB; no automatic cleanup")
    require(growth <= CAP, "19 GiB growth cap exceeded; preserve baseline and stop")
    return dict(freeBytes=free, scopedBytes=scoped, externalGrowthBytes=external,
                conservativeGrowthBytes=growth, capBytes=CAP, reserveBytes=RESERVE)


def resources():
    baseline = load(PF / "resources.json")
    old = ranking.history.previous
    return accounting(shutil.disk_usage(PF).free, baseline["initialFreeBytes"],
                      old.allocated(PF)+old.allocated(old.CODE),
                      sum(max(0,old.allocated(Path(p))-start) for p,start in baseline["externalBaselines"].items()))


def verify_prior():
    prior.verify()
    done = load(ranking.WORK / "checkpoint2-complete.json")
    for name, expected in done["hashes"].items():
        require(digest(ranking.WORK / name) == expected, "prior completed checkpoint changed")


def register():
    verify_prior()
    path = WORK / "approval.json"
    if path.exists():
        value=load(path)
        require(value["approvalSHA256"] == digest(WORK/"APPROVAL.md")
                and value["baselineSHA256"] == digest(PF/"resources.json")
                and value["capBytes"] == CAP and value["reserveBytes"]==RESERVE
                and value["baselineReset"] is False and value["stageBAllowed"] is False
                and value["priorCompletionSHA256"]==digest(ranking.WORK/"checkpoint2-complete.json"), "approval changed")
        return value
    result=dict(approvalReply="yes",stage="A only",stageBAllowed=False,capBytes=CAP,reserveBytes=RESERVE,
                baselineReset=False,baselineSHA256=digest(PF/"resources.json"),
                approvalSHA256=digest(WORK/"APPROVAL.md"),resources=resources(),
                priorCompletionSHA256=digest(ranking.WORK/"checkpoint2-complete.json"))
    publish(path,result)
    return result


class Paused(Exception): pass


def boundary():
    if _paused or (WORK/"pause.request.json").exists(): raise Paused("saved unit boundary")
    return resources()


@contextmanager
def worker(resume=False):
    global _paused
    WORK.mkdir(parents=True,exist_ok=True)
    with checked(WORK/"worker.lock").open("a+") as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        register()
        marker=WORK/"pause.request.json"
        if resume and marker.exists(): marker.rename(WORK/f"pause-resumed-{time.time_ns()}.json")
        _paused=False
        def requested(signum,frame):
            global _paused
            _paused=True
        previous={sig:signal.signal(sig,requested) for sig in (signal.SIGINT,signal.SIGTERM)}
        atomic(checked(WORK/"worker.json"),dict(pid=os.getpid(),running=True))
        try:
            boundary()
            yield
        finally:
            atomic(checked(WORK/"worker.json"),dict(pid=os.getpid(),running=False))
            for sig,handler in previous.items(): signal.signal(sig,handler)


def unit(path,payload,binding):
    publish(path,dict(bindingSHA256=binding,payloadSHA256=hashlib.sha256(encoded(payload)).hexdigest(),payload=payload))


def read_unit(path,binding):
    value=load(path)
    require(set(value)=={"bindingSHA256","payloadSHA256","payload"} and value["bindingSHA256"]==binding
            and value["payloadSHA256"]==hashlib.sha256(encoded(value["payload"])).hexdigest(),"unit integrity mismatch")
    return value["payload"]
