"""Compile explicit user choices separately from source-only policy inputs.

Annotated memberships are consulted only for scripted correction anchor selection.
Prefix gold and reviewer outcomes are never opened. This module writes no files.
"""

from __future__ import annotations

import hashlib
import json
from itertools import combinations, product
from pathlib import Path


RELEASE = Path(__file__).resolve().parents[2] / "Evaluation/OrganizationDiagnostics/release"
ORDERS = ("chronological", "shuffle-1", "shuffle-2")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _ancestry(event_id: str, events: dict, visiting: set | None = None) -> set:
    visiting = set() if visiting is None else visiting
    _require(event_id in events, f"Unknown dependency: {event_id}")
    _require(event_id not in visiting, "Cyclic event dependencies")
    ancestors = set()
    for dependency in events[event_id]["dependsOn"]:
        ancestors.add(dependency)
        ancestors.update(_ancestry(dependency, events, visiting | {event_id}))
    return ancestors


def compile_stream(released: dict, annotated: dict) -> tuple[dict, list[dict]]:
    """Project one released order and return a separate explicit-action audit."""
    _require(released["story"] == annotated["id"], "Story ID mismatch")
    authored_events = {event["id"]: event for event in annotated["events"]}
    _require(len(authored_events) == len(annotated["events"]), "Duplicate annotated event")
    capture_annotations = {capture["id"]: capture for capture in annotated["captures"]}
    _require(len(capture_annotations) == len(annotated["captures"]), "Duplicate annotated capture")
    seen_events, seen_sources, output, audit = set(), set(), [], []
    for event in released["events"]:
        event_id, kind = event["id"], event["kind"]
        _require(event_id in authored_events and event_id not in seen_events, "Unknown/duplicate released event")
        authored = authored_events[event_id]
        _require(kind == authored["kind"], "Event kind mismatch")
        ancestors = _ancestry(event_id, authored_events)
        _require(ancestors <= seen_events, f"Dependency follows event {event_id}")
        projected = {"id": event_id, "kind": kind}
        if kind == "capture":
            source = event["source"]
            _require(source["id"] == authored["capture"], "Capture ID mismatch")
            _require(source["id"] not in seen_sources, "Duplicate source")
            projected["source"] = {field: source[field] for field in ("id", "text", "modality")}
            _require(all(isinstance(value, str) and value.strip() for value in projected["source"].values()), "Invalid source evidence")
            seen_sources.add(source["id"])
        else:
            target = event["target"]
            _require(target == authored["target"] and target in seen_sources, "Unobserved or mismatched mutation target")
            projected["target"] = target
            if kind == "revise":
                _require(isinstance(event["text"], str) and event["text"].strip(), "Invalid revised text")
                projected["text"] = event["text"]
            elif kind == "correct":
                projects = event["userRequestedProjects"]
                _require(isinstance(projects, list) and all(isinstance(project, str) and project for project in projects), "Invalid explicit project selection")
                _require(len(set(projects)) == len(projects), "Duplicate explicit project selection")
                ancestor_sources = {authored_events[ancestor]["capture"] for ancestor in ancestors
                                    if authored_events[ancestor]["kind"] == "capture"}
                selected = []
                for project in sorted(projects):
                    eligible = sorted(source_id for source_id in ancestor_sources
                                      if source_id != target and capture_annotations[source_id]["memberships"] == [project])
                    _require(bool(eligible), f"No dependency anchor for {released['story']} {event_id} {project}")
                    anchor = eligible[0]
                    _require(anchor in seen_sources, "Anchor is not previously observed")
                    selected.append(anchor)
                    audit.append({"story": released["story"], "order": released["order"], "event": event_id,
                                  "target": target, "userRequestedProject": project, "anchor": anchor,
                                  "eligibleAncestorCaptures": eligible})
                projected["targetAnchors"] = sorted(set(selected))
            else:
                _require(kind in {"archive", "restore"}, f"Unknown event kind: {kind}")
        output.append(projected)
        seen_events.add(event_id)
    _require(seen_events == set(authored_events), "Missing released events")
    return {"story": released["story"], "order": released["order"], "events": output}, audit


def compile_inputs() -> tuple[list[dict], list[dict]]:
    """Read the fixed 36 C1 released streams and annotated correction dependencies."""
    streams, audit = [], []
    expected_paths = {RELEASE / "inputs" / f"story-{index:02d}-{order}.json"
                      for index in range(1, 13) for order in ORDERS}
    _require(set((RELEASE / "inputs").glob("*.json")) == expected_paths, "Expected exactly the 36 released streams")
    for index in range(1, 13):
        story_id = f"story-{index:02d}"
        annotated = json.loads((RELEASE / "gold" / f"{story_id}-adjudicated.json").read_text())
        for order in ORDERS:
            released = json.loads((RELEASE / "inputs" / f"{story_id}-{order}.json").read_text())
            _require((released["story"], released["order"]) == (story_id, order), "Released filename/identity mismatch")
            compiled, mappings = compile_stream(released, annotated)
            streams.append(compiled)
            audit.extend(mappings)
    return streams, audit


def catalogue(streams: list[dict]) -> dict:
    """All cross-source text-version pairs per story, deduplicated by exact hash.

    This offline cache index includes future versions. Policy callbacks must look up
    only the currently observed source versions when executing an online stream.
    """
    texts, stories, pairs = {}, {}, {}
    for stream in streams:
        versions = stories.setdefault(stream["story"], {})
        observed = set()
        for event in stream["events"]:
            if event["kind"] == "capture":
                source_id, text = event["source"]["id"], event["source"]["text"]
                _require(source_id not in observed, "Duplicate catalogue source")
                observed.add(source_id)
            elif event["kind"] == "revise":
                source_id, text = event["target"], event["text"]
                _require(source_id in observed, "Unobserved revision target")
            else:
                continue
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            _require(digest not in texts or texts[digest] == text, "Text SHA-256 collision")
            texts[digest] = text
            versions.setdefault(source_id, set()).add(digest)
    for versions in stories.values():
        for left, right in combinations(sorted(versions), 2):
            for first, second in product(versions[left], versions[right]):
                first, second = sorted((first, second))
                pairs[f"{first}--{second}"] = {"first": first, "second": second}
    return {"texts": dict(sorted(texts.items())), "pairs": dict(sorted(pairs.items()))}
