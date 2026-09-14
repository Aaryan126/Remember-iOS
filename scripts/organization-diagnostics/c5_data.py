"""C5 authored-data validator and explicit source/gold projection. No model imports."""
import hashlib
from itertools import combinations
import re

import c2_common as c

FIELDS = ("anchor", "other", "continuation", "bridge", "ambiguous", "clarification", "collision")
IDS = dict(zip(FIELDS, ("s01", "s02", "s03", "s04", "s05", "s06", "s07")))
LABELS = ("same_project", "separate_projects", "abstain")


def validate_authoring(document):
    c.require(set(document) == {"schemaVersion", "authorship", "families"} and document["schemaVersion"] == 1,
              "Invalid authored schema")
    c.require(isinstance(document["authorship"], str) and document["authorship"].strip(), "Missing authorship")
    c.require(isinstance(document["families"], list) and len(document["families"]) == 8, "Expected eight families")
    seen = set()
    for index, family in enumerate(document["families"], 1):
        c.require(set(family) == set(FIELDS) | {"id", "partition", "domain", "review", "risk"}, "Unknown authored field")
        c.require(all(isinstance(v, str) and v.strip() for v in family.values()), "Invalid authored value")
        c.require(family["id"] == f"f{index:02d}" and family["partition"] == ("discovery" if index <= 4 else "diagnostic"),
                  "Family split/order changed")
        for field in FIELDS:
            value = family[field]
            c.require(20 <= len(value) <= 2000 and value not in seen, "Duplicate or unbounded authored text")
            seen.add(value)
    return document


def validate_packet(packet):
    c.require(set(packet) == {"queryID", "view", "pair", "sources"}, "Leaky/invalid packet schema")
    c.require(isinstance(packet["queryID"], str) and re.fullmatch(r"q[0-9a-f]{24}", packet["queryID"]), "Invalid query ID")
    c.require(packet["view"] in {"pair", "context"}, "Invalid view")
    c.require(isinstance(packet["sources"], list) and 2 <= len(packet["sources"]) <= 4, "Invalid context size")
    ids = []
    for source in packet["sources"]:
        c.require(set(source) == {"id", "text"} and all(isinstance(v, str) and v.strip() for v in source.values()),
                  "Leaky/invalid source schema")
        ids.append(source["id"])
    c.require(len(ids) == len(set(ids)), "Duplicate visible source")
    pair = packet["pair"]
    c.require(isinstance(pair, list) and len(pair) == 2 and all(isinstance(k, str) and k in ids for k in pair)
              and pair[0] != pair[1], "Invalid query pair")
    c.require(packet["view"] != "pair" or set(ids) == set(pair), "Pair-only view contains context")
    return packet


def compile_family(family):
    a, b, continuation, bridge, memo, clarification, collision = FIELDS
    # These are independent diagnostic episodes, not production membership events.
    episodes = [
        ("scope-contrast", [a, b], [(a, b, "separate_projects", "separate_projects", "distinct-scope")]),
        ("continuation", [a, continuation], [(a, continuation, "same_project", "same_project", "negation-continuation")]),
        ("bridge", [a, b, bridge], [(a, b, "separate_projects", "separate_projects", "bridge-separation"),
                                   (a, bridge, "same_project", "same_project", "bridge-link"),
                                   (b, bridge, "same_project", "same_project", "bridge-link")]),
        ("before", [a, b, memo], [(a, memo, "abstain", "abstain", "unresolved-reference"),
                                 (b, memo, "abstain", "abstain", "unresolved-reference")]),
        ("after", [a, b, memo, clarification], [(a, memo, "abstain", "same_project", "context-resolution"),
                                               (b, memo, "abstain", "separate_projects", "context-resolution")]),
        ("collision", [a, collision], [(a, collision, "separate_projects", "separate_projects", "identifier-collision")])]
    packets, gold = [], []
    for number, (episode, visible, queries) in enumerate(episodes, 1):
        for first, second, pair_label, context_label, behavior in queries:
            for view, verdict in (("pair", pair_label), ("context", context_label)):
                visible_fields = [first, second] if view == "pair" else visible
                key = f"{family['id']}:{number}:{first}:{second}:{view}"
                query_id = "q" + hashlib.sha256(key.encode()).hexdigest()[:24]
                packet = {"queryID": query_id, "view": view, "pair": [IDS[first], IDS[second]],
                          "sources": [{"id": IDS[field], "text": family[field]} for field in visible_fields]}
                validate_packet(packet)
                support = [] if verdict == "abstain" else [first, second]
                if episode == "after" and view == "context":
                    support += [clarification]
                packets.append(packet)
                gold.append({"queryID": query_id, "family": family["id"], "partition": family["partition"],
                    "episode": episode, "behavior": behavior, "verdict": verdict,
                    "evidence": [{"sourceID": IDS[field], "quote": family[field]} for field in support],
                    "rationale": family["review"], "annotationStatus": "author-reviewed-not-independent"})
    c.require(len(packets) == len(gold) == 20 and len({p['queryID'] for p in packets}) == 20, "Projection coverage mismatch")
    return {"family": family["id"], "packets": packets, "gold": gold}


