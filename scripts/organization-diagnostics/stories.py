"""Validate fictional causal stories and publish source-only streams plus prefix gold.

This is a pure reference-state implementation, not production ledger replay or a
matcher. It never loads models, reads the vault, or changes original experiments.
"""
import argparse
import copy
import hashlib
import json

import checkpoint as c

MODALITIES = {"note", "image", "voice", "file", "video"}


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def validate(story):
    c.require(set(story) == {"schemaVersion", "id", "title", "threads", "captures", "events",
                             "challenges", "authorNotes"}, "Story schema keys differ")
    c.require(story["schemaVersion"] == 1 and isinstance(story["title"], str) and story["title"].strip(), "Invalid story header")
    threads = {thread["id"]: thread for thread in story["threads"]}
    c.require(len(threads) == len(story["threads"]) and len(threads) >= 3, "Duplicate/insufficient projects")
    for thread in threads.values():
        c.require(set(thread) == {"id", "title", "scope"} and all(isinstance(v, str) and v.strip() for v in thread.values()), "Invalid project definition")
    captures = {item["id"]: item for item in story["captures"]}
    c.require(len(story["captures"]) == 12 and set(captures) == {f"c{i:02d}" for i in range(1, 13)}, "Require c01-c12 exactly once")
    for capture in captures.values():
        c.require(set(capture) == {"id", "modality", "text", "memberships", "rationale"}, "Invalid capture keys")
        c.require(capture["modality"] in MODALITIES and isinstance(capture["text"], str)
                  and len(capture["text"].strip()) >= 10 and isinstance(capture["rationale"], str)
                  and len(capture["rationale"].strip()) >= 20, "Invalid capture evidence")
        memberships(capture["memberships"], threads)
    c.require(set(threads) == {t for capture in captures.values() for t in capture["memberships"]}, "Unused project")
    c.require(len({item["modality"] for item in captures.values()}) >= 2, "Need varied modality representations")
    events = story["events"]
    seen, created, last_mutation, archived, ancestors = set(), {}, {}, {}, {}
    kinds = set()
    for event in events:
        identifier, kind = event["id"], event["kind"]
        c.require(isinstance(identifier, str) and identifier and identifier not in seen, "Duplicate/invalid event ID")
        dependencies = event["dependsOn"]
        c.require(isinstance(dependencies, list) and len(dependencies) == len(set(dependencies))
                  and set(dependencies) <= seen, "Dependency absent, forward or duplicate")
        ancestors[identifier] = set(dependencies)
        for dependency in dependencies:
            ancestors[identifier].update(ancestors[dependency])
        keys = {"id", "kind", "dependsOn"}
        if kind == "capture":
            c.require(set(event) == keys | {"capture"}, "Invalid capture event fields")
            target = event["capture"]
            c.require(target in captures and target not in created, "Duplicate/unknown capture")
            created[target] = identifier
            archived[target] = False
        else:
            extras = {"revise": {"target", "text"}, "correct": {"target", "memberships", "reason"},
                      "archive": {"target"}, "restore": {"target"}}
            c.require(kind in extras and set(event) == keys | extras[kind], "Invalid mutation fields/kind")
            target = event["target"]
            c.require(target in created and created[target] in ancestors[identifier], "Mutation lacks target dependency")
            if target in last_mutation:
                c.require(last_mutation[target] in ancestors[identifier], "Mutation chain dependency missing")
            if kind == "archive":
                c.require(not archived[target], "Already archived")
                archived[target] = True
            elif kind == "restore":
                c.require(archived[target], "Restore without prior archive")
                archived[target] = False
            elif kind == "revise":
                c.require(not archived[target] and isinstance(event["text"], str) and event["text"].strip(), "Invalid revision")
            else:
                c.require(not archived[target], "Correction to archived source")
                memberships(event["memberships"], threads)
                c.require(isinstance(event["reason"], str) and len(event["reason"].strip()) >= 20, "Correction needs evidence")
                known_threads = {t for item in created for t in captures[item]["memberships"]}
                c.require(set(event["memberships"]) <= known_threads, "Correction targets unseen project")
                for thread in event["memberships"]:
                    c.require(any(thread in captures[item]["memberships"] and creation in ancestors[identifier]
                                  for item, creation in created.items()),
                              "Correction lacks causal dependency on target project evidence")
            last_mutation[target] = identifier
        seen.add(identifier)
        kinds.add(kind)
    c.require(set(created) == set(captures), "Every capture must be imported exactly once")
    c.require(kinds == {"capture", "revise", "correct", "archive", "restore"}, "Missing required history kinds")
    return story


