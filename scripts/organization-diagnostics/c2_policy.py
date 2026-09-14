"""Gold-free, deterministic online placement policies for checkpoint 2.

Callbacks consume only the currently observed text, modality, ID and revision.
This module performs no I/O, inference, semantic-label lookup, or model tuning.
"""

from __future__ import annotations

import copy
import hashlib
import math
from typing import Any, Callable


SEEDS = ("17", "29", "41")
POLICY_IDS = (
    "production-embedding-reference", "simple-baseline-strongest",
    *(f"hybrid-strongest-{seed}" for seed in SEEDS),
    *(f"hybrid-corroborated-{seed}" for seed in SEEDS),
)
ScoreCallback = Callable[[dict, dict], dict]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _number(value: Any, name: str, optional: bool = False) -> float | None:
    if value is None and optional:
        return None
    _require(isinstance(value, (int, float)) and not isinstance(value, bool)
             and math.isfinite(value), f"Invalid {name}")
    return float(value)


def _source(source_id: str, memory: dict) -> dict:
    return {"id": source_id, **{key: memory[key] for key in ("text", "modality", "revision")}}


def _snapshot(memories: dict) -> dict:
    return {source_id: {"memberships": list(memory["memberships"]),
                        "archived": memory["archived"], "revision": memory["revision"],
                        "textSHA256": hashlib.sha256(memory["text"].encode("utf-8")).hexdigest()}
            for source_id, memory in sorted(memories.items())}


def _retrieve(source: dict, active: dict, callback: ScoreCallback) -> list[dict]:
    scores = {}
    for source_id, member in sorted(active.items()):
        result = callback(copy.deepcopy(source), copy.deepcopy(member))
        scores[source_id] = {
            "contextual": _number(result.get("contextual"), "contextual score", True),
            "lexical": _number(result.get("lexical"), "lexical score"),
        }
    ranks = {}
    for channel in ("contextual", "lexical"):
        available = [source_id for source_id in scores if scores[source_id][channel] is not None]
        top = sorted(available, key=lambda source_id: (-scores[source_id][channel], source_id))[:5]
        for rank, source_id in enumerate(top, 1):
            ranks.setdefault(source_id, {})[channel] = rank
    retained = [{"id": source_id, "ranks": rank,
                 "rrf": sum(1.0 / (60 + value) for value in rank.values()),
                 **scores[source_id]} for source_id, rank in ranks.items()]
    return sorted(retained, key=lambda item: (-item["rrf"], item["id"]))


def _controlled(source: dict, memories: dict, policy: str, pair_scores: ScoreCallback,
                retrieval_scores: ScoreCallback, thresholds: dict) -> dict:
    active = {source_id: _source(source_id, memory) for source_id, memory in memories.items()
              if not memory["archived"]}
    retrieved = _retrieve(source, active, retrieval_scores)
    retrieved_ids = [item["id"] for item in retrieved]
    candidates = sorted({thread for source_id in retrieved_ids
                         for thread in memories[source_id]["memberships"]})
    pair_evidence = {source_id: copy.deepcopy(pair_scores(copy.deepcopy(source), copy.deepcopy(active[source_id])))
                     for source_id in retrieved_ids}
    baseline = policy == "simple-baseline-strongest"
    corroborated = policy.startswith("hybrid-corroborated-")
    seed = policy.rsplit("-", 1)[-1]
    threshold = _number(thresholds["baseline"] if baseline else thresholds["hybrids"][seed], "threshold")
    evidence, qualifying = [], []
    for thread in candidates:
        full_members = sorted(source_id for source_id in active if thread in memories[source_id]["memberships"])
        retrieved_members = [source_id for source_id in retrieved_ids if thread in memories[source_id]["memberships"]]
        tested = retrieved_members[:3] if corroborated else retrieved_members
        support = []
        for source_id in tested:
            pair = pair_evidence[source_id]
            if baseline:
                result = pair.get("baseline", {})
                score = _number(result.get("score"), "baseline pair score", True)
                eligible = result.get("eligible", False)
                _require(isinstance(eligible, bool), "Invalid baseline eligibility")
            else:
                score = _number(pair.get("hybrid", {}).get(seed), "hybrid pair score", True)
                eligible = True
            if eligible and score is not None and score >= threshold:
                support.append(source_id)
        required = min(2, len(full_members)) if corroborated else 1
        qualifies = len(support) >= required
        evidence.append({"threadID": thread, "activeMemberIDs": full_members,
                         "retrievedMemberIDs": retrieved_members, "testedMemberIDs": tested,
                         "supportingMemberIDs": support, "requiredSupport": required,
                         "threshold": threshold, "qualifies": qualifies})
        if qualifies:
            qualifying.append(thread)
    return {"retrievedIDs": retrieved_ids, "retrieval": retrieved, "pairEvidence": pair_evidence,
            "candidateEvidence": evidence, "qualifyingThreadIDs": qualifying,
            "selected": qualifying if len(qualifying) == 1 else [],
            "action": "attach" if len(qualifying) == 1 else "proposal" if qualifying else "new"}


