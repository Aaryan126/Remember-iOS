"""Explicit 21 GiB resource-policy adapter for the approved Stage A continuation.

Leave the checkpoint-bound controller and native tooling unchanged. The resource
callback is replaced only inside this adapter's context, then always restored.
All other worker locking, pause, integrity and generation limits remain intact.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import sys

import as_control as c

CAP = 21 * c.GIB
HOLD_SHA = "3c1452b7b747726105eac986e5253a47f2e1cdb4d95c0f4bf1e6b579e7475de7"
DOCUMENT = c.WORK / "RESOURCE-AMENDMENT-21.md"
RECORD = c.WORK / "resource-amendment-21-v2.json"
ORIGINAL_RECORD = c.WORK / "resource-amendment-21.json"
SNAPSHOT = c.WORK / "resource-amendment-original-snapshot.json"


def accounting(free, initial, scoped, external):
    c.require(all(type(v) is int and v >= 0 for v in (free,initial,scoped,external)),"invalid resource accounting")
    growth=max(scoped+external,max(0,initial-free))
    c.require(free>=c.RESERVE,"free reserve below 10 GiB; no automatic cleanup")
    c.require(growth<=CAP,"21 GiB growth cap exceeded; preserve baseline and stop")
    return dict(freeBytes=free,scopedBytes=scoped,externalGrowthBytes=external,
                conservativeGrowthBytes=growth,capBytes=CAP,reserveBytes=c.RESERVE)


def resources():
    baseline=c.load(c.PF/"resources.json")
    old=c.ranking.history.previous
    return accounting(shutil.disk_usage(c.PF).free,baseline["initialFreeBytes"],
                      old.allocated(c.PF)+old.allocated(old.CODE),
                      sum(max(0,old.allocated(Path(p))-start) for p,start in baseline["externalBaselines"].items()))


def verify_hold_artifact(path,expected,status_source):
    if path==c.RUN/"native-output/status.json":
        # This is a live diagnostic counter, not an immutable result. Preserve
        # its exact hold-time bytes; actual completion is verified from receipts.
        c.require(hashlib.sha256(status_source.encode()).hexdigest()==expected,"historical status snapshot changed")
    else:
        c.require(c.digest(path)==expected,"checkpoint artifact changed: "+str(path))


def verify_checkpoint():
    path=c.WORK/"resource-hold-checkpoint.json"
    c.require(c.digest(path)==HOLD_SHA,"stopped checkpoint changed")
    snapshot=c.load(SNAPSHOT)
    original=c.load(ORIGINAL_RECORD)
    c.require(snapshot["originalAmendmentSHA256"]==c.digest(ORIGINAL_RECORD)
              and hashlib.sha256(snapshot["adapterSource"].encode()).hexdigest()==original["adapterSHA256"],
              "original resource adapter snapshot changed")
    for name,expected in c.load(path)["hashes"].items():
        verify_hold_artifact(c.ROOT/name,expected,snapshot["nativeStatusSource"])
    c.register()  # Verifies original approval and previous experiment, not its disk cap.


def identity():
    return dict(stage="A only",stageBAllowed=False,capBytes=CAP,reserveBytes=c.RESERVE,
                baselineReset=False,holdSHA256=HOLD_SHA,
                originalApprovalSHA256=c.digest(c.WORK/"approval.json"),
                baselineSHA256=c.digest(c.PF/"resources.json"),
                documentSHA256=c.digest(DOCUMENT),adapterSHA256=c.digest(Path(__file__)),
                originalAmendmentSHA256=c.digest(ORIGINAL_RECORD),snapshotSHA256=c.digest(SNAPSHOT),
                lifecycleNoteSHA256=c.digest(c.WORK/"RESOURCE-RESUME-NOTE.md"))


def register():
    with (c.WORK/"worker.lock").open("a+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        c.require(c.load(c.WORK/"worker.json")["running"] is False,"worker still running")
        verify_checkpoint()
        resources()
        c.publish(RECORD,identity())
    return c.load(RECORD)


def verify_amendment():
    c.require(c.load(RECORD)==identity(),"resource amendment changed")
    verify_checkpoint()
    frozen=c.WORK/"resource-policy-frozen.json"
    if frozen.exists():
        value=c.load(frozen)
        c.require(value==dict(stageAFrozenSHA256=c.digest(c.WORK/"frozen.json"),
                            amendmentSHA256=c.digest(RECORD)),"frozen resource policy changed")


@contextmanager
def activate():
    verify_amendment()
    original=c.resources
    c.resources=resources
    try: yield
    finally: c.resources=original


def main():
    args=sys.argv[1:]
    c.require(bool(args),"use register, resources, runner <command>, or qa <command>")
    if args==["register"]:
        print(json.dumps(register()));return
    if args==["resources"]:
        verify_amendment();print(json.dumps(resources()));return
    c.require(args[0] in {"runner","qa"} and len(args)>=2,"unsupported Stage A entry point")
    if args[0]=="qa": c.require(args[1:] in (["tests"],["audit"]),"unsupported QA action")
    with activate():
        module="as_runner" if args[0]=="runner" else "as_qa"
        sys.argv=[module]+args[1:]
        runpy.run_module(module,run_name="__main__")
        if args[0:2]==["runner","freeze"] and (c.WORK/"frozen.json").exists():
            c.publish(c.WORK/"resource-policy-frozen.json",
                      dict(stageAFrozenSHA256=c.digest(c.WORK/"frozen.json"),amendmentSHA256=c.digest(RECORD)))


if __name__=="__main__":main()
