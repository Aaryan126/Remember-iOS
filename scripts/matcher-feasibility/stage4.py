#!/usr/bin/env python3
"""Isolated physical-phone feasibility runner. Never accesses the Remember vault."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import signal
import subprocess
import time
import uuid

from experiment import DATA, ROOT, read, save, sha, require
from stage3_common import WORKSPACE, HERE, now, files_in, verify_files

BUNDLE = "SimpleStudio.Remember.MatcherProbe"
STAGE3 = DATA / "runs/stage-3-attempt-03"
SOURCES = ["stage4.py", "stage4_report.py", "test_stage4.py", "Stage4ProbeApp.swift",
           "MatcherTokenizer.swift", "MatcherRuntime.swift", "MatcherProbe.pbxproj.template"]


def run_path(value):
    path = Path(value).resolve()
    require(path.parent == (DATA / "runs").resolve() and re.fullmatch(r"stage-4-attempt-\d+", path.name), "invalid Stage 4 run path")
    return path


def command(run, arguments, timeout=60):
    stamp = str(time.time_ns())
    log = run / "commands" / f"{stamp}.json"
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
    save(log, {"at": now(), "command": arguments, "returncode": result.returncode,
               "stdout": result.stdout, "stderr": result.stderr})
    require(result.returncode == 0, f"command failed ({result.returncode}); see {log}")
    return result


def verify(run):
    manifest = read(run / "manifest.json")
    require(manifest["bundleIdentifier"] == BUNDLE, "unsafe bundle")
    require(sha(STAGE3 / "complete.json") == manifest["stage3CompleteSHA256"], "upstream checkpoint changed")
    verify_files(HERE, manifest["sourceHashes"])
    verify_files(run / "source-snapshots", manifest["sourceHashes"])
    verify_files(Path(manifest["project"]), manifest["projectHashes"])
    if (run / "build.json").exists():
        receipt = read(run / "build.json")
        verify_files(Path(receipt["app"]), receipt["appHashes"])
    return manifest


def prepare(run, device):
    require(not run.exists(), "choose a new attempt; existing evidence is immutable")
    require(shutil.disk_usage(WORKSPACE).free >= 10 * 1024**3, "less than 10 GiB free")
    from stage3 import verify as verify_stage3
    verify_stage3(STAGE3, WORKSPACE)
    old = read(STAGE3 / "app-build.json")
    project = WORKSPACE / "stage4" / run.name / "project"
    require(not project.exists(), "external attempt exists")
    old_sources = WORKSPACE / old["project"] / "Sources"
    sources = project / "Sources"
    shutil.copytree(old_sources, sources, ignore=shutil.ignore_patterns("MatcherProbeApp.swift"))
    shutil.copy2(HERE / "Stage4ProbeApp.swift", sources / "Stage4ProbeApp.swift")
    (project / "MatcherProbe.xcodeproj").mkdir()
    shutil.copy2(HERE / "MatcherProbe.pbxproj.template", project / "MatcherProbe.xcodeproj/project.pbxproj")
    run.mkdir(parents=True)
    snapshots = run / "source-snapshots"; snapshots.mkdir()
    for name in SOURCES:
        shutil.copy2(HERE / name, snapshots / name)
    manifest = {"schemaVersion": 1, "stage": 4, "createdAt": now(), "runID": run.name,
        "authorizedBy": "user: go ahead with stage 4; connected phone; support pause/resume",
        "stopAfterStage": True, "bundleIdentifier": BUNDLE, "deviceIdentifier": device,
        "stage3CompleteSHA256": sha(STAGE3 / "complete.json"),
        "candidateID": read(sources / "candidate.json")["candidateID"],
        "sourceHashes": {name: sha(HERE / name) for name in SOURCES}, "project": str(project),
        "projectHashes": files_in(project), "computeUnits": "all", "coldProcessCount": 10,
        "warmMeasurementsPerLength": 100, "lengths": [256, 512], "warmupShortlistsPerLaunch": 3,
        "pairsPerShortlist": 10, "passesPerPair": 2, "sampleIntervalSeconds": .02,
        "latencyScope": "full sequential shortlist: tokenization, input allocation, 20 predictions, averaging and cancellation checks; excludes result serialization",
        "fixturePolicy": "index*10+offset modulo all 104 frozen fictional fixtures; includes eight edge cases; no test labels",
        "thermalPolicy": "retain nominal/fair samples; stop before next prediction at serious/critical, retain any completed samples",
        "memoryScope": "task_vm_info phys_footprint sampled every20ms; RSS separately; process only, no claim of total accelerator/system memory",
        "gates": {"warm256P95Seconds": 1.0, "peakFootprintBytes": 500_000_000,
                  "parityMaxProbabilityDifference": .01, "parityMinimumClassAgreement": .99}}
    save(run / "manifest.json", manifest)
    print(json.dumps({"prepared": True, "run": str(run), "project": str(project)}))


def build(run):
    manifest = verify(run)
    if (run / "build.json").exists():
        print('{"build": "already saved and verified"}'); return
    project = Path(manifest["project"])
    text = (ROOT / "Remember/Remember.xcodeproj/project.pbxproj").read_text()
    team = re.search(r"DEVELOPMENT_TEAM = ([A-Z0-9]+);", text)
    require(team is not None, "no existing development signing team")
    derived = project.parent / "build"
    command(run, ["xcodebuild", "-project", str(project / "MatcherProbe.xcodeproj"), "-scheme", "MatcherProbe",
        "-configuration", "Release", "-sdk", "iphoneos", "-destination", "generic/platform=iOS",
        "-derivedDataPath", str(derived), "-allowProvisioningUpdates", f"DEVELOPMENT_TEAM={team[1]}", "build"], timeout=600)
    app = derived / "Build/Products/Release-iphoneos/MatcherProbe.app"
    info = plistlib.loads((app / "Info.plist").read_bytes())
    require(info["CFBundleIdentifier"] == BUNDLE and not any(k.endswith("UsageDescription") for k in info), "unsafe app permissions")
    entitlements = command(run, ["codesign", "-d", "--entitlements", ":-", str(app)]).stdout
    document = plistlib.loads(entitlements.encode())
    require(not document.get("com.apple.security.application-groups"), "shared app groups forbidden")
    require(document.get("application-identifier", "").endswith("." + BUNDLE), "unexpected signed application")
    require(read(app / "fixtures.json") == read(project / "Sources/fixtures.json"), "phone inputs changed")
    save(run / "build.json", {"at": now(), "app": str(app), "appHashes": files_in(app),
        "bundleIdentifier": BUNDLE, "signed": True, "appLogicalBytes": sum(p.stat().st_size for p in app.rglob("*") if p.is_file()),
        "entitlements": document})
    print('{"build": "passed", "signed": true}')


def device_command(run, manifest, arguments, timeout=60):
    return command(run, ["xcrun", "devicectl", "device", *arguments,
        "--device", manifest["deviceIdentifier"], "--timeout", str(timeout - 5)], timeout=timeout)


def install(run):
    manifest = verify(run)
    receipt = read(run / "build.json")
    device_command(run, manifest, ["install", "app", receipt["app"]], timeout=120)
    save(run / "installations" / f"{time.time_ns()}.json", {"at": now(), "buildSHA256": sha(run / "build.json")})
    print('{"installed": true, "productionAppTouched": false}')


def merge_export(source, target):
    require(source.is_dir(), "device export missing")
    for path in sorted(source.rglob("*.json")):
        destination = target / path.relative_to(source)
        if destination.exists():
            require(sha(destination) == sha(path), f"completed device artifact changed: {destination}")
        else:
            # save() is exclusive + atomic, and serializes unchanged JSON values.
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(".pending")
            require(not temporary.exists(), "unfinished host copy; inspect before resuming")
            shutil.copy2(path, temporary)
            os.replace(temporary, destination)


def collect(run, manifest=None):
    manifest = manifest or verify(run)
    export = run / "exports" / str(time.time_ns())
    export.parent.mkdir(exist_ok=True)
    device_command(run, manifest, ["copy", "from", "--source", "Documents/" + run.name,
        "--destination", str(export), "--domain-type", "appDataContainer", "--domain-identifier", BUNDLE])
    merge_export(export, run / "device")
    print(json.dumps({"collected": True, "records": len(list((run / 'device').glob('*/records/*.json')))}), flush=True)


def pause(run):
    if (run / "complete.json").exists():
        print('{"status": "already stopped at completed checkpoint"}'); return
    path = run / "control/pause-requested.json"
    if not path.exists(): save(path, {"at": now(), "request": "pause at next prediction boundary"})
    print('{"status": "pause requested; wait for worker confirmation"}')


def launch(run, job, mode, length, count, resume=False, pause_after=None):
    manifest = verify(run)
    require(re.fullmatch(r"[a-z0-9-]{1,64}", job), "invalid job name")
    require(shutil.disk_usage(run).free >= 10 * 1024**3, "less than 10 GiB free")
    control = run / "control"; control.mkdir(exist_ok=True)
    marker = control / "pause-requested.json"
    if marker.exists():
        require(resume, "pause requested; explicitly resume after worker stops")
        marker.rename(control / f"pause-history-{time.time_ns()}.json")
    binding = {"job": job, "mode": mode, "length": length, "count": count}
    job_path = run / "jobs" / f"{job}.json"
    if job_path.exists(): require(read(job_path) == binding, "job configuration changed")
    else: save(job_path, binding)
    if (run / "jobs" / f"{job}-complete.json").exists():
        print('{"status": "job already complete"}'); return
    launch_id = str(uuid.uuid4())
    log_path = run / "console" / f"{launch_id}.log"; log_path.parent.mkdir(exist_ok=True)
    receipt_path = run / "launches" / f"{launch_id}.json"
    arguments = ["xcrun", "devicectl", "device", "process", "launch", "--device", manifest["deviceIdentifier"],
        "--terminate-existing", "--console", "--timeout", "1800", BUNDLE,
        "stage4", run.name, job, launch_id, mode, str(length), str(count)]
    save(receipt_path, {"at": now(), **binding, "launchID": launch_id, "command": arguments,
                       "interruptAfterSavedRecords": pause_after})
    signal.signal(signal.SIGINT, lambda *_: pause(run))
    signal.signal(signal.SIGTERM, lambda *_: pause(run))
    sent = False
    with log_path.open("x") as log:
        worker = subprocess.Popen(arguments, stdout=log, stderr=subprocess.STDOUT)
        started = time.monotonic()
        try:
            while worker.poll() is None:
                if pause_after is not None and not sent and log_path.read_text().count("STAGE4 saved") >= pause_after:
                    pause(run)
                if marker.exists() and not sent:
                    device_command(run, manifest, ["copy", "to", "--source", str(marker),
                        "--destination", f"Documents/{run.name}/pause-{launch_id}.json",
                        "--domain-type", "appDataContainer", "--domain-identifier", BUNDLE])
                    sent = True
                    print('{"status": "phone pause delivered; awaiting saved receipt"}', flush=True)
                require(time.monotonic() - started < 1860, "device job timeout")
                time.sleep(.5)
        except BaseException:
            worker.terminate()
            try: worker.wait(timeout=10)
            except subprocess.TimeoutExpired: worker.kill(); worker.wait()
            raise
    save(run / "launches" / f"{launch_id}-host-end.json", {"at": now(), "returncode": worker.returncode,
        "hostLaunchAndRunSeconds": time.monotonic() - started, "pauseSent": sent})
    collect(run, manifest)
    end_path = run / "device" / job / "launches" / launch_id / "end.json"
    require(end_path.exists(), "no saved phone end receipt; retain partial records and investigate before resuming")
    end = read(end_path)
    require(end["status"] in ["complete", "paused"], f"phone job failed: {end.get('message')}")
    require(worker.returncode == 0, "phone launch reported failure despite receipt")
    if end["status"] == "complete":
        save(run / "jobs" / f"{job}-complete.json", {"at": now(), "endSHA256": sha(end_path), "launchID": launch_id})
    else:
        save(run / "pauses" / f"{time.time_ns()}.json", {"at": now(), "job": job, "launchID": launch_id,
            "endSHA256": sha(end_path), "safeToDisconnect": True})
    print(json.dumps({"status": end["status"], "job": job, "safeToDisconnect": True}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "build", "install", "run", "collect", "pause", "verify", "report"])
    parser.add_argument("--run", required=True)
    parser.add_argument("--device")
    parser.add_argument("--job")
    parser.add_argument("--mode", choices=["cold", "warm", "parity", "interrupt"])
    parser.add_argument("--length", type=int, choices=[256, 512], default=256)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--pause-after", type=int)
    args = parser.parse_args(); run = run_path(args.run)
    if args.action == "prepare":
        require(bool(args.device), "--device required"); prepare(run, args.device); return
    if args.action == "pause": pause(run); return
    # A crash releases this advisory lock; no stale-PID guessing or forced lock deletion.
    with (run / "worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == "build": build(run)
        elif args.action == "install": install(run)
        elif args.action == "collect": collect(run)
        elif args.action == "verify": verify(run); print('{"verified": true}')
        elif args.action == "report":
            from stage4_report import report
            verify(run); report(run)
        else:
            require(bool(args.job and args.mode) and 1 <= args.count <= 100, "job, mode and count 1...100 required")
            launch(run, args.job, args.mode, args.length, args.count, args.resume, args.pause_after)


if __name__ == "__main__": main()
