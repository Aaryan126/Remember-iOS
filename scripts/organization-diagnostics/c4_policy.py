"""Gold-free, bounded proposals over frozen observed states; no storage or model I/O."""
import copy
import hashlib
import json
from itertools import combinations

import c2_common as c
from c2_policy import _snapshot, _source
from c3_policy import accepted, apply_event

SCORERS = ("baseline", "17", "29", "41")
KINDS = ("split", "reassign", "add", "merge")
ANCHORS = ("simple-baseline-corroborated", *(f"hybrid-corroborated-{s}" for s in SCORERS[1:]))


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def shared(state, a, b):
    return bool(set(state[a]["memberships"]) & set(state[b]["memberships"]))


def changes(before, after):
    return [(a, b) for a, b in combinations(sorted(before), 2)
            if shared(before, a, b) != shared(after, a, b)]


def apply_proposal(state, proposal, protected):
    """Reject stale or unsafe assignments before returning a new state."""
    c.require(signature(state) == proposal["beforeSHA256"], "Stale proposal")
    c.require(set(protected) <= set(state), "Unknown protected source")
    assignments = proposal["assignments"]
    c.require(assignments and set(assignments) <= set(state), "Invalid proposal targets")
    result = copy.deepcopy(state)
    guarded = set(protected) | {key for key in state if state[key]["archived"]}
    for key, groups in assignments.items():
        c.require(key not in guarded, "Protected membership mutation")
        c.require(isinstance(groups, list) and groups and all(isinstance(t, str) and t for t in groups)
                  and groups == sorted(set(groups)), "Invalid membership assignment")
        result[key]["memberships"] = groups
    delta = changes(state, result)
    c.require(delta, "No changed pair relation")
    c.require(not any(a in guarded or b in guarded for a, b in delta), "Protected relationship mutation")
    return result


def components(ids, edges):
    remaining, groups = set(ids), []
    while remaining:
        pending, found = [min(remaining)], set()
        while pending:
            key = pending.pop()
            if key in found:
                continue
            found.add(key)
            pending.extend(other for other in remaining - found if edges.get(tuple(sorted((key, other)))) is True)
        remaining -= found
        groups.append(sorted(found))
    return groups


def propose(memories, protected, scorer, pairs, thresholds):
    c.require(scorer in SCORERS, "Invalid scorer")
    state = _snapshot(memories)
    active = sorted(key for key in memories if not memories[key]["archived"])
    evidence, edges = [], {}
    for a, b in combinations(active, 2):
        value = pairs(_source(a, memories[a]), _source(b, memories[b]))
        raw = value["baseline"]["score"] if scorer == "baseline" else value["hybrid"][scorer]
        passes = accepted(value, scorer, thresholds) if raw is not None else None
        edges[a, b] = passes
        evidence.append({"a": a, "b": b, "passes": passes})
    threads = sorted({thread for key in active for thread in state[key]["memberships"]})
    members = {t: [key for key in active if t in state[key]["memberships"]] for t in threads}
    eligible = {kind: [] for kind in KINDS}
    before_sha = signature(state)

    def clique(ids):
        return all(edges[tuple(sorted((a, b)))] is True for a, b in combinations(sorted(set(ids)), 2))

    def offer(kind, key, assignments):
        assignments = {k: sorted(set(v)) for k, v in assignments.items() if sorted(set(v)) != state[k]["memberships"]}
        if not assignments:
            return
        proposal = {"kind": kind, "key": key, "beforeSHA256": before_sha, "assignments": assignments}
        try:
            after = apply_proposal(state, proposal, protected)
        except ValueError:
            return  # Candidate fails a documented protection/no-op guard.
        proposal["id"] = signature({"kind": kind, "key": key, "assignments": assignments})
        proposal["afterSHA256"] = signature(after)
        eligible[kind].append(proposal)

    for t in threads:
        ids = members[t]
        if any(edges[a, b] is None for a, b in combinations(ids, 2)):
            continue
        groups = components(ids, edges)
        if len(groups) > 1:
            assignments = {}
            for group in groups[1:]:
                new = "c4:split:" + signature([t, group])[:20]
                c.require(new not in threads, "Split ID collision")
                for key in group:
                    assignments[key] = [g for g in state[key]["memberships"] if g != t] + [new]
            offer("split", [t], assignments)
    for key in active:
        old_peers = [other for other in active if other != key and shared(state, key, other)]
        rejected_old = bool(old_peers) and all(edges[tuple(sorted((key, other)))] is False for other in old_peers)
        for t in threads:
            if t in state[key]["memberships"] or not clique([key, *members[t]]):
                continue
            if rejected_old:
                offer("reassign", [key, t], {key: [t]})
            if len(state[key]["memberships"]) < 3:
                offer("add", [key, t], {key: state[key]["memberships"] + [t]})
    for a, b in combinations(threads, 2):
        ids = sorted(set(members[a]) | set(members[b]))
        if clique(ids):
            new = "c4:merge:" + signature([a, b])[:20]
            c.require(new not in threads, "Merge ID collision")
            # Include archived members in assignments so the guard rejects retirement
            # that would silently leave them behind in an old parent thread.
            affected = [key for key in state if {a, b} & set(state[key]["memberships"])]
            offer("merge", [a, b], {key: [t for t in state[key]["memberships"] if t not in (a, b)] + [new]
                                    for key in affected})
    offered, seen = [], set()
    for kind in KINDS:
        if eligible[kind]:
            item = sorted(eligible[kind], key=lambda row: row["key"])[0]
            if item["afterSHA256"] not in seen:
                offered.append(item)
                seen.add(item["afterSHA256"])
    return {"scorer": scorer, "evidence": evidence, "eligibleByKind": {k: len(v) for k, v in eligible.items()},
            "proposals": offered}


def fixed_stream(trace, pairs, thresholds):
    memories, protected, rows = {}, set(), []
    for event in trace["events"]:
        assignments = event["expectedState"][event["source"]["id"]]["memberships"] if event["kind"] == "capture" else None
        apply_event(memories, event, assignments)
        if event["kind"] == "correct":
            protected.add(event["target"])
        c.require(_snapshot(memories) == event["expectedState"], "Anchor reconstruction mismatch")
        rows.append({"after": event["id"], "state": _snapshot(memories), "protected": sorted(protected),
                     "scorers": {s: propose(memories, protected, s, pairs, thresholds) for s in SCORERS}})
    return {"anchor": trace["policy"], "story": trace["story"], "order": trace["order"], "prefixes": rows}
