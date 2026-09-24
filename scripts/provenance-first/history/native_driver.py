"""Resource-guarded fictional simulator build/replay; no physical-device access."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

import benchmark
import control as c

DEVICE = "C530FCC2-DD67-4115-97D9-C4E34807EC57"
BUNDLE = "SimpleStudio.Remember.HistoryRecoveryProbe"
PROJECT = c.RUN / "project"
OUTPUT = c.RUN / "output"
APP = c.RUN / "build/Build/Products/Debug-iphonesimulator/HistoryRecoveryProbe.app"
BINDINGS = PROJECT / "Sources/bindings.json"


def sim(*args):
    return subprocess.check_output(["xcrun", "simctl", *args], text=True, timeout=60).strip()


def execute(command, phase, native=False):
    c.boundary()
    c.RUN.mkdir(parents=True, exist_ok=True)
    stamp = str(time.time_ns())
    log = c.RUN / f"{phase}-{stamp}.log"
    record = dict(command=command, phase=phase, log=str(log.relative_to(c.ROOT)))
    c.publish(c.RUN / f"{phase}-{stamp}.start.json", record)
    failure = None
    with c.checked(log).open("xb") as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            while process.poll() is None:
                time.sleep(1)
                try: c.boundary()
                except BaseException:
                    if native:
                        c.previous.atomic(c.checked(OUTPUT / "pause.request"), {"reason": "coordinator-stop"})
                        try: process.wait(timeout=30)
                        except subprocess.TimeoutExpired:
                            subprocess.run(["xcrun", "simctl", "terminate", DEVICE, BUNDLE],
                                           capture_output=True, timeout=15, check=False)
                    raise
            c.require(process.returncode == 0, f"{phase} failed; see {log}")
        except BaseException as error:
            failure = dict(type=type(error).__name__, message=str(error))
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
            raise
        finally:
            c.publish(c.RUN / f"{phase}-{stamp}.end.json", dict(**record, exitCode=process.returncode, failure=failure))


def verify_bindings():
    bindings = c.load(BINDINGS)
    for category in ("production", "harness", "tooling"):
        for name, expected in bindings[category].items():
            path = c.ROOT / name
            c.require(path.resolve().is_relative_to(c.ROOT), "native source escaped repository")
            c.require(c.digest(path) == expected, f"native source changed: {name}")
    for name, expected in bindings["generated"].items():
        path = PROJECT / name
        c.require(path.resolve().is_relative_to(PROJECT), "generated source escaped project")
        c.require(c.digest(path) == expected, f"generated native source changed: {name}")
    # Local package identity, not an implicit resolver/download.
    project = (PROJECT / "HistoryRecoveryProbe.xcodeproj/project.pbxproj").read_text()
    match = re.search(r'relativePath = ("[^\n]+?");', project)
    c.require(match is not None, "local GRDB path missing")
    package = Path(json.loads(match.group(1))).resolve()
    for name, expected in bindings["grdb"].items():
        path = package / name
        c.require(path.resolve().is_relative_to(package), "GRDB path escape")
        c.require(c.digest(path) == expected, f"GRDB source changed: {name}")
    return bindings


def prepare():
    c.verify_preserved()
    c.boundary()
    if PROJECT.exists():
        verify_bindings()
        return
    import prepare_native
    old_project = c.PF / "runs/checkpoint1/ledger/project/ProvenanceFirstProbe.xcodeproj/project.pbxproj"
    match = re.search(r'relativePath = ("[^\n]+?");', old_project.read_text())
    c.require(match is not None, "existing local dependency unavailable")
    package = Path(json.loads(match.group(1)))
    result = prepare_native.prepare(PROJECT, package)
    c.publish(c.WORK / "native-preparation.json", result)
    verify_bindings()


def build():
    c.verify_preserved()
    verify_bindings()
    receipt = c.WORK / "native-build.json"
    if receipt.exists():
        verify_build()
        return
    command = ["xcodebuild", "-project", str(PROJECT / "HistoryRecoveryProbe.xcodeproj"),
               "-scheme", "HistoryRecoveryProbe", "-configuration", "Debug",
               "-sdk", "iphonesimulator", "-destination", f"id={DEVICE}",
               "-derivedDataPath", str(c.RUN / "build"), "-disableAutomaticPackageResolution",
               "-skipPackageUpdates", "CODE_SIGNING_ALLOWED=NO", "build"]
    execute(command, "build")
    c.require((APP / "HistoryRecoveryProbe").is_file(), "native executable missing")
    c.require(c.digest(APP / "bindings.json") == c.digest(BINDINGS), "bundled bindings mismatch")
    c.publish(receipt, dict(executableSHA256=c.digest(APP / "HistoryRecoveryProbe"),
                          bindingsSHA256=c.digest(BINDINGS), command=command))


def verify_build():
    verify_bindings()
    record = c.load(c.WORK / "native-build.json")
    c.require(record["executableSHA256"] == c.digest(APP / "HistoryRecoveryProbe")
              and record["bindingsSHA256"] == c.digest(BINDINGS)
              and record["bindingsSHA256"] == c.digest(APP / "bindings.json"), "native build changed")


def run(maximum=None, resume=False, invariants=False):
    c.require(maximum is None or maximum > 0, "max-runs must be positive")
    benchmark.verify()
    verify_build()
    import verify_coverage
    verify_coverage.artifact_paths()
    if resume and (OUTPUT / "pause.request").exists():
        c.checked(OUTPUT / "pause.request").rename(c.RUN / f"native-pause-resumed-{time.time_ns()}.json")
    c.boundary()
    devices = json.loads(sim("list", "devices", "--json"))
    device = next(d for entries in devices["devices"].values() for d in entries if d["udid"] == DEVICE)
    if device["state"] == "Shutdown": sim("boot", DEVICE)
    sim("bootstatus", DEVICE, "-b")
    c.boundary()
    sim("install", DEVICE, str(APP))
    container = Path(sim("get_app_container", DEVICE, BUNDLE, "data")).resolve()
    allowed = Path.home() / "Library/Developer/CoreSimulator/Devices" / DEVICE / "data/Containers/Data/Application"
    c.require(container.parent == allowed and container.is_dir(), "unexpected fictional app container")
    installed = Path(sim("get_app_container", DEVICE, BUNDLE, "app"))
    c.require(c.digest(installed / "HistoryRecoveryProbe") == c.digest(APP / "HistoryRecoveryProbe"),
              "installed build differs")
    private = container / "Documents/HistoryRecovery"
    c.require(private.resolve().is_relative_to(container), "private input path escape")
    private.mkdir(parents=True, exist_ok=True)
    source = c.RUN / "input.json"
    target = private / (c.digest(source) + ".json")
    if not target.exists():
        with target.open("xb") as stream: stream.write(source.read_bytes())
    c.require(target.read_bytes() == source.read_bytes(), "staged input differs")
    completed = verify_coverage.verify()["completedLibraries"]
    if invariants:
        c.require(not (OUTPUT / "history-invariants.json").exists(), "do not overwrite invariant results")
    made = 0
    while completed < 24 or invariants:
        c.boundary()
        command = ["xcrun", "simctl", "launch", "--console", DEVICE, BUNDLE,
                   "--input", str(target), "--output", str(OUTPUT), "--max-runs", "1"]
        if invariants: command.append("--invariants")
        execute(command, "native", native=True)
        if invariants:
            paths = (OUTPUT / "history-invariants.json", OUTPUT / "invariants.receipt.json")
            c.require(all(p.is_file() for p in paths), "invariant results missing")
            c.publish(c.WORK / "invariant-execution.json", dict(batchSHA256=c.digest(source),
                      bindingsSHA256=c.digest(BINDINGS), command=command,
                      outputs={str(p.relative_to(c.ROOT)): c.digest(p) for p in paths}))
            invariants = False
        new_count = verify_coverage.verify()["completedLibraries"]
        c.require(new_count > completed or completed == 24, "native replay made no progress")
        made += new_count - completed
        completed = new_count
        print(json.dumps(dict(completedLibraries=completed, totalLibraries=24)), flush=True)
        if maximum is not None and made >= maximum: break


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "build", "run"))
    parser.add_argument("--max-runs", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--invariants", action="store_true")
    args = parser.parse_args()
    try:
        with c.worker(resume=args.resume):
            if args.command == "prepare": prepare()
            elif args.command == "build": build()
            else: run(args.max_runs, args.resume, args.invariants)
        print(json.dumps(dict(command=args.command, status="returned", workerStopped=True)))
    except c.Paused as error:
        print(json.dumps(dict(status="paused", reason=str(error), workerStopped=True)))


if __name__ == "__main__": main()
