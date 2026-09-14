"""P1 authoring, separated review packets and immutable benchmark release.

No model execution, downloads, prior test access or production imports.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import shutil

from prepare import DATA, ROOT, GIB, digest, publish, read, require, shingles, validate_corpus
import prepare

RUN = DATA / "runs/p1-01"
REVIEWER = {"author_a": "author_c", "author_b": "author_a", "author_c": "author_b"}
RELATIONS = {"same", "related", "unrelated", "uncertain"}


def capacity():
    policy = read(DATA / "contract.json")
    free = shutil.disk_usage(ROOT).free
    size = sum(p.stat().st_size for p in DATA.rglob("*") if p.is_file())
    require(free - 16 * 1024 ** 2 >= policy["freeSpaceReserveGiB"] * GIB, "pause: free-space reserve")
    require(size + 16 * 1024 ** 2 <= policy["newStorageCapGiB"] * GIB, "pause: new-storage budget")


def assignment():
    freeze = read(RUN / "assignment-freeze.json")
    require(freeze["familiesSHA256"] == digest(DATA / "families.json"), "family assignments changed")
    require(freeze["protocolSHA256"] == digest(DATA / "P1_PROTOCOL.md"), "review protocol changed")
    require(freeze["preparationSHA256"] == digest(DATA / "runs/preparation-01/complete.json"), "P0 binding changed")
    prepare.verify(DATA / "runs/preparation-01")
    families = read(DATA / "families.json")["families"]
    require(len(families) == 24 and len({f["id"] for f in families}) == 24, "family coverage")
    result = {}
    for family in families:
        require(len(family["libraries"]) == 2 and family["author"] in REVIEWER, "invalid family")
        for lid in family["libraries"]:
            require(lid not in result, "duplicate assigned library")
            result[lid] = family
    require(Counter(f["split"] for f in result.values()) == read(DATA / "contract.json")["requiredSplits"], "assigned split counts")
    return result


def validate_library(library, family):
    require(library["id"] in family["libraries"] and library["split"] == family["split"]
            and library["storyFamily"] == family["id"], "library assignment mismatch")
    require(set(library["threadDescriptions"]) == set(library["threads"]), "thread descriptions missing")
    require(all(isinstance(v, str) and v.strip() for v in library["threadDescriptions"].values()), "empty thread objective")
    require(3 <= len(library["threads"]) <= 6, "thread count outside protocol")
    items = library["items"]
    require([i["id"] for i in items] == [f'{library["id"]}-i{n:02d}' for n in range(1, 21)], "chronological source IDs")
    require(len({i["modality"] for i in items}) >= 3, "insufficient modality diversity")
    require(1 <= sum(not i["memberships"] for i in items) <= 3, "uncertain source count")
    policy = read(DATA / "contract.json") | {"requiredSplits": {library["split"]: 1}, "librariesPerStoryFamily": 1}
    result = validate_corpus({"schemaVersion": 1, "purpose": "qualification-release", "libraries": [library]}, policy, release=True)
    require(all(result[2]["relations"][label] for label in RELATIONS), "missing relation category")
    validate_history(library)
    return result


def validate_history(library):
    items = {i["id"]: i for i in library["items"]}
    positions = {i["id"]: n for n, i in enumerate(library["items"])}
    checks = library["historyChecks"]
    require(set(checks) == {"bridge", "revision", "rename", "undo"}, "history schema")
    bridge = checks["bridge"]
    require(bridge["item"] in items and len(set(bridge["threads"])) >= 2
            and set(bridge["threads"]) <= set(items[bridge["item"]]["memberships"]), "invalid bridge history")
    revision = checks["revision"]
    require(revision["earlier"] in items and revision["later"] in items, "missing revision source")
    require(positions[revision["earlier"]] < positions[revision["later"]], "revision reverses chronology")
    require(all(revision["thread"] in items[key]["memberships"] for key in (revision["earlier"], revision["later"])), "revision crosses threads")
    rename = checks["rename"]
    if rename:
        require(rename["evidenceItem"] in items and rename["thread"] in items[rename["evidenceItem"]]["memberships"], "rename evidence missing")
        require(isinstance(rename["from"], str) and isinstance(rename["to"], str)
                and rename["from"].strip() and rename["to"].strip() and rename["from"] != rename["to"], "invalid rename")
    undo = checks["undo"]
    if undo:
        require(undo["item"] in items and undo["wrongThread"] in library["threads"]
                and undo["wrongThread"] not in items[undo["item"]]["memberships"]
                and bool(undo["reason"].strip()), "invalid hypothetical undo")


def pair_sample(library):
    pairs = []
    for a, b in itertools.combinations(library["items"], 2):
        x, y = shingles(a["text"]), shingles(b["text"])
        similarity = len(x & y) / len(x | y) if x | y else 0
        pairs.append((a["id"] + "--" + b["id"], similarity, a, b))
    lexical = sorted(pairs, key=lambda p: (-p[1], p[0]))[:4]
    chosen = {p[0] for p in lexical}
    remainder = sorted((p for p in pairs if p[0] not in chosen),
                       key=lambda p: hashlib.sha256(("p1-pair-review-v1|" + p[0]).encode()).hexdigest())[:8]
    return [{"id": pid, "library": library["id"],
             "first": {k: a[k] for k in ("id", "text", "modality")},
             "second": {k: b[k] for k in ("id", "text", "modality")}}
            for pid, _, a, b in lexical + remainder]


def author_libraries(author):
    require(author in REVIEWER, "unknown author")
    assigned = assignment()
    libraries = []
    for lid, family in assigned.items():
        if family["author"] == author:
            library = read(DATA / "authoring" / f"{lid}.json")
            validate_library(library, family)
            libraries.append(library)
    require(len(libraries) == 16, "incomplete author batch")
    return libraries


def project(author):
    capacity()
    libraries = author_libraries(author)
    packet = {"schemaVersion": 1, "author": author, "reviewer": REVIEWER[author], "phase": "pair-first",
              "sourceHashes": {lib["id"]: digest(DATA / "authoring" / f'{lib["id"]}.json') for lib in libraries},
              "pairs": [p for lib in libraries for p in pair_sample(lib)]}
    publish(RUN / "packets" / f"{author}-pairs.json", packet)
    return {"author": author, "pairs": len(packet["pairs"]), "reviewer": REVIEWER[author]}


def validate_pair_review(review, packet, packet_sha):
    require(review["reviewer"] == packet["reviewer"] and review["author"] == packet["author"]
            and review["phase"] == "pair-first" and review["packetSHA256"] == packet_sha, "review identity/binding")
    require(len(review["pairs"]) == len(packet["pairs"]), "incomplete pair-first review")
    require({p["id"] for p in review["pairs"]} == {p["id"] for p in packet["pairs"]}, "pair review coverage")
    for pair in review["pairs"]:
        require(pair["relation"] in RELATIONS and pair["sufficiency"] in {"sufficient", "needs-context"}
                and isinstance(pair["evidence"], str) and pair["evidence"].strip(), "invalid pair judgment")


def seal_pairs(author):
    capacity()
    project(author)  # Verify author files still match immutable projected sources.
    packet_path = RUN / "packets" / f"{author}-pairs.json"
    packet = read(packet_path)
    review_path = DATA / "reviews" / f"{REVIEWER[author]}-pairs.json"
    validate_pair_review(read(review_path), packet, digest(packet_path))
    publish(RUN / "receipts" / f"{author}-pair-review.json",
            {"packetSHA256": digest(packet_path), "reviewSHA256": digest(review_path), "reviewer": REVIEWER[author]})
    # Publication is deliberately after the pair-review receipt, never before it.
    libraries = author_libraries(author)
    context = {"schemaVersion": 1, "author": author, "reviewer": REVIEWER[author], "phase": "context",
               "pairReviewSHA256": digest(review_path),
               "libraries": [{k: lib[k] for k in ("id", "threads", "threadDescriptions", "historyChecks")} |
                             {"items": [{k: i[k] for k in ("id", "text", "modality")} for i in lib["items"]]}
                             for lib in libraries]}
    publish(RUN / "packets" / f"{author}-context.json", context)
    return {"author": author, "pairReviewSealed": True, "contextAvailable": True}


def validate_context_review(review, packet, packet_sha):
    require(review["author"] == packet["author"] and review["reviewer"] == packet["reviewer"]
            and review["phase"] == "context" and review["packetSHA256"] == packet_sha, "context binding")
    expected = {lib["id"]: lib for lib in packet["libraries"]}
    require(len(review["libraries"]) == len(expected) and {lib["id"] for lib in review["libraries"]} == set(expected), "context library coverage")
    for reviewed in review["libraries"]:
        lib = expected[reviewed["id"]]
        assignments = reviewed["assignments"]
        require(len(assignments) == len(lib["items"]) and {i["id"] for i in assignments} == {i["id"] for i in lib["items"]}, "context source coverage")
        for item in assignments:
            require(len(item["memberships"]) == len(set(item["memberships"]))
                    and set(item["memberships"]) <= set(lib["threads"])
                    and isinstance(item["reason"], str) and item["reason"].strip(), "invalid context membership")
        links = reviewed["relatedThreads"]
        require(all(len(p) == 2 and p[0] != p[1] and set(p) <= set(lib["threads"]) for p in links), "invalid reviewed relation")
        require(len({frozenset(p) for p in links}) == len(links), "duplicate reviewed relation")
        require(isinstance(reviewed["historyVerdict"], str) and reviewed["historyVerdict"] in {"supported", "needs-correction"}
                and bool(reviewed["historyEvidence"].strip()), "history review missing")


def seal_context(author):
    capacity()
    seal_pairs(author)
    packet_path = RUN / "packets" / f"{author}-context.json"
    review_path = DATA / "reviews" / f"{REVIEWER[author]}-context.json"
    validate_context_review(read(review_path), read(packet_path), digest(packet_path))
    publish(RUN / "receipts" / f"{author}-context-review.json",
            {"packetSHA256": digest(packet_path), "reviewSHA256": digest(review_path), "reviewer": REVIEWER[author]})
    return {"author": author, "contextReviewSealed": True}


def status():
    assigned = assignment()
    authored = [lid for lid in assigned if (DATA / "authoring" / f"{lid}.json").exists()]
    return {"assignedLibraries": len(assigned), "authoredLibraries": len(authored),
            "authored": authored, "complete": (RUN / "complete.json").exists(), "trainingStarted": False,
            "pairReviewsSealed": [a for a in REVIEWER if (RUN / "receipts" / f"{a}-pair-review.json").exists()],
            "contextReviewsSealed": [a for a in REVIEWER if (RUN / "receipts" / f"{a}-context-review.json").exists()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "project", "seal-pairs", "seal-context"))
    parser.add_argument("--author", choices=tuple(REVIEWER))
    args = parser.parse_args()
    if args.command != "status":
        require(args.author is not None, "--author required")
    commands = {"project": project, "seal-pairs": seal_pairs, "seal-context": seal_context}
    print(json.dumps(status() if args.command == "status" else commands[args.command](args.author), indent=2))


if __name__ == "__main__":
    main()
