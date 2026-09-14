"""Publish/verify a compact evidence inventory without changing frozen experiments.

No model loading, downloads or Git writes. Ignored raw directories are fingerprinted,
not copied or backed up. Existing snapshots must match; publication never overwrites.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("Evaluation/CheckpointSnapshot/2026-09-13.json")
RAW_ROOTS = (
    "Evaluation/MatcherFeasibility/runs",
    "Evaluation/MatcherFeasibility/setup-attempts",
    "Evaluation/MatcherScreening/runs",
    "Evaluation/MatcherValidation/runs/validation-01",
    "Evaluation/MatcherValidation/runs/validation-02",
    "Evaluation/Organization/results",
)
RECEIPTS = (
    "Evaluation/MatcherValidation/runs/preparation-01/complete.json",
    "Evaluation/MatcherValidation/runs/p1-01/complete.json",
    "Evaluation/MatcherValidation/runs/validation-02/complete.json",
    "Evaluation/MatcherValidation/runs/validation-02/manifest.json",
    "Evaluation/MatcherValidation/runs/validation-02/report.json",
    "Evaluation/MatcherFeasibility/model-manifest.json",
    "Evaluation/MatcherFeasibility/environment.json",
    "Evaluation/MatcherFeasibility/runs/stage-2-attempt-01/complete.json",
    "Evaluation/MatcherFeasibility/runs/stage-3-attempt-03/complete.json",
    "Evaluation/MatcherFeasibility/runs/stage-4-attempt-02/complete.json",
    "Evaluation/MatcherFeasibility/runs/stage-5-attempt-01/complete.json",
    "Evaluation/MatcherScreening/runs/audit-attempt-01/complete.json",
    "Evaluation/MatcherScreening/runs/screen-attempt-01/complete.json",
    "Evaluation/Organization/results/core-complete-2026-09-11.json.gz",
)


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def inventory(root):
    if not root.is_dir():
        raise ValueError(f"Missing artifact directory: {root.name}")
    checksum = hashlib.sha256()
    count = total = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlinks are not supported in evidence inventories")
        # These are transient, not reproducible experiment evidence.
        if path.name in {"worker.lock", ".DS_Store"} or "__pycache__" in path.parts:
            continue
        if path.is_file():
            size = path.stat().st_size
            record = [path.relative_to(root).as_posix(), size, digest(path)]
            checksum.update((json.dumps(record, separators=(",", ":")) + "\n").encode())
            count += 1
            total += size
    return {"files": count, "bytes": total, "treeSHA256": checksum.hexdigest()}


def snapshot(root):
    report = json.loads((root / RECEIPTS[4]).read_text())
    # Store only allowlisted numerical results, not device logs or machine paths.
    metrics = {}
    for seed in ("17", "29", "41"):
        result = report["seeds"][seed]
        metrics[seed] = {
            name: {key: result[name][key] for key in
                   ("tp", "fp", "fn", "precision", "macroRecall", "acceptedUncertain")}
            for name in ("baseline", "hybrid")
        }
        metrics[seed]["qualification"] = result["qualification"]
    return {
        "schemaVersion": 1,
        "checkpoint": "2026-09-13-pre-diagnostic",
        "backupCreated": False,
        "inventoryExcludes": ["worker.lock", ".DS_Store", "__pycache__"],
        "rawDirectories": {name: inventory(root / name) for name in RAW_ROOTS},
        "evidence": {name: {"bytes": (root / name).stat().st_size,
                            "sha256": digest(root / name)} for name in RECEIPTS},
        "p2": {key: report[key] for key in
               ("allSeedsPassed", "oldTestOpened", "productionQualified", "productionReplayRun")}
              | {"seeds": metrics},
    }


def publish(path, record):
    if path.exists():
        if json.loads(path.read_text()) != record:
            raise ValueError("Snapshot differs; preserve it and investigate, do not overwrite")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("publish", "verify"))
    args = parser.parse_args()
    current = snapshot(ROOT)  # Missing excluded artifacts fail, never silently pass.
    path = ROOT / OUTPUT
    if args.command == "publish":
        publish(path, current)
    elif json.loads(path.read_text()) != current:
        raise ValueError("Local artifact inventory or selected results changed")
    print(json.dumps({"snapshot": OUTPUT.as_posix(), "verifiedLocalRawArtifacts": True,
                      "backupCreated": False, "command": args.command}))


if __name__ == "__main__":
    main()
