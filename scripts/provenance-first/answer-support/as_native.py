"""Reuse frozen replay logic in a newly scoped launcher; no blind unknown retries.

Call from the coordinator's as_control.worker lock. Builds are separately
coordinated; only the new fictional bundle is installed. No phone or old writes.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid

import as_control as c
import native_driver as old_native
import verify_coverage as old_coverage
import as_native_build as native_build

DEVICE = old_native.DEVICE
BUNDLE = native_build.BUNDLE
OUTPUT = c.RUN / "native-output"
MAC_ROOT = c.ROOT / "Evaluation/iOS27/stage1"


def inside(root, name):
    path = root / name
    c.require(path.resolve() == path and path != root and path.is_relative_to(root),
              "native path escape or symlink")
    return path


def verify_build():
    return native_build.verify_build()


def known_preflight_recovery(run, input_path, build):
    """One explicit, audited non-execution recovery; never a generic retry switch."""
    key = hashlib.sha256(run["id"].encode()).hexdigest()
    original = c.RUN / "native-reservations" / (key + ".json")
    if not original.exists(): return None
    c.require(key == "8d6e0c5ae0370fe3e308ef277e12a600e21bdf016cbbf05235014e79aeb8f3a5",
              "unknown original native reservation; no automatic recovery")
    paths = {
        "native-attempts/native-replay-1789810749812144000/reserved.json": "b3f21d5f94e2680929c5656493c9feff638e2ddf146f2e584069cd68788f259c",
        "native-attempts/native-replay-1789810749812144000/terminal.json": "684fbf834dd0f98ac1e729766e644f80048633da403cc3bc5f103b8d36e1b20a",
        "native-attempts/native-replay-1789810749812144000/output.log": "0216a29263b72cc3d274b7d229512d9421e7852dd79e63388e24141f4a8a182a",
        "native-reservations/" + key + ".json": "a716d1c9ee0cdfe34983b96d3f48dc508aa24f94ab5d7b992cf6a5752e4ec474",
        "native-cleanup/1789810755975708000.json": "ac78a4005eda155d3f0b2d84365ecc51630647936fe8e8f9be34b4a97ad16e2f",
    }
    for name, expected in paths.items():
        c.require(c.digest(inside(c.RUN, name)) == expected, "known failure artifact changed")
    old_native.verify_build()
    before = c.load(original)
    c.require(before["id"] == run["id"] and before["batchSHA256"] == c.digest(input_path)
              and before["build"]["bundle"] != build["bundle"] and build["bundle"] == BUNDLE,
              "recovery must preserve input and use newly isolated bundle")
    launcher = (old_native.PROJECT / "Sources/HistoryRecoveryApp.swift").read_text()
    c.require(launcher.index("input must be beneath") < launcher.index("createDirectory(at: output")
              < launcher.index("HistoryProbe.run"), "old failure not provably before replay")
    receipt = c.RUN / "native-recoveries" / (key + ".json")
    value = dict(id=run["id"], oldArtifacts=paths, inputSHA256=c.digest(input_path),
                 oldLauncherSHA256=c.digest(old_native.PROJECT / "Sources/HistoryRecoveryApp.swift"),
                 newBuildSHA256=c.digest(c.WORK / "native-build-v2.json"),
                 classification="known-pre-replay-input-policy-rejection", ledgerExecuted=False,
                 originalReservationPreserved=True, automaticUnknownRetry=False)
    if not receipt.exists():
        c.require(not OUTPUT.exists(), "new output exists; cannot certify original non-execution")
    c.publish(receipt, value)
    return c.digest(receipt)


def stop_group(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
    c.require(process.poll() is not None, "owned process exit unconfirmed")


def execute(command, phase, timeout=60, native=False):
    """Every dispatch has an immutable reservation and terminal host receipt."""
    c.boundary()
    folder = c.RUN / "native-attempts" / f"{phase}-{time.time_ns()}"
    c.publish(folder / "reserved.json", dict(command=command, timeoutSeconds=timeout,
              native=native, generation=False, startedUnix=time.time()))
    process, failure, native_cleanup = None, None, None
    started = time.monotonic()
    log = c.checked(folder / "output.log")
    with log.open("xb") as stream:
        try:
            process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            while process.poll() is None:
                time.sleep(.25)
                c.boundary()
                if time.monotonic() - started > timeout:
                    raise TimeoutError(f"{phase}: host watchdog expired")
            c.require(process.returncode == 0, f"{phase}: process failed; see {log}")
            if native:
                # simctl can return zero even when the app itself prints failure.
                stream.flush()
                output = log.read_text()
                c.require(output.count("ANSWER_HISTORY_REPLAY_FINISHED") == 1
                          and "REPLAY_FAILED" not in output,
                          "native app did not report successful replay; inspect terminal log")
        except BaseException as error:
            failure = dict(type=type(error).__name__, message=str(error))
            if native and process is not None:
                # Native replay observes this marker at its library boundary.
                c.atomic(c.checked(OUTPUT / "pause.request"), dict(reason="host-stop"))
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: pass
                try:
                    stopped = subprocess.run(["xcrun", "simctl", "terminate", DEVICE, BUNDLE],
                        capture_output=True, text=True, timeout=15, check=False)
                    native_cleanup = dict(returnCode=stopped.returncode,
                                          stdout=stopped.stdout, stderr=stopped.stderr)
                except subprocess.TimeoutExpired:
                    native_cleanup = dict(timeout=True)
            raise
        finally:
            if process is not None: stop_group(process)
            c.publish(folder / "terminal.json", dict(exitCode=process.returncode if process else None,
                failure=failure, hostProcessExited=process is None or process.poll() is not None,
                nativeCleanup=native_cleanup, elapsedSeconds=time.monotonic()-started,
                outputSHA256=c.digest(log)))
    return log.read_text()


def sim(*args):
    return execute(["xcrun", "simctl", *args], "simctl", timeout=60).strip()


def mac_readiness():
    """Metadata only: no generation unit, model request, old runner, or old writes."""
    c.boundary()
    manifest = c.load(MAC_ROOT / "manifest.json")
    binary = MAC_ROOT / "build/compatibility-probe"
    c.require(c.digest(binary) == manifest["macBinarySHA256"], "old Mac binary changed")
    for name, expected in manifest["generated"].items():
        if name.startswith(("build/Sources/", "build/Resources/")):
            c.require(c.digest(inside(MAC_ROOT, name)) == expected, "old Mac resources changed")
    receipt = c.WORK / "mac-readiness.json"
    identity = dict(manifestSHA256=c.digest(MAC_ROOT / "manifest.json"),
                    binarySHA256=c.digest(binary))
    if receipt.exists():
        saved = c.load(receipt)
        c.require(saved["identity"] == identity, "readiness runtime binding changed")
        return saved
    reservation = c.WORK / "mac-readiness-reserved.json"
    c.require(not reservation.exists(), "unresolved readiness attempt; inspect before retry")
    c.publish(reservation, dict(identity=identity, generation=False, unit="environment"))
    output = execute([str(binary), "--unit", "environment", "--root", str(MAC_ROOT / "build/Resources")],
                     "mac-environment", timeout=60)
    lines = [line.removeprefix("IOS27_RESULT ") for line in output.splitlines()
             if line.startswith("IOS27_RESULT ")]
    c.require(len(lines) == 1, "missing or duplicate environment result")
    result = json.loads(lines[0])
    c.require(result.get("unit") == "environment" and result.get("syntheticOnly") is True
              and result.get("schemaVersion") == 1 and result.get("status") == "ok",
              "invalid Mac environment result")
    payload = dict(identity=identity, result=result, generationRequests=0,
                   available=result["result"]["foundationModelsAvailable"],
                   resources=c.resources(), readinessOnly=True, controlsQualified=False)
    c.publish(receipt, payload)
    return payload


def source_uuid(name):
    return str(uuid.UUID(bytes=hashlib.sha256(
        ("organization-diagnostics-v1:" + name).encode()).digest()[:16])).upper()


def verify_run(run, input_path, bindings_path=None):
    """Check ledger/projection bindings, every prefix, archive/version scope, reopen."""
    key = hashlib.sha256(run["id"].encode()).hexdigest()
    path = OUTPUT / (key + ".history.receipt.json")
    if not path.exists(): return None
    bindings_path = bindings_path or native_build.BINDINGS
    receipt = c.load(path)
    native = c.load(inside(OUTPUT, key + ".receipt.json"))
    attempt = native["attempt"]
    c.require(attempt.startswith(key + "-"), "invalid native attempt name")
    uuid.UUID(attempt[len(key)+1:])
    ledger_path = inside(OUTPUT, attempt + "/ledger.json")
    ledger = c.load(ledger_path)
    c.require(receipt["projection"] == key + ".projection.json", "projection name mismatch")
    projection_path = inside(OUTPUT, receipt["projection"])
    projection = c.load(projection_path)
    expected_count = len(run["events"])
    c.require(native["restartVerified"] is True and receipt["restartVerified"] is True
              and projection["restartVerified"] is True
              and native["historicalPrefixesVerified"] == expected_count,
              "native prefix/reopen proof missing")
    for row in (native, receipt, projection):
        c.require(row["id"] == run["id"] and row["batchSHA256"] == c.digest(input_path)
                  and row["bindingsSHA256"] == c.digest(bindings_path)
                  and row["ledgerSHA256"] == c.digest(ledger_path), "native binding mismatch")
    c.require(c.digest(projection_path) == receipt["projectionSHA256"], "projection hash mismatch")
    c.require(native["prefixCount"] == receipt["prefixCount"] == len(projection["prefixes"])
              == len(native["prefixes"]) == expected_count, "prefix count mismatch")
    c.require(receipt["queryCount"] == len(projection["queries"]) == len(run["queries"]),
              "query count mismatch")
    source_map = {source_uuid(e["source"]["id"]): e["source"]["id"] for e in run["events"]
                  if e["kind"] == "capture"}
    versions, prefixes = set(), {}
    for event, prefix, native_prefix in zip(run["events"], projection["prefixes"], native["prefixes"]):
        c.require(event["id"] == prefix["id"] == native_prefix["id"], "prefix ordering mismatch")
        count = native_prefix["ledgerCount"]
        c.require(type(count) is int and 0 < count <= len(ledger), "invalid ledger boundary")
        c.require(prefix["sequence"] == ledger[count-1]["sequence"], "prefix sequence mismatch")
        state = event["expectedState"]
        versions.update((sid, value["revision"]) for sid, value in state.items())
        current = {(sid, value["revision"]) for sid, value in state.items() if not value["archived"]}
        old_coverage.check_candidates(prefix["current"], ledger, prefix["sequence"], current, source_map)
        old_coverage.check_candidates(prefix["includeHistory"], ledger, prefix["sequence"], versions, source_map)
        for candidate in prefix["includeHistory"]:
            c.require(candidate["isArchived"] == state[source_map[candidate["sourceID"].upper()]]["archived"],
                      "candidate archive flag mismatch")
        prefixes[event["id"]] = prefix
    queries = {row["id"]: row for row in projection["queries"]}
    c.require(len(queries) == len(run["queries"]), "duplicate native query")
    for query in run["queries"]:
        value = queries[query["id"]]
        prefix = prefixes[query["afterEvent"]]
        c.require(value["scope"] == query["scope"] and value["afterEvent"] == query["afterEvent"]
                  and value["sequence"] == prefix["sequence"]
                  and value["candidates"] == prefix[query["scope"]], "query scope/prefix mismatch")
    return dict(id=run["id"], prefixes=expected_count, queries=len(queries), restartVerified=True,
                receiptSHA256=c.digest(path), projectionSHA256=c.digest(projection_path))


def run(input_path, maximum=1, resume=False):
    """Launch one or more bounded libraries; requires coordinator freeze beforehand.

    Existing completed runs are verified and skipped. Incomplete reservations stop
    for inspection; no automatic recreation of partially executed native work.
    """
    c.require(type(maximum) is int and maximum > 0, "maximum must be positive")
    input_path = c.checked(Path(input_path).absolute())
    build = verify_build()
    batch = c.load(input_path)
    c.require(batch["schemaVersion"] == 1 and batch["runs"], "invalid native batch")
    c.require(len({row["id"] for row in batch["runs"]}) == len(batch["runs"]), "duplicate native run")
    completed = [result for row in batch["runs"] if (result := verify_run(row, input_path))]
    if len(completed) == len(batch["runs"]): return completed
    recoveries = {row["id"]: known_preflight_recovery(row, input_path, build) for row in batch["runs"]}
    pause_path = OUTPUT / "pause.request"
    if resume and pause_path.exists():
        c.checked(pause_path).rename(c.RUN / f"native-pause-resumed-{time.time_ns()}.json")
    c.boundary()
    devices = json.loads(sim("list", "devices", "--json"))["devices"]
    device = next(d for group in devices.values() for d in group if d["udid"] == DEVICE)
    c.require(device["state"] == "Shutdown", "dedicated simulator must be shut down before owned replay")
    # Only a simulator booted by this invocation is shut down by it.
    booted = False
    try:
        # Set ownership before dispatch: a pause can arrive after boot succeeded
        # but before its host wrapper returned.
        booted = True
        sim("boot", DEVICE)
        sim("bootstatus", DEVICE, "-b")
        sim("install", DEVICE, str(native_build.APP))
        installed = Path(sim("get_app_container", DEVICE, BUNDLE, "app"))
        c.require(c.digest(installed / native_build.NAME) == build["executableSHA256"]
                  and c.digest(installed / "bindings.json") == build["bindingsSHA256"],
                  "installed newly scoped fictional probe differs")
        container = Path(sim("get_app_container", DEVICE, BUNDLE, "data")).resolve()
        expected = Path.home() / "Library/Developer/CoreSimulator/Devices" / DEVICE / "data/Containers/Data/Application"
        c.require(container.parent == expected and container.is_dir(), "unexpected fictional container")
        private = container / "Documents/AnswerSupportHistory"
        c.require(private.resolve() == private and private.is_relative_to(container), "input staging path escape")
        private.mkdir(parents=True, exist_ok=True)
        target = private / (c.digest(input_path) + ".json")
        if not target.exists():
            with target.open("xb") as stream: stream.write(input_path.read_bytes())
        c.require(target.read_bytes() == input_path.read_bytes(), "staged input mismatch")
        made = 0
        for row in batch["runs"]:
            c.boundary()
            result = verify_run(row, input_path)
            if result is not None: continue
            key = hashlib.sha256(row["id"].encode()).hexdigest()
            reservation = c.RUN / "native-reservations-v2" / (key + ".json")
            c.require(not reservation.exists(), "unresolved native run; inspect before retry")
            c.publish(reservation, dict(id=row["id"], batchSHA256=c.digest(input_path), build=build,
                                       recoverySHA256=recoveries[row["id"]]))
            execute(["xcrun", "simctl", "launch", "--console", DEVICE, BUNDLE,
                     "--input", str(target), "--output", str(OUTPUT), "--max-runs", "1"],
                    "native-replay", timeout=120, native=True)
            result = verify_run(row, input_path)
            c.require(result is not None, "native receipt missing; unknown execution, do not retry")
            c.publish(c.WORK / "native-units" / (key + ".json"), result)
            completed.append(result)
            made += 1
            if made >= maximum: break
    finally:
        if booted:
            # Cleanup must run even when the pause marker/resource guard is active.
            stopped = subprocess.run(["xcrun", "simctl", "shutdown", DEVICE],
                                     capture_output=True, text=True, timeout=30, check=False)
            state_check = subprocess.run(["xcrun", "simctl", "list", "devices", "--json"],
                                        capture_output=True, text=True, timeout=15, check=False)
            shutdown = False
            if state_check.returncode == 0:
                states = json.loads(state_check.stdout)["devices"]
                shutdown = any(d["udid"] == DEVICE and d["state"] == "Shutdown"
                               for group in states.values() for d in group)
            c.publish(c.RUN / "native-cleanup" / f"{time.time_ns()}.json",
                      dict(simulator=DEVICE, returnCode=stopped.returncode,
                           stdout=stopped.stdout, stderr=stopped.stderr,
                           shutdownConfirmed=shutdown))
            c.require(shutdown, "owned simulator shutdown unconfirmed")
    return completed
