"""Post-freeze semantic diagnostics, separate from gold-free placement policies.

Call score_trace only after prediction receipts have been frozen by the runner.
Runtime thread IDs and semantic project IDs are deliberately never compared.
"""

from __future__ import annotations

from itertools import combinations


def _rate(numerator: int | float, denominator: int) -> dict:
    return {"numerator": numerator, "denominator": denominator,
            "value": numerator / denominator if denominator else None}


def _shared(left: dict, right: dict) -> bool:
    return bool(set(left["memberships"]) & set(right["memberships"]))


def _pair_counts(predicted: dict, truth: dict, target: str | None = None) -> dict:
    active = sorted(source_id for source_id in truth if not truth[source_id]["archived"]
                    and not predicted[source_id]["archived"])
    counts = {"truePositive": 0, "falsePositive": 0, "falseNegative": 0, "trueNegative": 0,
              "knownPairs": 0, "uncertainPairs": 0, "uncertainJoinedPairs": 0}
    for left, right in combinations(active, 2):
        if target is not None and target not in (left, right):
            continue
        joined = _shared(predicted[left], predicted[right])
        if not truth[left]["memberships"] or not truth[right]["memberships"]:
            counts["uncertainPairs"] += 1
            counts["uncertainJoinedPairs"] += int(joined)
            continue
        same = _shared(truth[left], truth[right])
        counts["knownPairs"] += 1
        counts["truePositive" if same and joined else "falsePositive" if joined else
               "falseNegative" if same else "trueNegative"] += 1
    counts["precision"] = _rate(counts["truePositive"], counts["truePositive"] + counts["falsePositive"])
    counts["recall"] = _rate(counts["truePositive"], counts["truePositive"] + counts["falseNegative"])
    return counts


def _structure(predicted: dict, truth: dict) -> dict:
    projects, clusters = {}, {}
    active = [source_id for source_id in truth if not truth[source_id]["archived"]
              and not predicted[source_id]["archived"]]
    for source_id in active:
        for project in truth[source_id]["memberships"]:
            projects.setdefault(project, set()).update(predicted[source_id]["memberships"])
        for thread in predicted[source_id]["memberships"]:
            clusters.setdefault(thread, []).append(source_id)
    known_clusters = {thread: [source_id for source_id in members if truth[source_id]["memberships"]]
                      for thread, members in clusters.items()}
    known_clusters = {thread: members for thread, members in known_clusters.items() if members}
    mixed = [thread for thread, members in known_clusters.items()
             if any(not _shared(truth[left], truth[right]) for left, right in combinations(members, 2))]
    fragmented = sum(len(threads) > 1 for threads in projects.values())
    return {"projectClusterCounts": {project: len(threads) for project, threads in sorted(projects.items())},
            "fragmentedProjects": _rate(fragmented, len(projects)),
            "excessProjectClusters": sum(max(0, len(threads) - 1) for threads in projects.values()),
            "mixedClusters": _rate(len(mixed), len(known_clusters)), "mixedClusterIDs": sorted(mixed),
            "activeSources": len(active), "unresolvedSources": sum(not truth[key]["memberships"] for key in active)}


def _mean(values: list) -> dict:
    present = [value for value in values if value is not None]
    return _rate(sum(present), len(present))


