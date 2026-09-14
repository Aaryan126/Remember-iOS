"""Post-freeze C3 one-step causal diagnostics. No score or decision generation."""
from collections import Counter

import c2_common as c
from c3_policy import POLICIES, SCORERS, accepted


def capture_counts(context, decision, truth):
    source_id, prior = context["sourceID"], context["prior"]
    target = set(truth[source_id]["memberships"])
    active = [key for key, value in prior.items() if not value["archived"]]
    shared = {key for key in active if target & set(truth[key]["memberships"])}
    disjoint = {key for key in active if target and truth[key]["memberships"] and key not in shared}
    uncertain = set(active) - shared - disjoint
    selected = set(decision["selected"])
    joined = {key for key in active if selected & set(prior[key]["memberships"])}
    wrong, missed = joined & disjoint, shared - joined
    support = {key for candidate in decision["candidateEvidence"] if candidate["threadID"] in selected
               for key in candidate["supportingMemberIDs"]}
    category = ("directDisjointSupport" if support & disjoint else "uncertainSupport" if support & uncertain
                else "inheritedOrNontransitive") if wrong else None
    safe_complete = [candidate["threadID"] for candidate in decision["candidateEvidence"]
                     if shared and shared <= set(candidate["activeMemberIDs"])
                     and not disjoint & set(candidate["activeMemberIDs"])]
    counts = {"contexts": 1, "eligibleWrongEvents": int(bool(shared | disjoint)), "eligibleMissedEvents": int(bool(shared)),
              "wrongEvents": int(bool(wrong)), "missedEvents": int(bool(missed)),
              "wrongPairs": len(wrong), "missedPairs": len(missed), "truePositivePairs": len(joined & shared),
              "knownPairs": len(shared | disjoint), "sharedPairs": len(shared),
              "uncertainJoinedPairs": len(joined & uncertain), "proposals": int(decision["action"] == "proposal"),
              "attachments": int(decision["action"] == "attach"), "newSingletons": int(decision["action"] == "new"),
              "directDisjointSupport": int(category == "directDisjointSupport"),
              "uncertainSupport": int(category == "uncertainSupport"),
              "inheritedOrNontransitive": int(category == "inheritedOrNontransitive"),
              "missedViaProposal": int(bool(missed) and decision["action"] == "proposal"),
              "missedViaNew": int(bool(missed) and decision["action"] == "new"),
              "missedViaAttach": int(bool(missed) and decision["action"] == "attach"),
              "missedBridgeEvents": int(bool(missed) and len(target) > 1),
              "missedWithSafeCompleteCandidate": int(bool(missed) and bool(safe_complete)),
              "missedWithoutSafeCompleteCandidate": int(bool(missed) and not safe_complete)}
    c.require(sum(counts[key] for key in ("directDisjointSupport", "uncertainSupport", "inheritedOrNontransitive")) == counts["wrongEvents"],
              "Wrong-event decomposition failed")
    return counts, {"wrongIDs": sorted(wrong), "missedIDs": sorted(missed), "supportCategory": category,
                    "knownLabelSafeCompleteCandidates": safe_complete}


def score_fixed(fixed, gold, thresholds):
    c.require((fixed["story"], fixed["order"]) == (gold["story"], gold["order"]), "Fixed/gold identity mismatch")
    gold_by_event = {row["after"]: row["state"] for row in gold["prefixes"]}
    totals = {policy: Counter() for policy in POLICIES}
    pair_totals = {scorer: Counter() for scorer in SCORERS}
    errors = []
    for context in fixed["contexts"]:
        truth = gold_by_event[context["event"]]
        source_id = context["sourceID"]
        c.require(set(context["prior"]) | {source_id} == set(truth), "Fixed/gold source inventory mismatch")
        for key, state in context["prior"].items():
            c.require(all(state[field] == truth[key][field] for field in ("textSHA256", "archived", "revision")),
                      "Fixed/gold observed state mismatch")
        c.require(set(context["decisions"]) == set(POLICIES), "Incomplete fixed-state comparisons")
        for policy, decision in context["decisions"].items():
            counts, details = capture_counts(context, decision, truth)
            totals[policy].update(counts)
            if counts["wrongEvents"] or counts["missedEvents"]:
                errors.append({"event": context["event"], "policy": policy, "action": decision["action"], **details})
        target = set(truth[source_id]["memberships"])
        for scorer in SCORERS:
            for key, pair in context["pairEvidence"].items():
                candidate = set(truth[key]["memberships"])
                yes = accepted(pair, scorer, thresholds)
                if not target or not candidate:
                    pair_totals[scorer]["uncertainPairs"] += 1
                    pair_totals[scorer]["uncertainAcceptedPairs"] += int(yes)
                    continue
                same = bool(target & candidate)
                pair_totals[scorer]["TP" if same and yes else "FP" if yes else "FN" if same else "TN"] += 1
    return {"anchor": fixed["anchor"], "story": fixed["story"], "order": fixed["order"],
            "counts": {key: dict(value) for key, value in totals.items()},
            "pairClassification": {key: dict(value) for key, value in pair_totals.items()}, "errors": errors}


def combine(rows, field="counts"):
    result = {}
    for key in rows[0][field]:
        total = Counter()
        for row in rows:
            total.update(row[field][key])
        result[key] = dict(total)
    return result