def run_stream(stream: dict, policy: str, pair_scores: ScoreCallback,
               retrieval_scores: ScoreCallback, thresholds: dict,
               reference: Callable[[dict, dict], dict] | None = None) -> dict:
    """Replay one ordered input stream without changing previous placements implicitly.

    Reference clusters map thread IDs to active source dictionaries. A reference
    callback returns {selected: [at most one existing thread ID], details: ...}.
    An explicit correction uses targetAnchors to copy the anchors' current runtime
    memberships, including archived anchors; an empty anchor list clears membership.
    """
    _require(policy in POLICY_IDS, f"Unknown policy: {policy}")
    _require(isinstance(stream.get("story"), str) and isinstance(stream.get("order"), str), "Missing story/order")
    _require(isinstance(stream.get("events"), list), "Missing events")
    memories, events, event_ids = {}, [], set()
    for observed in stream["events"]:
        _require(isinstance(observed, dict) and isinstance(observed.get("id"), str), "Invalid event")
        _require(observed["id"] not in event_ids, "Duplicate event ID")
        event_ids.add(observed["id"])
        kind = observed.get("kind")
        if kind == "capture":
            captured = observed["source"]
            _require(set(captured) == {"id", "text", "modality"}, "Capture must contain only source evidence")
            _require(all(isinstance(captured[key], str) and captured[key].strip() for key in captured), "Invalid source")
            source_id = captured["id"]
            _require(source_id not in memories, "Duplicate source ID")
            source = {**captured, "revision": 0}
            if policy == "production-embedding-reference":
                _require(reference is not None, "Reference callback is required")
                clusters = {}
                for member_id, memory in sorted(memories.items()):
                    if not memory["archived"]:
                        for thread in memory["memberships"]:
                            clusters.setdefault(thread, []).append(_source(member_id, memory))
                result = reference(copy.deepcopy(source), copy.deepcopy(clusters))
                selected = result.get("selected")
                _require(isinstance(selected, list) and len(selected) <= 1
                         and all(thread in clusters for thread in selected), "Invalid reference selection")
                decision = {"action": "attach" if selected else "new", "selected": list(selected),
                            "retrievedIDs": [], "candidateEvidence": [], "details": copy.deepcopy(result)}
            else:
                decision = _controlled(source, memories, policy, pair_scores, retrieval_scores, thresholds)
            memberships = decision["selected"] or [f"t:{source_id}"]
            memories[source_id] = {"text": captured["text"], "modality": captured["modality"],
                                   "memberships": list(memberships), "archived": False, "revision": 0}
            decision["assignedMemberships"] = list(memberships)
        else:
            target = observed.get("target")
            _require(target in memories, "Mutation target not yet observed")
            memory = memories[target]
            if kind in {"revise", "correct"}:
                _require(not memory["archived"], "Cannot revise/correct archived target")
            if kind == "revise":
                _require(isinstance(observed.get("text"), str) and observed["text"].strip(), "Invalid revision text")
                memory["text"] = observed["text"]
                memory["revision"] += 1
            elif kind == "correct":
                anchors = observed.get("targetAnchors")
                _require(isinstance(anchors, list) and all(isinstance(anchor, str) and anchor in memories for anchor in anchors),
                         "Correction anchors must already exist")
                memory["memberships"] = sorted({thread for anchor in anchors for thread in memories[anchor]["memberships"]})
            elif kind in {"archive", "restore"}:
                _require(memory["archived"] == (kind == "restore"), "Archive/restore state mismatch")
                memory["archived"] = kind == "archive"
            else:
                raise ValueError(f"Unknown event kind: {kind}")
            decision = {"action": kind, "target": target, "assignedMemberships": list(memory["memberships"])}
        events.append({**copy.deepcopy(observed), "decision": decision, "expectedState": _snapshot(memories)})
    return {"id": stream.get("id", f"{stream['story']}:{stream['order']}:{policy}"),
            "story": stream["story"], "order": stream["order"], "policy": policy, "events": events}
