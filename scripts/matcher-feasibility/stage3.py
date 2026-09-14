#!/usr/bin/env python3
"""Stage 3 driver. Explicit pause/resume, immutable receipts, no device install."""
import argparse
import json
from pathlib import Path
import selectors
import subprocess
import sys
import time

import stage3_common as common
from stage3_common import HERE, DATA, WORKSPACE, read, save, sha, require, paths, initialize, boundary, Paused, files_in, verify_files


def request_pause(run, reason="user pause request"):
    require((run / "manifest.json").exists(), "no initialized Stage 3 attempt")
    if (run / "complete.json").exists():
        return "already_complete_and_stopped"
    marker = run / "control/pause-requested.json"
    if not marker.exists():
        save(marker, {"at": common.now(), "reason": reason})
    return "pause_requested_wait_for_worker_confirmation"


def run_worker(run, workspace, script):
    boundary(run, f"before:{script}")
    log_path = run / "logs" / f"{Path(script).stem}-{time.time_ns()}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(HERE / script), "--run", str(run), "--workspace", str(workspace)]
    with log_path.open("x") as log:
        worker = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(worker.stdout, selectors.EVENT_READ)
                while worker.poll() is None:
                    if common.requested:
                        request_pause(run, "driver signal")
                    if selector.select(timeout=1):
                        line = worker.stdout.readline()
                        log.write(line); log.flush()
                        print(line, end="", flush=True)
                remainder = worker.stdout.read()
                log.write(remainder); print(remainder, end="", flush=True)
            require(worker.returncode == 0, f"phase failed: {script}; see {log_path.name}")
        finally:
            if worker.poll() is None:
                worker.terminate()
                try:
                    worker.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    worker.kill(); worker.wait()
            worker.stdout.close()
    boundary(run, f"after:{script}")


def verify(run, workspace):
    receipt = read(run / "complete.json")
    verify_files(run, receipt["files"])
    verify_files(workspace, receipt["workspaceFiles"])
    verify_files(HERE, receipt["sourceFiles"])
    common.initialize(run, workspace)
    return {"verified": True, "files": len(receipt["files"]), "workspaceFiles": len(receipt["workspaceFiles"]),
            "sourceFiles": len(receipt["sourceFiles"]), "completeSHA256": sha(run / "complete.json")}


def complete(run, workspace):
    for filename in ("tokenizer-summary.json", "parity-summary.json", "app-build.json"):
        require(read(run / filename)["passed"], f"incomplete/failed phase: {filename}")
    names = ["stage3.py", "stage3_common.py", "stage3_convert.py", "stage3_parity.py", "stage3_build.py", "test_stage3.py",
             "MatcherTokenizer.swift", "MatcherRuntime.swift", "MatcherProbeApp.swift", "Stage3TokenizerProbe.swift", "Stage3RuntimeProbe.swift", "MatcherProbe.pbxproj.template"]
    conversion = read(run / "conversion.json")
    workspace_files = {str((workspace / conversion["package"] / name).relative_to(workspace)): value for name, value in conversion["packageFiles"].items()}
    build = read(run / "app-build.json")
    for key in ("project", "app", "nativeProbe"):
        folder = workspace / build[key]
        if folder.is_dir():
            workspace_files.update({str((folder / name).relative_to(workspace)): value for name, value in files_in(folder).items()})
        else:
            workspace_files[str(folder.relative_to(workspace))] = sha(folder)
    artifacts = {name: value for name, value in files_in(run).items() if not name.startswith("control/") and name != "complete.json"}
    save(run / "complete.json", {"schemaVersion": 1, "stage": 3, "completedAt": common.now(),
         "status": "converted_verified_probe_built", "files": artifacts, "workspaceFiles": workspace_files,
         "sourceFiles": {name: sha(HERE / name) for name in names}, "stage4Started": False,
         "phoneInstalled": False, "testResultsOpened": False, "untrainedHead": True})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "pause", "verify"])
    parser.add_argument("--run", required=True)
    parser.add_argument("--workspace", default=WORKSPACE)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    run, workspace = paths(args.run, args.workspace)
    if args.command == "pause":
        print(json.dumps({"status": request_pause(run)})); return
    if args.command == "verify":
        print(json.dumps(verify(run, workspace))); return
    marker = run / "control/pause-requested.json"
    if args.resume and marker.exists():
        marker.rename(run / "control" / f"resumed-request-{time.time_ns()}.json")
    common.setup_signals()
    try:
        initialize(run, workspace)
        if (run / "complete.json").exists():
            print(json.dumps(verify(run, workspace))); return
        for script in ("stage3_convert.py", "stage3_parity.py", "stage3_build.py"):
            run_worker(run, workspace, script)
        boundary(run, "before-completion")
        complete(run, workspace)
        print(json.dumps(verify(run, workspace)))
    except Paused as error:
        print(json.dumps({"status": "paused", "safeBoundary": str(error), "safeToCloseLaptop": True}), flush=True)
    except Exception as error:
        common.failure(run, error)
        raise


if __name__ == "__main__":
    main()
