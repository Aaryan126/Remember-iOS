"""Prepare/build a newly scoped launcher without changing frozen replay sources."""
import hashlib
import json
import os
from pathlib import Path
import re

import as_control as c
import native_driver as old

NAME = "AnswerSupportHistoryProbe"
BUNDLE = "SimpleStudio.Remember.AnswerSupportHistoryProbe"
PROJECT = c.RUN / "native-project"
DERIVED = c.RUN / "native-build"
PACKAGE = c.RUN / "native-dependency/GRDB"
APP = DERIVED / f"Build/Products/Debug-iphonesimulator/{NAME}.app"
BINDINGS = PROJECT / "Sources/bindings.json"
ESTIMATED_ADDITIONAL_BYTES = 512 * 1024**2


def byte_hash(data): return hashlib.sha256(data).hexdigest()


def publish_bytes(path, data):
    path = c.checked(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): c.require(path.read_bytes() == data, "prepared file changed")
    else:
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())


def original_package():
    project = (old.PROJECT / "HistoryRecoveryProbe.xcodeproj/project.pbxproj").read_text()
    match = re.search(r'relativePath = ("[^\n]+?");', project)
    c.require(match is not None, "frozen local GRDB path unavailable")
    return Path(json.loads(match.group(1))).resolve()


def launcher_text():
    source = old.PROJECT / "Sources/HistoryRecoveryApp.swift"
    text = source.read_text()
    c.require(text.count(str(old.c.RUN)) == 1, "old launcher workspace identity changed")
    return (text.replace(str(old.c.RUN), str(c.RUN))
            .replace("HistoryRecoveryApp", "AnswerSupportHistoryApp")
            .replace('appendingPathComponent("HistoryRecovery")', 'appendingPathComponent("AnswerSupportHistory")')
            .replace("HISTORY_REPLAY_", "ANSWER_HISTORY_REPLAY_")
            .replace("Fictional history recovery proof", "Fictional answer-support evidence proof"))


def source_files():
    old.verify_build()
    c.require(os.environ.get("SPI_BUILDER") != "1", "remote dependency environment disallowed")
    c.require(os.environ.get("SQLITE_ENABLE_PREUPDATE_HOOK") != "1", "GRDB compile environment differs")
    previous = c.load(old.BINDINGS)
    package = original_package()
    files = {}
    for category in ("production", "harness"):
        for name, expected in previous[category].items():
            path = c.ROOT / name
            c.require(c.digest(path) == expected, "frozen native source differs")
            destination = PROJECT / "Sources" / path.name
            c.require(destination not in files, "duplicate native basename")
            files[destination] = path.read_bytes()
    # Copy the already-present package locally so even package-manager metadata
    # cannot modify the prior experiment's dependency directory. Never copy Git.
    for path in sorted(package.rglob("*")):
        relative = path.relative_to(package)
        if any(part in {".git", ".build", ".swiftpm"} for part in relative.parts): continue
        if path.is_file():
            c.require(path.resolve().is_relative_to(package), "dependency symlink escape")
            files[PACKAGE / relative] = path.read_bytes()
    for name, expected in previous["grdb"].items():
        c.require(byte_hash(files[PACKAGE / name]) == expected, "copied GRDB binding differs")
    text = (old.PROJECT / "HistoryRecoveryProbe.xcodeproj/project.pbxproj").read_text()
    text = text.replace("HistoryRecoveryProbe", NAME).replace("History Recovery", "Answer Support History")
    text = text.replace(json.dumps(str(package)), json.dumps(str(PACKAGE)))
    c.require(str(package) not in text and BUNDLE in text, "project did not isolate dependency/bundle")
    files[PROJECT / f"{NAME}.xcodeproj/project.pbxproj"] = text.encode()
    files[PROJECT / "Sources/AnswerSupportHistoryApp.swift"] = launcher_text().encode()
    return files


