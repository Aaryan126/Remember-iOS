"""Gold-free C3 controlled policies; frozen C2 retrieval and snapshot primitives."""
import copy

import c2_common as c
from c2_policy import _retrieve, _source, _snapshot, _number

SCORERS = ("baseline", "17", "29", "41")
RULES = ("strongest", "corroborated")
POLICIES = ("simple-baseline-strongest", "simple-baseline-corroborated",
            *(f"hybrid-{rule}-{seed}" for rule in RULES for seed in SCORERS[1:]))
NEW = "simple-baseline-corroborated"


def spec(policy):
    c.require(policy in POLICIES, "Unknown C3 policy")
    return ("baseline", policy.rsplit("-", 1)[-1]) if policy.startswith("simple-") else (policy.rsplit("-", 1)[-1], policy.split("-")[1])


def accepted(pair, scorer, thresholds):
    if scorer == "baseline":
        eligible = pair["baseline"]["eligible"]
        c.require(isinstance(eligible, bool), "Invalid baseline eligibility")
        score, threshold = pair["baseline"]["score"], thresholds["baseline"]
    else:
        eligible = True
        score, threshold = pair["hybrid"][scorer], thresholds["hybrids"][scorer]
    score = _number(score, "pair score", True)
    threshold = _number(threshold, "threshold")
    return eligible and score is not None and score >= threshold


def decide(source, memories, policy, pair_scores, retrieval_scores, thresholds):
    scorer, rule = spec(policy)
    active = {key: _source(key, value) for key, value in memories.items() if not value["archived"]}
    retrieval = _retrieve(source, active, retrieval_scores)
    ids = [row["id"] for row in retrieval]
    pairs = {key: copy.deepcopy(pair_scores(copy.deepcopy(source), copy.deepcopy(active[key]))) for key in ids}
    candidates = sorted({thread for key in ids for thread in memories[key]["memberships"]})
    evidence, qualifying = [], []
    threshold = thresholds["baseline"] if scorer == "baseline" else thresholds["hybrids"][scorer]
    for thread in candidates:
        members = sorted(key for key in active if thread in memories[key]["memberships"])
        retrieved = [key for key in ids if thread in memories[key]["memberships"]]
        tested = retrieved[:3] if rule == "corroborated" else retrieved
        support = [key for key in tested if accepted(pairs[key], scorer, thresholds)]
        required = min(2, len(members)) if rule == "corroborated" else 1
        qualifies = len(support) >= required
        evidence.append({"threadID": thread, "activeMemberIDs": members, "retrievedMemberIDs": retrieved,
                         "testedMemberIDs": tested, "supportingMemberIDs": support, "requiredSupport": required,
                         "threshold": threshold, "qualifies": qualifies})
        if qualifies:
            qualifying.append(thread)
    return {"retrievedIDs": ids, "retrieval": retrieval, "pairEvidence": pairs, "candidateEvidence": evidence,
            "qualifyingThreadIDs": qualifying, "selected": qualifying if len(qualifying) == 1 else [],
            "action": "attach" if len(qualifying) == 1 else "proposal" if qualifying else "new"}


def apply_event(memories, event, assignments=None):
    """Apply observed text/actions and runtime assignments, never semantic gold."""
    kind = event["kind"]
    if kind == "capture":
        source = event["source"]
        c.require(set(source) == {"id", "text", "modality"} and source["id"] not in memories, "Invalid capture")
        c.require(all(isinstance(value, str) and value.strip() for value in source.values()), "Invalid source evidence")
        c.require(assignments is not None, "Capture assignments required")
        memories[source["id"]] = {"text": source["text"], "modality": source["modality"],
                                  "memberships": list(assignments), "archived": False, "revision": 0}
        return
    target = event["target"]
    c.require(target in memories, "Unobserved mutation target")
    memory = memories[target]
    if kind in ("correct", "revise"):
        c.require(not memory["archived"], "Cannot revise/correct archived target")
    if kind == "revise":
        c.require(isinstance(event["text"], str) and event["text"].strip(), "Invalid revision")
        memory["text"] = event["text"]
        memory["revision"] += 1
    elif kind == "correct":
        anchors = event["targetAnchors"]
        c.require(isinstance(anchors, list) and all(key in memories for key in anchors), "Unobserved correction anchor")
        memory["memberships"] = sorted({thread for key in anchors for thread in memories[key]["memberships"]})
    elif kind in ("archive", "restore"):
        c.require(memory["archived"] == (kind == "restore"), "Invalid archive/restore")
        memory["archived"] = kind == "archive"
    else:
        raise ValueError("Invalid event kind")


def run_stream(stream, policy, pairs, retrieval, thresholds):
    memories, events, seen = {}, [], set()
    spec(policy)
    for event in stream["events"]:
        c.require(event["id"] not in seen, "Duplicate event")
        seen.add(event["id"])
        if event["kind"] == "capture":
            source = {**event["source"], "revision": 0}
            decision = decide(source, memories, policy, pairs, retrieval, thresholds)
            assigned = decision["selected"] or [f"t:{source['id']}"]
            decision["assignedMemberships"] = assigned
            apply_event(memories, event, assigned)
        else:
            apply_event(memories, event)
            decision = {"action": event["kind"], "target": event["target"],
                        "assignedMemberships": list(memories[event["target"]]["memberships"])}
        events.append({**copy.deepcopy(event), "decision": decision, "expectedState": _snapshot(memories)})
    return {"id": f"{policy}:{stream['story']}:{stream['order']}", "story": stream["story"],
            "order": stream["order"], "policy": policy, "events": events}


def contexts(trace):
    """Yield observed pre-capture evidence; subsequent states always come from anchor."""
    memories = {}
    for event in trace["events"]:
        if event["kind"] == "capture":
            yield event["id"], {**event["source"], "revision": 0}, copy.deepcopy(memories)
            apply_event(memories, event, event["expectedState"][event["source"]["id"]]["memberships"])
        else:
            apply_event(memories, event)
        c.require(_snapshot(memories) == event["expectedState"], "Anchor text/state reconstruction mismatch")


def fixed_trace(trace, pairs, retrieval, thresholds):
    rows = []
    for event_id, source, memories in contexts(trace):
        decisions = {policy: decide(source, memories, policy, pairs, retrieval, thresholds) for policy in POLICIES}
        shared = decisions[POLICIES[0]]
        for decision in decisions.values():
            c.require(decision["retrieval"] == shared["retrieval"] and decision["pairEvidence"] == shared["pairEvidence"],
                      "Fixed-state retrieval/evidence diverged")
        rows.append({"event": event_id, "sourceID": source["id"], "prior": _snapshot(memories),
                     "retrieval": shared["retrieval"], "pairEvidence": shared["pairEvidence"],
                     "decisions": {policy: {key: value for key, value in decision.items()
                                            if key not in ("retrieval", "pairEvidence")}
                                   for policy, decision in decisions.items()}})
    return {"anchor": trace["policy"], "story": trace["story"], "order": trace["order"], "contexts": rows}
