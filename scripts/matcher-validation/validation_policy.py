"""Prospective operating-point rules. No model, file access or old-test imports."""
import math
from collections import Counter

RELATIONS = {"same", "related", "unrelated", "uncertain"}


def validate_rows(rows):
    seen = set()
    for row in rows:
        if not isinstance(row.get("id"), str) or not row["id"] or row["id"] in seen:
            raise ValueError("missing or duplicate prediction ID")
        seen.add(row["id"])
        if not row.get("library") or row.get("relation") not in RELATIONS:
            raise ValueError("invalid library or relation")
        if row.get("split") not in {"calibration", "evaluation"}:
            raise ValueError("pilot/training predictions cannot qualify")
        score = row.get("score")
        if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float))
                                  or not math.isfinite(score) or not 0 <= score <= 1):
            raise ValueError("invalid probability")
        if not isinstance(row.get("eligible", True), bool):
            raise ValueError("eligible must be boolean")


def accepted(row, threshold):
    return (threshold is not None and row.get("score") is not None
            and row.get("eligible", True) and row["score"] >= threshold)


def metrics(rows, threshold):
    validate_rows(rows)
    if threshold is not None and (isinstance(threshold, bool) or not isinstance(threshold, (int, float))
                                  or not math.isfinite(threshold) or not 0 <= threshold <= 1):
        raise ValueError("invalid threshold")
    per_library = {}
    for library in sorted({row["library"] for row in rows}):
        subset = [r for r in rows if r["library"] == library and r["relation"] != "uncertain"]
        tp = sum(accepted(r, threshold) and r["relation"] == "same" for r in subset)
        fp = sum(accepted(r, threshold) and r["relation"] != "same" for r in subset)
        positives = sum(r["relation"] == "same" for r in subset)
        per_library[library] = {"tp": tp, "fp": fp, "fn": positives - tp,
                                "recall": tp / positives if positives else None}
    tp, fp, fn = (sum(v[key] for v in per_library.values()) for key in ("tp", "fp", "fn"))
    recalls = [v["recall"] for v in per_library.values() if v["recall"] is not None]
    return {"tp": tp, "fp": fp, "fn": fn, "acceptedKnown": tp + fp,
            "precision": tp / (tp + fp) if tp + fp else None,
            "macroRecall": sum(recalls) / len(recalls) if recalls else None,
            "falseRelated": sum(accepted(r, threshold) and r["relation"] == "related" for r in rows),
            "falseUnrelated": sum(accepted(r, threshold) and r["relation"] == "unrelated" for r in rows),
            "acceptedUncertain": sum(accepted(r, threshold) and r["relation"] == "uncertain" for r in rows),
            "missingKnown": sum(r.get("score") is None and r["relation"] != "uncertain" for r in rows),
            "missingUncertain": sum(r.get("score") is None and r["relation"] == "uncertain" for r in rows),
            "perLibrary": per_library}


def gates(candidate, baseline, policy):
    """Use this exact rule both when choosing and when judging a hybrid threshold."""
    baseline_supported = (baseline is not None and baseline["precision"] is not None
                          and baseline["macroRecall"] is not None
                          and baseline["acceptedKnown"] >= policy["minimumAcceptedKnown"]
                          and baseline["missingKnown"] == 0)
    required_precision = max(policy["minimumPrecision"], baseline["precision"] - policy["maximumPrecisionDrop"]
                             ) if baseline_supported else policy["minimumPrecision"]
    result = {
        "baselineSupported": baseline_supported,
        "precision": candidate["precision"] is not None and candidate["precision"] >= required_precision,
        "minimumCount": candidate["acceptedKnown"] >= policy["minimumAcceptedKnown"],
        "recallGain": baseline_supported and candidate["macroRecall"] is not None
                      and candidate["macroRecall"] >= baseline["macroRecall"] + policy["minimumMacroRecallGain"],
        "completeKnownCoverage": candidate["missingKnown"] == 0,
    }
    return {"passed": all(result.values()), "checks": result, "requiredPrecision": required_precision}


def select_threshold(rows, policy, baseline=None, hybrid=False):
    validate_rows(rows)
    if not rows or {r["split"] for r in rows} != {"calibration"}:
        raise ValueError("threshold selection requires calibration rows only")
    if any(r.get("score") is None and r["relation"] != "uncertain" for r in rows):
        return None
    # Whole score ties enter together. This sweep is independent of evaluation labels.
    positives = Counter(r["library"] for r in rows if r["relation"] == "same")
    candidates = sorted((r for r in rows if r["relation"] != "uncertain"
                         and r.get("score") is not None and r.get("eligible", True)),
                        key=lambda r: -r["score"])
    tp = fp = 0
    hits = Counter()
    best = None
    for index, row in enumerate(candidates):
        if row["relation"] == "same":
            tp += 1
            hits[row["library"]] += 1
        else:
            fp += 1
        if index + 1 < len(candidates) and row["score"] == candidates[index + 1]["score"]:
            continue
        precision = tp / (tp + fp)
        recall = sum(hits[key] / n for key, n in positives.items()) / len(positives) if positives else None
        summary = {"precision": precision, "macroRecall": recall, "acceptedKnown": tp + fp, "missingKnown": 0}
        qualifies = (gates(summary, baseline, policy)["passed"] if hybrid else
                     precision >= policy["minimumPrecision"] and tp + fp >= policy["minimumAcceptedKnown"])
        if qualifies and recall is not None:
            rank = (recall, precision, row["score"])
            if best is None or rank > best:
                best = rank
    return None if best is None else {"threshold": best[2], "metrics": metrics(rows, best[2])}


def align_predictions(baseline_rows, hybrid_rows, split):
    for rows in (baseline_rows, hybrid_rows):
        validate_rows(rows)
        if not rows or {r["split"] for r in rows} != {split}:
            raise ValueError("wrong split")
    identity = lambda rows: {r["id"]: (r["library"], r["relation"]) for r in rows}
    if identity(baseline_rows) != identity(hybrid_rows):
        raise ValueError("baseline/hybrid coverage or gold differs")


def calibrate(baseline_rows, hybrid_rows, policy):
    align_predictions(baseline_rows, hybrid_rows, "calibration")
    baseline = select_threshold(baseline_rows, policy)
    hybrid = select_threshold(hybrid_rows, policy, baseline["metrics"] if baseline else None, hybrid=True)
    return {"baseline": baseline, "hybrid": hybrid}


def evaluate_frozen(baseline_rows, hybrid_rows, thresholds, policy):
    """No selection: callers must bind these thresholds in a pre-evaluation manifest."""
    align_predictions(baseline_rows, hybrid_rows, "evaluation")
    baseline = metrics(baseline_rows, thresholds["baseline"])
    hybrid = metrics(hybrid_rows, thresholds["hybrid"])
    return {"baseline": baseline, "hybrid": hybrid, "qualification": gates(hybrid, baseline, policy)}
