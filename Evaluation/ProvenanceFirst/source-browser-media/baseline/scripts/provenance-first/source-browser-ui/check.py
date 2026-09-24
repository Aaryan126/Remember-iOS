#!/usr/bin/env python3
"""Isolated app-source integration build. Never resolves a remote package or changes Git."""
import argparse
import fcntl
import hashlib
import json
import os
import plistlib
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

CODE = Path(__file__).resolve().parent
ROOT = CODE.parents[2]
RUN = ROOT / "Evaluation/ProvenanceFirst/runs/source-browser-ui"
WORK = ROOT / "Evaluation/ProvenanceFirst/source-browser-ui"
PROJECT = RUN / "project"
BUILD = RUN / "build"
SIMULATOR = "C530FCC2-DD67-4115-97D9-C4E34807EC57"
PHONE = "00008150-000A123A2EC0C01C"
BUNDLE = "SimpleStudio.Remember.SourceBrowserUI"
sys.path.insert(0, str(CODE.parent / "answer-support-screen"))
import sb_control as prior
import as_control as historical_accounting

GIB = 1024**3
CAP, RESERVE = 26 * GIB, 10 * GIB
RESOURCE_APPROVAL = WORK / "resource-amendment-26.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accounting(free, initial, scoped, external, reservation=0):
    if not all(type(value) is int and value >= 0 for value in (free, initial, scoped, external, reservation)):
        raise ValueError("invalid resource accounting")
    growth = max(scoped + external, max(0, initial - free))
    if free - reservation < RESERVE:
        raise SystemExit("10 GiB free-space reserve reached; preserve artifacts and stop")
    if growth + reservation > CAP:
        raise SystemExit("26 GiB growth cap reached; preserve original baseline and stop")
    return dict(freeBytes=free, scopedBytes=scoped, externalGrowthBytes=external,
                conservativeGrowthBytes=growth, capBytes=CAP, reserveBytes=RESERVE,
                reservationBytes=reservation)


def resource_snapshot():
    """Read-only measurement remains available even when a work gate is closed."""
    baseline_path = prior.PF / "resources.json"
    approval = prior.load(RESOURCE_APPROVAL)
    if (approval["capBytes"] != CAP or approval["reserveBytes"] != RESERVE
            or approval["baselineReset"] is not False
            or approval["baselineSHA256"] != digest(baseline_path)):
        raise ValueError("checkpoint resource approval or original baseline changed")
    baseline = prior.load(baseline_path)
    old = historical_accounting.ranking.history.previous
    free = shutil.disk_usage(prior.PF).free
    scoped = old.allocated(prior.PF) + old.allocated(old.CODE)
    external = sum(max(0, old.allocated(Path(path)) - start)
                   for path, start in baseline["externalBaselines"].items())
    growth = max(scoped + external, max(0, baseline["initialFreeBytes"] - free))
    return dict(freeBytes=free, initialFreeBytes=baseline["initialFreeBytes"],
        scopedBytes=scoped, externalGrowthBytes=external, conservativeGrowthBytes=growth,
        capBytes=CAP, reserveBytes=RESERVE, withinLimit=free >= RESERVE and growth <= CAP,
        approvalSHA256=digest(RESOURCE_APPROVAL))


def boundary(reservation=0):
    if (WORK / "PAUSE").exists():
        raise SystemExit("Paused before next integration unit")
    snapshot = resource_snapshot()
    result = accounting(snapshot["freeBytes"], snapshot["initialFreeBytes"],
        snapshot["scopedBytes"], snapshot["externalGrowthBytes"], reservation)
    result["approvalSHA256"] = snapshot["approvalSHA256"]
    return result


def copy_file(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists() or digest(source) != digest(destination):
        shutil.copy2(source, destination)


def verify_baseline():
    """Verify old results against exact archived inputs, never rewrite old receipts."""
    name = "Remember/Remember/ProjectView.swift"
    approval = prior.load(ROOT / "Evaluation/ProvenanceFirst/history-recovery/approval.json")
    expected = approval["preserved"][name]
    archived = WORK / "baseline/ProjectView.swift"
    if not archived.exists():
        original = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=ROOT)
        if hashlib.sha256(original).hexdigest() != expected:
            raise ValueError("HEAD is not the frozen screen; recover exact baseline before proceeding")
        archived.parent.mkdir(parents=True, exist_ok=True)
        with archived.open("xb") as stream: stream.write(original)
    if digest(archived) != expected:
        raise ValueError("archived screen differs from frozen input")
    # Importing prior controls loads this module. Override only its input-path
    # resolution for this one explicitly archived UI file, with the same old hash.
    modules = [module for module in list(sys.modules.values())
               if getattr(module, "__file__", None) == str(CODE.parent / "history/control.py")]
    if len(modules) != 1:
        raise ValueError("ambiguous historical verifier")
    module = modules[0]
    original_digest = module.digest
    def archived_digest(path):
        return original_digest(archived if Path(path) == ROOT / name else path)
    module.digest = archived_digest
    try:
        prior.verify_prior()
        prior.verify_frozen()
        for relative, expected_hash in prior.load(prior.WORK / "checkpoint-stop.json")["hashes"].items():
            if digest(prior.WORK / relative) != expected_hash:
                raise ValueError("previous stopped artifact changed: " + relative)
        saved = prior.load(ROOT / "Evaluation/ProvenanceFirst/source-browser/checkpoint-stop.json")
        for relative, expected_hash in saved["hashes"].items():
            if digest(ROOT / relative) != expected_hash:
                raise ValueError("foundation checkpoint changed: " + relative)
    finally:
        module.digest = original_digest
    return {"archivedInput": str(archived.relative_to(ROOT)), "originalPath": name,
            "frozenSHA256": expected, "currentSHA256": digest(ROOT / name),
            "historicalReceiptsModified": False, "foundationFilesVerified": len(saved["hashes"])}


