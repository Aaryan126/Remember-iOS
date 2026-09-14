"""Isolated Stage 2 screening authority, immutable evidence and safe recovery."""
from __future__ import annotations

import fcntl
import importlib.metadata
import os
from pathlib import Path
import re
import shutil
import signal
import time

from experiment import ROOT, DATA, read, save, sha, require
from environment import publish_bytes, verify_assets
from stage3_common import WORKSPACE, now, files_in, verify_files
from screening_common import SCREENING, BASELINE, NEURAL, load_split, gold, logical_bytes, GIB

HERE = Path(__file__).resolve().parent
AUDIT = SCREENING/"runs/audit-attempt-01"
SOURCES = ["screening2.py","screening2_common.py","screening2_data.py","screening2_metrics.py",
           "screening2_models.py","screening2_neural.py","screening2_report.py","audit_screening2.py","test_screening2.py"]
requested = False


class Paused(Exception):
    pass


def setup():
    def handler(*_):
        global requested
        requested = True
    signal.signal(signal.SIGINT,handler);signal.signal(signal.SIGTERM,handler)
    os.environ.update(HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",TOKENIZERS_PARALLELISM="false")


def paths(value):
    path = Path(value)
    require(not path.is_symlink(),"run symlink rejected")
    run = path.resolve()
    require(run.parent==(SCREENING/"runs").resolve() and re.fullmatch(r"screen-attempt-\d+",run.name),"invalid screening Stage2 run")
    external = WORKSPACE/"screening"/run.name
    require(not external.is_symlink() and not external.parent.is_symlink(),"external symlink rejected")
    return run,external


def wants_pause(run):
    return requested or (run/"control/pause-requested.json").exists()


def request_pause(run,reason="user"):
    require((run/"manifest.json").exists(),"run not prepared")
    if (run/"complete.json").exists(): return "already_complete_and_stopped"
    path = run/"control/pause-requested.json"
    if not path.exists(): save(path,{"at":now(),"reason":reason})
    return "pause_requested_wait_for_worker_exit"


def capacity(planned=2*1024**2):
    used = logical_bytes(SCREENING)+logical_bytes(WORKSPACE/"screening")
    return used+planned<=4*GIB and shutil.disk_usage(WORKSPACE).free-planned>=10*GIB


def boundary(run,phase,planned=2*1024**2):
    if not wants_pause(run) and not capacity(planned): request_pause(run,"storage_budget")
    if wants_pause(run):
        save(run/"pauses"/f"{time.time_ns()}.json",{"at":now(),"phase":phase,"safeToCloseLaptop":True})
        raise Paused(phase)


def lock(run):
    run.mkdir(parents=True,exist_ok=True)
    handle=(run/"worker.lock").open("a")
    try: fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except Exception: handle.close();raise
    return handle


def bindings():
    files=[HERE/name for name in SOURCES]
    # Bind every reused Stage1 helper transitively, without modifying that freeze.
    files += [ROOT/name for name in read(AUDIT/"manifest.json")["bindings"]]
    files += [AUDIT/"complete.json",AUDIT/"stage2-trials.json",AUDIT/"folds.json",
              SCREENING/"STAGE2_PLAN.md",HERE/"environment.py",HERE/"stage5.py",HERE/"screening.py"]
    return {str(p.relative_to(ROOT)):sha(p) for p in files}


def verify_environment():
    distributions=sorted((d.metadata["Name"].lower(),d.version) for d in importlib.metadata.distributions())
    expected="# Resolved in isolated Python 3.11 macOS arm64 environment.\n"+"".join(f"{k}=={v}\n" for k,v in distributions)
    require((DATA/"environment.lock.txt").read_text()==expected,"pinned environment changed")
    verify_assets(WORKSPACE,read(DATA/"model-manifest.json"))


def initialize(run,external):
    current=bindings()
    if (run/"manifest.json").exists():
        manifest=read(run/"manifest.json")
        require(manifest["bindings"]==current,"frozen implementation/data changed; preserve and start a new attempt")
        require(read(run/"trials.json")==read(AUDIT/"stage2-trials.json"),"trial proposal changed")
        require(read(run/"folds.json")==read(AUDIT/"folds.json"),"folds changed")
        return manifest
    require(capacity(64*1024**2),"screening storage reserve insufficient")
    external.mkdir(parents=True,exist_ok=True)
    for target,value in ((run/"trials.json",read(AUDIT/"stage2-trials.json")),(run/"folds.json",read(AUDIT/"folds.json"))):
        if target.exists(): require(read(target)==value,"partial initialization changed")
        else: save(target,value)
    for name in SOURCES:
        target=run/"source-snapshots"/name
        if target.exists(): require(sha(target)==sha(HERE/name),"partial source snapshot changed")
        else: publish_bytes(target,(HERE/name).read_bytes())
    manifest={"schemaVersion":1,"stage":"screening-2","createdAt":now(),"bindings":current,
        "authorization":"user 2026-09-12: carry on with next step; allow pause before laptop closure",
        "stage2Authorized":True,"testAccess":False,"stopAfterStage":True,
        "proposalExecutionAuthority":"This manifest supersedes the proposal's historical authorizedToExecute:false; proposal remains immutable.",
        "storageCapBytes":4*GIB,"freeReserveBytes":10*GIB,"retention":"latest two global Stage2 recovery blobs; all fit exports/predictions/receipts retained"}
    save(run/"manifest.json",manifest)
    return manifest


def recovery_receipts(run):
    return sorted([read(p) for p in (run/"recovery").glob("*.json")],key=lambda r:r["stamp"])


def rotate(run,external):
    rows=recovery_receipts(run)
    for row in rows[-2:]: require(sha(external/row["file"])==row["SHA256"],"latest recovery corrupted")
    for row in rows[:-2]:
        original=external/row["file"]
        require(not any(p.is_symlink() for p in (external,external/"recovery",original)),"symlink recovery rejected")
        path=original.resolve()
        require(path.parent==(external/"recovery").resolve() and path.name.endswith(".pt.gz"),"unscoped recovery removal")
        receipt=run/"retention"/f"{row['stamp']}.json"
        if not path.exists(): require(receipt.exists(),"missing unrecorded recovery");continue
        require(sha(path)==row["SHA256"],"superseded recovery corrupted")
        if not receipt.exists(): save(receipt,row|{"removedAt":now(),"authorization":"approved Stage2 rolling recovery; permanent fit exports retained"})
        path.unlink()


def verify_upstream():
    from screening import verify,verify_upstream as prior
    verify(AUDIT,WORKSPACE/"screening"/AUDIT.name)
    verify_environment()
    return prior()