def validate_projection(units):
    ids = [packet["queryID"] for unit in units for packet in unit["packets"]]
    c.require(len(ids) == len(set(ids)) == 160, "Release query inventory mismatch")
    for unit in units:
        c.require(len(unit["packets"]) == len(unit["gold"]) == 20, "Missing family query")
        index = {row["queryID"]: row for row in unit["gold"]}
        c.require(len(index) == 20, "Duplicate gold ID")
        for packet in unit["packets"]:
            validate_packet(packet)
            row = index[packet["queryID"]]
            c.require(row["family"] == unit["family"] and row["verdict"] in LABELS, "Invalid gold binding")
            texts = {s["id"]: s["text"] for s in packet["sources"]}
            for quote in row["evidence"]:
                c.require(quote["sourceID"] in texts and quote["quote"] and quote["quote"] in texts[quote["sourceID"]],
                          "Gold cites invisible evidence")
        for view in ("pair", "context"):
            visible = [p for p in unit["packets"] if p["view"] == view]
            bridge = [index[p['queryID']]['verdict'] for p in visible if index[p['queryID']]['episode'] == "bridge"]
            c.require(bridge == ["separate_projects", "same_project", "same_project"], "Transitive bridge corruption")
            before = [p for p in visible if index[p['queryID']]['episode'] == "before"]
            after = [p for p in visible if index[p['queryID']]['episode'] == "after"]
            for initial, later in zip(before, after):
                c.require(initial["pair"] == later["pair"], "Clarification pair changed")
                if view == "pair":
                    c.require(initial["sources"] == later["sources"] and index[later['queryID']]['verdict'] == "abstain",
                              "Future clarification leaked into pair view")
                else:
                    c.require(initial["sources"] == later["sources"][:-1], "Context is not prefix-preserving")
                c.require(index[initial['queryID']]['verdict'] == "abstain", "Premature resolution")
    return True


def novelty(document, previous_texts):
    rows = [(family["id"], family["partition"], field, family[field]) for family in document["families"] for field in FIELDS]
    old_hashes = {c.text_sha(text) for text in previous_texts}
    c.require(all(c.text_sha(text) not in old_hashes for _, _, _, text in rows), "Exact historical source reuse")
    def trigrams(text):
        words = re.findall(r"\w+", text.casefold())
        return set(zip(words, words[1:], words[2:]))
    def overlap(a, b):
        return len(a & b) / len(a | b) if a | b else 0.0
    old = [trigrams(t) for t in previous_texts]
    current = {f"{family}:{field}": trigrams(text) for family, _, field, text in rows}
    closest = []
    for family, _, field, text in rows:
        key = family + ":" + field
        ranked = [(overlap(current[key], tokens), i) for i, tokens in enumerate(old)]
        score, index = max(ranked) if ranked else (0.0, None)
        closest.append({"source": key, "maximumTrigramJaccard": score,
                        "previousTextSHA256": c.text_sha(previous_texts[index]) if index is not None else None})
    across = []
    for left, right in combinations(rows, 2):
        if left[1] != right[1]:
            a, b = left[0] + ":" + left[2], right[0] + ":" + right[2]
            across.append({"left": a, "right": b, "trigramJaccard": overlap(current[a], current[b])})
    return {"newTexts": len(rows), "previousTexts": len(previous_texts), "exactHistoricalMatches": 0,
            "closestHistorical": closest, "largestCrossPartitionOverlaps": sorted(across, key=lambda x: (-x['trigramJaccard'], x['left'], x['right']))[:10],
            "semanticIndependenceEstablished": False}
