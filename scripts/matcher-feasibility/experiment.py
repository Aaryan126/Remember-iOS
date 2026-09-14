#!/usr/bin/env python3
"""Stage-1 data projection, review comparison, integrity checks and immutable freeze.

No model inference. All filesystem writes are explicit CLI outputs and refuse
overwrites. Review context names are arbitrary; comparisons use source pairs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Evaluation/MatcherFeasibility"
SPLITS = {"train": 18, "development": 6, "test": 6}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    """Install fully flushed JSON without replacing a completed artifact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), f"refusing overwrite: {path}")
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Hard-link publication fails if a concurrent writer already completed it.
        os.link(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        os.unlink(temporary)


def normalized(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


def validate_inputs(inputs, complete=True):
    require(set(inputs) == {"schemaVersion", "libraries"} and inputs["schemaVersion"] == 1,
            "invalid input root")
    seen_libraries, seen_items, texts = set(), set(), set()
    counts = Counter()
    for library in inputs["libraries"]:
        require(set(library) == {"id", "split", "items"}, "input library contains forbidden metadata")
        lid = library["id"]
        require(re.fullmatch(r"mf\d{2}", lid) and lid not in seen_libraries, "invalid/duplicate library")
        seen_libraries.add(lid)
        require(library["split"] in SPLITS, "invalid split")
        number = int(lid[2:])
        expected = "train" if 1 <= number <= 18 else "development" if 19 <= number <= 24 else "test" if 25 <= number <= 30 else None
        require(library["split"] == expected, "library ID/split mismatch")
        counts[library["split"]] += 1
        require(len(library["items"]) == 20, f"{lid}: expected 20 inputs")
        require({i.get("id") for i in library["items"]} == {f"{lid}-i{n:02}" for n in range(1, 21)},
                "library source IDs must cover i01 through i20")
        for item in library["items"]:
            require(set(item) == {"id", "text"}, "labels or metadata leaked into input")
            require(isinstance(item["id"], str) and re.fullmatch(lid + r"-i\d{2}", item["id"]), "invalid item ID")
            require(item["id"] not in seen_items, "duplicate item ID")
            seen_items.add(item["id"])
            require(isinstance(item["text"], str) and item["text"].strip(), "empty/nontext input")
            require(not re.search(r"mf\d{2}-[cg]\d", item["text"]), "internal context ID leaked into text")
            value = normalized(item["text"])
            require(value not in texts, "duplicate normalized source text")
            texts.add(value)
    if complete:
        require(dict(counts) == SPLITS, f"unexpected split counts: {counts}")
    return {"libraries": len(seen_libraries), "items": len(seen_items), "splits": dict(counts)}


def project(authors, complete=True, amendments=None):
    libraries, labels = [], []
    domains, templates = set(), set()
    for document in authors:
        require(document["schemaVersion"] == 1, "invalid author schema")
        for row in document["libraries"]:
            for key, used in [("domain", domains), ("templateFamily", templates)]:
                value = normalized(row[key])
                require(value and value not in used, f"repeated {key}")
                used.add(value)
            libraries.append({"id": row["id"], "split": row["split"],
                              "items": [{"id": i["id"], "text": i["text"]} for i in row["items"]]})
            context_ids = [g["id"] for g in row["contexts"]]
            require(len(set(context_ids)) == len(context_ids) and 4 <= len(context_ids) <= 6,
                    "invalid author contexts")
            require(all(type(i["ambiguous"]) is bool for i in row["items"]), "invalid ambiguity flag")
            labels.append({"id": row["id"], "groups": [
                {"id": g["id"], "members": [i["id"] for i in row["items"] if g["id"] in i["memberships"]],
                 "evidence": g["description"]} for g in row["contexts"]],
                "relatedGroupPairs": row["relatedContextPairs"],
                "ambiguous": [{"id": i["id"], "reason": i["rationale"]} for i in row["items"] if i["ambiguous"]],
                "issues": []})
            for item in row["items"]:
                require(len(set(item["memberships"])) == len(item["memberships"]), "duplicate membership")
                require(set(item["memberships"]).issubset(context_ids), "unknown author membership")
                require(bool(item["memberships"]) != item["ambiguous"], "ambiguous membership inconsistency")
    inputs = {"schemaVersion": 1, "libraries": sorted(libraries, key=lambda r: r["id"])}
    gold = {"schemaVersion": 1, "libraries": sorted(labels, key=lambda r: r["id"])}
    if amendments is not None:
        require(amendments.get("schemaVersion") == 1, "invalid amendment schema")
        by_id = {i["id"]: i for r in inputs["libraries"] for i in r["items"]}
        seen = set()
        for change in amendments["items"]:
            require(change["id"] in by_id and change["id"] not in seen, "invalid/duplicate amended item")
            item = by_id[change["id"]]
            require(hashlib.sha256(item["text"].encode()).hexdigest() == change["originalTextSHA256"], "amendment original hash mismatch")
            require(isinstance(change["reason"], str) and change["reason"].strip(), "amendment needs reason")
            require(isinstance(change["text"], str) and change["text"].strip(), "amendment needs text")
            item["text"] = change["text"]
            seen.add(change["id"])
    validate_inputs(inputs, complete=complete)
    validate_labels(inputs, gold)
    return inputs, gold


def library_truth(library, label):
    require(label["id"] == library["id"], "label library ID mismatch")
    ids = {i["id"] for i in library["items"]}
    memberships = {i: set() for i in ids}
    groups = set()
    ambiguous = set()
    for item in label["ambiguous"]:
        require(item["id"] in ids and item["id"] not in ambiguous, "invalid/duplicate ambiguous ID")
        require(isinstance(item["reason"], str) and item["reason"].strip(), "ambiguity needs reason")
        ambiguous.add(item["id"])
    for group in label["groups"]:
        require(isinstance(group["id"], str) and group["id"] and group["id"] not in groups, "invalid/duplicate group")
        groups.add(group["id"])
        require(isinstance(group["evidence"], str) and group["evidence"].strip(), "group needs evidence")
        members = group["members"]
        require(len(members) >= 2 and len(members) == len(set(members)), "invalid group members")
        require(set(members).issubset(ids - ambiguous), "unknown or ambiguous group member")
        for item in members:
            memberships[item].add(group["id"])
    require(all(bool(memberships[i]) != (i in ambiguous) for i in ids), "incomplete/ambiguous membership coverage")
    for group in groups:
        require(sum(value == {group} for value in memberships.values()) >= 2, "context needs two single-context sources")
    related = set()
    for pair in label["relatedGroupPairs"]:
        require(isinstance(pair, list) and len(pair) == 2 and pair[0] != pair[1] and set(pair).issubset(groups), "invalid related group pair")
        canonical = tuple(sorted(pair))
        require(canonical not in related, "duplicate related group pair")
        related.add(canonical)
    require(isinstance(label["issues"], list) and all(isinstance(i, str) for i in label["issues"]), "invalid issues")
    return memberships, ambiguous, related


def validate_labels(inputs, labels):
    require(labels["schemaVersion"] == 1, "invalid labels schema")
    by_id = {r["id"]: r for r in labels["libraries"]}
    require(len(by_id) == len(labels["libraries"]) and set(by_id) == {r["id"] for r in inputs["libraries"]}, "label library coverage mismatch")
    for row in inputs["libraries"]:
        library_truth(row, by_id[row["id"]])


def pair_rows(library, label):
    memberships, ambiguous, related = library_truth(library, label)
    result = []
    for first, second in combinations(sorted(memberships), 2):
        if first in ambiguous or second in ambiguous:
            relation = "uncertain"
        elif memberships[first] & memberships[second]:
            relation = "same"
        elif any(tuple(sorted((a, b))) in related for a in memberships[first] for b in memberships[second]):
            relation = "related"
        else:
            relation = "unrelated"
        result.append({"first": first, "second": second, "relation": relation})
    return result


def validate_review(inputs, review):
    require(review.get("blindToAuthorLabels") is True and review.get("blindToPredictions") is True, "review is not blind")
    require(isinstance(review.get("reviewer"), str) and review["reviewer"], "missing reviewer")
    require(isinstance(review.get("model"), str) and review["model"], "missing model provenance")
    validate_labels(inputs, review)


def compare(inputs, first, second):
    validate_labels(inputs, first)
    validate_labels(inputs, second)
    a, b = [{r["id"]: r for r in doc["libraries"]} for doc in (first, second)]
    differences = []
    for library in inputs["libraries"]:
        left, right = pair_rows(library, a[library["id"]]), pair_rows(library, b[library["id"]])
        diff = [{"first": x["first"], "second": x["second"], "a": x["relation"], "b": y["relation"]}
                for x, y in zip(left, right) if x["relation"] != y["relation"]]
        if diff:
            differences.append({"id": library["id"], "pairs": diff})
    return {"schemaVersion": 1, "disagreementLibraries": len(differences),
            "disagreementPairs": sum(len(r["pairs"]) for r in differences), "libraries": differences}


def merge_reviews(inputs, batches, batch_inputs):
    """Bind each review to the sources it saw, including superseded revisions."""
    require(bool(batches) and len(batches) == len(batch_inputs), "review/input batch count mismatch")
    require(len({b["reviewer"] for b in batches}) == 1, "cannot merge different reviewers")
    require(len({b["model"] for b in batches}) == 1, "review model provenance changed")
    rows, reviewed_sources = {}, {}
    for batch, sources in zip(batches, batch_inputs):
        validate_inputs(sources, complete=False)
        validate_review(sources, batch)
        rows.update({r["id"]: r for r in batch["libraries"]})
        reviewed_sources.update({r["id"]: r for r in sources["libraries"]})
    final_sources = {r["id"]: r for r in inputs["libraries"]}
    require(reviewed_sources == final_sources, "latest reviewed sources differ from final inputs")
    result = {k: batches[0][k] for k in ["schemaVersion", "reviewer", "model", "blindToAuthorLabels", "blindToPredictions"]}
    result["libraries"] = sorted(rows.values(), key=lambda r: r["id"])
    validate_review(inputs, result)
    return result


def audit(inputs, labels, historical=None):
    totals = validate_inputs(inputs)
    validate_labels(inputs, labels)
    by_id = {r["id"]: r for r in labels["libraries"]}
    pairs, libraries = [], []
    all_items = []
    for library in inputs["libraries"]:
        values = pair_rows(library, by_id[library["id"]])
        counts = Counter(p["relation"] for p in values)
        memberships, ambiguous, _ = library_truth(library, by_id[library["id"]])
        bridges = sum(len(v) > 1 for v in memberships.values())
        lengths = [len(i["text"].split()) for i in library["items"]]
        libraries.append({"id": library["id"], "split": library["split"], "pairs": dict(counts),
                          "ambiguousItems": len(ambiguous), "bridgeItems": bridges,
                          "wordCountMin": min(lengths), "wordCountMax": max(lengths)})
        pairs.append({"id": library["id"], "split": library["split"], "pairs": values})
        all_items.extend((library["split"], item) for item in library["items"])
    corpus_classes = Counter()
    for row in libraries:
        corpus_classes.update(row["pairs"])
    require(all(corpus_classes[c] > 0 for c in ("same", "related", "unrelated", "uncertain")), "missing corpus class coverage")
    require(sum(r["bridgeItems"] for r in libraries) > 0, "corpus needs bridge examples")
    # Detect repeated surface templates across splits; findings need adjudication,
    # not automatic relabeling. Exact duplicates already fail input validation.
    def shingles(text):
        words = normalized(text).split()
        return set(zip(*(words[i:] for i in range(5))))
    prepared = [(split, item, shingles(item["text"])) for split, item in all_items]
    overlap = []
    for (sa, a, ga), (sb, b, gb) in combinations(prepared, 2):
        if sa == sb or not ga or not gb:
            continue
        score = len(ga & gb) / len(ga | gb)
        if score >= 0.20:
            overlap.append({"first": a["id"], "second": b["id"], "fiveGramJaccard": score})
    historical_matches = []
    if historical:
        old = {normalized(i["text"]) for row in historical["libraries"] for i in row["items"]}
        historical_matches = [i["id"] for _, i in all_items if normalized(i["text"]) in old]
        require(not historical_matches, "duplicate historical benchmark source")
    return {"schemaVersion": 1, **totals, "pairCount": sum(len(r["pairs"]) for r in pairs),
            "libraries": libraries, "crossSplitTemplateFlags": overlap, "historicalExactMatches": historical_matches,
            "limitations": "Lexical screening cannot prove semantic or template independence. Agent review is not human validation."}, {"schemaVersion": 1, "libraries": pairs}


def verify_freeze(path):
    manifest = read(path)
    require(manifest.get("schemaVersion") == 1 and manifest.get("stage") == 1, "invalid freeze")
    require(bool(manifest.get("files")), "empty freeze")
    for name, expected in manifest["files"].items():
        target = (ROOT / name).resolve()
        require(target.is_relative_to(ROOT.resolve()), "freeze path escapes repository")
        require(target.is_file() and sha(target) == expected, f"frozen artifact mismatch: {name}")
    return {"verified": True, "files": len(manifest["files"]), "freezeSHA256": sha(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("project")
    p.add_argument("--authors", nargs="+", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--partial", action="store_true", help="review-only projection before all author batches arrive")
    p.add_argument("--amendments")
    p = sub.add_parser("audit")
    p.add_argument("--inputs", required=True)
    p.add_argument("--labels", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--historical")
    p = sub.add_parser("compare")
    p.add_argument("--inputs", required=True)
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("freeze")
    p.add_argument("--release", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("verify")
    p.add_argument("--freeze", required=True)
    p = sub.add_parser("baseline-context")
    p.add_argument("--output", required=True)
    p = sub.add_parser("merge-reviews")
    p.add_argument("--inputs", required=True)
    p.add_argument("--batches", nargs="+", required=True)
    p.add_argument("--batch-inputs", nargs="+", required=True, help="source-only input file for each review batch, in matching order")
    p.add_argument("--output", required=True)
    p = sub.add_parser("finalize")
    p.add_argument("--release", required=True)
    p.add_argument("--decisions", required=True)
    args = parser.parse_args()
    if args.command == "project":
        inputs, labels = project([read(p) for p in args.authors], complete=not args.partial,
                                amendments=read(args.amendments) if args.amendments else None)
        output = Path(args.output)
        require(not output.exists(), "projection release already exists")
        save(output / "inputs.json", inputs)
        save(output / "author-labels.json", labels)
        for split in SPLITS:
            save(output / f"inputs-{split}.json", {"schemaVersion": 1, "libraries": [r for r in inputs["libraries"] if r["split"] == split]})
        print(json.dumps(validate_inputs(inputs, complete=not args.partial)))
    elif args.command == "audit":
        report, pairs = audit(read(args.inputs), read(args.labels), read(args.historical) if args.historical else None)
        output = Path(args.output)
        require(not output.exists(), "audit output already exists")
        save(output / "validation.json", report)
        save(output / "pairs.json", pairs)
        print(json.dumps({k: v for k, v in report.items() if k != "libraries"}))
    elif args.command == "compare":
        result = compare(read(args.inputs), read(args.a), read(args.b))
        save(args.output, result)
        print(json.dumps({k: v for k, v in result.items() if k != "libraries"}))
    elif args.command == "verify":
        print(json.dumps(verify_freeze(args.freeze)))
    elif args.command == "merge-reviews":
        batches = [read(p) for p in args.batches]
        # Later batches explicitly supersede the SAME reviewer's earlier source
        # version; preserve every batch and record the lineage in the aggregate.
        result = merge_reviews(read(args.inputs), batches, [read(p) for p in args.batch_inputs])
        result["batchSHA256"] = {str(Path(p).resolve().relative_to(ROOT)): sha(p) for p in args.batches}
        result["sourceLineage"] = [{"review": str(Path(review).resolve().relative_to(ROOT)),
                                    "inputs": str(Path(source).resolve().relative_to(ROOT)),
                                    "inputsSHA256": sha(source)}
                                   for review, source in zip(args.batches, args.batch_inputs)]
        save(args.output, result)
        print(json.dumps({"reviewer": result["reviewer"], "libraries": len(result["libraries"])}))
    elif args.command == "finalize":
        release = Path(args.release)
        inputs = read(release / "inputs.json")
        decisions = read(args.decisions)
        a, b = [read(DATA / f"reviews/reviewer-{name}.json") for name in ["a", "b"]]
        validate_review(inputs, a)
        validate_review(inputs, b)
        choices = {"reviewer-a": {r["id"]: r for r in a["libraries"]}, "reviewer-b": {r["id"]: r for r in b["libraries"]}}
        require(decisions.get("resolved") is True, "unresolved adjudication decisions")
        rows = []
        for decision in decisions["libraries"]:
            require(isinstance(decision.get("reason"), str) and decision["reason"].strip(), "adjudication requires reason")
            selection = decision["selection"]
            require(selection in {*choices, "custom"}, "invalid adjudication selection")
            row = decision["label"] if selection == "custom" else choices[selection][decision["id"]]
            require(row["id"] == decision["id"], "adjudication ID mismatch")
            rows.append(row)
        labels = {"schemaVersion": 1, "libraries": sorted(rows, key=lambda r: r["id"])}
        validate_labels(inputs, labels)
        audit(inputs, labels)
        save(release / "labels.json", labels)
        for split in SPLITS:
            ids = {r["id"] for r in inputs["libraries"] if r["split"] == split}
            save(release / f"labels-{split}.json", {"schemaVersion": 1, "libraries": [r for r in labels["libraries"] if r["id"] in ids]})
        adjudication = {**decisions, "inputsSHA256": sha(release / "inputs.json"), "labelsSHA256": sha(release / "labels.json"),
                        "reviewSHA256": {"reviewer-a": sha(DATA / "reviews/reviewer-a.json"), "reviewer-b": sha(DATA / "reviews/reviewer-b.json")},
                        "decisionSourceSHA256": sha(args.decisions)}
        save(DATA / "reviews/adjudication.json", adjudication)
        print(json.dumps({"finalizedLibraries": len(rows), "labelsSHA256": adjudication["labelsSHA256"]}))
    elif args.command == "baseline-context":
        previous = ROOT / "Evaluation/Organization"
        artifacts = [previous / "freeze.json", previous / "results/core-complete-score-2026-09-11.json",
                     previous / "results/core-complete-2026-09-11.json.gz", previous / "inputs-reviewed.json",
                     previous / "labels.json", ROOT / "docs/evaluations/2026-09-10-organization-benchmark.md"]
        source = sorted((ROOT / "Remember/Remember").glob("*.swift")) + sorted((ROOT / "Remember/Shared").glob("*.swift"))
        snapshot = {"schemaVersion": 1, "capturedAt": datetime.now(timezone.utc).isoformat(),
                    "historicalBaselineOnly": True, "comparableToNewDataset": False,
                    "englishHeldout": {"embedding": {"pairPrecision": 0.7712, "pairRecall": 0.3165},
                                       "embeddingPlusLocalReasoning": {"pairPrecision": 0.1801, "pairRecall": 0.5950}},
                    "artifacts": {str(p.relative_to(ROOT)): sha(p) for p in artifacts},
                    "productionSources": {str(p.relative_to(ROOT)): sha(p) for p in source}}
        save(args.output, snapshot)
        print(json.dumps({"historicalArtifacts": len(artifacts), "productionSources": len(source)}))
    elif args.command == "freeze":
        release = Path(args.release).resolve()
        require(release.is_relative_to(DATA.resolve()), "release must be in experiment directory")
        inputs, labels = read(release / "inputs.json"), read(release / "labels.json")
        validate_inputs(inputs)
        validate_labels(inputs, labels)
        a, b = read(DATA / "reviews/reviewer-a.json"), read(DATA / "reviews/reviewer-b.json")
        validate_review(inputs, a)
        validate_review(inputs, b)
        require(a["reviewer"] != b["reviewer"], "reviewers must differ")
        adjudication = read(DATA / "reviews/adjudication.json")
        require(adjudication.get("resolved") is True, "adjudication unresolved")
        require(adjudication.get("inputsSHA256") == sha(release / "inputs.json"), "adjudication input binding mismatch")
        require(adjudication.get("labelsSHA256") == sha(release / "labels.json"), "adjudication label binding mismatch")
        require(adjudication.get("reviewSHA256") == {"reviewer-a": sha(DATA / "reviews/reviewer-a.json"),
                                                    "reviewer-b": sha(DATA / "reviews/reviewer-b.json")}, "adjudication review binding mismatch")
        decisions = adjudication.get("libraries", [])
        require(len(decisions) == 30 and {r["id"] for r in decisions} == {r["id"] for r in inputs["libraries"]}, "adjudication coverage mismatch")
        require(all(isinstance(r.get("reason"), str) and r["reason"].strip() for r in decisions), "adjudication needs source-grounded reasons")
        report, _ = audit(inputs, labels, read(ROOT / "Evaluation/Organization/inputs-reviewed.json"))
        require(not report["crossSplitTemplateFlags"], "unresolved cross-split lexical template flags")
        files = [DATA / "CONTRACT.md", DATA / "PLAN.md", DATA / "configuration.json", DATA / "model-manifest.json", DATA / "environment.lock.txt", DATA / "environment.json", DATA / "baseline-context.json"]
        files += sorted((DATA / "authoring").glob("*.json"))
        files += sorted((DATA / "reviews").glob("*.json"))
        files += sorted((DATA / "review-inputs").rglob("*.json"))
        files += sorted(release.rglob("*.json"))
        files += [Path(__file__).resolve(), Path(__file__).with_name("test_experiment.py"), Path(__file__).with_name("environment.py"), Path(__file__).with_name("requirements.in")]
        require(all(p.is_file() for p in files), "missing freeze artifact")
        manifest = {"schemaVersion": 1, "stage": 1, "createdAt": datetime.now(timezone.utc).isoformat(),
                    "status": "prepared_not_evaluated", "testResultsOpened": False,
                    "files": {str(p.relative_to(ROOT)): sha(p) for p in files}}
        save(args.output, manifest)
        print(json.dumps(verify_freeze(args.output)))


if __name__ == "__main__":
    main()
