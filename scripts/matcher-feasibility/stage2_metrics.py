"""Pair metrics and deterministic operating-point selection; no filesystem I/O."""
from collections import Counter
import numpy as np

CLASSES = ["same", "related", "unrelated"]


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def accepted(row, threshold):
    p = row.get("probabilities")
    return bool(threshold is not None and p is not None
                and int(np.argmax(p)) == 0 and p[0] >= threshold)


def metrics(rows, threshold):
    known = [r for r in rows if r["relation"] != "uncertain"]
    ambiguous = [r for r in rows if r["relation"] == "uncertain"]
    tp = sum(accepted(r, threshold) and r["relation"] == "same" for r in known)
    fp = sum(accepted(r, threshold) and r["relation"] != "same" for r in known)
    positives = sum(r["relation"] == "same" for r in known)
    confusion = [[0] * 3 for _ in CLASSES]
    for row in known:
        if row.get("probabilities") is not None:
            confusion[CLASSES.index(row["relation"])][int(np.argmax(row["probabilities"]))] += 1
    by_library = {}
    for lid in sorted({r["library"] for r in rows}):
        subset = [r for r in known if r["library"] == lid]
        hit = sum(accepted(r, threshold) and r["relation"] == "same" for r in subset)
        wrong = sum(accepted(r, threshold) and r["relation"] != "same" for r in subset)
        count = sum(r["relation"] == "same" for r in subset)
        by_library[lid] = {"tp": hit, "fp": wrong, "fn": count - hit,
                           "precision": ratio(hit, hit + wrong), "recall": ratio(hit, count)}
    recalls = [r["recall"] for r in by_library.values() if r["recall"] is not None]
    return {"pairs": len(rows), "knownPairs": len(known), "uncertainPairs": len(ambiguous),
            "tp": tp, "fp": fp, "fn": positives - tp, "acceptedKnownPairs": tp + fp,
            "precision": ratio(tp, tp + fp), "recall": ratio(tp, positives),
            "macroLibraryRecall": float(np.mean(recalls)) if recalls else None,
            "automationFraction": ratio(sum(accepted(r, threshold) for r in rows), len(rows)),
            "acceptedUncertainPairs": sum(accepted(r, threshold) for r in ambiguous),
            "acceptedUncertainFraction": ratio(sum(accepted(r, threshold) for r in ambiguous), len(ambiguous)),
            "missingPredictionPairs": sum(r.get("probabilities") is None for r in rows),
            "classOrder": CLASSES, "argmaxConfusionMatrix": confusion,
            "perLibrary": by_library}


def select_threshold(rows, minimum_precision=0.95, minimum_accepted=30):
    """Sweep sorted same-winning scores once; tied scores enter together."""
    positives = Counter(r["library"] for r in rows if r["relation"] == "same")
    candidates = [r for r in rows if r["relation"] != "uncertain"
                  and r.get("probabilities") is not None and np.argmax(r["probabilities"]) == 0]
    candidates.sort(key=lambda r: -r["probabilities"][0])
    tp = fp = 0
    hits = Counter()
    best = None
    for index, row in enumerate(candidates):
        if row["relation"] == "same":
            tp += 1
            hits[row["library"]] += 1
        else:
            fp += 1
        threshold = row["probabilities"][0]
        if index + 1 < len(candidates) and candidates[index + 1]["probabilities"][0] == threshold:
            continue
        precision = tp / (tp + fp)
        recall = sum(hits[k] / n for k, n in positives.items()) / len(positives) if positives else 0
        if tp + fp >= minimum_accepted and precision >= minimum_precision:
            rank = (recall, precision, threshold)
            if best is None or rank > best[0]:
                best = (rank, threshold)
    return None if best is None else {"threshold": best[1], "metrics": metrics(rows, best[1])}


def bootstrap(rows, threshold, count=2000, seed=1729):
    per_library = metrics(rows, threshold)["perLibrary"]
    values = list(per_library.values())
    rng = np.random.default_rng(seed)
    samples = {"precision": [], "recall": [], "macroLibraryRecall": []}
    for _ in range(count):
        chosen = [values[i] for i in rng.integers(0, len(values), len(values))]
        tp, fp, fn = (sum(v[k] for v in chosen) for k in ("tp", "fp", "fn"))
        recalls = [v["recall"] for v in chosen if v["recall"] is not None]
        for key, value in [("precision", ratio(tp, tp + fp)), ("recall", ratio(tp, tp + fn)),
                           ("macroLibraryRecall", float(np.mean(recalls)) if recalls else None)]:
            if value is not None and np.isfinite(value):
                samples[key].append(float(value))
    return {"resamples": count, "seed": seed, "unit": "library",
            "intervals": {k: {"lower": float(np.quantile(v, .025)) if v else None,
                               "upper": float(np.quantile(v, .975)) if v else None,
                               "definedResamples": len(v)} for k, v in samples.items()},
            "limitation": "Descriptive development intervals after selection, not heldout confidence."}


def retrieval_metrics(libraries, pair_gold, candidates):
    reports = []
    for library in libraries:
        same = {i["id"]: set() for i in library["items"]}
        for pair in pair_gold[library["id"]]:
            if pair["relation"] == "same":
                same[pair["first"]].add(pair["second"])
                same[pair["second"]].add(pair["first"])
        eligible = hits = found = total = 0
        for item, relevant in same.items():
            if relevant:
                eligible += 1
                retrieved = set(candidates[item]) & relevant
                hits += bool(retrieved)
                found += len(retrieved)
                total += len(relevant)
        reports.append({"id": library["id"], "eligibleSources": eligible, "sourcesWithHit": hits,
                        "relevantCandidatesFound": found, "relevantCandidates": total})
    sums = {k: sum(r[k] for r in reports) for k in ["eligibleSources", "sourcesWithHit", "relevantCandidatesFound", "relevantCandidates"]}
    return {**sums, "atLeastOneRecallAt10": ratio(sums["sourcesWithHit"], sums["eligibleSources"]),
            "allRelevantRecall": ratio(sums["relevantCandidatesFound"], sums["relevantCandidates"]),
            "libraries": reports, "candidateCondition": "unordered pair included if either source retrieves the other"}
