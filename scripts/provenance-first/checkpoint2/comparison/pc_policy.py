"""Gold-free online state, D3 adapter and retrieval-assisted River policies."""
from collections import Counter
from copy import deepcopy
import hashlib
import math
import uuid

from pc_native import c

THRESHOLDS = (0.9804276486193665, 0.99, 0.995)


def native_id(sid):
    c.require(len(sid) == 3 and sid[0] == "s" and sid[1:].isdigit(), "invalid source/thread ID")
    digest = hashlib.sha256(("organization-diagnostics-v1:localc" + sid[1:]).encode()).digest()[:16]
    return str(uuid.UUID(bytes=digest)).upper()


def ordered(values):
    return sorted(values, key=native_id)


def retrieve(candidates):
    ranks = {}
    for channel in ("contextual", "lexical"):
        group = [sid for sid, row in candidates.items() if row[channel] is not None and math.isfinite(row[channel])]
        for rank, sid in enumerate(sorted(group, key=lambda sid: (-candidates[sid][channel], native_id(sid)))[:5]):
            ranks[sid] = ranks.get(sid, 0.) + 1/(61+rank)
    return sorted(ranks, key=lambda sid: (-ranks[sid], native_id(sid)))


def qualify(candidates, retrieved, counts, threshold, exclusive=False):
    threads = ordered({thread for sid in retrieved for thread in candidates[sid]["memberships"]})
    support, qualifying = {}, []
    for thread in threads:
        tested = [sid for sid in retrieved if thread in candidates[sid]["memberships"]][:3]
        matches = [sid for sid in tested if threshold <= candidates[sid]["score"] <= 1
                   and (not exclusive or candidates[sid]["memberships"] == [thread])]
        support[thread] = matches
        if counts[thread] > 0 and len(matches) >= min(2, counts[thread]):
            qualifying.append(thread)
    return qualifying, support


def decision(text, memories, score_pair, native, variant, threshold, automatic=True):
    active = {sid: value for sid, value in memories.items() if not value["archived"]}
    counts = Counter(thread for value in active.values() for thread in value["memberships"])
    candidates = {sid: {**score_pair(text, value["text"]), "memberships": value["memberships"]}
                  for sid, value in active.items()}
    for row in candidates.values():
        c.require(set(row) == {"contextual", "lexical", "score", "memberships"}, "unexpected pair-score fields")
        c.require(all(type(row[key]) in (int, float) and math.isfinite(row[key]) for key in ("contextual", "lexical", "score")), "invalid score")
        c.require(0 <= row["score"] <= 1, "invalid matcher output")
    retrieved = retrieve(candidates)
    proposals, proposal_support = qualify(candidates, retrieved, counts, THRESHOLDS[0])
    qualifying, support = qualify(candidates, retrieved, counts, threshold)
    selected = qualifying if len(qualifying) == 1 and automatic else []
    if variant == "C":
        exclusive, support = qualify(candidates, retrieved, counts, threshold, exclusive=True)
        selected = selected if selected and selected[0] in exclusive else []
    if variant == "A":
        c.require(threshold == THRESHOLDS[0] and automatic, "reference configuration changed")
        observed = native({"kind": "decide", "candidates": [
            {"id": native_id(sid), "memberships": [native_id(t) for t in value["memberships"]],
             **{key: value[key] for key in ("contextual", "lexical", "score")}}
            for sid, value in candidates.items()], "memberCounts": {native_id(t): n for t, n in counts.items()}})
        c.require(observed["retrieved"] == [native_id(sid) for sid in retrieved]
                  and observed["qualifying"] == [native_id(t) for t in qualifying]
                  and observed["selected"] == [native_id(t) for t in selected]
                  and observed["support"] == {native_id(t): [native_id(s) for s in v] for t, v in support.items()},
                  "adapter differs from production D3")
    def citations(supporting):
        return {thread: [{"sourceId": sid, "revision": active[sid]["revision"],
                          "locator": active[sid]["locator"], "quote": active[sid]["text"]} for sid in ids]
                for thread, ids in supporting.items()}
    return {"selected": selected, "qualifying": qualifying, "retrieved": retrieved,
            "scores": candidates, "support": citations(support),
            "proposals": proposals if variant == "C" else [],
            "proposalSupport": citations(proposal_support) if variant == "C" else {},
            "threshold": threshold, "automaticEnabled": automatic}


def validate_event(event):
    required = {"id", "kind", "sourceId"}
    extra = {"capture": {"text", "modality", "locator"}, "revise": {"text", "locator"},
             "correct": {"reason", "assignedProjectRoots"}, "archive": set(), "restore": set()}
    c.require(event["kind"] in extra and set(event) == required | extra[event["kind"]], "event has missing/leaked fields")
    native_id(event["sourceId"])