def memberships(values, threads):
    c.require(isinstance(values, list) and all(isinstance(value, str) for value in values)
              and len(values) == len(set(values)) and set(values) <= set(threads), "Invalid memberships")


def ordered(story, mode):
    events = story["events"]
    if mode == "chronological":
        return events
    remaining = {event["id"]: event for event in events}
    result, done = [], set()
    while remaining:
        available = [event for event in remaining.values() if set(event["dependsOn"]) <= done]
        c.require(available, "Cyclic event dependencies")
        chosen = min(available, key=lambda event: c.ranked(event["id"], story["id"] + ":" + mode))
        result.append(chosen)
        done.add(chosen["id"])
        del remaining[chosen["id"]]
    return result


def project(story, events):
    """Return model-visible capture/edit inputs, explicit user actions, and separate gold."""
    captures = {item["id"]: item for item in story["captures"]}
    state, prefixes, inputs = {}, [], []
    seen = set()
    for event in events:
        c.require(set(event["dependsOn"]) <= seen, "Reordered event violates dependencies")
        kind = event["kind"]
        if kind == "capture":
            item = captures[event["capture"]]
            c.require(item["id"] not in state, "Duplicate capture in replay")
            state[item["id"]] = {"memberships": sorted(item["memberships"]), "archived": False,
                                 "textSHA256": text_hash(item["text"]), "revision": 0}
            shown = {"id": event["id"], "kind": kind, "source": {key: item[key] for key in ("id", "modality", "text")}}
        else:
            target = event["target"]
            c.require(target in state, "Mutation target not yet observed")
            if kind == "revise":
                c.require(not state[target]["archived"], "Cannot revise archived source")
                state[target]["textSHA256"] = text_hash(event["text"])
                state[target]["revision"] += 1
            elif kind == "correct":
                c.require(not state[target]["archived"], "Cannot correct archived source")
                state[target]["memberships"] = sorted(event["memberships"])
            elif kind in {"archive", "restore"}:
                c.require(state[target]["archived"] == (kind == "restore"), "Archive/restore state mismatch")
                state[target]["archived"] = kind == "archive"
            else:
                raise ValueError("Unknown mutation")
            shown = {key: value for key, value in event.items() if key not in {"dependsOn", "memberships"}}
            if kind == "correct":
                # User commands are evaluated separately; these are NEVER pair-model features.
                shown["userRequestedProjects"] = event["memberships"]
                shown["explicitUserAction"] = True
        inputs.append(shown)
        prefixes.append({"after": event["id"], "state": copy.deepcopy(state)})
        seen.add(event["id"])
    return inputs, prefixes


