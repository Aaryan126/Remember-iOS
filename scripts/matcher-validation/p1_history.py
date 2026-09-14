"""Reference history fixtures, not an execution of Remember's production engine."""
from copy import deepcopy

from prepare import require
from p1 import validate_history


def build(library):
    validate_history(library)
    checks = library["historyChecks"]
    events = []
    for source in library["items"]:
        events.append({"type": "insert", "source": source["id"], "memberships": source["memberships"]})
        revision = checks["revision"]
        if revision["later"] == source["id"]:
            events.append({"type": "revision", "earlier": revision["earlier"],
                           "later": revision["later"], "thread": revision["thread"]})
        rename = checks["rename"]
        if rename and rename["evidenceItem"] == source["id"]:
            events.append({"type": "rename", "thread": rename["thread"], "from": rename["from"], "to": rename["to"]})
        undo = checks["undo"]
        if undo and undo["item"] == source["id"]:
            events.extend([{"type": "hypothetical-link", "source": source["id"], "thread": undo["wrongThread"]},
                           {"type": "undo-link", "source": source["id"], "thread": undo["wrongThread"]}])
    names = dict(library["threadDescriptions"])
    if checks["rename"]:
        names[checks["rename"]["thread"]] = checks["rename"]["from"]
    result = replay(events, names)
    expected = {source["id"]: sorted(source["memberships"]) for source in library["items"]}
    require(result["memberships"] == expected, "history changed source memberships")
    require(len(result["revisions"]) == 1 and len(result["memberships"]) == 20, "history loses provenance")
    return {"library": library["id"], "scope": "reference-fixture-not-production-replay",
            "initialThreadNames": names, "relatedThreads": library["relatedThreads"],
            "events": events, "expected": result,
            "bridgeWitness": checks["bridge"], "automaticTransitiveMergeAllowed": False}


def replay(events, initial_names):
    memberships, revisions, names = {}, [], deepcopy(initial_names)
    pending = None
    for event in events:
        kind = event["type"]
        if pending is not None:
            require(kind == "undo-link", "hypothetical association not immediately undone")
        if kind == "insert":
            require(event["source"] not in memberships, "duplicate source insert")
            require(set(event["memberships"]) <= set(names), "unknown thread")
            memberships[event["source"]] = sorted(event["memberships"])
        elif kind == "revision":
            require(event["earlier"] in memberships and event["later"] in memberships, "revision source missing")
            require(event["earlier"] != event["later"] and all(event["thread"] in memberships[key]
                    for key in (event["earlier"], event["later"])), "invalid revision lineage")
            revisions.append({k: event[k] for k in ("earlier", "later", "thread")})
        elif kind == "rename":
            require(names.get(event["thread"]) == event["from"], "rename changes unknown identity")
            names[event["thread"]] = event["to"]
        elif kind == "hypothetical-link":
            require(event["source"] in memberships and event["thread"] in names
                    and event["thread"] not in memberships[event["source"]], "invalid hypothetical link")
            pending = (event["source"], event["thread"])
            memberships[event["source"]].append(event["thread"])
        elif kind == "undo-link":
            require(pending == (event["source"], event["thread"]), "undo does not match previous link")
            memberships[event["source"]].remove(event["thread"])
            pending = None
        else:
            raise ValueError("unsupported history operation")
    require(pending is None, "unfinished hypothetical action")
    return {"memberships": {key: sorted(value) for key, value in memberships.items()},
            "revisions": revisions, "threadNames": names}
