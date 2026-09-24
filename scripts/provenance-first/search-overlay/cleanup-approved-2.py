#!/usr/bin/env python3
"""Execute only the 19 project targets explicitly approved on 24 September."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / "Evaluation/ProvenanceFirst/search-overlay"
RUN = ROOT / "Evaluation/ProvenanceFirst/runs/search-overlay"
TARGETS = [
    "Evaluation/ProvenanceFirst/runs/" + name + "/build" for name in (
        "search-transition-deployment", "search-spacing-deployment", "search-motion-deployment",
        "unified-search-deployment", "search-options-deployment", "source-browser-ui",
        "source-browser-media", "history-recovery")
] + ["Evaluation/iOS27/" + name + "/build" for name in (
    "safeguards", "embedding-recovery", "embedding-recovery-v2", "precision")
] + ["Evaluation/ProvenanceFirst/runs/search-overlay/" + name for name in (
    "guarded-native-motion.mp4", "native-prepare-motion.mp4", "overlay-motion-retry.mp4",
    "overlay-motion.mp4", "query-reset-motion.mp4", "shared-scroll-motion.mp4", "stable-scroll-motion.mp4")]

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def main():
    receipt = RUN / "cleanup-approved-2.json"
    if receipt.exists():
        raise RuntimeError("Cleanup already started; inspect its receipt before retrying")
    proposal = WORK / "CLEANUP-PROPOSAL-2.md"
    listed = re.findall(r"^\| `([^`]+)` \|", proposal.read_text(), re.M)
    if listed != TARGETS:
        raise RuntimeError("Proposal differs from the exact approved targets")
    backups = {}
    for name in ("backup-1790223832209990000", "post-install-1790224085878947000"):
        folder = ROOT / "Evaluation/ProvenanceFirst/runs/search-dismissal-deployment" / name
        manifest = json.loads((folder / "verified.json").read_text())
        for relative, expected in manifest["hashes"].items():
            if digest(folder / relative) != expected:
                raise RuntimeError("Protected backup verification failed")
        backups[name] = len(manifest["hashes"])
    validated = []
    for name in TARGETS:
        path = ROOT / name
        if not path.exists() or path.is_symlink() or path.resolve() != path or not path.is_relative_to(ROOT):
            raise RuntimeError("Missing or redirected target: " + name)
        if subprocess.check_output(["git", "ls-files", "--", name], cwd=ROOT):
            raise RuntimeError("Tracked files in target: " + name)
        allocated = int(subprocess.check_output(["du", "-sk", str(path)], text=True).split()[0]) * 1024
        validated.append(dict(path=name, allocatedBytes=allocated))
    result = dict(approval="User yes to CLEANUP-PROPOSAL-2.md", proposalSHA256=digest(proposal),
                  protectedBackupsVerified=backups, targets=validated, deleted=[],
                  freeBytesBefore=shutil.disk_usage(ROOT).free, complete=False)
    receipt.write_text(json.dumps(result, indent=2) + "\n")
    for item in validated:
        path = ROOT / item["path"]
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        result["deleted"].append(item["path"])
        receipt.write_text(json.dumps(result, indent=2) + "\n")
    result.update(complete=True, freeBytesAfter=shutil.disk_usage(ROOT).free)
    result["netFreeBytesRecovered"] = result["freeBytesAfter"] - result["freeBytesBefore"]
    receipt.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"targets", "deleted"}}))

if __name__ == "__main__":
    main()