def prepare():
    c.boundary()
    files = source_files()
    bindings = dict(schemaVersion=1, experiment="answer-support-native-v2", bundleIdentifier=BUNDLE,
                    previousBindingsSHA256=c.digest(old.BINDINGS), previousBuildSHA256=c.digest(old.c.WORK / "native-build.json"),
                    files={str(path.relative_to(c.ROOT)): byte_hash(data) for path, data in sorted(files.items())})
    c.publish(c.WORK / "native-preparation-v2.json", bindings)
    for path, data in files.items(): publish_bytes(path, data)
    c.publish(BINDINGS, bindings)
    return bindings


def verify_preparation():
    value = c.load(BINDINGS)
    c.require(value == c.load(c.WORK / "native-preparation-v2.json"), "native preparation seal changed")
    old.verify_build()
    c.require(value["previousBindingsSHA256"] == c.digest(old.BINDINGS)
              and value["previousBuildSHA256"] == c.digest(old.c.WORK / "native-build.json"), "old native identity changed")
    for name, expected in value["files"].items():
        path = c.checked(c.ROOT / name)
        c.require(c.digest(path) == expected, "prepared native/dependency source changed")
    c.require((PROJECT / "Sources/AnswerSupportHistoryApp.swift").read_text() == launcher_text(),
              "launcher differs from declared narrow scope change")
    return value


def build():
    from as_native import execute
    receipt = c.WORK / "native-build-v2.json"
    if receipt.exists(): return verify_build()
    resources = c.boundary()
    c.require(resources["conservativeGrowthBytes"] + ESTIMATED_ADDITIONAL_BYTES <= c.CAP,
              "native build needs estimated 512 MiB headroom; stop, do not increase cap")
    prepare()
    verify_preparation()
    reservation = c.WORK / "native-build-v2-reserved.json"
    c.require(not reservation.exists(), "unresolved native build; inspect before retry")
    command = ["xcodebuild", "-project", str(PROJECT / f"{NAME}.xcodeproj"), "-scheme", NAME,
               "-configuration", "Debug", "-sdk", "iphonesimulator", "-destination", f"id={old.DEVICE}",
               "-derivedDataPath", str(DERIVED), "-clonedSourcePackagesDirPath", str(DERIVED / "SourcePackages"),
               "-disableAutomaticPackageResolution", "-skipPackageUpdates", "CODE_SIGNING_ALLOWED=NO",
               f"CLANG_MODULE_CACHE_PATH={DERIVED / 'ModuleCache.noindex'}",
               f"SWIFT_MODULE_CACHE_PATH={DERIVED / 'ModuleCache.noindex'}", "build"]
    before = dict(bindingsSHA256=c.digest(BINDINGS), command=command,
                  tooling={str(path.relative_to(c.ROOT)): c.digest(path)
                           for path in (Path(__file__), c.CODE / "as_native.py", c.CODE / "as_control.py")},
                  estimatedAdditionalBytes=ESTIMATED_ADDITIONAL_BYTES, resources=resources)
    c.publish(reservation, before)
    execute(command, "native-build-v2", timeout=600)
    verify_preparation()
    c.require(before["bindingsSHA256"] == c.digest(BINDINGS)
              and all(c.digest(c.ROOT / name) == expected for name, expected in before["tooling"].items()),
              "native source/tooling changed during build")
    c.require(c.digest(APP / "bindings.json") == c.digest(BINDINGS), "bundled bindings mismatch")
    result = dict(executableSHA256=c.digest(APP / NAME), bindingsSHA256=c.digest(BINDINGS),
                  simulator=old.DEVICE, bundle=BUNDLE, rebuilt=True, installed=False,
                  reservationSHA256=c.digest(reservation), command=command)
    c.publish(receipt, result)
    return result


def verify_build():
    verify_preparation()
    row = c.load(c.WORK / "native-build-v2.json")
    reserved = c.load(c.WORK / "native-build-v2-reserved.json")
    c.require(row["reservationSHA256"] == c.digest(c.WORK / "native-build-v2-reserved.json")
              and row["executableSHA256"] == c.digest(APP / NAME)
              and row["bindingsSHA256"] == c.digest(BINDINGS) == c.digest(APP / "bindings.json")
              and all(c.digest(c.ROOT / name) == expected for name, expected in reserved["tooling"].items()),
              "native v2 build identity changed")
    return row
