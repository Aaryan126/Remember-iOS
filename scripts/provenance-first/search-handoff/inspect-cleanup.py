#!/usr/bin/env python3
"""Read-only inventory for an exact cleanup proposal. Never deletes or writes."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "Evaluation/ProvenanceFirst/runs"
GENERATED = [
    "search-dismissal-deployment/build",
    "search-dismissal-deployment/project",
    "search-overlay/project",
    "search-overlay/dependency",
    "search-overlay-deployment/build/Build/Intermediates.noindex",
    "search-overlay-deployment/build/ModuleCache.noindex",
    "search-overlay-deployment/build/SDKExplicitPrecompiledModules",
]
OLDER_BACKUPS = [
    "search-dismissal-deployment/backup-1790223832209990000",
    "search-dismissal-deployment/post-install-1790224085878947000",
]
PROTECTED = [
    "search-overlay-deployment/backup-1790230453931123000",
    "search-overlay-deployment/post-install-1790231053409891000",
]

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def inventory(name):
    path = RUN / name
    if not path.is_dir() or path.is_symlink() or path.resolve() != path:
        raise ValueError("Missing or redirected target: " + name)
    if not path.is_relative_to(ROOT) or any(p.name == ".git" for p in path.rglob("*")):
        raise ValueError("Outside project or contains Git metadata: " + name)
    relative = str(path.relative_to(ROOT))
    if subprocess.check_output(["git", "ls-files", "--", relative], cwd=ROOT):
        raise ValueError("Tracked files in target: " + name)
    allocated = int(subprocess.check_output(["du", "-sk", str(path)], text=True).split()[0]) * 1024
    return {"path": relative, "allocatedBytes": allocated}

def verify_backup(name):
    folder = RUN / name
    manifest = json.loads((folder / "verified.json").read_text())
    if not manifest["complete"]:
        raise ValueError("Incomplete backup: " + name)
    for name, expected in manifest["hashes"].items():
        path = folder / name
        if not path.resolve().is_relative_to(folder) or digest(path) != expected:
            raise ValueError("Backup integrity check failed")
    originals = {name: expected for name, expected in manifest["hashes"].items()
                 if name.startswith("app/Library/Application Support/Remember/Originals/")}
    if not originals:
        raise ValueError("No original files in backup")
    return len(manifest["hashes"]), originals

if __name__ == "__main__":
    groups = {"generated": [inventory(name) for name in GENERATED],
              "optionalOlderBackups": [inventory(name) for name in OLDER_BACKUPS]}
    checked = {}
    reference = None
    for name in PROTECTED + OLDER_BACKUPS:
        count, originals = verify_backup(name)
        if reference is None:
            reference = originals
        if originals != reference:
            raise ValueError("Original files differ between restore points; do not propose removal")
        checked[name] = {"verifiedFiles": count, "matchingOriginalFiles": len(originals)}
    # Existing preservation receipts are aggregates, not personal source text.
    preserved = {}
    for scope in ["search-dismissal-deployment", "search-overlay-deployment"]:
        report = json.loads((RUN / scope / "preservation.json").read_text())
        keys = ["sqliteIntegrityOK", "allOriginalBytesUnchanged", "allMemoryRowsUnchanged", "historicalEventsUnchanged"]
        if not all(report[key] for key in keys):
            raise ValueError("Prior preservation gate failed: " + scope)
        preserved[scope] = {key: report[key] for key in keys + ["memoryCountAfter", "eventCountAfter"]}
    print(json.dumps({"groups": groups,
        "groupBytes": {key: sum(row["allocatedBytes"] for row in rows) for key, rows in groups.items()},
        "backupsVerified": checked, "preservationReceipts": preserved,
        "freeBytes": shutil.disk_usage(ROOT).free, "deleted": False}, indent=2))