def score_trace(trace: dict, gold: dict) -> dict:
    """Return prefix diagnostics and stream totals; undefined rates are null.

    False/missed attachment events mean a new source has respectively at least one
    known disjoint joined predecessor / at least one known shared unjoined
    predecessor. Both can happen together. Denominators are known captures with a
    known active predecessor / known captures with a shared active predecessor.
    Pair totals across prefixes intentionally count repeated exposure; macro prefix
    means and final-prefix results are reported separately. Uncertain gold [] is
    excluded from known pair denominators, never treated as a negative label.
    """
    if (trace["story"], trace["order"]) != (gold["story"], gold["order"]):
        raise ValueError("Trace and gold story/order differ")
    if len(trace["events"]) != len(gold["prefixes"]):
        raise ValueError("Trace and gold prefix lengths differ")
    prefixes = []
    totals = {"captures": 0, "knownCapturesWithKnownPrior": 0, "capturesWithSharedPrior": 0,
              "falseAttachmentEvents": 0, "missedAttachmentEvents": 0,
              "falseAttachmentPairs": 0, "missedAttachmentPairs": 0,
              "knownCapturePairs": 0, "sharedCapturePairs": 0,
              "uncertainCaptureEvents": 0, "uncertainCaptureJoinedEvents": 0,
              "uncertainJoinedCapturePairs": 0, "proposals": 0, "abstentions": 0,
              "autoAttachments": 0, "retrievableSharedPairs": 0, "retrievedSharedPairs": 0,
              "corrections": 0, "correctionErrorsBefore": 0, "correctionErrorsAfter": 0}
    previous_predicted = {}
    for event, gold_prefix in zip(trace["events"], gold["prefixes"]):
        if event["id"] != gold_prefix["after"]:
            raise ValueError("Trace and gold event order differ")
        predicted, truth = event["expectedState"], gold_prefix["state"]
        if set(predicted) != set(truth):
            raise ValueError("Trace and gold source IDs differ")
        for source_id in truth:
            for field in ("archived", "revision", "textSHA256"):
                if predicted[source_id].get(field) != truth[source_id].get(field):
                    raise ValueError(f"Trace and gold observed state differs: {event['id']} {source_id} {field}")
        item = {"after": event["id"], "pairs": _pair_counts(predicted, truth),
                "structure": _structure(predicted, truth)}
        if event["kind"] == "capture":
            source_id = event["source"]["id"]
            counts = _pair_counts(predicted, truth, source_id)
            shared = counts["truePositive"] + counts["falseNegative"]
            totals["captures"] += 1
            totals["knownCapturesWithKnownPrior"] += int(counts["knownPairs"] > 0)
            totals["capturesWithSharedPrior"] += int(shared > 0)
            totals["falseAttachmentEvents"] += int(counts["falsePositive"] > 0)
            totals["missedAttachmentEvents"] += int(counts["falseNegative"] > 0)
            totals["falseAttachmentPairs"] += counts["falsePositive"]
            totals["missedAttachmentPairs"] += counts["falseNegative"]
            totals["knownCapturePairs"] += counts["knownPairs"]
            totals["sharedCapturePairs"] += shared
            uncertain = not truth[source_id]["memberships"]
            totals["uncertainCaptureEvents"] += int(uncertain)
            totals["uncertainCaptureJoinedEvents"] += int(uncertain and counts["uncertainJoinedPairs"] > 0)
            totals["uncertainJoinedCapturePairs"] += counts["uncertainJoinedPairs"]
            action = event["decision"]["action"]
            totals["proposals"] += int(action == "proposal")
            totals["abstentions"] += int(action in {"new", "proposal"})
            totals["autoAttachments"] += int(action == "attach")
            if trace["policy"] != "production-embedding-reference":
                retrieved = set(event["decision"]["retrievedIDs"])
                shared_ids = {prior for prior in truth if prior != source_id and not truth[prior]["archived"]
                              and _shared(truth[source_id], truth[prior])}
                totals["retrievableSharedPairs"] += len(shared_ids)
                totals["retrievedSharedPairs"] += len(shared_ids & retrieved)
                counts["retrievalSharedCoverage"] = _rate(len(shared_ids & retrieved), len(shared_ids))
            item["capture"] = counts
        elif event["kind"] == "correct":
            target = event["target"]
            before = _pair_counts(previous_predicted, truth, target)
            after = _pair_counts(predicted, truth, target)
            before_errors = before["falsePositive"] + before["falseNegative"]
            after_errors = after["falsePositive"] + after["falseNegative"]
            item["correction"] = {"target": target, "errorsBefore": before_errors, "errorsAfter": after_errors,
                                  "knownPairs": after["knownPairs"]}
            totals["corrections"] += 1
            totals["correctionErrorsBefore"] += before_errors
            totals["correctionErrorsAfter"] += after_errors
        prefixes.append(item)
        previous_predicted = predicted
    rates = {
        "falseAttachments": _rate(totals["falseAttachmentEvents"], totals["knownCapturesWithKnownPrior"]),
        "missedAttachments": _rate(totals["missedAttachmentEvents"], totals["capturesWithSharedPrior"]),
        "falseAttachmentPairs": _rate(totals["falseAttachmentPairs"], totals["knownCapturePairs"]),
        "missedAttachmentPairs": _rate(totals["missedAttachmentPairs"], totals["sharedCapturePairs"]),
        "uncertainCaptureJoined": _rate(totals["uncertainCaptureJoinedEvents"], totals["uncertainCaptureEvents"]),
        "proposals": _rate(totals["proposals"], totals["captures"]),
        "abstentions": _rate(totals["abstentions"], totals["captures"]),
        "retrievalSharedCoverage": _rate(totals["retrievedSharedPairs"], totals["retrievableSharedPairs"]),
    }
    macro = {name: _mean([prefix["pairs"][name]["value"] for prefix in prefixes]) for name in ("precision", "recall")}
    macro.update({name: _mean([prefix["structure"][name]["value"] for prefix in prefixes])
                  for name in ("fragmentedProjects", "mixedClusters")})
    return {"story": trace["story"], "order": trace["order"], "policy": trace["policy"],
            "prefixes": prefixes, "counts": totals, "rates": rates, "macroPrefix": macro,
            "final": prefixes[-1] if prefixes else None,
            "qualification": "Exposed fictional diagnostics only; no qualification claim."}
