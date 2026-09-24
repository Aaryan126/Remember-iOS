"""Strict fictional-input validation and ideal-label ledger compilation; no inference."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re


class InvalidFixture(ValueError):
    pass


def require(value, message):
    if not value:
        raise InvalidFixture(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def evidence_valid(evidence, revisions, label):
    require(isinstance(evidence, list), f"{label}: evidence must be list")
    for item in evidence:
        require(set(item) == {"sourceId", "revision", "quote"}, f"{label}: invalid evidence fields")
        key = (item["sourceId"], item["revision"])
        require(type(item["revision"]) is int and item["revision"] >= 0, f"{label}: invalid revision")
        require(key in revisions, f"{label}: missing/future source revision {key}")
        require(nonempty(item["quote"]) and item["quote"] in revisions[key], f"{label}: quotation not in source {key}")


def validate_library(library):
    key = library["id"]
    require(re.fullmatch(r"(?:dev|eval)(?:0[1-9]|1[0-2])", key), "invalid library ID")
    require(nonempty(library["family"]) and nonempty(library["description"]), f"{key}: family/description required")
    projects = {p["id"]: p for p in library["projects"]}
    require(len(projects) == len(library["projects"]) and 2 <= len(projects) <= 3, f"{key}: projects")
    require(all(re.fullmatch(r"p[1-3]", p) for p in projects), f"{key}: project IDs")
    require(len({p["rootSourceId"] for p in projects.values()}) == len(projects), f"{key}: shared project roots")
    require(all(nonempty(p["title"]) for p in projects.values()), f"{key}: empty project title")
    events = library["events"]
    require(len(events) == 12, f"{key}: requires 12 events")
    state, revisions, prefixes, ancestors, revision_events, last_event, modes = {}, {}, {}, {}, {}, {}, set()
    for index, event in enumerate(events, 1):
        eid, sid, kind = event["id"], event["sourceId"], event["kind"]
        label = f"{key}/{eid}"
        require(eid == f"e{index:02d}", f"{label}: event ID/order")
        require(re.fullmatch(r"s[0-9]{2}", sid), f"{label}: source ID")
        require(kind in {"capture", "revise", "correct", "archive", "restore"}, f"{label}: kind")
        require(isinstance(event["dependsOn"], list) and len(set(event["dependsOn"])) == len(event["dependsOn"]), f"{label}: dependencies")
        require(all(d in ancestors for d in event["dependsOn"]), f"{label}: forward/missing dependency")
        ancestors[eid] = set(event["dependsOn"])
        for dep in event["dependsOn"]:
            ancestors[eid].update(ancestors[dep])
        gold = event["gold"]
        membership = gold["memberships"]
        related = gold["relatedProjects"]
        require(isinstance(membership, list) and len(set(membership)) == len(membership), f"{label}: memberships")
        require(isinstance(related, list) and len(set(related)) == len(related), f"{label}: related projects")
        require(set(membership + related) <= projects.keys() and not set(membership) & set(related), f"{label}: project references")
        disposition = gold["disposition"]
        require(disposition in {"confirmed", "related", "unresolved", "independent"}, f"{label}: disposition")
        require(bool(membership) == (disposition == "confirmed"), f"{label}: membership/disposition mismatch")
        require(disposition != "related" or related, f"{label}: related requires a relationship")
        require(nonempty(gold["rationale"]), f"{label}: rationale")
        if kind == "capture":
            require(disposition not in {"confirmed", "related"} or gold["evidence"], f"{label}: supported capture needs source evidence")
            require(sid not in state and "assignments" not in event, f"{label}: duplicate capture or leaked assignments")
            require(nonempty(event["text"]) and event["text"] == event["text"].strip(), f"{label}: text whitespace/empty")
            require(nonempty(event["locator"]), f"{label}: locator")
            require(event["modality"] in {"note", "photo", "voice", "video", "pdf", "link"}, f"{label}: modality")
            modes.add(event["modality"])
            state[sid] = {"revision": 0, "archived": False, "memberships": membership,
                          "disposition": disposition, "relatedProjects": related, "modality": event["modality"]}
            revisions[(sid, 0)] = event["text"]
            revision_events[(sid, 0)] = eid
        else:
            require(sid in state and last_event[sid] in ancestors[eid], f"{label}: missing source/causal dependency")
            prior = state[sid]
            if kind == "correct":
                require(not prior["archived"], f"{label}: correcting archived source")
                require(nonempty(event["reason"]) and event["assignments"] and sorted(event["assignments"]) == sorted(membership), f"{label}: explicit correction differs")
            else:
                require(sorted(membership) == sorted(prior["memberships"]), f"{label}: implicit reassignment")
                require(disposition == prior["disposition"] and sorted(related) == sorted(prior["relatedProjects"]), f"{label}: implicit relation change")
            if kind == "revise":
                require(prior["modality"] == "note" and not prior["archived"], f"{label}: only active note revisions")
                require(nonempty(event["text"]) and event["text"] == event["text"].strip() and nonempty(event["locator"]), f"{label}: revision text/locator")
                prior["revision"] += 1
                revisions[(sid, prior["revision"])] = event["text"]
                revision_events[(sid, prior["revision"])] = eid
            if kind in {"archive", "restore"}:
                require(prior["archived"] == (kind == "restore"), f"{label}: redundant visibility event")
                prior["archived"] = kind == "archive"
            prior.update(memberships=membership, disposition=disposition, relatedProjects=related)
        for pid in membership + related:
            root = projects[pid]["rootSourceId"]
            require(root in state, f"{label}: project root not observed")
            require(root == sid or revision_events[(root, 0)] in ancestors[eid], f"{label}: missing project-root dependency")
        evidence_valid(gold["evidence"], revisions, label)
        for citation in gold["evidence"]:
            producer = revision_events[(citation["sourceId"], citation["revision"])]
            require(producer == eid or producer in ancestors[eid], f"{label}: missing evidence dependency {producer}")
        last_event[sid] = eid
        prefixes[eid] = (deepcopy(state), dict(revisions))
    for pid, project in projects.items():
        root = next((e for e in events if e["sourceId"] == project["rootSourceId"] and e["kind"] == "capture"), None)
        require(root is not None and root["gold"]["memberships"] == [pid], f"{key}: root must introduce own project")
    require(len(modes) >= 2 and any(e["kind"] != "capture" for e in events), f"{key}: modality/lifecycle coverage")
    tasks = library["tasks"]
    require(len(tasks) == 4 and {t["id"] for t in tasks} == {"q1", "q2", "q3", "q4"}, f"{key}: four unique tasks")
    for task in tasks:
        label = f"{key}/{task['id']}"
        require(task["atEvent"] in prefixes, f"{label}: unknown prefix")
        require(task["mode"] in {"current", "historical", "overlap", "uncertain"}, f"{label}: mode")
        require(nonempty(task["question"]) and nonempty(task["rationale"]), f"{label}: question/rationale")
        require(type(task["answerable"]) is bool and bool(task["expectedEvidence"]) == task["answerable"], f"{label}: answerability/evidence")
        snapshot, observed = prefixes[task["atEvent"]]
        evidence_valid(task["expectedEvidence"], observed, label)
        if task["mode"] != "historical":
            require(all(not snapshot[e["sourceId"]]["archived"] and snapshot[e["sourceId"]]["revision"] == e["revision"]
                        for e in task["expectedEvidence"]), f"{label}: stale/archived evidence in nonhistorical task")
    return prefixes


def validate_split(document):
    require(document["schemaVersion"] == 1 and document["split"] in {"development", "evaluation"}, "split schema")
    libraries = document["libraries"]
    prefix = "dev" if document["split"] == "development" else "eval"
    require(len(libraries) == 12 and {lib["id"] for lib in libraries} == {f"{prefix}{i:02d}" for i in range(1, 13)}, "12 unique library IDs required")
    require(len({lib["family"] for lib in libraries}) == 12, "duplicate scenario family")
    for library in libraries:
        validate_library(library)
    for kind in ("revise", "correct", "archive", "restore"):
        require(sum(any(e["kind"] == kind for e in lib["events"]) for lib in libraries) >= 4, f"insufficient {kind} coverage")
    require(sum(any(len(e["gold"]["memberships"]) > 1 for e in lib["events"]) for lib in libraries) >= 4, "insufficient overlap coverage")
    require(any(not t["answerable"] for lib in libraries for t in lib["tasks"]), "missing unresolved task")


def validate_pair(development, evaluation):
    for split in (development, evaluation):
        validate_split(split)
    require(development["split"] == "development" and evaluation["split"] == "evaluation", "swapped splits")
    require(not {x["family"] for x in development["libraries"]} & {x["family"] for x in evaluation["libraries"]}, "family leakage")
    text_sets = [{e["text"].casefold() for lib in split["libraries"] for e in lib["events"] if "text" in e} for split in (development, evaluation)]
    require(not text_sets[0] & text_sets[1], "exact source leakage")


def alternate_events(events):
    """Stable reverse-ID topological schedule, respecting all declared dependencies."""
    remaining, observed, result = {e["id"]: e for e in events}, set(), []
    while remaining:
        ready = sorted((eid for eid, e in remaining.items() if set(e["dependsOn"]) <= observed), reverse=True)
        require(ready, "cyclic dependencies")
        eid = ready[0]
        result.append(remaining.pop(eid))
        observed.add(eid)
    return result


def local_source(sid):
    return "localc" + sid[1:]


def singleton(sid):
    return "t:c" + sid[1:]


def compile_library(library, alternate=False):
    validate_library(library)
    roots = {p["id"]: singleton(p["rootSourceId"]) for p in library["projects"]}
    state, commands = {}, []
    events = alternate_events(library["events"]) if alternate else library["events"]
    for event in events:
        sid, kind = event["sourceId"], event["kind"]
        local = local_source(sid)
        memberships = sorted(roots[p] for p in event["gold"]["memberships"]) or [singleton(sid)]
        command = {"id": event["id"], "kind": kind}
        if kind == "capture":
            command["source"] = {"id": local, "text": event["text"], "modality": {"photo": "image"}.get(event["modality"], event["modality"])}
            command["assignments"] = memberships
            state[local] = {"memberships": memberships, "archived": False, "revision": 0, "textSHA256": sha(event["text"].encode())}
        else:
            command["target"] = local
            if kind == "correct":
                command["assignments"] = sorted(roots[p] for p in event["assignments"])
                state[local]["memberships"] = memberships
            elif kind == "revise":
                command["text"] = event["text"]
                state[local]["textSHA256"] = sha(event["text"].encode())
                state[local]["revision"] += 1
            else:
                state[local]["archived"] = kind == "archive"
        command["expectedState"] = deepcopy(state)
        commands.append(command)
    return {"id": library["id"] + ("-alternate" if alternate else "-chronological"), "events": commands}


def observed_inputs(library):
    """Allowlisted source-only export. Gold, project metadata and task answers excluded."""
    # Dependency edges can encode gold project/evidence relationships. They are
    # scheduling metadata only and must not reach a scorer or retrieval query.
    fields = {"id", "kind", "sourceId", "text", "modality", "locator", "reason"}
    roots = {p["id"]: p["rootSourceId"] for p in library["projects"]}
    events = []
    for event in library["events"]:
        visible = {k: deepcopy(v) for k, v in event.items() if k in fields}
        if event["kind"] == "correct":
            visible["assignedProjectRoots"] = [roots[p] for p in event["assignments"]]
        events.append(visible)
    return {"id": library["id"], "events": events,
            "queries": [{k: t[k] for k in ("id", "atEvent", "question")} for t in library["tasks"]]}


def observed_packet(library, event_id, task_id=None):
    """The checkpoint-2 consumer boundary: only an observed prefix, never a full future trace."""
    trace = observed_inputs(library)
    indices = {event["id"]: i for i, event in enumerate(trace["events"])}
    require(event_id in indices, "unknown observed prefix")
    packet = {"libraryId": library["id"], "observedPrefix": event_id,
              "events": trace["events"][:indices[event_id] + 1]}
    if task_id is not None:
        tasks = [q for q in trace["queries"] if q["id"] == task_id and q["atEvent"] == event_id]
        require(len(tasks) == 1, "query must match observed prefix")
        packet["query"] = tasks[0]["question"]
    return packet


def relationship_records(library):
    records, revisions, corrections, locators = [], {}, {}, {}
    for event in library["events"]:
        sid = event["sourceId"]
        if event["kind"] == "capture":
            revisions[sid] = 0
        elif event["kind"] == "revise":
            revisions[sid] += 1
        elif event["kind"] == "correct":
            corrections[sid] = event["id"]
        if event["kind"] in {"capture", "revise"}:
            locators[(sid, revisions[sid])] = event["locator"]
        gold = event["gold"]
        records.append({"schemaVersion": 1, "policyVersion": "ideal-label-contract-v1",
                        "libraryId": library["id"], "observedPrefix": event["id"],
                        "sourceId": sid, "sourceRevision": revisions[sid],
                        "memberships": gold["memberships"], "relatedProjects": gold["relatedProjects"],
                        "status": "confirmed" if gold["memberships"] else ("suggested" if gold["relatedProjects"] else "unresolved"),
                        "disposition": gold["disposition"],
                        "support": [{**e, "locator": locators[(e["sourceId"], e["revision"])]} for e in gold["evidence"]],
                        "authority": "explicit-user-correction" if sid in corrections else "reviewed-ideal-label",
                        "correctionEventId": corrections.get(sid),
                        "mutatesProduction": False})
    return records
