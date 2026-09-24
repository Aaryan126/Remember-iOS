"""Independent coverage/citation checks. Candidate availability is NOT recall@k."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import uuid

import benchmark
import control as c


def source_uuid(source_id):
    canonical = "localc" + source_id[1:]
    return str(uuid.UUID(bytes=hashlib.sha256(("organization-diagnostics-v1:" + canonical).encode())
                         .digest()[:16])).upper()


def inside(root, name):
    path = root / name
    c.require(path.resolve() == path and path.is_relative_to(root) and path != root,
              "native artifact path escape/symlink")
    return path


def artifact_paths():
    output = c.RUN / "output"
    values = {}
    for path in output.glob("*.receipt.json"):
        c.require(not path.is_symlink(), "symlinked native receipt")
        row = c.load(path)
        if path.name.endswith(".history.receipt.json"):
            target = inside(output, row["projection"])
            c.require(c.digest(target) == row["projectionSHA256"], "history projection tampered")
        elif path.name == "history-invariants.bound.receipt.json":
            for name, expected in row["artifacts"].items():
                c.require(c.digest(inside(output, name)) == expected, "invariant artifact tampered")
        elif path.name != "invariants.receipt.json":
            target = inside(output, row["attempt"] + "/ledger.json")
            c.require(c.digest(target) == row["ledgerSHA256"], "native ledger tampered")
        values[str(path.relative_to(c.ROOT))] = dict(sha256=c.digest(path), mtimeNS=path.stat().st_mtime_ns)
    return values


def check_candidates(candidates, ledger, sequence, expected_keys, source_map):
    c.require(len({item["id"] for item in candidates}) == len(candidates), "duplicate candidate ID")
    events = {event["id"].upper(): event for event in ledger}
    version_orders = {}
    for event in ledger:
        if event["sequence"] > sequence: continue
        if event["kind"] in ("capture", "imported", "revision"):
            version_orders.setdefault(event["memoryID"].upper(), []).append(event["id"].upper())
    actual = set()
    for item in candidates:
        sid = item["sourceID"].upper()
        c.require(sid in source_map, "unexpected candidate source")
        key = (source_map[sid], item["revision"])
        actual.add(key)
        version = events[item["versionID"].upper()]
        snapshot = events[item["snapshotID"].upper()]
        c.require(version["sequence"] == item["sourceSequence"] <= sequence
                  and snapshot["sequence"] == item["snapshotSequence"] <= sequence,
                  "candidate has future/mismatched sequence")
        c.require(version["kind"] in ("capture", "imported", "revision")
                  and version["memoryID"].upper() == sid and snapshot["memoryID"].upper() == sid,
                  "candidate source-version mismatch")
        c.require(version_orders[sid].index(version["id"].upper()) == item["revision"], "revision ordinal mismatch")
        c.require(item["isCurrentVersion"] == (version_orders[sid][-1] == version["id"].upper()),
                  "current-version label mismatch")
        payload = json.loads(snapshot["payloadJSON"])
        if snapshot["id"] != version["id"]:
            c.require(snapshot["kind"] == "enrichment"
                      and payload["sourceRevisionID"].upper() == version["id"].upper(), "snapshot lacks version authority")
        field = item["evidenceField"]
        c.require(field in ("extractedText", "userCaption"), "generated metadata used as source")
        source_text = payload["memory"].get(field, "")
        c.require(bool(item["quote"]) and item["quote"] in source_text.replace("\r\n", "\n").strip(),
                  "candidate quote absent from source snapshot")
        c.require(item["locatorAvailability"] == "retained-ledger-text"
                  and item["mediaLocatorAvailability"] == "unavailable"
                  and item["originalAssetAvailability"] == "unavailable", "fabricated historical locator/asset")
        identity = ":".join((sid, item["versionID"].upper(), item["snapshotID"].upper(), field, str(item["ordinal"])))
        c.require(item["id"] == hashlib.sha256(identity.encode()).hexdigest(), "unstable evidence identity")
    c.require(actual == expected_keys, f"candidate coverage differs: missing={expected_keys-actual}, extra={actual-expected_keys}")


def verify_library(library):
    run = benchmark.native_run(library)
    key = hashlib.sha256(run["id"].encode()).hexdigest()
    output = c.RUN / "output"
    receipt_path = output / (key + ".history.receipt.json")
    if not receipt_path.exists(): return None
    receipt = c.load(receipt_path)
    native = c.load(output / (key + ".receipt.json"))
    projection = c.load(inside(output, receipt["projection"]))
    ledger_path = inside(output, native["attempt"] + "/ledger.json")
    ledger = c.load(ledger_path)
    c.require(native["restartVerified"] and native["historicalPrefixesVerified"] == 12
              and receipt["restartVerified"] and projection["restartVerified"], "native reopen/prefix proof missing")
    for row in (native, receipt, projection):
        c.require(row["id"] == run["id"] and row["batchSHA256"] == c.digest(c.RUN / "input.json")
                  and row["bindingsSHA256"] == c.digest(c.RUN / "project/Sources/bindings.json")
                  and row["ledgerSHA256"] == c.digest(ledger_path), "native receipt binding mismatch")
    c.require(c.digest(inside(output, receipt["projection"])) == receipt["projectionSHA256"], "projection hash mismatch")
    c.require(receipt["prefixCount"] == len(projection["prefixes"]) == 12
              and receipt["queryCount"] == len(projection["queries"]) == 4, "incomplete native projection")
    source_map = {source_uuid(e["sourceId"]): e["sourceId"] for e in library["events"] if e["kind"] == "capture"}
    state, versions, prefixes = {}, set(), {}
    for event, prefix, native_prefix in zip(library["events"], projection["prefixes"], native["prefixes"]):
        c.require(event["id"] == prefix["id"] == native_prefix["id"], "prefix order mismatch")
        c.require(prefix["sequence"] == ledger[native_prefix["ledgerCount"] - 1]["sequence"], "prefix boundary mismatch")
        sid, kind = event["sourceId"], event["kind"]
        if kind == "capture": state[sid] = dict(revision=0, archived=False)
        elif kind == "revise": state[sid]["revision"] += 1
        elif kind in ("archive", "restore"): state[sid]["archived"] = kind == "archive"
        versions.add((sid, state[sid]["revision"]))
        current = {(s, v["revision"]) for s, v in state.items() if not v["archived"]}
        check_candidates(prefix["current"], ledger, prefix["sequence"], current, source_map)
        check_candidates(prefix["includeHistory"], ledger, prefix["sequence"], versions, source_map)
        for item in prefix["includeHistory"]:
            c.require(item["isArchived"] == state[source_map[item["sourceID"].upper()]]["archived"], "archive label mismatch")
        prefixes[prefix["id"]] = prefix
    results = []
    queries = {q["id"]: q for q in projection["queries"]}
    c.require(set(queries) == {t["id"] for t in library["tasks"]}, "query IDs differ")
    for task in library["tasks"]:
        query = queries[task["id"]]
        prefix = prefixes[task["atEvent"]]
        c.require(query["scope"] == task["scope"] and query["afterEvent"] == task["atEvent"]
                  and query["sequence"] == prefix["sequence"]
                  and query["candidates"] == prefix[task["scope"]], "explicit query scope/prefix mismatch")
        expected = task["expectedEvidence"]
        covered = []
        for evidence in expected:
            matches = [item["id"] for item in query["candidates"]
                       if source_map[item["sourceID"].upper()] == evidence["sourceId"]
                       and item["revision"] == evidence["revision"] and evidence["quote"] in item["quote"]]
            c.require(bool(matches), f"retained expected evidence unreachable: {library['id']}/{task['id']}")
            covered.append(dict(sourceId=evidence["sourceId"], revision=evidence["revision"], candidates=matches))
        results.append(dict(id=task["id"], mode=task["mode"], scope=task["scope"],
                            expectedEvidenceCount=len(expected), covered=covered,
                            unrankedCandidateCount=len(query["candidates"])))
    return dict(id=library["id"], prefixes=12, restartVerified=True, tasks=results,
                receiptSHA256=c.digest(receipt_path))


def verify(complete=False):
    benchmark.verify()
    artifact_paths()
    libraries = [lib for doc in benchmark.documents() for lib in doc["libraries"]]
    completed = [value for lib in libraries if (value := verify_library(lib)) is not None]
    if complete:
        c.require(len(completed) == 24, "history checkpoint native coverage incomplete")
        output = c.RUN / "output"
        bound = c.load(output / "history-invariants.bound.receipt.json")
        c.require(bound["batchSHA256"] == c.digest(c.RUN / "input.json")
                  and bound["bindingsSHA256"] == c.digest(c.RUN / "project/Sources/bindings.json")
                  and len(bound["artifacts"]) == 5, "invariant execution not bound to this build/batch")
        history = c.load(output / "history-invariants.json")
        production = c.load(output / "invariants.receipt.json")
        c.require(history["status"] == production["status"] == "passed"
                  and int(history["count"]) >= 33 and int(production["checks"]) >= 31, "native invariant checks incomplete")
        status = c.load(output / "status.json")
        c.require(status["status"] == "complete" and int(status["completed"]) == 24, "native batch incomplete")
    return dict(schemaVersion=1, completedLibraries=len(completed), libraries=completed,
                prefixes=sum(row["prefixes"] for row in completed), rankingMeasured=False,
                checkpoint2Allowed=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--complete", action="store_true")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()
    result = verify(args.complete)
    if args.save: c.publish(c.WORK / "coverage.json", result)
    print(json.dumps(dict(completedLibraries=result["completedLibraries"], prefixes=result["prefixes"], rankingMeasured=False)))