def prepare(fixture=False):
    boundary()
    if RUN.resolve() != RUN:
        raise ValueError("redirected integration runs root")
    baseline = verify_baseline()
    RUN.mkdir(parents=True, exist_ok=True)
    bindings = {}
    for folder in ["Remember", "RememberTests", "RememberUITests", "RememberShareExtension", "Shared"]:
        for path in sorted((ROOT / "Remember" / folder).rglob("*")):
            if not path.is_file() or any(p in {".git", ".DS_Store"} for p in path.parts):
                continue
            copy_file(path, PROJECT / folder / path.relative_to(ROOT / "Remember" / folder))
            bindings[str(path.relative_to(ROOT))] = digest(path)
    dependency = ROOT / "Evaluation/ProvenanceFirst/runs/answer-support/native-dependency/GRDB"
    for path in sorted(dependency.rglob("*")):
        relative = path.relative_to(dependency)
        if any(p in {".git", ".build", ".swiftpm", ".DS_Store"} for p in relative.parts) or not path.is_file():
            continue
        copy_file(path, RUN / "dependency/GRDB" / relative)
    source = ROOT / "Remember/Remember.xcodeproj/project.pbxproj"
    project = source.read_text().replace("SimpleStudio.Remember", "SimpleStudio.Remember.SourceBrowserUI")
    project, count = re.subn(r'isa = XCRemoteSwiftPackageReference;\s*repositoryURL = "https://github.com/groue/GRDB.swift.git";\s*requirement = \{.*?\};',
        'isa = XCLocalSwiftPackageReference; relativePath = ' + json.dumps(str(RUN / "dependency/GRDB")) + ';', project, flags=re.S)
    if count != 1 or "repositoryURL" in project:
        raise ValueError("remote dependency not fully replaced")
    target = PROJECT / "Remember.xcodeproj/project.pbxproj"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(project)
    if fixture:
        copy_file(CODE / "FixtureApp.swift", PROJECT / "Remember/RememberApp.swift")
    receipt = {"fixtureLauncher": fixture, "sourceBindings": bindings, "baselineVerification": baseline,
               "originalProjectSHA256": digest(source), "generatedProjectSHA256": digest(target),
               "fixtureLauncherSHA256": digest(CODE / "FixtureApp.swift") if fixture else None,
               "bundle": "SimpleStudio.Remember.SourceBrowserUI", "sharedAppGroupsEnabled": False}
    (RUN / "preparation.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


def phone_products():
    products = BUILD / "Build/Products/Debug-iphoneos"
    apps = sorted(products.rglob("*.app")) + sorted(products.rglob("*.appex"))
    if not any(path.name == "Remember.app" for path in apps):
        raise ValueError("missing isolated phone app")
    bindings = {}
    for app in apps:
        info = plistlib.loads((app / "Info.plist").read_bytes())
        if not info["CFBundleIdentifier"].startswith(BUNDLE):
            raise ValueError("phone product is not an isolated diagnostic")
        signed = subprocess.run(["codesign", "-d", "--entitlements", ":-", str(app)],
                                capture_output=True, check=True)
        entitlements = plistlib.loads(signed.stdout)
        if entitlements.get("com.apple.security.application-groups"):
            raise ValueError("diagnostic must not access shared app groups")
        subprocess.run(["codesign", "--verify", "--strict", str(app)], check=True, capture_output=True)
        for name in ["Info.plist", "_CodeSignature/CodeResources", info["CFBundleExecutable"]]:
            path = app / name
            bindings[str(path.relative_to(RUN))] = digest(path)
    return bindings


def execute(action, only=None, phone=False):
    if not (RUN / "preparation.json").is_file():
        raise ValueError("prepare the isolated build first")
    preparation = prior.load(RUN / "preparation.json")
    if phone and not preparation["fixtureLauncher"]:
        raise ValueError("phone checks require the fictional launcher")
    if phone and action == "test-without-building":
        saved = prior.load(RUN / "phone-build.json")
        if saved["preparationSHA256"] != digest(RUN / "preparation.json") or saved["products"] != phone_products():
            raise ValueError("phone build binding changed; rebuild and verify before installation")
    before = boundary((1024 if phone and action == "build-for-testing" else
                       768 if action == "build" else 256) * 1024**2)
    if os.environ.get("SPI_BUILDER") == "1":
        raise ValueError("remote dependency mode is disallowed")
    command = ["xcodebuild", "-project", str(PROJECT / "Remember.xcodeproj"), "-scheme", "Remember",
               "-configuration", "Debug", "-destination", f"platform=iOS,id={PHONE}" if phone else f"platform=iOS Simulator,id={SIMULATOR}",
               "-derivedDataPath", str(BUILD), "-clonedSourcePackagesDirPath", str(BUILD / "SourcePackages"),
               "-disableAutomaticPackageResolution", "-skipPackageUpdates", "-parallel-testing-enabled", "NO",
               "-collect-test-diagnostics", "never",
               "CODE_SIGN_ENTITLEMENTS=", "COMPILER_INDEX_STORE_ENABLE=NO",
               "INFOPLIST_KEY_CFBundleDisplayName=Evidence Check",
               "DEBUG_INFORMATION_FORMAT=dwarf", "SWIFT_EMIT_LOC_STRINGS=NO",
               f"CLANG_MODULE_CACHE_PATH={BUILD / 'ModuleCache.noindex'}",
               f"SWIFT_MODULE_CACHE_PATH={BUILD / 'ModuleCache.noindex'}"]
    if phone:
        team = re.search(r'DEVELOPMENT_TEAM = ([A-Z0-9]+);',
                         (PROJECT / "Remember.xcodeproj/project.pbxproj").read_text())[1]
        command += ["CODE_SIGNING_ALLOWED=YES", f"DEVELOPMENT_TEAM={team}"]
        if action == "build-for-testing":
            # Standard development signing for the isolated bundle IDs only.
            command += ["-allowProvisioningUpdates"]
    else:
        command += ["CODE_SIGNING_ALLOWED=NO"]
    if only:
        command += ["-only-testing:" + name for name in (only if isinstance(only, list) else [only])]
    run_id = str(time.time_ns())
    runner_sha = digest(Path(__file__))
    if action in {"test", "test-without-building"}:
        command += ["-resultBundlePath", str(RUN / (run_id + ".xcresult"))]
    command += [action]
    with (RUN / (run_id + ".log")).open("w") as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + 1200
        try:
            while process.poll() is None:
                time.sleep(3)
                try:
                    boundary()
                    if time.monotonic() > deadline:
                        raise TimeoutError("bounded integration unit exceeded 20 minutes")
                except BaseException:
                    os.killpg(process.pid, signal.SIGTERM)
                    try: process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL); process.wait()
                    raise
        finally:
            receipt = {"command": command, "exitCode": process.poll(), "resourcesBefore": before,
                       "runnerSHA256": runner_sha,
                       "preparationSHA256": digest(RUN / "preparation.json"),
                       "preparation": json.loads((RUN / "preparation.json").read_text()),
                       "log": str(RUN / (run_id + ".log"))}
            (RUN / (run_id + ".json")).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    if process.returncode == 0 and phone and action == "build-for-testing":
        (RUN / "phone-build.json").write_text(json.dumps({
            "preparationSHA256": digest(RUN / "preparation.json"), "products": phone_products(),
            "buildReceipt": run_id + ".json", "sharedAppGroupsEnabled": False}, indent=2) + "\n")
    print(json.dumps({"exitCode": process.returncode, "log": receipt["log"], "resourcesAfter": boundary()}))
    raise SystemExit(process.returncode)