def build():
    # The shared phase validator verifies authoring, packet, reviewer and adjudication
    # seals. Import at this boundary to avoid a module-initialization cycle.
    from finalize import validate_story_adjudication
    validate_story_adjudication()
    adjudication = c.read(c.DATA / "story-adjudication.json")
    c.require(adjudication["reviewSHA256"] == c.digest(c.DATA / "reviews/alpha-stories.json"), "Story adjudication review changed")
    paths = sorted((c.DATA / "stories").glob("story-*.json"))
    c.require([path.stem for path in paths] == [f"story-{i:02d}" for i in range(1, 13)], "Need all 12 stories")
    receipt = {"schemaVersion": 1, "stories": {}, "outputs": {}, "productionReplayRun": False,
               "diagnosticOnly": True, "referenceStateOnly": True}
    pending = {}
    for path in paths:
        story = validate(apply_adjudication(c.read(path), adjudication))
        c.require(story["id"] == path.stem, "Story ID/path mismatch")
        receipt["stories"][path.name] = c.digest(path)
        adjudicated = c.DATA / f"release/gold/{story['id']}-adjudicated.json"
        pending[adjudicated] = story
        orders, finals = [], []
        for mode in ("chronological", "shuffle-1", "shuffle-2"):
            events = ordered(story, mode)
            inputs, prefixes = project(story, events)
            orders.append([event["id"] for event in events])
            finals.append(prefixes[-1]["state"])
            for category, value in (("inputs", {"story": story["id"], "order": mode, "events": inputs}),
                                    ("gold", {"story": story["id"], "order": mode, "prefixes": prefixes})):
                destination = c.DATA / f"release/{category}/{story['id']}-{mode}.json"
                pending[destination] = value
        c.require(len({tuple(order) for order in orders}) == 3, "Shuffles must differ from each other and chronology")
        c.require(finals[0] == finals[1] == finals[2], "Causal orders produce different reference final state")
    receipt["sources"] = {str(path.relative_to(c.ROOT)): c.digest(path) for path in
                          (c.DATA / "CONTRACT.md", c.DATA / "STORY_AUTHORING.md", c.DATA / "story-adjudication.json",
                           c.DATA / "reviews/alpha-stories.json", c.ROOT / "scripts/organization-diagnostics/stories.py")}
    # Validate the whole batch and existing destinations before any publication.
    # Interruption can leave identical resumable files, never failed-order outputs.
    for path, value in pending.items():
        if path.exists():
            expected = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
            c.require(path.read_bytes() == expected, "Existing release differs; preserve and investigate")
    for path, value in pending.items():
        c.publish(path, value)
        receipt["outputs"][str(path.relative_to(c.DATA))] = c.digest(path)
    c.publish(c.DATA / "receipts/stories.json", receipt)
    return {"stories": len(paths), "captures": 12 * len(paths), "orders": 3 * len(paths), "productionReplayRun": False}


def apply_adjudication(story, adjudication):
    """Apply explicit reviewed amendments to a copy; preserve authored files and reviews."""
    result = copy.deepcopy(story)
    items = {item["id"]: item for item in result["captures"]}
    events = {event["id"]: event for event in result["events"]}
    seen = set()
    for decision in adjudication["decisions"]:
        if decision["story"] != story["id"]:
            continue
        identifier = decision["capture"]
        c.require(identifier in items and identifier not in seen, "Unknown/duplicate membership amendment")
        c.require(items[identifier]["memberships"] == decision["authored"], "Authored membership changed")
        memberships(decision["final"], {thread["id"] for thread in result["threads"]})
        items[identifier]["memberships"] = decision["final"]
        items[identifier]["rationale"] = decision["rationale"]
        seen.add(identifier)
    seen = set()
    for addition in adjudication["dependencyAdditions"]:
        if addition["story"] != story["id"]:
            continue
        identifier = addition["event"]
        c.require(identifier in events and identifier not in seen, "Unknown/duplicate dependency amendment")
        c.require(isinstance(addition["dependsOn"], list) and set(addition["dependsOn"]) <= set(events), "Invalid added dependencies")
        events[identifier]["dependsOn"] = sorted(set(events[identifier]["dependsOn"]) | set(addition["dependsOn"]))
        seen.add(identifier)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build"))
    args = parser.parse_args()
    if args.command == "build":
        result = build()
    else:
        paths = sorted((c.DATA / "stories").glob("story-*.json"))
        for path in paths:
            validate(c.read(path))
        result = {"validatedAvailableStories": len(paths), "completeSet": len(paths) == 12}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
