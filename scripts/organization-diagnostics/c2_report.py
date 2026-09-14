#!/usr/bin/env python3
"""Semantic scoring only after all C2 predictions are frozen. Never invokes models."""
from collections import defaultdict
import argparse
from itertools import combinations
import json
import math

import c2_common as c
from c2_metrics import score_trace
from c2_policy import POLICY_IDS


def ratio(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "value": numerator / denominator if denominator else None}


def mean(values):
    defined = [value for value in values if value is not None]
    return ratio(sum(defined), len(defined))


def summarize(rows):
    counts = {key: sum(row["counts"][key] for row in rows) for key in rows[0]["counts"]}
    rates = {key: ratio(sum(row["rates"][key]["numerator"] for row in rows),
                        sum(row["rates"][key]["denominator"] for row in rows)) for key in rows[0]["rates"]}
    finals = {key: sum(row["final"]["pairs"][key] for row in rows)
              for key in ("truePositive", "falsePositive", "falseNegative", "trueNegative", "knownPairs")}
    finals["precision"] = ratio(finals["truePositive"], finals["truePositive"] + finals["falsePositive"])
    finals["recall"] = ratio(finals["truePositive"], finals["truePositive"] + finals["falseNegative"])
    return {"streams": len(rows), "counts": counts, "rates": rates, "finalPairsPooled": finals,
            "macroStreamPrefix": {key: mean([row["macroPrefix"][key]["value"] for row in rows])
                                  for key in rows[0]["macroPrefix"]},
            "finalMacro": {key: mean([row["final"]["pairs"][key]["value"] for row in rows])
                           for key in ("precision", "recall")},
            "finalStructureMacro": {key: mean([row["final"]["structure"][key]["value"] for row in rows])
                                    for key in ("fragmentedProjects", "mixedClusters")},
            "correctionErrorChange": counts["correctionErrorsAfter"] - counts["correctionErrorsBefore"]}


def order_sensitivity(traces):
    by_story = defaultdict(list)
    for trace in traces:
        by_story[trace["story"]].append(trace)
    result = []
    for story, variants in sorted(by_story.items()):
        for first, second in combinations(sorted(variants, key=lambda row: row["order"]), 2):
            a, b = first["events"][-1]["expectedState"], second["events"][-1]["expectedState"]
            c.require(set(a) == set(b), "Order final inventories differ")
            active = [key for key in sorted(a) if not a[key]["archived"] and not b[key]["archived"]]
            disagreement = 0
            for left, right in combinations(active, 2):
                same_a = bool(set(a[left]["memberships"]) & set(a[right]["memberships"]))
                same_b = bool(set(b[left]["memberships"]) & set(b[right]["memberships"]))
                disagreement += int(same_a != same_b)
            result.append({"story": story, "firstOrder": first["order"], "secondOrder": second["order"],
                           "activePairDisagreement": ratio(disagreement, len(active) * (len(active) - 1) // 2)})
    return {"comparisons": result, "macroPairDisagreement": mean([r["activePairDisagreement"]["value"] for r in result]),
            "note": "Membership overlap comparison; ignores runtime thread-name permutations. Includes uncertain-label sources."}


def verify_predictions():
    receipt = c.read(c.RUN / "predictions-complete.json")
    c.require(receipt["manifestSHA256"] == c.digest(c.RUN / "manifest.json"), "Prediction manifest changed")
    c.require(receipt["streams"] == 288 and receipt["prefixes"] == 4632, "Incomplete frozen prediction inventory")
    c.require(c.digest(c.RUN / "pair-scores.json") == receipt["pairScoresSHA256"], "Pair scores changed")
    c.require(len(receipt["traces"]) == 288, "Trace inventory incomplete")
    for name, expected in receipt["traces"].items():
        path = (c.RUN / name).resolve()
        c.require(path.is_relative_to(c.RUN) and c.digest(path) == expected, "Frozen trace changed")
    return receipt


def evaluate():
    c.verify_bindings()
    receipt = verify_predictions()
    rows, traces, errors = [], defaultdict(list), []
    for name in sorted(receipt["traces"]):
        c.boundary("metrics-" + name)
        trace = c.read_unit(c.RUN / name)
        # First semantic-gold read in this command occurs after full prediction verification.
        gold = c.read(c.DATA / f"release/gold/{trace['story']}-{trace['order']}.json")
        result = score_trace(trace, gold)
        c.publish(c.RUN / "metrics" / trace["policy"] / f"{trace['story']}-{trace['order']}.json", result)
        rows.append(result)
        traces[trace["policy"]].append(trace)
        for event, prefix in zip(trace["events"], result["prefixes"]):
            counts = prefix.get("capture", {})
            if counts.get("falsePositive", 0) or counts.get("falseNegative", 0):
                errors.append({"policy": trace["policy"], "story": trace["story"], "order": trace["order"],
                               "event": event["id"], "source": event["source"]["id"],
                               "falseAttachmentPairs": counts["falsePositive"], "missedAttachmentPairs": counts["falseNegative"],
                               "decision": event["decision"]})
    summary = {"schemaVersion": 1, "diagnosticOnly": True, "agentReviewedNotHumanReviewed": True,
               "predictionReceiptSHA256": c.digest(c.RUN / "predictions-complete.json"), "policy": {}}
    for policy in POLICY_IDS:
        selected = [row for row in rows if row["policy"] == policy]
        summary["policy"][policy] = {"allOrders": summarize(selected),
            "byOrder": {order: summarize([row for row in selected if row["order"] == order])
                        for order in ("chronological", "shuffle-1", "shuffle-2")},
            "byStory": {story: summarize([row for row in selected if row["story"] == story])
                        for story in sorted({row["story"] for row in selected})},
            "orderSensitivity": order_sensitivity(traces[policy])}
    c.publish(c.RUN / "metrics-summary.json", summary)
    c.publish(c.RUN / "errors.json", {"events": errors})
    c.publish(c.RUN / "metrics-complete.json", {"summarySHA256": c.digest(c.RUN / "metrics-summary.json"),
        "errorsSHA256": c.digest(c.RUN / "errors.json"), "predictionReceiptSHA256": c.digest(c.RUN / "predictions-complete.json"),
        "prefixes": sum(len(row["prefixes"]) for row in rows)})
    c.log("metrics-saved", streams=len(rows), errorEvents=len(errors), diagnosticOnly=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        with c.worker(args.resume):
            evaluate()
    except c.Paused as pause:
        c.log("paused", boundary=str(pause), safeToClose=True)
        raise SystemExit(75)
