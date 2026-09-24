#!/usr/bin/env python3
"""Checkpoint-1 coordinator. It cannot run models or start checkpoint 2."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import re
import shutil
import sys
import time

from fixtures import (compile_library, encoded, load, observed_inputs, relationship_records,
                      require, sha, validate_pair)

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "Evaluation/ProvenanceFirst"
CODE = ROOT / "scripts/provenance-first"
GIB = 1024 ** 3


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("wb") as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def allocated(path):
    if not path.exists():
        return 0
    if path.is_symlink():
        return 0
    if path.is_file():
        return path.stat().st_blocks * 512
    return sum(p.lstat().st_blocks * 512 for p in path.rglob("*") if p.is_file() and not p.is_symlink())


def resource_check(work=WORK):
    info = load(work / "resources.json")
    free = shutil.disk_usage(work).free
    scoped = allocated(work) + allocated(CODE)
    external = sum(max(0, allocated(Path(p)) - start) for p, start in info["externalBaselines"].items())
    growth = max(scoped + external, max(0, info["initialFreeBytes"] - free))
    require(free >= 10 * GIB, "free-space reserve below 10 GiB; stop, do not clean automatically")
    require(growth <= 4 * GIB, "new-write budget above 4 GiB; stop, do not clean automatically")
    return {"freeBytes": free, "scopedBytes": scoped, "externalGrowthBytes": external, "conservativeGrowthBytes": growth}


@contextmanager
def writer(work):
    with (work / "worker.lock").open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("checkpoint worker already running")
        atomic(work / "worker.json", {"pid": os.getpid(), "running": True})
        try:
            yield
        finally:
            atomic(work / "worker.json", {"pid": os.getpid(), "running": False})
            fcntl.flock(stream, fcntl.LOCK_UN)


def documents(work):
    return [load(work / "authored" / f"{split}.json") for split in ("development", "evaluation")]


def reviewed(work):
    for split in ("development", "evaluation"):
        digest = sha((work / "authored" / f"{split}.json").read_bytes())
        review = load(work / "reviews" / f"{split}.json")
        require(review["split"] == split and review["inputSHA256"] == digest, f"{split}: review is stale")
        author = "/root/pf_author_dev" if split == "development" else "/root/pf_author_eval"
        require(review["author"] == author and review["reviewer"] != author and review["reviewer"], f"{split}: independent reviewer required")
        expected = {lib["id"] for lib in load(work / "authored" / f"{split}.json")["libraries"]}
        require(len(review["libraries"]) == 12 and {x["id"] for x in review["libraries"]} == expected, "incomplete review")
        require(all(x["verdict"] == "pass" for x in review["libraries"]), f"{split}: review has unresolved cases")
        issues = review["crossLibraryIssues"] + [i for x in review["libraries"] for i in x["issues"]]
        require(all(i["severity"] == "warning" for i in issues), f"{split}: unresolved review error")


def hashes(work):
    paths = [work / name for name in ("CONTRACT.md", "FORMAT.md", "PLAN.md", "METRICS.md")]
    paths += sorted((work / "authored").glob("*.json")) + sorted((work / "reviews").glob("*.json"))
    paths += sorted((work / "authored").glob("*.changes.md")) + sorted((work / "review-inputs").glob("*.json"))
    paths += sorted(CODE.glob("*.py"))
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths}


def freeze(work):
    development, evaluation = documents(work)
    validate_pair(development, evaluation)
    reviewed(work)
    manifest = {"schemaVersion": 1, "stage": "checkpoint-1", "hashes": hashes(work),
                "libraryCount": 24, "eventCount": 288, "taskCount": 96,
                "limits": {"bytes": 4 * GIB, "freeReserveBytes": 10 * GIB},
                "evaluationUse": "representation only; checkpoint-2 labels sealed from policy selection",
                "trainingAllowed": False, "checkpoint2Allowed": False}
    target = work / "frozen.json"
    if target.exists():
        require(load(target) == manifest, "freeze changed; do not overwrite a frozen experiment")
    else:
        atomic(target, manifest)
    return manifest


def verify_manifest(work):
    manifest = load(work / "frozen.json")
    require(manifest["hashes"] == hashes(work), "frozen input/code/review hashes changed")
    return manifest


def verify_units(work):
    manifest = verify_manifest(work)
    manifest_hash = sha(encoded(manifest))
    completed = []
    for document in documents(work):
        for library in document["libraries"]:
            unit = work / "units" / library["id"]
            if not (unit / "receipt.json").exists():
                continue
            saved = load(unit / "receipt.json")
            require(saved["libraryId"] == library["id"], "receipt library mismatch")
            require(saved["manifestSHA256"] == manifest_hash and saved["inputSHA256"] == sha(encoded(library)), "resume identity mismatch")
            require(set(saved["outputs"]) == {"ledger.json", "relationships.json", "source-only.json"}, "invalid receipt output set")
            for name, expected in saved["outputs"].items():
                require(sha((unit / name).read_bytes()) == expected, f"corrupt resumed unit {library['id']}/{name}")
            completed.append(library["id"])
    return completed


def verify_native(work):
    completed = verify_units(work)
    require(len(completed) == 24, "compiler units incomplete")
    folder = work / "runs/checkpoint1"
    input_path = folder / "input.json"
    runs = [load(work / "units" / key / "ledger.json")["runs"][0] for key in completed]
    require(load(input_path) == {"schemaVersion": 1, "runs": runs}, "native input differs from frozen compiled units")
    project = folder / "ledger/project"
    binding_path = project / "Sources/bindings.json"
    bindings = load(binding_path)
    for category in ("production", "harness", "tooling"):
        for name, expected in bindings[category].items():
            path = ROOT / name
            require(path.resolve().is_relative_to(ROOT), "source binding path escapes repository")
            require(sha(path.read_bytes()) == expected, f"native binding changed: {name}")
    for name, expected in bindings["generated"].items():
        path = project / name
        require(path.resolve().is_relative_to(project.resolve()), "generated binding path escapes project")
        require(sha(path.read_bytes()) == expected, f"generated binding changed: {name}")
    project_text = (project / "ProvenanceFirstProbe.xcodeproj/project.pbxproj").read_text()
    package_match = re.search(r'relativePath = ("[^\n]+?");', project_text)
    require(package_match is not None, "native package path unavailable")
    import json
    package = Path(json.loads(package_match.group(1)))
    for name, expected in bindings["grdb"].items():
        path = package / name
        require(path.resolve().is_relative_to(package.resolve()), "dependency path escape")
        require(sha(path.read_bytes()) == expected, f"dependency changed: {name}")
    output = folder / "output"
    verify_native_paths(output)
    state = load(output / "status.json")
    batch_hash, binding_hash = sha(input_path.read_bytes()), sha(binding_path.read_bytes())
    require(state["status"] == "complete" and int(state["completed"]) == 24 and state["batchSHA256"] == batch_hash
            and state["bindingsSHA256"] == binding_hash, "native replay incomplete or binding mismatch")
    prefixes, receipts = 0, []
    for run in runs:
        receipt_path = output / (sha(run["id"].encode()) + ".receipt.json")
        receipt = load(receipt_path)
        require(receipt["id"] == run["id"] and receipt["batchSHA256"] == batch_hash
                and receipt["bindingsSHA256"] == binding_hash, "native receipt identity mismatch")
        require(receipt["restartVerified"] is True and receipt["prefixCount"] == 12
                and receipt["historicalPrefixesVerified"] == 12, "native prefix/restart incomplete")
        require([p["id"] for p in receipt["prefixes"]] == [e["id"] for e in run["events"]], "native prefix IDs mismatch")
        ledger = output / receipt["attempt"] / "ledger.json"
        require(ledger.resolve().is_relative_to(output.resolve()), "native receipt path escape")
        require(sha(ledger.read_bytes()) == receipt["ledgerSHA256"], "native ledger hash mismatch")
        require(len(load(ledger)) == receipt["ledgerCount"], "native ledger event count mismatch")
        prefixes += receipt["prefixCount"]
        receipts.append(sha(receipt_path.read_bytes()))
    invariant = load(output / "invariants.receipt.json")
    require(invariant["status"] == "passed" and int(invariant["checks"]) > 0, "invariants missing/failed")
    invariant_ledger = output / invariant["attempt"] / "ledger.json"
    require(invariant_ledger.resolve().is_relative_to(output.resolve()), "invariant receipt path escape")
    require(sha(invariant_ledger.read_bytes()) == invariant["ledgerSHA256"], "invariant ledger changed")
    execution = load(output / "invariant-execution.json")
    require(execution["batchSHA256"] == batch_hash and execution["bindingsSHA256"] == binding_hash
            and execution["invariantReceiptSHA256"] == sha((output / "invariants.receipt.json").read_bytes())
            and execution["executedInvariants"] is True, "invariants not bound to current native execution")
    return {"nativeLibraries": 24, "prefixes": prefixes, "historicalPrefixes": prefixes,
            "restartChecks": 24, "invariantChecks": int(invariant["checks"]),
            "batchSHA256": batch_hash, "bindingsSHA256": binding_hash,
            "receiptHashes": receipts, "semanticQualityMeasured": False, "checkpoint2Allowed": False}


def verify_native_paths(output):
    """Validate receipts before the legacy Swift resume code can read their paths."""
    if not output.exists():
        return
    require(output.resolve() == output.absolute(), "native output directory redirected by symlink")
    for path in output.glob("*.receipt.json"):
        require(not path.is_symlink(), "native receipt symlink rejected")
        receipt = load(path)
        attempt = receipt["attempt"]
        require(isinstance(attempt, str) and bool(attempt) and Path(attempt).name == attempt
                and attempt not in {".", ".."}, "native receipt path escape")
        ledger = output / attempt / "ledger.json"
        require(ledger.resolve().is_relative_to(output.resolve()), "native receipt path escape")


def run(work, maximum=None, resume=False):
    require(maximum is None or maximum > 0, "max-libraries must be positive")
    with writer(work):
        manifest = verify_manifest(work)
        manifest_hash = sha(encoded(manifest))
        verified = set(verify_units(work))
        if resume:
            for path in (work / "pause.request.json", work / "runs/checkpoint1/output/pause.request"):
                if path.exists():
                    path.rename(path.with_name(path.name + f".resumed-{time.time_ns()}"))
        completed, new = [], 0
        for document in documents(work):
            for library in document["libraries"]:
                key = library["id"]
                unit = work / "units" / key
                receipt = unit / "receipt.json"
                if key in verified:
                    completed.append(key)
                    continue
                if (work / "pause.request.json").exists() or (maximum is not None and new >= maximum):
                    atomic(work / "status.json", {"status": "paused", "completedLibraries": completed, "checkpoint2Allowed": False})
                    return
                resource_check(work)
                outputs = {"ledger.json": {"schemaVersion": 1, "runs": [compile_library(library)]},
                           "relationships.json": relationship_records(library), "source-only.json": observed_inputs(library)}
                for name, value in outputs.items():
                    atomic(unit / name, value)
                atomic(receipt, {"libraryId": key, "manifestSHA256": manifest_hash,
                                "inputSHA256": sha(encoded(library)),
                                "outputs": {name: sha(encoded(value)) for name, value in outputs.items()}})
                completed.append(key)
                new += 1
                atomic(work / "status.json", {"status": "compiling", "completedLibraries": completed, "checkpoint2Allowed": False})
        runs = [load(work / "units" / key / "ledger.json")["runs"][0] for key in completed]
        atomic(work / "runs" / "checkpoint1" / "input.json", {"schemaVersion": 1, "runs": runs})
        atomic(work / "status.json", {"status": "compiled-awaiting-native-replay", "completedLibraries": completed,
                                     "checkpoint2Allowed": False, "semanticQualityMeasured": False})


def status(work):
    state = load(work / "status.json") if (work / "status.json").exists() else {"status": "preparing"}
    busy = False
    lock = work / "worker.lock"
    if lock.exists():
        with lock.open("r") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(stream, fcntl.LOCK_UN)
            except BlockingIOError:
                busy = True
    # Native replay, builds and author/review agents are coordinated separately.
    return {**state, "compilerRunning": busy,
            "safeToClose": False, "note": "Root must also verify native/build processes and agent checkpoints before confirming safe to close."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "snapshot", "validate", "freeze", "run", "pause", "resume", "status", "verify", "verify-native", "resources"))
    parser.add_argument("--max-libraries", type=int)
    parser.add_argument("--external-root", action="append", type=Path, default=[])
    args = parser.parse_args()
    work = WORK
    if args.command == "init":
        require(not (work / "resources.json").exists(), "resources already initialized")
        roots = {}
        allowed = Path.home() / "Library/Developer/CoreSimulator/Devices"
        for path in args.external_root:
            actual = path.resolve()
            require(actual.parent == allowed and actual.is_dir(), "only an existing explicit simulator-device directory can be registered")
            roots[str(actual)] = allocated(actual)
        atomic(work / "resources.json", {"initialFreeBytes": shutil.disk_usage(work).free, "externalBaselines": roots})
        result = resource_check(work)
    elif args.command == "snapshot":
        result = {}
        for path in sorted((work / "authored").glob("*.json")):
            value = load(path)
            digest = sha(path.read_bytes())
            target = work / "review-inputs" / (digest + ".json")
            if not target.exists():
                # Store original bytes, not a normalization; the name is the source hash.
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(path.read_bytes())
                    stream.flush()
                    os.fsync(stream.fileno())
            require(sha(target.read_bytes()) == digest, "review snapshot corrupted")
            result[path.name] = digest
    elif args.command == "validate":
        validate_pair(*documents(work))
        result = {"valid": True, "libraries": 24, "events": 288, "tasks": 96}
    elif args.command == "freeze":
        resource_check(work)
        result = freeze(work)
    elif args.command == "pause":
        atomic(work / "pause.request.json", {"requestedAtUnix": time.time(), "scope": "compiler-and-native-between-libraries"})
        output = work / "runs/checkpoint1/output"
        output.mkdir(parents=True, exist_ok=True)
        atomic(output / "pause.request", {"requested": True})
        result = status(work)
    elif args.command in {"run", "resume"}:
        run(work, args.max_libraries, resume=args.command == "resume")
        result = status(work)
    elif args.command == "verify":
        completed = verify_units(work)
        result = {"manifestValid": True, "verifiedLibraries": completed, "resources": resource_check(work), **status(work)}
    elif args.command == "verify-native":
        result = verify_native(work)
        atomic(work / "native-verification.json", result)
    elif args.command == "resources":
        result = resource_check(work)
    else:
        result = status(work)
    sys.stdout.write(encoded(result).decode())


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f"CHECKPOINT_FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
