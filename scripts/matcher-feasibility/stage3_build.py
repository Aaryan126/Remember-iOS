#!/usr/bin/env python3
"""Build a label-free isolated iOS probe; exercise the same runtime on the Mac."""
import argparse
import hashlib
import json
import plistlib
import selectors
import shutil
import subprocess
import time

from stage3_common import *
from stage3_parity import fixture_requests, comparison, summarize


def phone_inputs(document):
    require(len(document["fixtures"]) == 104, "unexpected phone fixture count")
    result = {"schemaVersion": 1, "fixtures": [{key: f[key] for key in ("id", "first", "second")} for f in document["fixtures"]]}
    require(len({f["id"] for f in result["fixtures"]}) == 104, "duplicate phone fixture ID")
    require(all(re.fullmatch(r"[A-Za-z0-9-]+", f["id"]) and isinstance(f["first"], str) and isinstance(f["second"], str)
                for f in result["fixtures"]), "unsafe phone fixture")
    return result


def build(run, workspace):
    if (run / "app-build.json").exists():
        require(read(run / "app-build.json")["passed"], "saved app build failed")
        return
    require(read(run / "parity-summary.json")["passed"], "parity must pass before probe build")
    tokenizer = read(run / "tokenizer-summary.json")
    require(sha(HERE / "MatcherTokenizer.swift") == tokenizer["sourceSHA256"]["MatcherTokenizer.swift"], "tokenizer changed after parity")
    names = ["stage3_build.py", "MatcherTokenizer.swift", "MatcherRuntime.swift", "MatcherProbeApp.swift", "Stage3RuntimeProbe.swift", "MatcherProbe.pbxproj.template"]
    identity = hashlib.sha256(json.dumps({name: sha(HERE / name) for name in names}, sort_keys=True).encode()).hexdigest()
    snapshot(run, "app-" + identity[:12], names)
    external = workspace / "stage3" / run.name
    project_receipt = run / "projects" / f"{identity}.json"
    conversion = read(run / "conversion.json")
    package = workspace / conversion["package"]
    verify_files(package, conversion["packageFiles"])
    if project_receipt.exists():
        project_root = workspace / read(project_receipt)["project"]
        verify_files(project_root, read(project_receipt)["files"])
    else:
        boundary(run, "before-probe-project")
        project_root = external / f"probe-project-{identity[:12]}-{time.time_ns()}"
        sources = project_root / "Sources"
        sources.mkdir(parents=True)
        for name in ("MatcherTokenizer.swift", "MatcherRuntime.swift", "MatcherProbeApp.swift"):
            publish_bytes(sources / name, (HERE / name).read_bytes())
        publish_bytes(project_root / "MatcherProbe.xcodeproj/project.pbxproj", (HERE / "MatcherProbe.pbxproj.template").read_bytes())
        original = workspace / read(DATA / "model-manifest.json")["workspaceRelativeDirectory"]
        publish_bytes(sources / "vocab.txt", (original / "vocab.txt").read_bytes())
        publish_bytes(sources / "MODEL_CARD.txt", (original / "README.md").read_bytes())
        shutil.copytree(package, sources / "MatcherReference.mlpackage")
        save(sources / "fixtures.json", phone_inputs(read(STAGE2 / "reference/fixtures.json")))
        candidate_id = hashlib.sha256(json.dumps(conversion["packageFiles"], sort_keys=True).encode()).hexdigest()
        save(sources / "candidate.json", {"candidateID": candidate_id, "untrainedHead": True,
             "classOrder": ["same", "related", "unrelated"]})
        save(project_receipt, {"project": str(project_root.relative_to(workspace)), "files": files_in(project_root), "sourceIdentity": identity})
    native = external / f"native-{identity[:12]}"
    native.mkdir(parents=True, exist_ok=True)
    executable = native / "RuntimeProbe"
    if not executable.exists():
        boundary(run, "before-native-runtime-build")
        command = ["xcrun", "swiftc", "-parse-as-library", "-O", "-target", "arm64-apple-macos15.0",
                   str(HERE / "MatcherTokenizer.swift"), str(HERE / "MatcherRuntime.swift"), str(HERE / "Stage3RuntimeProbe.swift"), "-o", str(executable)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        save(run / "build-logs" / f"native-{time.time_ns()}.json", {"command": command, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        require(result.returncode == 0, "native Swift runtime compile failed")
    compiled = native / "MatcherReference.mlmodelc"
    if not compiled.exists():
        boundary(run, "before-mac-native-model-compile")
        import coremltools as ct
        model = ct.models.MLModel(str(package), compute_units=ct.ComputeUnit.ALL)
        pending = native / f"pending-compiled-{time.time_ns()}.mlmodelc"
        shutil.copytree(model.get_compiled_model_path(), pending)
        pending.rename(compiled)
        del model
    native_cases = run / "native-cases" / identity[:12]
    requests = fixture_requests()
    log_path = run / "build-logs" / f"native-stderr-{time.time_ns()}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("x") as log:
        worker = subprocess.Popen([str(executable), str(compiled), str(project_root / "Sources/vocab.txt")],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True, bufsize=1)
        try:
            for index, request in enumerate(requests):
                boundary(run, f"native-inference:{request['id']}")
                path = native_cases / f"{request['id']}.json"
                if path.exists():
                    continue
                worker.stdin.write(json.dumps(request) + "\n"); worker.stdin.flush()
                with selectors.DefaultSelector() as selector:
                    selector.register(worker.stdout, selectors.EVENT_READ)
                    require(bool(selector.select(timeout=120)), "native model response timeout")
                    line = worker.stdout.readline()
                require(bool(line), "native model exited without response")
                actual = json.loads(line)
                original_path = STAGE2 / "reference/cases" / path.name
                original = read(original_path)
                require(actual["id"] == request["id"] and actual["prediction"]["inputs"] == original["inputs"], "native token/ID mismatch")
                delta = comparison([actual["prediction"]["probabilities"]], original["probabilities"])
                save(path, {"id": request["id"], **delta, "recordedAt": now(), "referenceSHA256": sha(original_path),
                            "prediction": actual["prediction"]})
                if (index + 1) % 40 == 0:
                    print(json.dumps({"phase": "native-inference", "completed": index + 1, "total": len(requests)}), flush=True)
        finally:
            worker.stdin.close()
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker.kill(); worker.wait()
            worker.stdout.close()
    native_summary = summarize([read(native_cases / f"{r['id']}.json") for r in requests])
    require(native_summary["passed"], "native Swift model parity failed")
    boundary(run, "before-unsigned-ios-build")
    derived = external / f"build-{identity[:12]}"
    command = ["xcodebuild", "-project", str(project_root / "MatcherProbe.xcodeproj"), "-scheme", "MatcherProbe",
               "-configuration", "Release", "-sdk", "iphoneos", "-destination", "generic/platform=iOS",
               "-derivedDataPath", str(derived), "CODE_SIGNING_ALLOWED=NO", "CODE_SIGNING_REQUIRED=NO", "build"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=600)
    build_log = run / "build-logs" / f"ios-{time.time_ns()}.json"
    save(build_log, {"command": command, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    require(result.returncode == 0, f"iOS probe build failed; see {build_log.name}")
    app = derived / "Build/Products/Release-iphoneos/MatcherProbe.app"
    info = plistlib.loads((app / "Info.plist").read_bytes())
    require(info["CFBundleIdentifier"] == "SimpleStudio.Remember.MatcherProbe", "unsafe probe bundle identifier")
    require(not any(key.endswith("UsageDescription") for key in info), "probe unexpectedly requests private-data permissions")
    payload = read(app / "fixtures.json")
    require(payload == phone_inputs(read(STAGE2 / "reference/fixtures.json")), "phone payload changed")
    require((app / "MatcherReference.mlmodelc").is_dir(), "compiled iOS model missing")
    require(not list(project_root.rglob("*.entitlements")), "probe must not share production entitlements")
    save(run / "app-build.json", {"passed": True, "createdAt": now(), "project": str(project_root.relative_to(workspace)),
         "app": str(app.relative_to(workspace)), "nativeProbe": str(executable.relative_to(workspace)),
         "nativeCasesDirectory": str(native_cases.relative_to(run)), "nativeParity": native_summary,
         "appBytes": sum(p.stat().st_size for p in app.rglob("*") if p.is_file()),
         "compiledModelBytes": sum(p.stat().st_size for p in (app / "MatcherReference.mlmodelc").rglob("*") if p.is_file()),
         "bundleIdentifier": info["CFBundleIdentifier"], "signed": False, "installed": False,
         "phoneInputsContainLabels": False, "productionAppGroup": False, "sourceIdentity": identity,
         "buildLog": str(build_log.relative_to(run))})
    print(json.dumps({"phase": "ios-probe", "built": True, "installed": False}), flush=True)
    boundary(run, "app-build-saved")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--workspace", default=WORKSPACE)
    args = parser.parse_args()
    run, workspace = paths(args.run, args.workspace)
    setup_signals()
    try:
        initialize(run, workspace)
        build(run, workspace)
    except Paused as error:
        print(json.dumps({"status": "paused", "safeBoundary": str(error)}), flush=True)
    except Exception as error:
        failure(run, error)
        raise


if __name__ == "__main__":
    main()
