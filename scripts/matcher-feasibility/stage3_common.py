"""Stage 3 persistence, upstream integrity and cooperative safe boundaries."""
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import signal
import time

from experiment import ROOT, DATA, read, save, sha, require, verify_freeze
from environment import publish_bytes

HERE = Path(__file__).resolve().parent
STAGE2 = DATA / "runs/stage-2-attempt-01"
WORKSPACE = Path.home() / "Library/Application Support/RememberMatcherFeasibility/v1"
requested = False


class Paused(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def paths(run, workspace=WORKSPACE):
    run, workspace = Path(run).resolve(), Path(workspace).resolve()
    require(run.is_relative_to((DATA / "runs").resolve()) and re.fullmatch(r"stage-3-attempt-\d+", run.name), "invalid Stage 3 run")
    require(workspace.name == "v1" and workspace.parent.name == "RememberMatcherFeasibility", "unexpected workspace")
    return run, workspace


def signal_pause(signum, frame):
    global requested
    requested = True


def setup_signals():
    signal.signal(signal.SIGTERM, signal_pause)
    signal.signal(signal.SIGINT, signal_pause)


def boundary(run, phase):
    if requested or (run / "control/pause-requested.json").exists():
        save(run / "pauses" / f"{time.time_ns()}.json", {"at": now(), "phase": phase, "status": "paused"})
        raise Paused(phase)
    require(shutil.disk_usage(run).free >= 10 * 1024**3, "less than 10 GiB free")


def files_in(directory):
    directory = Path(directory)
    return {str(p.relative_to(directory)): sha(p) for p in sorted(directory.rglob("*")) if p.is_file()}


def verify_files(directory, files):
    directory = Path(directory).resolve()
    require(bool(files), "empty artifact manifest")
    for name, expected in files.items():
        path = (directory / name).resolve()
        require(path.is_relative_to(directory) and path.is_file() and sha(path) == expected, f"artifact mismatch: {name}")


def initialize(run, workspace):
    from stage2 import verify_run
    first = verify_freeze(DATA / "freeze.json")
    second = verify_run(STAGE2, workspace)
    path = run / "manifest.json"
    binding = {"stage1FreezeSHA256": first["freezeSHA256"], "stage2CompleteSHA256": second["completeSHA256"]}
    if path.exists():
        previous = read(path)
        require(all(previous[k] == v for k, v in binding.items()), "upstream checkpoint changed")
    else:
        save(path, {"schemaVersion": 1, "stage": 3, "createdAt": now(), **binding,
                   "authorizedBy": "user: carry on with stage 3, with pause support", "stopAfterStage": True,
                   "minimumDeploymentTarget": "iOS18", "modelPrecision": "float16", "lengths": [256, 512],
                   "batchSize": 1, "macOnly": True, "testResultsOpened": False,
                   "phoneInstallationAuthorized": False, "parityGate": {"maxProbabilityDifference": .01, "minimumClassAgreement": .99}})
    boundary(run, "initialized")


def snapshot(run, phase, names):
    folder = run / "source-snapshots" / phase
    for name in names:
        publish_bytes(folder / name, (HERE / name).read_bytes())
    return files_in(folder)


def failure(run, error):
    save(run / "failures" / f"{time.time_ns()}.json", {"at": now(), "errorType": type(error).__name__, "error": str(error)})
