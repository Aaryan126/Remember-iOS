"""Stage 5 isolation, immutable artifacts, pause boundaries and integrity."""
import fcntl
import gzip
import os
from pathlib import Path
import re
import shutil
import signal
import tempfile
import time

from experiment import ROOT, DATA, read, save, sha, require
from stage3_common import HERE, WORKSPACE, now, files_in, verify_files

STAGE2 = DATA / "runs/stage-2-attempt-01"
STAGE4 = DATA / "runs/stage-4-attempt-02"
RELEASE = DATA / "releases/v1"
CLASSES = ["same", "related", "unrelated"]
SOURCES = ["stage5.py", "stage5_common.py", "stage5_data.py", "stage5_train.py",
           "stage5_evaluate.py", "test_stage5.py"]
requested = False


class Paused(Exception): pass


def paths(value):
    run = Path(value).resolve()
    require(run.parent == (DATA / "runs").resolve() and re.fullmatch(r"stage-5-attempt-\d+", run.name), "invalid Stage 5 run")
    return run, WORKSPACE / "stage5" / run.name


def signal_pause(*_):
    global requested
    requested = True


def setup():
    for key in ["HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"]: os.environ[key] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    signal.signal(signal.SIGINT, signal_pause)
    signal.signal(signal.SIGTERM, signal_pause)


def wants_pause(run):
    return requested or (run / "control/pause-requested.json").exists()


def request_pause(run):
    require((run / "manifest.json").exists(), "run not initialized")
    if (run / "complete.json").exists(): return "already_complete_and_stopped"
    marker = run / "control/pause-requested.json"
    if not marker.exists(): save(marker, {"at": now(), "reason": "user/driver pause request"})
    return "pause_requested_wait_for_confirmation"


def boundary(run, phase):
    if wants_pause(run):
        save(run / "pauses" / f"{time.time_ns()}.json", {"at": now(), "phase": phase, "safeToCloseLaptop": True})
        raise Paused(phase)
    require(shutil.disk_usage(run).free >= 10 * 1024**3, "less than 10 GiB free; stop heavyweight work")


def authorize_test(run):
    path = run / "selection.json"
    require(path.exists(), "test split sealed until development selection is frozen")
    choice = read(path)
    require(choice["status"] == "selected" and choice["threshold"] is not None, "no qualifying frozen neural candidate")
    weights = Path(choice["weights"])
    require(weights.is_file() and sha(weights) == choice["weightsSHA256"], "selected weights changed")
    require(sha(STAGE2 / "baseline-selected.json") == choice["baselineSHA256"], "baseline changed")
    return choice


def initialize(run, external):
    require(shutil.disk_usage(WORKSPACE).free >= 10 * 1024**3, "less than 10 GiB free")
    from stage3 import verify as verify_stage3
    verify_stage3(DATA / "runs/stage-3-attempt-03", WORKSPACE)
    from environment import verify_assets
    verify_assets(WORKSPACE, read(DATA / "model-manifest.json"))
    stage4 = read(STAGE4 / "complete.json")
    verify_files(STAGE4, stage4["files"])
    require(stage4["feasibilityPassed"], "device feasibility not passed")
    current = {name: sha(HERE / name) for name in SOURCES}
    if (run / "manifest.json").exists():
        manifest = read(run / "manifest.json")
        require(manifest["sourceHashes"] == current and manifest["stage4CompleteSHA256"] == sha(STAGE4 / "complete.json"), "source/upstream changed; create a new attempt")
        verify_files(run / "source-snapshots", current)
        return manifest
    run.mkdir(parents=True, exist_ok=True); external.mkdir(parents=True, exist_ok=True)
    (run / "source-snapshots").mkdir()
    for name in SOURCES: shutil.copy2(HERE / name, run / "source-snapshots" / name)
    manifest = {"schemaVersion": 1, "stage": 5, "createdAt": now(),
        "authorizedBy": "user: start Stage 5; allow pause before laptop closure", "stopAfterStage": True,
        "sourceHashes": current, "stage4CompleteSHA256": sha(STAGE4 / "complete.json"),
        "modelManifestSHA256": sha(DATA / "model-manifest.json"), "baselineSHA256": sha(STAGE2 / "baseline-selected.json"),
        "inputHashes": {f"{kind}-{split}.json": sha(RELEASE / f"{kind}-{split}.json")
                        for kind in ["inputs", "labels"] for split in ["train", "development", "test"]},
        "seeds": [17, 29, 41], "epochs": 3, "learningRate": 2e-5, "weightDecay": .01,
        "effectiveBatch": 16, "initialMicrobatch": 8, "maxLength": 512,
        "padding": "truncate longest-first at 512; pad each effective batch to its maximum nonpadding length rounded up to32",
        "loss": "inverse-training-frequency cross entropy; each orientation has half weight; normalize once over entire effective batch",
        "optimizer": "AdamW, constant learning rate; default betas/epsilon; all trainable parameters; no scheduler/clipping",
        "checkpointEveryOptimizerSteps": 50, "checkpointFormat": "gzip PyTorch tensor/state dictionary; weights_only loading; atomic immutable receipts",
        "checkpointRetention": "preserve all unless a separately recorded explicit user authorization permits rolling recovery state",
        "candidateSelection": "epoch checkpoints only; development threshold/ranking per contract; ties earlier epoch then seed17,29,41",
        "evaluationLength": 512, "evaluationDirectionalBatch": 2, "classOrder": CLASSES,
        "testAccess": "only after selection.json binds chosen weights and threshold; never post-test tuning",
        "noPhone": True, "productionIntegration": False}
    save(run / "manifest.json", manifest)
    return manifest


def publish_tensor_file(path, writer):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), "refusing tensor overwrite")
    fd, name = tempfile.mkstemp(prefix="pending-", dir=path.parent)
    os.close(fd)
    pending = Path(name)
    try:
        writer(pending)
        with pending.open("rb") as stream: os.fsync(stream.fileno())
        os.link(pending, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        # Only this operation's explicitly created temporary file is removed.
        pending.unlink(missing_ok=True)


def save_state(path, value):
    import torch
    def write(pending):
        with gzip.GzipFile(filename=str(pending), mode="wb", compresslevel=1, mtime=0) as stream:
            torch.save(value, stream)
    publish_tensor_file(path, write)


def load_state(path, expected):
    import torch
    require(sha(path) == expected, "recovery checkpoint hash mismatch")
    with gzip.open(path, "rb") as stream:
        return torch.load(stream, map_location="cpu", weights_only=True)


def lock(run):
    run.mkdir(parents=True, exist_ok=True)
    handle = (run / "worker.lock").open("a")
    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return handle
