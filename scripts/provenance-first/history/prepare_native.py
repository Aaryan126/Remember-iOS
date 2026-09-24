#!/usr/bin/env python3
"""Prepare history-only local simulator bindings; never build, download or launch."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("history_ledger_preparation", HERE.parent / "prepare_ledger.py")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)
REPOSITORY = BASE.REPOSITORY
BUNDLE_ID = "SimpleStudio.Remember.HistoryRecoveryProbe"


def runs_root() -> Path:
    root = BASE.runs_root() / "history-recovery"
    if root.resolve() != root:
        raise ValueError("history runs workspace must not be redirected by symlinks")
    return root


def launcher_text() -> str:
    return (BASE.launcher_text(runs_root())
            .replace("ProvenanceFirstReplayApp", "HistoryRecoveryApp")
            .replace('appendingPathComponent("ProvenanceFirst")', 'appendingPathComponent("HistoryRecovery")')
            .replace("DiagnosticInvariants.run(output: output)", "HistoryInvariants.runBound(output: output, input: input, bindings: bindings)")
            .replace("DiagnosticReplay.run(input:", "HistoryProbe.run(input:")
            .replace("LEDGER_REPLAY_", "HISTORY_REPLAY_")
            .replace("Fictional provenance-first ledger proof", "Fictional history recovery proof"))


def prepare(output: Path, package: Path) -> dict:
    output = output.resolve()
    if output == runs_root() or not output.is_relative_to(runs_root()) or output.exists():
        raise ValueError("new project output must be beneath history-recovery runs")
    if os.environ.get("SPI_BUILDER") == "1":
        raise ValueError("SPI_BUILDER enables remote dependency resolution")
    package = package.resolve()
    grdb = BASE.package_bindings(package)
    production = [REPOSITORY / "Remember/Remember" / name for name in BASE.PRODUCTION_SOURCES]
    production.append(REPOSITORY / "Remember/Shared/CaptureInbox.swift")
    harness = [REPOSITORY / "scripts/organization-diagnostics/ledger/OrganizationDiagnosticReplay.swift"]
    harness.append(REPOSITORY / "scripts/organization-diagnostics/ledger/DiagnosticInvariants.swift")
    harness += [HERE / name for name in ("HistoryIndex.swift", "HistoryProbe.swift", "HistoryInvariants.swift")]
    tooling = [Path(BASE.__file__), BASE.OLD_TOOL, Path(__file__).resolve()]
    for path in production + harness + tooling:
        if not path.is_file():
            raise ValueError(f"missing source binding: {path}")
    launcher = launcher_text()
    project = BASE.ORIGINAL.project_text(package).replace("OrganizationLedgerProbe", "HistoryRecoveryProbe").replace(
        "Ledger Diagnostics", "History Recovery")
    bindings = {
        "schemaVersion": 1, "experiment": "history-recovery-checkpoint1-v1", "bundleIdentifier": BUNDLE_ID,
        "production": {str(p.relative_to(REPOSITORY)): BASE.digest(p) for p in production},
        "harness": {str(p.relative_to(REPOSITORY)): BASE.digest(p) for p in harness},
        "tooling": {str(p.relative_to(REPOSITORY)): BASE.digest(p) for p in tooling},
        "generated": {
            "Sources/HistoryRecoveryApp.swift": BASE.hashlib.sha256(launcher.encode()).hexdigest(),
            "HistoryRecoveryProbe.xcodeproj/project.pbxproj": BASE.hashlib.sha256(project.encode()).hexdigest(),
        }, "grdb": grdb,
    }
    output.mkdir(parents=True, exist_ok=False)
    sources = output / "Sources"
    sources.mkdir()
    for path in production + harness:
        (sources / path.name).symlink_to(path)
    (sources / "HistoryRecoveryApp.swift").write_text(launcher)
    (sources / "bindings.json").write_text(json.dumps(bindings, sort_keys=True, indent=2) + "\n")
    project_path = output / "HistoryRecoveryProbe.xcodeproj"
    project_path.mkdir()
    (project_path / "project.pbxproj").write_text(project)
    return {"project": str(project_path), "bundleIdentifier": BUNDLE_ID,
            "bindingsSHA256": BASE.digest(sources / "bindings.json"),
            "productionSourceCount": len(production), "harnessSourceCount": len(harness)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--grdb-package", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.output, args.grdb_package), sort_keys=True))
    except ValueError as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    main()
