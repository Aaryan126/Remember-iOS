#!/usr/bin/env python3
"""Prepare an isolated, local-dependency ledger probe; never build or launch it."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
OLD_TOOL = REPOSITORY / "scripts/organization-diagnostics/ledger/prepare_project.py"
SPEC = importlib.util.spec_from_file_location("original_ledger_preparation", OLD_TOOL)
ORIGINAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORIGINAL)

# Keep the established bindings and include their current compile dependencies.
# None of these services is constructed by the replay entry point; no model
# resources, media originals, credentials or production app entry point are bundled.
PRODUCTION_SOURCES = ORIGINAL.PRODUCTION_SOURCES + (
    "D3ProjectOrganizer.swift", "D3Features.swift", "D3PairMatcher.swift",
    "D3OrganizationPolicy.swift", "D3Tokenizer.swift", "VideoContentExtractor.swift",
    "OnDeviceSpeechTranscriber.swift", "LocalVideoPlayerView.swift", "RememberAppearance.swift",
)
HARNESS_SOURCES = ("OrganizationDiagnosticReplay.swift", "DiagnosticInvariants.swift")
BUNDLE_ID = "SimpleStudio.Remember.ProvenanceFirstProbe"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runs_root() -> Path:
    # Do not resolve an escaped runs symlink into a different authorized workspace.
    expected = REPOSITORY.resolve() / "Evaluation/ProvenanceFirst/runs"
    if expected.resolve() != expected:
        raise ValueError("runs workspace must not be redirected by symlinks")
    return expected


def checked_output(output: Path) -> Path:
    allowed = runs_root()
    output = output.resolve()
    if output == allowed or not output.is_relative_to(allowed):
        raise ValueError("project output must be beneath Evaluation/ProvenanceFirst/runs")
    if output.exists():
        raise ValueError("project output already exists; choose a new directory")
    return output


def launcher_text(allowed: Path) -> str:
    if any(ord(character) < 32 for character in str(allowed)):
        raise ValueError("workspace path contains control characters")
    return r'''import Foundation
import SwiftUI

@main
struct ProvenanceFirstReplayApp: App {
    var body: some Scene {
        WindowGroup {
            Text("Fictional provenance-first ledger proof")
                .task { await execute() }
        }
    }

    private func execute() async {
        let arguments = ProcessInfo.processInfo.arguments
        func option(_ key: String) -> String? {
            guard let index = arguments.firstIndex(of: key), index + 1 < arguments.count else { return nil }
            return arguments[index + 1]
        }
        func beneath(_ value: URL, _ root: URL) -> Bool {
            let path = value.standardizedFileURL.resolvingSymlinksInPath().path
            let base = root.standardizedFileURL.resolvingSymlinksInPath().path
            return path.hasPrefix(base + "/")
        }
        do {
            guard let inputPath = option("--input"), let outputPath = option("--output"),
                  let bindings = Bundle.main.url(forResource: "bindings", withExtension: "json") else {
                throw DiagnosticFailure(description: "--input, --output and bundled bindings.json are required")
            }
            let input = URL(fileURLWithPath: inputPath).standardizedFileURL.resolvingSymlinksInPath()
            let output = URL(fileURLWithPath: outputPath).standardizedFileURL.resolvingSymlinksInPath()
            let workspace = URL(fileURLWithPath: WORKSPACE_PATH).standardizedFileURL
            try diagnosticRequire(workspace.resolvingSymlinksInPath().path == workspace.path,
                "runs workspace must not be redirected by symlinks")
            let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                .resolvingSymlinksInPath()
            let privateInputs = documents.appendingPathComponent("ProvenanceFirst")
            try diagnosticRequire(privateInputs.resolvingSymlinksInPath().path == privateInputs.path,
                "private inputs must not be redirected by symlinks")
            try diagnosticRequire(beneath(input, workspace) || beneath(input, privateInputs),
                "input must be beneath this workspace or the probe's private inputs")
            try diagnosticRequire(beneath(output, workspace), "output must be beneath this runs workspace")
            var maxRuns: Int?
            if arguments.contains("--max-runs") {
                guard let raw = option("--max-runs"), let parsed = Int(raw), parsed > 0 else {
                    throw DiagnosticFailure(description: "--max-runs must be positive")
                }
                maxRuns = parsed
            }
            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
            if arguments.contains("--invariants") { try await DiagnosticInvariants.run(output: output) }
            try await DiagnosticReplay.run(input: input, output: output, bindings: bindings, maximumRuns: maxRuns)
            print("LEDGER_REPLAY_FINISHED")
            exit(0)
        } catch {
            print("LEDGER_REPLAY_FAILED: \(error)")
            exit(1)
        }
    }
}
'''.replace("WORKSPACE_PATH", json.dumps(str(allowed), ensure_ascii=False))


def project_text(package: Path) -> str:
    return ORIGINAL.project_text(package).replace(
        "OrganizationLedgerProbe", "ProvenanceFirstProbe"
    ).replace("Ledger Diagnostics", "Provenance-first Proof")


def package_bindings(package: Path) -> dict[str, str]:
    if not (package / "Package.swift").is_file() or not all(
        (package / directory).is_dir() for directory in ("GRDB", "Sources/GRDBSQLite")
    ):
        raise ValueError("an existing local GRDB package with sources is required; no downloads allowed")
    result = {}
    for path in sorted(package.rglob("*")):
        relative = path.relative_to(package)
        if not (relative.parts[0] in {"Package.swift", "GRDB"}
                or relative == Path("Sources")
                or relative.parts[:2] == ("Sources", "GRDBSQLite")):
            continue
        if path.is_symlink() and not path.resolve().is_relative_to(package):
            raise ValueError("GRDB source symlink escapes the local package")
        if path.is_file():
            result[str(relative)] = digest(path)
    if not any(name.endswith(".swift") and name.startswith("GRDB/") for name in result):
        raise ValueError("local GRDB package has no Swift sources")
    if "Sources/GRDBSQLite/module.modulemap" not in result:
        raise ValueError("local GRDB package is missing its SQLite module map")
    return result


def prepare(output: Path, package: Path) -> dict:
    output = checked_output(output)
    if os.environ.get("SPI_BUILDER") == "1":
        raise ValueError("SPI_BUILDER enables a remote dependency; unset it first")
    package = package.resolve()
    grdb = package_bindings(package)
    production = [REPOSITORY / "Remember/Remember" / name for name in PRODUCTION_SOURCES]
    production.append(REPOSITORY / "Remember/Shared/CaptureInbox.swift")
    ledger = REPOSITORY / "scripts/organization-diagnostics/ledger"
    harness = [ledger / name for name in HARNESS_SOURCES]
    tools = [ledger / "prepare_project.py", ledger / "DiagnosticReplayApp.swift",
             REPOSITORY / "scripts/provenance-first/prepare_ledger.py"]
    for path in production + harness + tools:
        if not path.is_file():
            raise ValueError(f"missing source binding: {path}")
    launcher = launcher_text(runs_root())
    project = project_text(package)
    bindings = {
        "schemaVersion": 1,
        "experiment": "provenance-first-ideal-label-v1",
        "bundleIdentifier": BUNDLE_ID,
        "production": {str(p.relative_to(REPOSITORY)): digest(p) for p in production},
        "harness": {str(p.relative_to(REPOSITORY)): digest(p) for p in harness},
        "tooling": {str(p.relative_to(REPOSITORY)): digest(p) for p in tools},
        "generated": {
            "Sources/ProvenanceFirstReplayApp.swift": hashlib.sha256(launcher.encode()).hexdigest(),
            "ProvenanceFirstProbe.xcodeproj/project.pbxproj": hashlib.sha256(project.encode()).hexdigest(),
        },
        "grdb": grdb,
    }
    # Every validation above precedes the first write. Existing projects are never overwritten.
    output.mkdir(parents=True, exist_ok=False)
    sources = output / "Sources"
    sources.mkdir()
    for path in production + harness:
        (sources / path.name).symlink_to(path)
    (sources / "ProvenanceFirstReplayApp.swift").write_text(launcher)
    (sources / "bindings.json").write_text(json.dumps(bindings, sort_keys=True, indent=2) + "\n")
    project_path = output / "ProvenanceFirstProbe.xcodeproj"
    project_path.mkdir()
    (project_path / "project.pbxproj").write_text(project)
    return {"project": str(project_path), "bundleIdentifier": BUNDLE_ID,
            "bindingsSHA256": digest(sources / "bindings.json"),
            "productionSourceCount": len(production), "harnessSourceCount": len(harness) + 1}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--grdb-package", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        result = prepare(arguments.output, arguments.grdb_package)
    except ValueError as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
