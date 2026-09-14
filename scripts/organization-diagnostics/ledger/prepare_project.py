#!/usr/bin/env python3
"""Generate an isolated simulator project without changing production or Git state.

Only generates files. Building and launching are separate, explicitly coordinated steps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
PRODUCTION_SOURCES = (
    "LibraryFileStore.swift", "LivingWiki.swift", "LivingWikiCompiler.swift", "LocalAI.swift", "MemoryAnalyzer.swift",
    "MemoryChunk.swift", "MemoryCollection.swift", "MemoryContentExtractor.swift",
    "MemoryItem.swift", "MemorySearch.swift", "MemoryStore.swift", "OpenAIAPI.swift",
    "PrivacyActivity.swift", "ProjectGraphService.swift", "ProjectIntelligence.swift",
    "ProjectMemory.swift", "ProjectViewModel.swift", "Provenance.swift",
    "RememberAssistant.swift", "VisionImageClassifier.swift",
)
HARNESS_SOURCES = (
    "DiagnosticReplayApp.swift", "OrganizationDiagnosticReplay.swift", "DiagnosticInvariants.swift",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_text(package: Path) -> str:
    # JSON quoting is also a valid OpenStep quoted string; it is never passed to a shell.
    package_path = json.dumps(str(package))
    return '''// !$*UTF8*$!
{
 archiveVersion = 1; classes = {}; objectVersion = 77;
 objects = {
  A00000000000000000000001 = { isa = PBXProject; buildConfigurationList = A00000000000000000000006; compatibilityVersion = "Xcode 16.0"; mainGroup = A00000000000000000000002; productRefGroup = A00000000000000000000003; projectDirPath = ""; projectRoot = ""; targets = (A00000000000000000000004); packageReferences = (A00000000000000000000020); };
  A00000000000000000000002 = { isa = PBXGroup; children = (A00000000000000000000005, A00000000000000000000003); sourceTree = "<group>"; };
  A00000000000000000000003 = { isa = PBXGroup; children = (A00000000000000000000009); name = Products; sourceTree = "<group>"; };
  A00000000000000000000004 = { isa = PBXNativeTarget; buildConfigurationList = A00000000000000000000007; buildPhases = (A00000000000000000000008, A00000000000000000000012, A00000000000000000000013); buildRules = (); dependencies = (); fileSystemSynchronizedGroups = (A00000000000000000000005); name = OrganizationLedgerProbe; productName = OrganizationLedgerProbe; productReference = A00000000000000000000009; productType = "com.apple.product-type.application"; packageProductDependencies = (A00000000000000000000021); };
  A00000000000000000000005 = { isa = PBXFileSystemSynchronizedRootGroup; path = Sources; sourceTree = "<group>"; };
  A00000000000000000000006 = { isa = XCConfigurationList; buildConfigurations = (A00000000000000000000010); defaultConfigurationIsVisible = 0; defaultConfigurationName = Debug; };
  A00000000000000000000007 = { isa = XCConfigurationList; buildConfigurations = (A00000000000000000000011); defaultConfigurationIsVisible = 0; defaultConfigurationName = Debug; };
  A00000000000000000000008 = { isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; };
  A00000000000000000000009 = { isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = OrganizationLedgerProbe.app; sourceTree = BUILT_PRODUCTS_DIR; };
  A00000000000000000000012 = { isa = PBXResourcesBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; };
  A00000000000000000000013 = { isa = PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = (A00000000000000000000022); runOnlyForDeploymentPostprocessing = 0; };
  A00000000000000000000010 = { isa = XCBuildConfiguration; buildSettings = { SDKROOT = iphoneos; IPHONEOS_DEPLOYMENT_TARGET = 26.0; SWIFT_VERSION = 5.0; CLANG_ENABLE_MODULES = YES; }; name = Debug; };
  A00000000000000000000011 = { isa = XCBuildConfiguration; buildSettings = {
    PRODUCT_BUNDLE_IDENTIFIER = SimpleStudio.Remember.OrganizationLedgerProbe;
    PRODUCT_NAME = "$(TARGET_NAME)";
    GENERATE_INFOPLIST_FILE = YES;
    INFOPLIST_KEY_UIApplicationSceneManifest_Generation = YES;
    INFOPLIST_KEY_UILaunchScreen_Generation = YES;
    INFOPLIST_KEY_CFBundleDisplayName = "Ledger Diagnostics";
    TARGETED_DEVICE_FAMILY = 1;
    SWIFT_OPTIMIZATION_LEVEL = "-Onone";
    SWIFT_COMPILATION_MODE = wholemodule;
    SWIFT_APPROACHABLE_CONCURRENCY = YES;
    SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor;
    SWIFT_UPCOMING_FEATURE_MEMBER_IMPORT_VISIBILITY = YES;
    DEBUG_INFORMATION_FORMAT = dwarf;
    ENABLE_PREVIEWS = NO;
    COMPILER_INDEX_STORE_ENABLE = NO;
    CODE_SIGNING_ALLOWED = NO;
    CURRENT_PROJECT_VERSION = 1;
    MARKETING_VERSION = 1.0;
  }; name = Debug; };
  A00000000000000000000020 = { isa = XCLocalSwiftPackageReference; relativePath = PACKAGE_PATH; };
  A00000000000000000000021 = { isa = XCSwiftPackageProductDependency; package = A00000000000000000000020; productName = GRDB; };
  A00000000000000000000022 = { isa = PBXBuildFile; productRef = A00000000000000000000021; };
 };
 rootObject = A00000000000000000000001;
}
'''.replace("PACKAGE_PATH", package_path)


def prepare(output: Path, package: Path) -> dict:
    output = output.resolve()
    package = package.resolve()
    allowed = (REPOSITORY / "Evaluation/OrganizationDiagnostics/runs").resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        raise ValueError("project output must be beneath Evaluation/OrganizationDiagnostics/runs")
    if output.exists():
        raise ValueError("project output already exists; choose a new empty directory")
    if not (package / "Package.swift").is_file():
        raise ValueError("an existing local GRDB package is required; no downloads are allowed")
    production = [REPOSITORY / "Remember/Remember" / name for name in PRODUCTION_SOURCES]
    production.append(REPOSITORY / "Remember/Shared/CaptureInbox.swift")
    harness = [HERE / name for name in HARNESS_SOURCES]
    files = production + harness
    for path in files:
        if not path.is_file():
            raise ValueError(f"missing source binding: {path}")
    bindings = {
        "schemaVersion": 1,
        "production": {str(p.relative_to(REPOSITORY)): digest(p) for p in production},
        "harness": {str(p.relative_to(REPOSITORY)): digest(p) for p in harness},
        "grdb": {str(p.relative_to(package)): digest(p) for p in sorted(package.rglob("*"))
                 if p.is_file() and ".git" not in p.parts and
                 (p == package / "Package.swift" or p.relative_to(package).parts[0] in {"GRDB", "GRDBSQLite"})},
    }
    sources = output / "Sources"
    sources.mkdir(parents=True)
    for path in files:
        (sources / path.name).symlink_to(path)
    (sources / "bindings.json").write_text(json.dumps(bindings, sort_keys=True, indent=2) + "\n")
    project = output / "OrganizationLedgerProbe.xcodeproj"
    project.mkdir()
    (project / "project.pbxproj").write_text(project_text(package))
    return {"project": str(project), "bindingsSHA256": digest(sources / "bindings.json"),
            "productionSourceCount": len(production), "harnessSourceCount": len(harness)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--grdb-package", required=True, type=Path)
    arguments = parser.parse_args()
    if os.environ.get("SPI_BUILDER") == "1":
        raise SystemExit("SPI_BUILDER would add a remote GRDB dependency; unset it first")
    print(json.dumps(prepare(arguments.output, arguments.grdb_package), sort_keys=True))


if __name__ == "__main__":
    main()
