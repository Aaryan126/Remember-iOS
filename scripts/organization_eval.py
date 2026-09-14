#!/usr/bin/env python3
"""Deterministic, dependency-free organization benchmark validation and scoring."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import gzip
import itertools
import json
import math
from pathlib import Path
import random
import statistics


def read(path):
    path = Path(path)
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def memberships(value, ids):
    require(isinstance(value, dict) and set(value) == set(ids), "membership IDs must exactly cover inputs")
    result = {}
    for item, groups in value.items():
        require(isinstance(groups, list) and groups and all(isinstance(g, str) and g for g in groups),
                f"invalid memberships for {item}")
        require(len(set(groups)) == len(groups), f"duplicate membership for {item}")
        result[item] = set(groups)
    return result


def validate(inputs, labels=None):
    require(inputs.get("schemaVersion") == 1, "unsupported input schema")
    seen, libraries = set(), set()
    for library in inputs["libraries"]:
        require(library["id"] not in libraries, "duplicate library")
        libraries.add(library["id"])
        require(library["split"] in {"development", "heldout", "public"}, "invalid split")
        require(library["slice"] in {"english", "multilingual", "public", "media"}, "invalid slice")
        require(bool(library["items"]), "empty library")
        for item in library["items"]:
            require(item["id"] not in seen, "duplicate item")
            seen.add(item["id"])
            require(isinstance(item["text"], str), "invalid text")
            require(isinstance(item["timestamp"], (int, float)) and math.isfinite(item["timestamp"]), "invalid time")
            require(item["kind"] in {"text", "image", "pdf", "audio", "video", "link"}, "invalid kind")
            require(not any(k in item for k in ("memberships", "topic", "label", "gold")), "label leaked into input")
    if labels is not None:
        require(labels.get("schemaVersion") == 1, "unsupported label schema")
        rows = labels["libraries"]
        require(len(rows) == len(libraries) and {r["id"] for r in rows} == libraries, "label library mismatch")
        by_id = {r["id"]: r for r in rows}
        for library in inputs["libraries"]:
            row = by_id[library["id"]]
            ids = [i["id"] for i in library["items"]]
            groups = memberships(row["memberships"], ids)
            require(set(row.get("ambiguous", [])).issubset(ids), "unknown ambiguous item")
            all_groups = set().union(*groups.values())
            for relation in row.get("relationships", []):
                require(relation["first"] in all_groups and relation["second"] in all_groups,
                        "unknown relationship group")
                require(relation["first"] != relation["second"], "self relationship")
                require(type(relation["related"]) is bool, "invalid relation truth")
                require(set(relation["evidence"]).issubset(ids), "unknown relationship evidence")
    return {"libraries": len(libraries), "items": len(seen)}


def ratio(a, b):
    return a / b if b else None


def harmonic(a, b):
    return None if a is None or b is None else (2 * a * b / (a + b) if a + b else 0.0)


def cluster_metrics(gold, predicted, excluded=()):
    ids = sorted(set(gold) - set(excluded))
    require(set(gold) == set(predicted), "missing or unexpected predictions")
    tp = fp = fn = tn = 0
    for a, b in itertools.combinations(ids, 2):
        g, p = bool(gold[a] & gold[b]), bool(predicted[a] & predicted[b])
        if g and p: tp += 1
        elif p: fp += 1
        elif g: fn += 1
        else: tn += 1
    b_precision, b_recall = [], []
    for a in ids:
        precision, recall = [], []
        for b in ids:
            p, g = len(predicted[a] & predicted[b]), len(gold[a] & gold[b])
            if p: precision.append(min(p, g) / p)
            if g: recall.append(min(p, g) / g)
        b_precision.append(statistics.mean(precision))
        b_recall.append(statistics.mean(recall))
    bp = statistics.mean(b_precision) if ids else None
    br = statistics.mean(b_recall) if ids else None
    groups = {g for i in ids for g in gold[i]}
    fragmentation = {g: len({p for i in ids if g in gold[i] for p in predicted[i]}) for g in sorted(groups)}
    return {"evaluatedItems": len(ids), "ambiguousItems": len(set(gold) - set(ids)),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "pairPrecision": ratio(tp, tp + fp), "pairRecall": ratio(tp, tp + fn),
            "pairF1": harmonic(ratio(tp, tp + fp), ratio(tp, tp + fn)),
            "bcubedPrecision": bp, "bcubedRecall": br, "bcubedF1": harmonic(bp, br),
            "goldThreads": len(groups), "predictedThreads": len({p for i in ids for p in predicted[i]}),
            "fragmentation": fragmentation,
            "groupedItemFraction": ratio(sum(any(predicted[i] & predicted[j] for j in ids if i != j) for i in ids), len(ids))}


def baselines(library, label):
    ids = [i["id"] for i in library["items"]]
    gold = memberships(label["memberships"], ids)
    singleton = {i: {i} for i in ids}
    exact = {i["id"]: {hashlib.sha256(" ".join(i["text"].casefold().split()).encode()).hexdigest()}
             for i in library["items"]}
    return {"singleton": cluster_metrics(gold, singleton, label.get("ambiguous", [])),
            "exactText": cluster_metrics(gold, exact, label.get("ambiguous", []))}


def bootstrap(values):
    if not values: return None
    rng = random.Random(1729)
    means = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(2000))
    return {"mean": statistics.mean(values), "libraries": len(values),
            "descriptive95Interval": [means[49], means[1949]]}


def decision_metrics(run, gold, excluded):
    """Retrospective checks are intentionally not advertised as temporal decision recall."""
    merges = correct = unsafe = unscored = 0
    for event in run.get("events", []):
        if event.get("kind") != "merge": continue
        merges += 1
        ids = set(event.get("assignments", {}))
        if len(ids) < 2 or not ids.issubset(gold) or ids & set(excluded):
            unscored += 1
        elif set.intersection(*(gold[i] for i in ids)):
            correct += 1
        else:
            unsafe += 1
    return {"mergeEvents": merges, "retrospectivelyConsistentMerges": correct,
            "retrospectivelyProhibitedMerges": unsafe, "unscoredMerges": unscored,
            "retrospectiveMergePrecision": ratio(correct, correct + unsafe),
            "mergeRecall": None, "splitProposalQuality": None,
            "limitation": "Temporal action recall requires separately labeled checkpoint opportunities."}


def edge_metrics(run, gold, label):
    if "edges" not in run:
        return {"status": "not_recorded"}
    gold_groups, observed = defaultdict(set), defaultdict(set)
    for item, groups in gold.items():
        for group in groups: gold_groups[group].add(item)
    for item, groups in run["memberships"].items():
        for group in groups: observed[group].add(item)
    mapped, tied = {}, set()
    for group, members in observed.items():
        ranked = sorted(((len(members & items) / len(members | items), key)
                         for key, items in gold_groups.items()), key=lambda x: (-x[0], x[1]))
        if ranked:
            mapped[group] = ranked[0][1]
            if len(ranked) > 1 and ranked[0][0] == ranked[1][0]: tied.add(group)
    truth = {tuple(sorted((r["first"], r["second"]))): r["related"] for r in label.get("relationships", [])}
    actual, unmapped, tie_edges = set(), 0, 0
    for edge in run["edges"]:
        a, b = edge["first"], edge["second"]
        if a not in mapped or b not in mapped: unmapped += 1; continue
        if a in tied or b in tied: tie_edges += 1
        if mapped[a] != mapped[b]: actual.add(tuple(sorted((mapped[a], mapped[b]))))
    positives = {pair for pair, related in truth.items() if related}
    tp = len(actual & positives)
    fp = sum(pair in truth and not truth[pair] for pair in actual)
    return {"status": "scored" if truth else "no_relationship_labels", "tp": tp, "fp": fp,
            "fn": len(positives - actual), "precisionOnLabeledPairs": ratio(tp, tp + fp),
            "recall": ratio(tp, len(positives)), "unlabeledEdges": len(actual - set(truth)),
            "unmappedEdges": unmapped, "tiedMappingEdges": tie_edges,
            "limitation": "Graph display is capped at40nodes; this is not cluster membership or lineage."}


def score(inputs, labels, result):
    validate(inputs, labels)
    require(result.get("schemaVersion") == 1, "unsupported result schema")
    libraries = {v["id"]: v for v in inputs["libraries"]}
    truths = {v["id"]: v for v in labels["libraries"]}
    output, seen = [], set()
    for run in result["runs"]:
        require(run["runID"] not in seen, "duplicate run ID")
        seen.add(run["runID"])
        require(run["libraryID"] in libraries, "unknown result library")
        library, label = libraries[run["libraryID"]], truths[run["libraryID"]]
        base = {k: run[k] for k in ("runID", "libraryID", "mode", "order", "repeat", "status")}
        base.update(split=library["split"], slice=library["slice"])
        base["mediaMode"] = run.get("mediaMode", "not_applicable")
        base["availability"] = run.get("availability", {})
        base["extractionCoverage"] = {"attempted": len(run.get("extractions", [])),
            "completed": sum(r.get("status") == "completed" for r in run.get("extractions", [])),
            "blockedIDs": [r["itemID"] for r in run.get("extractions", []) if r.get("status") == "blocked"],
            "noEvidenceIDs": [r["itemID"] for r in run.get("extractions", []) if r.get("status") == "no_source_evidence"],
            "expectedNoEvidenceIDs": [r["itemID"] for r in run.get("extractions", []) if r.get("expectedNoEvidence") is True]}
        base["timings"] = run.get("timings", {})
        if run["status"] != "completed":
            output.append(dict(base, failure=run.get("error", "incomplete scenario")))
            continue
        ids = [i["id"] for i in library["items"]]
        require(len(run["inputIDs"]) == len(ids) and set(run["inputIDs"]) == set(ids), "run input coverage mismatch")
        gold, prediction = memberships(label["memberships"], ids), memberships(run["memberships"], ids)
        measured = cluster_metrics(gold, prediction, label.get("ambiguous", []))
        steps = []
        for snapshot in run.get("snapshots", []):
            step_ids = set(snapshot["memberships"])
            require(step_ids.issubset(ids), "snapshot contains unknown input")
            # Final gold context is a diagnostic only, not a temporal expectation oracle.
            steps.append({"step": snapshot["step"], "retrospectiveOnly": True,
                          **cluster_metrics({i: gold[i] for i in step_ids},
                                            memberships(snapshot["memberships"], step_ids), label.get("ambiguous", []))})
        output.append(dict(base, metrics=measured, retrospectiveSteps=steps,
                           eventCount=len(run.get("events", [])),
                           decisionQuality=decision_metrics(run, gold, label.get("ambiguous", [])),
                           relationshipQuality=edge_metrics(run, gold, label)))
    aggregates = []
    for mode, split, slice_name, media_mode in sorted({(r["mode"], r["split"], r["slice"], r["mediaMode"]) for r in output}):
        selected = [r for r in output if (r["mode"], r["split"], r["slice"], r["mediaMode"]) == (mode, split, slice_name, media_mode)]
        by_library = defaultdict(list)
        for row in selected:
            if "metrics" in row: by_library[row["libraryID"]].append(row["metrics"])
        summary = {}
        for metric in ("pairPrecision", "pairRecall", "bcubedPrecision", "bcubedRecall", "groupedItemFraction"):
            values = [statistics.mean([m[metric] for m in rows if m[metric] is not None])
                      for rows in by_library.values() if any(m[metric] is not None for m in rows)]
            summary[metric] = bootstrap(values)
        aggregates.append({"mode": mode, "split": split, "slice": slice_name, "mediaMode": media_mode,
                           "completedRuns": sum("metrics" in r for r in selected), "attemptedRuns": len(selected),
                           "blockedExtractions": sum(len(r["extractionCoverage"]["blockedIDs"]) for r in selected),
                           "noEvidenceExtractions": sum(len(r["extractionCoverage"]["noEvidenceIDs"]) for r in selected),
                           "unavailableEmbeddingObservations": sum(len(r["availability"].get("unavailableEmbeddingIDs", [])) for r in selected),
                           "macroAcrossLibraries": summary})
    expected = set(result.get("manifest", {}).get("expectedRunIDs", []))
    return {"schemaVersion": 1, "runs": output, "aggregates": aggregates,
            "baselines": {i: baselines(libraries[i], truths[i]) for i in libraries},
            "missingLibraries": sorted(set(libraries) - {r["libraryID"] for r in output}),
            "missingRequestedRuns": sorted(expected - seen),
            "limitations": ["Agent-reviewed labels are not human ground truth.",
                            "Missing runs are not successes; compare against the requested run manifest.",
                            "Intervals resample libraries, not dependent pairs or arrival orders."]}


def freeze(inputs_path, labels_path, review_paths, contract_path, evidence_paths=()):
    inputs, labels = read(inputs_path), read(labels_path)
    counts = validate(inputs, labels)
    require(len(review_paths) >= 2, "two independent reviews required")
    reviewers = set()
    for path in review_paths:
        review = read(path)
        require(review.get("blindToPredictions") is True, "review must be blind")
        require(review.get("inputsSHA256") == digest(inputs_path), "review is not bound to current inputs")
        require(review["reviewer"] not in reviewers, "reviewers must be distinct")
        reviewers.add(review["reviewer"])
        validate(inputs, {"schemaVersion": 1, "libraries": review["libraries"]})
    return {"schemaVersion": 1, "inputsSHA256": digest(inputs_path), "labelsSHA256": digest(labels_path),
            "contractSHA256": digest(contract_path), "scorerSHA256": digest(__file__),
            "reviews": [{"path": str(p), "sha256": digest(p)} for p in review_paths],
            "evidence": [{"path": str(p), "sha256": digest(p)} for p in evidence_paths],
            "counts": counts, "targets": {"pairPrecision": .99, "pairRecall": .85, "prohibitedMerges": 0},
            "claim": "agent-reviewed baseline; no human validation or model-family independence claimed"}


def verify_frozen_score(inputs_path, labels_path, results, freeze_path, contract_path):
    frozen = read(freeze_path)
    require(frozen.get("inputsSHA256") == digest(inputs_path), "frozen inputs mismatch")
    require(frozen.get("labelsSHA256") == digest(labels_path), "frozen labels mismatch")
    require(results.get("manifest", {}).get("inputsSHA256") == digest(inputs_path), "results input hash mismatch")
    require(results.get("manifest", {}).get("freezeSHA256") == digest(freeze_path), "results were not run with this freeze")
    if "scorerSHA256" in frozen:
        require(frozen["scorerSHA256"] == digest(__file__), "scorer changed after freeze")
    if "contractSHA256" in frozen:
        require(frozen["contractSHA256"] == digest(contract_path), "contract changed after freeze")
    return {"inputsAndLabelsBound": True, "scorerBound": "scorerSHA256" in frozen,
            "contractBound": "contractSHA256" in frozen}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    archive = sub.add_parser("archive")
    archive.add_argument("--results", type=Path, required=True)
    archive.add_argument("--output", type=Path, required=True)
    for name in ("validate", "score", "freeze"):
        p = sub.add_parser(name)
        p.add_argument("--inputs", type=Path, required=True)
        p.add_argument("--labels", type=Path, required=True)
        p.add_argument("--output", type=Path)
        if name == "score":
            p.add_argument("--results", type=Path, required=True)
            p.add_argument("--freeze", type=Path, required=True)
            p.add_argument("--contract", type=Path, default=Path("Evaluation/Organization/CONTRACT.md"))
        if name == "freeze":
            p.add_argument("--reviews", type=Path, nargs="+", required=True)
            p.add_argument("--contract", type=Path, default=Path("Evaluation/Organization/CONTRACT.md"))
            p.add_argument("--evidence", type=Path, nargs="*", default=[])
    args = parser.parse_args()
    if args.command == "archive":
        value = read(args.results)
        require(value.get("schemaVersion") == 1 and "runs" in value and "manifest" in value, "invalid run artifact")
        require(not args.output.exists(), "refusing to overwrite archived results")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(gzip.compress(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(), mtime=0))
        print(json.dumps({"archive": str(args.output), "sha256": digest(args.output), "runs": len(value["runs"])}))
        return
    if args.command == "validate": value = validate(read(args.inputs), read(args.labels))
    elif args.command == "score":
        result = read(args.results)
        binding = verify_frozen_score(args.inputs, args.labels, result, args.freeze, args.contract)
        value = score(read(args.inputs), read(args.labels), result)
        value["integrityBinding"] = binding
    else: value = freeze(args.inputs, args.labels, args.reviews, args.contract, args.evidence)
    text = json.dumps(value, indent=2, allow_nan=False) + "\n"
    if args.output:
        require(not args.output.exists(), "refusing to overwrite an existing artifact")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else: print(text, end="")


if __name__ == "__main__":
    main()
