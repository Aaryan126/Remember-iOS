#!/usr/bin/env python3
"""Bounded normal-app deployment. Private device artifacts never leave ignored runs."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import time

CODE = Path(__file__).resolve().parent
ROOT = CODE.parents[2]
WORK = ROOT / "Evaluation/ProvenanceFirst/main-app-deployment"
RUN = ROOT / "Evaluation/ProvenanceFirst/runs/main-app-deployment"
PHONE = "00008150-000A123A2EC0C01C"
BUNDLE = "SimpleStudio.Remember"
GROUP = "group.SimpleStudio.Remember"
TEAM = "397P48LWC5"
GIB = 1024**3
PROJECT = RUN / "project"
BUILD = RUN / "build"
APP = BUILD / "Build/Products/Debug-iphoneos/Remember.app"
DOMAINS = {"app": ("appDataContainer", BUNDLE), "group": ("appGroupDataContainer", GROUP)}
spec = importlib.util.spec_from_file_location("deployment_resource_guard", CODE.parent / "source-browser-ui/check.py")
guard = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = guard
spec.loader.exec_module(guard)
guard.CAP = 31 * GIB
guard.RESOURCE_APPROVAL = WORK / "resource-amendment-31.json"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def load(path):
    return json.loads(path.read_text())


def resources(reservation=0):
    if (WORK / "PAUSE").exists():
        raise RuntimeError("Paused; no next unit dispatched")
    snap = guard.resource_snapshot()
    if snap["freeBytes"] - reservation < 10 * GIB:
        raise RuntimeError("10 GiB free reserve would be exceeded")
    if snap["conservativeGrowthBytes"] + reservation > 31 * GIB:
        raise RuntimeError("31 GiB ceiling would be exceeded; preserve baseline")
    return snap


def run(command, label, reservation=0, timeout=120, critical=False):
    before = resources(reservation)
    run_id = str(time.time_ns())
    path = RUN / "operations" / (run_id + ".log")
    path.parent.mkdir(parents=True, exist_ok=True)
    failure = None
    with path.open("x") as log:
        worker = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + timeout
        try:
            while worker.poll() is None:
                time.sleep(3)
                try:
                    if time.monotonic() > deadline:
                        raise TimeoutError("bounded operation timed out")
                    resources()
                except BaseException as error:
                    # Let an installation finish atomically; the tool also has its
                    # own timeout. Never dispatch the next operation after this flag.
                    if critical and time.monotonic() <= deadline:
                        failure = str(error)
                        continue
                    raise
        except BaseException as error:
            failure = str(error)
            if worker.poll() is None:
                os.killpg(worker.pid, signal.SIGTERM)
                try:
                    worker.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(worker.pid, signal.SIGKILL)
                    worker.wait()
        finally:
            write(path.with_suffix(".json"), {"label": label, "command": command,
                "exitCode": worker.returncode, "failure": failure, "resourcesBefore": before,
                "resourcesAfter": guard.resource_snapshot(), "scriptSHA256": digest(Path(__file__))})
    if failure or worker.returncode:
        raise RuntimeError(f"{label} did not complete successfully; inspect private operation {run_id}")
    return run_id


def device(arguments):
    result = subprocess.run(["xcrun", "devicectl", "device", *arguments,
        "--device", PHONE, "--timeout", "60", "--json-output", "-", "--quiet"],
        capture_output=True, timeout=75, check=True)
    data = json.loads(result.stdout)
    if data["info"]["outcome"] != "success":
        raise RuntimeError("device read failed")
    return data["result"]


def installed():
    apps = device(["info", "apps", "--bundle-id", BUNDLE,
        "--include-app-group-identifiers", "--include-container-paths"])["apps"]
    if len(apps) != 1 or apps[0]["bundleIdentifier"] != BUNDLE or not apps[0]["containerAccessible"]:
        raise ValueError("normal installed app identity/access mismatch")
    if apps[0]["appGroupIdentifiers"] != [GROUP]:
        raise ValueError("unexpected app groups")
    return apps[0]


def inventory(domain):
    kind, identifier = DOMAINS[domain]
    return device(["info", "files", "--domain-type", kind, "--domain-identifier", identifier])["files"]


def file_inventory(entries):
    output = {}
    for entry in entries:
        name = entry["relativePath"]
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or entry["resources"]["isSymbolicLink"]:
            raise ValueError("unsafe device backup entry")
        if entry["resources"]["isDirectory"]:
            continue
        size = entry["metadata"]["size"]
        if type(size) is not int or size < 0 or name in output:
            raise ValueError("invalid/duplicate backup entry")
        output[name] = size
    return output


def stop_app():
    app = installed()
    prefix = app["url"].removeprefix("file://")
    for process in device(["info", "processes"])["runningProcesses"]:
        executable = process["executable"]
        if isinstance(executable, str) and executable.removeprefix("file://").startswith(prefix):
            device(["process", "terminate", "--pid", str(process["processIdentifier"])])
    return app


def verify_old():
    receipt = ROOT / "Evaluation/ProvenanceFirst/source-browser-media/checkpoint-stop.json"
    if (WORK / "baseline.json").exists() and load(WORK / "baseline.json")["previous"]["receiptSHA256"] != digest(receipt):
        raise ValueError("previous completion receipt changed")
    saved = load(receipt)
    if not saved["complete"] or not saved["stopForReview"]:
        raise ValueError("previous checkpoint incomplete")
    for name, expected in saved["hashes"].items():
        archived = WORK / "baseline/provenance-first.md"
        # The product overview can record deployment after its exact prior bytes
        # are archived. Research, sources, tests and other historical files stay frozen.
        path = archived if name == "docs/provenance-first.md" and archived.exists() else ROOT / name
        if digest(path) != expected:
            raise ValueError("completed media input changed: " + name)
    return {"receiptSHA256": digest(receipt), "filesVerified": len(saved["hashes"])}


def archive_overview():
    verified = verify_old()
    target = WORK / "baseline/provenance-first.md"
    if target.exists():
        raise ValueError("overview already archived")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "docs/provenance-first.md", target)
    write(WORK / "baseline.json", {"previous": verified, "originalPath": "docs/provenance-first.md",
        "archivedPath": str(target.relative_to(ROOT)), "sha256": digest(target)})
    print(json.dumps(verify_old()))


def backup(label):
    resources(600 * 1024**2)
    target = RUN / (label + "-" + str(time.time_ns()))
    target.mkdir(mode=0o700, parents=True)
    app = stop_app()
    write(target / "installed.json", app)
    combined = {}
    for domain, (kind, identifier) in DOMAINS.items():
        before = inventory(domain)
        expected = file_inventory(before)
        write(target / (domain + "-inventory-before.json"), before)
        resources(sum(expected.values()) + 64 * 1024**2)
        run(["xcrun", "devicectl", "device", "copy", "from", "--device", PHONE,
             "--domain-type", kind, "--domain-identifier", identifier, "--source", ".",
             "--destination", str(target / domain), "--timeout", "180", "--quiet"],
            "backup-" + domain, timeout=210)
        after = inventory(domain)
        write(target / (domain + "-inventory-after.json"), after)
        if expected != file_inventory(after):
            raise ValueError("device files changed during backup")
        local = {str(p.relative_to(target / domain)): p.stat().st_size
                 for p in (target / domain).rglob("*") if p.is_file()}
        if local != expected:
            raise ValueError("backup inventory mismatch; preserve incomplete copy")
        combined.update({domain + "/" + name: digest(target / domain / name) for name in local})
    write(target / "verified.json", {"complete": True, "hashes": combined,
        "fileCount": len(combined), "bytes": sum((target / p).stat().st_size for p in combined)})
    print(json.dumps({"backup": str(target.relative_to(ROOT)), "verifiedFiles": len(combined)}))


def inspect_backup():
    folders = sorted(p for p in RUN.glob("backup-*") if p.is_dir() and (p / "verified.json").exists())
    if not folders:
        raise ValueError("no completed backup")
    folder = folders[-1]
    saved = load(folder / "verified.json")
    for name, expected in saved["hashes"].items():
        if digest(folder / name) != expected:
            raise ValueError("backup integrity mismatch")
    inspection = folder / "inspection"
    inspection.mkdir(mode=0o700)
    database = folder / "app/Library/Application Support/Remember/remember.sqlite"
    for suffix in ["", "-wal", "-shm"]:
        source = Path(str(database) + suffix)
        if source.exists():
            shutil.copy2(source, inspection / source.name)
    with sqlite3.connect((inspection / "remember.sqlite").as_uri() + "?mode=ro", uri=True) as connection:
        if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("backup SQLite integrity check failed")
        migrations = sorted(row[0] for row in connection.execute("SELECT identifier FROM grdb_migrations"))
        expected_migrations = sorted(re.findall(r'registerMigration\("([^\"]+)"',
            (ROOT / "Remember/Remember/MemoryStore.swift").read_text() +
            (ROOT / "Remember/Remember/Provenance.swift").read_text()))
        if migrations != expected_migrations:
            raise ValueError("database migrations differ; stop for compatibility review")
        rows = connection.execute("SELECT * FROM memory ORDER BY id").fetchall()
        memory_hash = hashlib.sha256(json.dumps(rows, default=lambda value: value.hex()).encode()).hexdigest()
        state_counts = dict(connection.execute("SELECT state, count(*) FROM memory GROUP BY state"))
        kind_counts = dict(connection.execute("SELECT kind, count(*) FROM memory GROUP BY kind"))
        events = connection.execute("SELECT * FROM provenanceEvent ORDER BY sequence").fetchall()
        event_hash = hashlib.sha256(json.dumps(events, default=lambda value: value.hex()).encode()).hexdigest()
    preferences = folder / "app/Library/Preferences/SimpleStudio.Remember.plist"
    prefs = plistlib.loads(preferences.read_bytes()) if preferences.exists() else {}
    cloud = prefs.get("remember.project.cloudAssistance", False)
    if type(cloud) is not bool:
        raise ValueError("unexpected cloud preference type")
    evidence = {"backup": str(folder.relative_to(ROOT)), "sqliteIntegrityOK": True,
        "migrationsMatch": True, "migrationCount": len(migrations), "memoryCount": len(rows),
        "memoryRowsSHA256": memory_hash, "eventCount": len(events), "eventRowsSHA256": event_hash,
        "stateCounts": state_counts, "kindCounts": kind_counts, "cloudAssistanceEnabled": cloud}
    write(RUN / "backup-approved.json", evidence)
    # Keep first real launch narrowly bounded. Unprocessed captures or any videos
    # require a separate review of existing startup/requeue behavior, not a toggle.
    group_files = [p for p in saved["hashes"] if p.startswith("group/")]
    if not cloud and not group_files and not kind_counts.get("video", 0) and not any(state_counts.get(s, 0) for s in ["captured", "processing"]):
        write(RUN / "launch-approved.json", {"basis": "cloud disabled, no pending captures/shared inbox or video requeue",
            "backupApprovalSHA256": digest(RUN / "backup-approved.json"), "forceRegrouping": False,
            "note": "Existing local index/organizer startup still runs; verify ledger preservation afterward"})
    print(json.dumps({key: value for key, value in evidence.items() if key not in {"memoryRowsSHA256", "eventRowsSHA256"}}))
    print(json.dumps({"launchPreflightPassed": (RUN / "launch-approved.json").exists()}))


def prepare():
    resources(300 * 1024**2)
    baseline = verify_old()
    if (RUN / "preparation.json").exists():
        raise ValueError("preparation already saved; do not overwrite")
    bindings = {}
    for folder in ["Remember", "Shared", "RememberShareExtension", "RememberTests", "RememberUITests"]:
        for source in sorted((ROOT / "Remember" / folder).rglob("*")):
            if not source.is_file() or any(p in {".git", ".DS_Store"} for p in source.parts):
                continue
            target = PROJECT / folder / source.relative_to(ROOT / "Remember" / folder)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            bindings[str(source.relative_to(ROOT))] = digest(source)
    dependency = ROOT / "Evaluation/ProvenanceFirst/runs/source-browser-media/dependency/GRDB"
    if not (dependency / "Package.swift").is_file():
        raise ValueError("existing local dependency unavailable")
    source = ROOT / "Remember/Remember.xcodeproj/project.pbxproj"
    bindings[str(source.relative_to(ROOT))] = digest(source)
    project, count = re.subn(r'isa = XCRemoteSwiftPackageReference;\s*repositoryURL = "https://github.com/groue/GRDB.swift.git";\s*requirement = \{.*?\};',
        'isa = XCLocalSwiftPackageReference; relativePath = ' + json.dumps(str(dependency)) + ';', source.read_text(), flags=re.S)
    if count != 1 or "repositoryURL" in project or "SourceBrowserUI" in project:
        raise ValueError("normal project dependency conversion failed")
    target = PROJECT / "Remember.xcodeproj/project.pbxproj"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(project)
    shutil.copy2(CODE / "MainAppSmokeTests.swift", PROJECT / "RememberUITests/MainAppSmokeTests.swift")
    write(RUN / "preparation.json", {"sourceBindings": bindings, "baseline": baseline,
        "generatedProjectSHA256": digest(target), "normalEntrypoint": True,
        "smokeTestSHA256": digest(CODE / "MainAppSmokeTests.swift"),
        "dependencyBindings": {str(p.relative_to(dependency)): digest(p) for p in dependency.rglob("*")
             if p.is_file() and not any(n in {".git", ".build", ".swiftpm"} for n in p.relative_to(dependency).parts)}})
    print(json.dumps({"prepared": True, "normalBundle": BUNDLE, "sourceFiles": len(bindings)}))


def verify_sources():
    saved = load(RUN / "preparation.json")
    for name, expected in saved["sourceBindings"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("source changed after preparation: " + name)
        rel = Path(name).relative_to("Remember")
        if rel != Path("Remember.xcodeproj/project.pbxproj") and digest(PROJECT / rel) != expected:
            raise ValueError("copied source changed")
    if digest(PROJECT / "Remember.xcodeproj/project.pbxproj") != saved["generatedProjectSHA256"]:
        raise ValueError("generated project changed")
    if digest(PROJECT / "RememberUITests/MainAppSmokeTests.swift") != saved["smokeTestSHA256"]:
        raise ValueError("smoke test changed")
    dependency = ROOT / "Evaluation/ProvenanceFirst/runs/source-browser-media/dependency/GRDB"
    for name, expected in saved["dependencyBindings"].items():
        if digest(dependency / name) != expected:
            raise ValueError("local dependency changed")


def xcode(action):
    verify_sources()
    command = ["xcodebuild", "-project", str(PROJECT / "Remember.xcodeproj"), "-scheme", "Remember",
        "-configuration", "Debug", "-destination", "platform=iOS,id=" + PHONE,
        "-derivedDataPath", str(BUILD), "-disableAutomaticPackageResolution", "-skipPackageUpdates",
        "-parallel-testing-enabled", "NO", "-collect-test-diagnostics", "never",
        "COMPILER_INDEX_STORE_ENABLE=NO", "DEBUG_INFORMATION_FORMAT=dwarf", "SWIFT_EMIT_LOC_STRINGS=NO",
        "CODE_SIGNING_ALLOWED=YES", "DEVELOPMENT_TEAM=" + TEAM,
        "CLANG_MODULE_CACHE_PATH=" + str(BUILD / "ModuleCache.noindex"),
        "SWIFT_MODULE_CACHE_PATH=" + str(BUILD / "ModuleCache.noindex"),
        "-only-testing:RememberUITests/MainAppSmokeTests"]
    if action == "build-for-testing":
        command += ["-allowProvisioningUpdates"]
    else:
        verify_signed()
        command += ["-resultBundlePath", str(RUN / ("smoke-" + str(time.time_ns()) + ".xcresult"))]
        require_backup()
        if not (RUN / "launch-approved.json").exists():
            raise ValueError("pending-work/cloud preflight approval missing")
    run_id = run(command + [action], action, reservation=(1536 if action == "build-for-testing" else 256) * 1024**2, timeout=1200)
    if action == "build-for-testing":
        signed = signed_products()
        write(RUN / "signed-build.json", {"operation": run_id, "products": signed,
            "preparationSHA256": digest(RUN / "preparation.json")})
    print(json.dumps({"action": action, "operation": run_id, "passed": True}))


def signed_products():
    output = {}
    for path, bundle in [(APP, BUNDLE), (APP / "PlugIns/RememberShareExtension.appex", BUNDLE + ".RememberShareExtension")]:
        info = plistlib.loads((path / "Info.plist").read_bytes())
        if info["CFBundleIdentifier"] != bundle:
            raise ValueError("normal product identity mismatch")
        subprocess.run(["codesign", "--verify", "--strict", str(path)], check=True, capture_output=True)
        result = subprocess.run(["codesign", "-d", "--entitlements", ":-", str(path)], check=True, capture_output=True)
        entitlements = plistlib.loads(result.stdout)
        if entitlements.get("com.apple.developer.team-identifier") != TEAM or entitlements.get("application-identifier") != TEAM + "." + bundle:
            raise ValueError("signing team mismatch")
        if entitlements.get("com.apple.security.application-groups") != [GROUP]:
            raise ValueError("shared inbox entitlement mismatch")
        for key in ["Info.plist", "_CodeSignature/CodeResources", info["CFBundleExecutable"]]:
            output[str((path / key).relative_to(RUN))] = digest(path / key)
    if not list(APP.rglob("D3Matcher.mlmodelc")):
        raise ValueError("trained local model not bundled")
    return output


def verify_signed():
    saved = load(RUN / "signed-build.json")
    if saved["preparationSHA256"] != digest(RUN / "preparation.json") or saved["products"] != signed_products():
        raise ValueError("signed build binding changed")
    verify_sources()


def refresh_smoke():
    # A harness-only correction gets its own preparation revision. Never alter
    # production inputs or silently reuse products built from a different test.
    verify_sources()
    old = RUN / "preparation.json"
    previous_hash = digest(old)
    saved = load(old)
    old.rename(RUN / ("preparation-before-smoke-" + str(time.time_ns()) + ".json"))
    shutil.copy2(CODE / "MainAppSmokeTests.swift", PROJECT / "RememberUITests/MainAppSmokeTests.swift")
    saved["smokeTestSHA256"] = digest(CODE / "MainAppSmokeTests.swift")
    saved["previousPreparationSHA256"] = previous_hash
    write(old, saved)
    signed = RUN / "signed-build.json"
    if signed.exists():
        signed.rename(RUN / ("signed-build-before-smoke-" + str(time.time_ns()) + ".json"))
    print("Smoke harness refreshed; signed rebuild required")


def require_backup():
    receipt = load(RUN / "backup-approved.json")
    folder = ROOT / receipt["backup"]
    verified = load(folder / "verified.json")
    if not verified["complete"] or not receipt["sqliteIntegrityOK"] or not receipt["migrationsMatch"]:
        raise ValueError("verified backup/compatibility missing")
    for name, expected in verified["hashes"].items():
        if digest(folder / name) != expected:
            raise ValueError("backup changed")
    return folder


def install():
    verify_signed()
    backup_folder = require_backup()
    app = stop_app()
    for domain in DOMAINS:
        before = load(backup_folder / (domain + "-inventory-after.json"))
        current = inventory(domain)
        if file_inventory(before) != file_inventory(current):
            raise ValueError("device inventory changed since backup; take a new backup before installation")
        stamps = lambda entries: {p["relativePath"]: p["metadata"]["lastModDate"]
                                  for p in entries if not p["resources"]["isDirectory"]}
        if stamps(before) != stamps(current):
            raise ValueError("device files modified since backup; take a new backup before installation")
    run_id = run(["xcrun", "devicectl", "device", "install", "app", "--device", PHONE,
        str(APP), "--timeout", "180", "--quiet"], "install-in-place", reservation=128 * 1024**2, timeout=210, critical=True)
    after = installed()
    write(RUN / "installation.json", {"operation": run_id, "before": app, "after": after,
        "uninstalled": False, "signedBuildSHA256": digest(RUN / "signed-build.json")})
    print(json.dumps({"installed": BUNDLE, "operation": run_id, "uninstalled": False}))


def compare_after():
    before = require_backup()
    folders = sorted(p for p in RUN.glob("post-install-*") if p.is_dir() and (p / "verified.json").exists())
    if not folders:
        raise ValueError("no verified post-install snapshot")
    after = folders[-1]
    old_manifest = load(before / "verified.json")["hashes"]
    new_manifest = load(after / "verified.json")["hashes"]
    for name, expected in new_manifest.items():
        if digest(after / name) != expected:
            raise ValueError("post-install snapshot changed")
    original_names = [name for name in old_manifest if name.startswith("app/Library/Application Support/Remember/Originals/")]
    originals_match = all(new_manifest.get(name) == old_manifest[name] for name in original_names)
    inspection = after / "inspection"
    inspection.mkdir(mode=0o700)
    database = after / "app/Library/Application Support/Remember/remember.sqlite"
    for suffix in ["", "-wal", "-shm"]:
        source = Path(str(database) + suffix)
        if source.exists():
            shutil.copy2(source, inspection / source.name)
    approved = load(RUN / "backup-approved.json")
    with sqlite3.connect((inspection / "remember.sqlite").as_uri() + "?mode=ro", uri=True) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        memories = connection.execute("SELECT * FROM memory ORDER BY id").fetchall()
        events = connection.execute("SELECT * FROM provenanceEvent ORDER BY sequence").fetchall()
        hash_rows = lambda rows: hashlib.sha256(json.dumps(rows, default=lambda value: value.hex()).encode()).hexdigest()
        same_memories = hash_rows(memories) == approved["memoryRowsSHA256"]
        prefix_preserved = hash_rows(events[:approved["eventCount"]]) == approved["eventRowsSHA256"]
    result = {"backup": str(before.relative_to(ROOT)), "postSnapshot": str(after.relative_to(ROOT)),
        "sqliteIntegrityOK": integrity, "originalFilesChecked": len(original_names),
        "allOriginalBytesUnchanged": originals_match, "allMemoryRowsUnchanged": same_memories,
        "memoryCountBefore": approved["memoryCount"], "memoryCountAfter": len(memories),
        "historicalEventsUnchanged": prefix_preserved, "eventCountBefore": approved["eventCount"],
        "eventCountAfter": len(events)}
    write(RUN / "preservation.json", result)
    print(json.dumps(result))
    if not all([integrity, originals_match, same_memories, prefix_preserved]):
        raise ValueError("preservation differs; review before handoff, never auto-restore")


def finish():
    previous = verify_old()
    verify_signed()
    require_backup()
    preservation = load(RUN / "preservation.json")
    if not all(preservation[key] for key in ["sqliteIntegrityOK", "allOriginalBytesUnchanged",
            "allMemoryRowsUnchanged", "historicalEventsUnchanged"]):
        raise ValueError("preservation gate failed")
    installation = load(RUN / "installation.json")
    if installation["uninstalled"] or installation["after"]["bundleIdentifier"] != BUNDLE:
        raise ValueError("normal in-place installation not verified")
    suites = sorted(RUN.glob("smoke-*.xcresult"))
    summaries = []
    for suite in suites:
        summary = json.loads(subprocess.check_output(["xcrun", "xcresulttool", "get", "test-results",
            "summary", "--path", str(suite), "--compact"]))
        summaries.append((suite.name, summary))
    if not summaries:
        raise ValueError("missing smoke result")
    name, summary = summaries[-1]
    if summary["result"] != "Passed" or summary["totalTestCount"] != 1 or summary["passedTests"] != 1 or summary["skippedTests"]:
        raise ValueError("normal-app smoke did not pass")
    artifacts = set(CODE.glob("*.py")) | set(CODE.glob("*.swift")) | set(WORK.glob("*.md"))
    artifacts.update([WORK / "resource-amendment-31.json", WORK / "baseline.json", WORK / "baseline/provenance-first.md",
        ROOT / "docs/provenance-first.md", RUN / "preparation.json", RUN / "signed-build.json",
        RUN / "backup-approved.json", RUN / "launch-approved.json", RUN / "installation.json", RUN / "preservation.json"])
    artifacts.update(RUN / "operations" / p.name for p in (RUN / "operations").glob("*.json"))
    artifacts.update(RUN / "operations" / p.name for p in (RUN / "operations").glob("*.log"))
    artifacts.update(ROOT / p for p in load(RUN / "preparation.json")["sourceBindings"])
    for folder in [ROOT / preservation["backup"], ROOT / preservation["postSnapshot"]]:
        artifacts.add(folder / "verified.json")
    record = {"complete": True, "stopForReview": True, "normalBundle": BUNDLE, "previous": previous,
        "resources": resources(), "smokeResult": name, "smokeSummary": summary,
        "preservation": preservation, "uninstalled": False,
        "hashes": {str(p.relative_to(ROOT)): digest(p) for p in sorted(artifacts)}}
    write(WORK / "checkpoint-stop.json", record)
    print(json.dumps({"complete": True, "installed": BUNDLE, "stopForReview": True, "filesBound": len(artifacts)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["resources", "verify-old", "archive-overview", "backup", "inspect-backup", "post-backup", "compare-after", "prepare", "refresh-smoke", "build", "verify-signed", "install", "smoke", "finish"])
    args = parser.parse_args()
    os.umask(0o077)
    RUN.mkdir(mode=0o700, parents=True, exist_ok=True)
    RUN.chmod(0o700)
    if args.action == "resources":
        print(json.dumps(guard.resource_snapshot()))
        return
    with (WORK / "worker.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == "verify-old": print(json.dumps(verify_old()))
        elif args.action == "archive-overview": archive_overview()
        elif args.action == "backup": backup("backup")
        elif args.action == "inspect-backup": inspect_backup()
        elif args.action == "post-backup": backup("post-install")
        elif args.action == "compare-after": compare_after()
        elif args.action == "prepare": prepare()
        elif args.action == "refresh-smoke": refresh_smoke()
        elif args.action == "build": xcode("build-for-testing")
        elif args.action == "verify-signed": verify_signed(); print("Signed normal app and share extension verified")
        elif args.action == "install": install()
        elif args.action == "smoke": xcode("test-without-building")
        elif args.action == "finish": finish()


if __name__ == "__main__": main()