def save_hold():
    if not (WORK / "PAUSE").exists():
        raise ValueError("a stopped checkpoint needs its dispatch guard")
    artifacts = set(CODE.glob("*.py")) | set(WORK.glob("*.md")) | set(RUN.glob("*.json")) | set(RUN.glob("*.log"))
    artifacts.update([CODE / "FixtureApp.swift", WORK / "PAUSE", RESOURCE_APPROVAL,
                      ROOT / "docs/provenance-first.md"])
    preparation = prior.load(RUN / "preparation.json")
    artifacts.update(ROOT / name for name in preparation["sourceBindings"])
    value = {"complete": False, "reason": (WORK / "PAUSE").read_text().strip(),
             "baselineVerification": verify_baseline(), "resources": resource_snapshot(),
             "verificationStatus": "Consult individual receipts and STATUS.md; a saved hold is not completion",
             "hashes": {str(path.relative_to(ROOT)): digest(path) for path in sorted(artifacts)}}
    path = WORK / ("resource-hold-" + str(time.time_ns()) + ".json")
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write("\n")
    print(json.dumps({"complete": False, "checkpoint": str(path.relative_to(ROOT)), "filesBound": len(artifacts)}))


def checkpoint(args):
    baseline = verify_baseline()
    resources = boundary()
    summaries = {}
    artifacts = set()
    for role, run_id, count in [("unit", args.unit_run, 21), ("ui", args.ui_run, 3),
                                 ("phone", args.phone_run, 3), ("build", args.build_run, None)]:
        if not run_id or not re.fullmatch(r"[0-9]+", run_id):
            raise ValueError("provide all four successful run IDs")
        path = RUN / (run_id + ".json")
        receipt = prior.load(path)
        if receipt["exitCode"] != 0:
            raise ValueError("cannot complete with a failed run: " + role)
        for name, expected in receipt["preparation"]["sourceBindings"].items():
            if digest(ROOT / name) != expected:
                raise ValueError("verified app source changed since " + role + ": " + name)
        command = receipt["command"]
        if (role == "build" and (command[-1] != "build" or receipt["preparation"]["fixtureLauncher"])):
            raise ValueError("full production-entrypoint build is required")
        if role == "phone" and f"platform=iOS,id={PHONE}" not in command:
            raise ValueError("physical phone result is required")
        if count is not None:
            summary = json.loads(subprocess.check_output(["xcrun", "xcresulttool", "get", "test-results", "summary",
                "--path", str(RUN / (run_id + ".xcresult")), "--compact"]))
            if (summary["result"] != "Passed" or summary["passedTests"] != count
                    or summary["totalTestCount"] != count or summary["skippedTests"] != 0):
                raise ValueError("unexpected test result: " + role)
            summaries[role] = summary
        artifacts.update([path, RUN / (run_id + ".log")])
    phone_build = prior.load(RUN / "phone-build.json")
    if phone_build["products"] != phone_products():
        raise ValueError("signed phone products changed")
    artifacts.add(RUN / "phone-build.json")
    artifacts.update(CODE.glob("*.py"))
    artifacts.add(CODE / "FixtureApp.swift")
    artifacts.update(WORK.glob("*.md"))
    artifacts.add(RESOURCE_APPROVAL)
    artifacts.add(ROOT / "docs/provenance-first.md")
    artifacts.update(ROOT / name for name in receipt["preparation"]["sourceBindings"])
    value = {"complete": True, "stopForReview": True, "baselineVerification": baseline,
             "resources": resources, "summaries": summaries,
             "runs": {"unit": args.unit_run, "ui": args.ui_run, "phone": args.phone_run, "build": args.build_run},
             "hashes": {str(path.relative_to(ROOT)): digest(path) for path in sorted(artifacts)}}
    path = WORK / "checkpoint-stop.json"
    if path.exists():
        raise ValueError("checkpoint already exists; do not overwrite completion evidence")
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write("\n")
    print(json.dumps({"complete": True, "stopForReview": True, "filesBound": len(artifacts)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("unit", choices=["verify", "resources", "prepare", "prepare-fixture", "build", "test-unit", "test-ui", "test-entry", "build-phone", "test-phone", "checkpoint", "save-hold"])
    for name in ["unit", "ui", "phone", "build"]: parser.add_argument("--" + name + "-run")
    args = parser.parse_args()
    # Do not copy inputs or launch a second simulator/device operation mid-unit.
    if args.unit not in {"verify", "resources"}:
        lock = (WORK / "worker.lock").open("a+")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.unit == "verify":
        print(json.dumps(verify_baseline()))
    elif args.unit == "resources": print(json.dumps(resource_snapshot()))
    elif args.unit == "checkpoint": checkpoint(args)
    elif args.unit == "save-hold": save_hold()
    elif args.unit.startswith("prepare"):
        prepare(fixture=args.unit == "prepare-fixture")
    elif args.unit == "build": execute("build")
    elif args.unit == "test-unit": execute("test", ["RememberTests/SourceEvidenceBrowserTests",
        "RememberTests/ThreadPresentationTests", "RememberTests/AppearanceTests"])
    elif args.unit == "test-entry": execute("test", "RememberUITests/SourceEvidenceUITests/testEntryFromThreadsPreservesThreadFinder")
    elif args.unit == "build-phone": execute("build-for-testing", "RememberUITests/SourceEvidenceUITests", phone=True)
    elif args.unit == "test-phone": execute("test-without-building", "RememberUITests/SourceEvidenceUITests", phone=True)
    else: execute("test", "RememberUITests/SourceEvidenceUITests")


if __name__ == "__main__": main()