def apply(memories, event, selected=None):
    validate_event(event)
    sid, kind = event["sourceId"], event["kind"]
    if kind == "capture":
        c.require(sid not in memories and selected is not None, "duplicate/unassigned capture")
        c.require(all(thread in memories for thread in selected), "automatic target not observed")
        memories[sid] = {"text": event["text"], "locator": event["locator"], "modality": event["modality"],
                         "revision": 0, "archived": False, "memberships": list(selected) or [sid],
                         "pinned": False, "created": len(memories)}
        return
    c.require(sid in memories, "mutation before capture")
    value = memories[sid]
    if kind in ("revise", "correct"):
        c.require(not value["archived"], "editing archived source")
    if kind == "revise":
        value.update(text=event["text"], locator=event["locator"], revision=value["revision"]+1)
    elif kind == "correct":
        roots = event["assignedProjectRoots"]
        c.require(roots and len(set(roots)) == len(roots) and all(root in memories for root in roots), "correction target unavailable")
        value.update(memberships=ordered(roots), pinned=True)
    else:
        c.require(value["archived"] == (kind == "restore"), "invalid visibility change")
        value["archived"] = kind == "archive"


def recover(query, memories, native):
    c.require(set(query) == {"id", "atEvent", "question"}, "query contains hidden annotations")
    documents = [{"id": sid, **{k: value[k] for k in ("text", "revision", "locator", "created")}}
                 for sid, value in memories.items() if not value["archived"]]
    hits = native({"kind": "search", "query": query["question"], "documents": documents})["hits"]
    seen = set()
    for hit in hits:
        sid, revision = hit["sourceId"], hit["revision"]
        c.require(sid in memories and not memories[sid]["archived"] and revision == memories[sid]["revision"], "stale/archived search hit")
        c.require(hit["quote"] and hit["quote"] in memories[sid]["text"] and (sid, revision) not in seen, "invalid/duplicate citation")
        expected_locator = memories[sid]["locator"] + (f", part {hit['ordinal']+1}" if hit["ordinal"] else "")
        c.require(hit["locator"] == expected_locator, "search locator mismatch")
        seen.add((sid, revision))
    river = ordered(memories[hits[0]["sourceId"]]["memberships"])[0] if hits else None
    confirmed = [hit for hit in hits if river in memories[hit["sourceId"]]["memberships"]][:3]
    suggested = [hit for hit in hits if river not in memories[hit["sourceId"]]["memberships"]][:3]
    allowed = {hit["sourceId"] for hit in confirmed + suggested}
    union = [hit for hit in hits if hit["sourceId"] in allowed][:3]
    return {"id": query["id"], "atEvent": query["atEvent"], "river": river,
            "confirmed": confirmed, "suggested": suggested, "combined": union}


def run_stream(stream, score_pair, native, variant, threshold, automatic=True):
    c.require(set(stream) == {"id", "order", "events", "queries"}, "stream contains evaluator metadata")
    memories, rows, queries, observed = {}, [], [], set()
    for event in stream["events"]:
        validate_event(event)
        c.require(event["id"] not in observed, "duplicate event")
        observed.add(event["id"])
        prior = deepcopy(memories)
        if event["kind"] == "capture":
            choice = decision(event["text"], memories, score_pair, native, variant, threshold, automatic)
            apply(memories, event, choice["selected"])
        else:
            apply(memories, event)
            choice = {"action": event["kind"], "selected": []}
        for sid, old in prior.items():
            if event["kind"] != "correct" or sid != event["sourceId"]:
                c.require(memories[sid]["memberships"] == old["memberships"], "implicit membership mutation")
            if old["pinned"]:
                c.require(memories[sid]["pinned"], "correction pin lost")
        rows.append({"event": deepcopy(event), "decision": choice, "state": deepcopy(memories)})
        for query in stream["queries"]:
            if query["atEvent"] == event["id"]:
                queries.append(recover(query, memories, native))
    c.require(len(queries) == len(stream["queries"]), "query prefix missing")
    return {"id": stream["id"], "order": stream["order"], "variant": variant, "threshold": threshold,
            "automatic": automatic, "events": rows, "queries": queries}


def ledger_run(trace):
    """Expected state is derived from policy outputs, never from native replay."""
    local = c.fixtures.local_source
    thread = c.fixtures.singleton
    commands = []
    for row in trace["events"]:
        event, state = row["event"], row["state"]
        sid, kind = event["sourceId"], event["kind"]
        command = {"id": event["id"], "kind": kind}
        if kind == "capture":
            command["source"] = {"id": local(sid), "text": event["text"], "modality": {"photo": "image"}.get(event["modality"], event["modality"])}
            command["assignments"] = sorted(thread(t) for t in state[sid]["memberships"])
        else:
            command["target"] = local(sid)
            if kind == "correct":
                command["assignments"] = sorted(thread(t) for t in event["assignedProjectRoots"])
            if kind == "revise":
                command["text"] = event["text"]
        command["expectedState"] = {local(key): {"memberships": sorted(thread(t) for t in value["memberships"]),
                   "archived": value["archived"], "revision": value["revision"], "textSHA256": c.text_hash(value["text"])}
                   for key, value in state.items()}
        commands.append(command)
    return {"id": f"{trace['id']}-{trace['order']}-{trace['variant']}", "events": commands}
