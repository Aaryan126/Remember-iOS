"""Validate/review/freeze fresh coverage fixtures. No ranking, training or inference."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import control as c
from fixtures import compile_library, load, observed_inputs, require, validate_pair, validate_split


def documents():
    return [load(c.WORK / "authored" / f"{split}.json") for split in ("development", "evaluation")]


def validate_history_split(document):
    validate_split(document)
    for library in document["libraries"]:
        modes = [task["mode"] for task in library["tasks"]]
        require(sorted(modes) == ["current", "historical", "overlap", "uncertain"],
                f"{library['id']}: one task per required mode")
        for task in library["tasks"]:
            expected_scope = "includeHistory" if task["mode"] == "historical" else "current"
            require(task.get("scope") == expected_scope, f"{library['id']}/{task['id']}: scope mismatch")
            require(task["answerable"] == (task["mode"] != "uncertain"), "unanswerable task required")
        historical = next(t for t in library["tasks"] if t["mode"] == "historical")
        archived_case = int(library["id"][-2:]) <= 6
        observed = {}
        for event in library["events"]:
            sid = event["sourceId"]
            if event["kind"] == "capture": observed[sid] = {"revision": 0, "archived": False}
            elif event["kind"] == "revise": observed[sid]["revision"] += 1
            elif event["kind"] in {"archive", "restore"}:
                observed[sid]["archived"] = event["kind"] == "archive"
            if event["id"] == historical["atEvent"]: break
        require(bool(historical["expectedEvidence"]), "historical task requires evidence")
        for evidence in historical["expectedEvidence"]:
            state = observed[evidence["sourceId"]]
            if archived_case:
                require(state["archived"] and state["revision"] == evidence["revision"],
                        f"{library['id']}: historical task must target archived latest revision")
            else:
                require(not state["archived"] and evidence["revision"] < state["revision"],
                        f"{library['id']}: historical task must target superseded active note")


def validate_documents():
    development, evaluation = documents()
    validate_pair(development, evaluation)
    for document in (development, evaluation): validate_history_split(document)
    # Old exposed cases may be regression inputs, never copied into the fresh study.
    old = [load(c.PF / "authored" / f"{split}.json") for split in ("development", "evaluation")]
    old_families = {lib["family"] for doc in old for lib in doc["libraries"]}
    old_texts = {event["text"].casefold() for doc in old for lib in doc["libraries"]
                 for event in lib["events"] if "text" in event}
    for document in (development, evaluation):
        for library in document["libraries"]:
            require(library["family"] not in old_families, "old scenario family reused")
            require(not any(e["text"].casefold() in old_texts for e in library["events"] if "text" in e),
                    "old source text reused")
    return development, evaluation


def reviews(document):
    split = document["split"]
    path = c.WORK / "authored" / f"{split}.json"
    review = load(c.WORK / "reviews" / f"{split}.json")
    require(review["split"] == split and review["inputSHA256"] == c.digest(path), "stale review")
    require(review["author"] == f"/root/history_author_{'dev' if split == 'development' else 'eval'}"
            and review["reviewer"] != review["author"] and bool(review["reviewer"]), "independent review required")
    require(len(review["libraries"]) == 12 and {r["id"] for r in review["libraries"]}
            == {lib["id"] for lib in document["libraries"]}, "review incomplete")
    require(all(r["verdict"] == "pass" for r in review["libraries"]), "unresolved review verdict")
    issues = review["crossLibraryIssues"] + [issue for r in review["libraries"] for issue in r["issues"]]
    require(all(issue["severity"] == "warning" for issue in issues), "unresolved review error")


def source_packet(library):
    packet = observed_inputs(library)
    scopes = {t["id"]: t["scope"] for t in library["tasks"]}
    for query in packet["queries"]: query["scope"] = scopes[query["id"]]
    return packet


def native_run(library):
    # expectedState is the ideal-state oracle for the legacy native ledger harness;
    # the index itself receives only provenance events, never this expected state.
    run = compile_library(library)
    run["id"] = "history-" + run["id"]
    run["queries"] = [dict(id=t["id"], afterEvent=t["atEvent"], scope=t["scope"], limit=10000)
                      for t in library["tasks"]]
    return run


def bindings():
    paths = [c.WORK / name for name in ("PLAN.md", "BUDGET.md", "approval.json", "AUDIT.md",
                                       "native-build.json", "native-preparation.json")]
    paths.append(c.RUN / "project/Sources/bindings.json")
    paths += sorted((c.WORK / "authored").glob("*"))
    paths += sorted((c.WORK / "reviews").glob("*"))
    paths += sorted(c.CODE.glob("*.py")) + sorted(c.CODE.glob("*.swift"))
    return {str(p.relative_to(c.ROOT)): c.digest(p) for p in paths if p.is_file()}


def freeze():
    c.verify_preserved()
    docs = validate_documents()
    for doc in docs: reviews(doc)
    manifest = dict(schemaVersion=1, checkpoint="history-coverage-1", hashes=bindings(),
                    libraries=24, events=288, queries=96, rankingMeasured=False,
                    heldOutUse="coverage/integrity only; no policy selection", checkpoint2Allowed=False)
    c.publish(c.WORK / "frozen.json", manifest)
    return manifest


def verify():
    manifest = load(c.WORK / "frozen.json")
    require(manifest["hashes"] == bindings(), "frozen history inputs/code changed")
    c.verify_preserved()
    return manifest


def prepare(maximum=None):
    require(maximum is None or maximum > 0, "max-units must be positive")
    verify()
    binding = c.digest(c.WORK / "frozen.json")
    made = 0
    for document in documents():
        for library in document["libraries"]:
            c.boundary()
            folder = c.WORK / "units" / library["id"]
            output = {"source-only.json": source_packet(library), "native.json": native_run(library)}
            receipt = dict(libraryId=library["id"], bindingSHA256=binding,
                           inputSHA256=__import__("hashlib").sha256(c.encoded(library)).hexdigest(),
                           outputs={name: __import__("hashlib").sha256(c.encoded(value)).hexdigest()
                                    for name, value in output.items()})
            existed = (folder / "receipt.json").exists()
            for name, value in output.items(): c.publish(folder / name, value)
            c.publish(folder / "receipt.json", receipt)
            if not existed:
                made += 1
                if maximum is not None and made >= maximum:
                    raise c.Paused("bounded fixture-unit limit")
    c.publish(c.RUN / "input.json", dict(schemaVersion=1,
              runs=[native_run(lib) for doc in documents() for lib in doc["libraries"]]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "freeze", "prepare", "verify"))
    parser.add_argument("--max-units", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.command == "validate":
        validate_documents()
        print("24 history libraries validated (not reviewed/frozen by this command)")
        return
    try:
        with c.worker(resume=args.resume):
            if args.command == "freeze": freeze()
            elif args.command == "prepare": prepare(args.max_units)
            else: verify()
        print(json.dumps(dict(command=args.command, status="complete", checkpoint2Allowed=False)))
    except c.Paused as error:
        print(json.dumps(dict(status="paused", reason=str(error), workerStopped=True)))


if __name__ == "__main__": main()
