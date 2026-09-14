"""Post-freeze oracle review; gold never enters the proposal module."""
from collections import Counter

import c2_common as c
from c2_metrics import _pair_counts, _structure
from c4_policy import SCORERS, KINDS, apply_proposal, changes, shared, signature


def review(state, proposal, protected, truth):
    after = apply_proposal(state, proposal, protected)
    c.require(signature(after) == proposal["afterSHA256"], "Proposal result mismatch")
    repaired, introduced, uncertain = [], [], []
    for a, b in changes(state, after):
        c.require(not state[a]["archived"] and not state[b]["archived"], "Archived pair changed")
        if not truth[a]["memberships"] or not truth[b]["memberships"]:
            uncertain.append([a, b])
        elif shared(after, a, b) == shared(truth, a, b):
            repaired.append([a, b])
        else:
            introduced.append([a, b])
    label = "harmful" if introduced else "indeterminate" if uncertain else "beneficial" if repaired else "neutral"
    return {"proposalID": proposal["id"], "kind": proposal["kind"], "label": label,
            "repairedPairs": repaired, "introducedPairs": introduced, "uncertainPairs": uncertain}


def score_stream(unit, gold):
    c.require((unit["story"], unit["order"]) == (gold["story"], gold["order"]), "Gold identity mismatch")
    c.require(len(unit["prefixes"]) == len(gold["prefixes"]), "Gold prefix count mismatch")
    rows = []
    for context, target in zip(unit["prefixes"], gold["prefixes"]):
        c.require(context["after"] == target["after"], "Gold event mismatch")
        state, truth = context["state"], target["state"]
        c.require(set(state) == set(truth), "Gold source mismatch")
        for key in state:
            c.require(all(state[key][field] == truth[key][field] for field in ("archived", "revision", "textSHA256")),
                      "Observed metadata mismatch")
        before = {"pairs": _pair_counts(state, truth), "structure": _structure(state, truth)}
        results = {}
        for scorer in SCORERS:
            proposals = context["scorers"][scorer]["proposals"]
            reviews = [review(state, p, context["protected"], truth) for p in proposals]
            chosen = next((p for p, r in zip(proposals, reviews) if r["label"] == "beneficial"), None)
            after = apply_proposal(state, chosen, context["protected"]) if chosen else state
            pairs = _pair_counts(after, truth)
            c.require(all(pairs[k] <= before["pairs"][k] for k in ("falsePositive", "falseNegative")), "Oracle review increased errors")
            results[scorer] = {"reviews": reviews, "acceptance": {"actor": "simulated-perfect-reviewer",
                "usesGold": True, "acceptedProposalID": chosen["id"] if chosen else None,
                "decision": "explicit-accept" if chosen else "reject-all", "maximumAccepted": 1},
                "afterState": after, "after": {"pairs": pairs, "structure": _structure(after, truth)}}
        rows.append({"after": context["after"], "beforeState": state, "before": before, "scorers": results})
    return {key: unit[key] for key in ("anchor", "story", "order")} | {"prefixes": rows}


def aggregate(units, scorer, final_only=False):
    counts, before, after = Counter(), Counter(), Counter()
    kinds = {kind: Counter() for kind in KINDS}
    unique = set()
    for unit in units:
        contexts = unit["prefixes"][-1:] if final_only else unit["prefixes"]
        for row in contexts:
            value = row["scorers"][scorer]
            counts["contexts"] += 1
            counts["contextsWithErrors"] += int(row["before"]["pairs"]["falsePositive"] + row["before"]["pairs"]["falseNegative"] > 0)
            useful = any(r["label"] == "beneficial" for r in value["reviews"])
            counts["contextsWithBeneficialProposal"] += int(useful)
            counts["accepted"] += int(value["acceptance"]["decision"] == "explicit-accept")
            counts["contextsWithProposals"] += int(bool(value["reviews"]))
            for r in value["reviews"]:
                counts["proposals"] += 1
                counts[r["label"]] += 1
                kinds[r["kind"]][r["label"]] += 1
                counts["proposedRepairedPairs"] += len(r["repairedPairs"])
                counts["proposedIntroducedPairs"] += len(r["introducedPairs"])
                counts["proposedUncertainPairs"] += len(r["uncertainPairs"])
                unique.add((unit["anchor"], unit["story"], unit["order"], r["proposalID"]))
            for dest, metrics in ((before, row["before"]), (after, value["after"])):
                dest.update({key: amount for key, amount in metrics["pairs"].items() if isinstance(amount, int)})
                dest["mixedThreads"] += metrics["structure"]["mixedClusters"]["numerator"]
    for key in ("beneficial", "harmful", "indeterminate", "neutral", "proposals", "accepted", "contextsWithErrors",
                "contextsWithBeneficialProposal", "contextsWithProposals"):
        counts.setdefault(key, 0)
    counts["uniqueProposalSignaturesWithinStreams"] = len(unique)
    counts["errorContextsWithoutBeneficialProposal"] = counts["contextsWithErrors"] - counts["contextsWithBeneficialProposal"]
    def fraction(n, d):
        return n / d if d else None
    def pair_result(value):
        return dict(value) | {"precision": fraction(value["truePositive"], value["truePositive"] + value["falsePositive"]),
                              "recall": fraction(value["truePositive"], value["truePositive"] + value["falseNegative"])}
    return {"counts": dict(counts), "byKind": {k: dict(v) for k, v in kinds.items()},
            "beneficialProposalRate": fraction(counts["beneficial"], counts["proposals"]),
            "errorContextCoverage": fraction(counts["contextsWithBeneficialProposal"], counts["contextsWithErrors"]),
            "before": pair_result(before), "afterOracleAcceptance": pair_result(after)}


def summarize(units):
    anchors = sorted({u["anchor"] for u in units})
    def group(rows):
        return {scorer: {"allPrefixes": aggregate(rows, scorer), "finalPrefixes": aggregate(rows, scorer, True)} for scorer in SCORERS}
    return {"diagnosticOnly": True, "goldUsedForExplicitSimulatedAcceptance": True, "onlineRepairTrajectory": False,
            "byAnchor": {a: group([u for u in units if u["anchor"] == a]) for a in anchors},
            "byStory": {s: group([u for u in units if u["story"] == s]) for s in sorted({u['story'] for u in units})},
            "byOrder": {o: group([u for u in units if u["order"] == o]) for o in sorted({u['order'] for u in units})},
            "pooled": group(units)}
