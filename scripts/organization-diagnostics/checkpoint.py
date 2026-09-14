"""Checkpoint-1 diagnostic preparation and sealed review plumbing; no model execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Evaluation/OrganizationDiagnostics"
RELEASE = ROOT / "Evaluation/MatcherValidation/releases/v1"
RUN = ROOT / "Evaluation/MatcherValidation/runs/validation-02"
REVIEWERS = ("alpha", "beta")
RELATIONS = {"same", "related", "unrelated", "uncertain"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish(path, value):
    """Atomically publish once; identical retries succeed, different content fails."""
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == data, f"Refusing to overwrite {path.name}")
        return
    descriptor, temporary = tempfile.mkstemp(prefix=".publish-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # link is an atomic, no-overwrite publication on the local filesystem.
        try:
            os.link(temporary, path)
        except FileExistsError:
            require(path.read_bytes() == data, f"Concurrent publication differs: {path.name}")
    finally:
        os.unlink(temporary)


def ranked(identifier, salt):
    return hashlib.sha256((salt + ":" + identifier).encode()).hexdigest()


def outcome(row, threshold):
    require(row["relation"] in RELATIONS, "Invalid source relation")
    if row["relation"] == "uncertain":
        return None
    accepted = (threshold is not None and row["score"] is not None
                and row.get("eligible", True) and row["score"] >= threshold)
    return ("TP" if accepted else "FN") if row["relation"] == "same" else ("FP" if accepted else "TN")


def select(reports, count=20):
    """Distinct union-of-seed strata; FP then FN then TP then TN takes precedence.

    A pair can be FP for one seed and TN for another. Select it only once, retaining
    every seed's outcome; these are not confusion-matrix frequencies.
    """
    by_seed = {seed: {row["id"]: row for row in report["predictions"]["hybrid"]}
               for seed, report in reports.items()}
    require(len(by_seed) == 3 and set(by_seed) == {"17", "29", "41"}, "Require all seeds")
    identifiers = set(by_seed["17"])
    require(all(set(rows) == identifiers for rows in by_seed.values()), "Seed pair sets differ")
    labels = {}
    for identifier in identifiers:
        source = by_seed["17"][identifier]
        require(all(all(rows[identifier][key] == source[key] for key in
                        ("first", "second", "library", "relation", "split"))
                    for rows in by_seed.values()), "Seed source/gold mismatch")
        labels[identifier] = {seed: outcome(rows[identifier], reports[seed]["thresholds"]["hybrid"])
                              for seed, rows in by_seed.items()}
    selected, used, counts = [], set(), {}
    for stratum in ("FP", "FN", "TP", "TN"):
        pool = [identifier for identifier in identifiers
                if stratum in labels[identifier].values() and identifier not in used]
        counts[stratum] = len(pool)
        require(len(pool) >= count, f"Insufficient distinct {stratum}: {len(pool)} < {count}")
        chosen = sorted(pool, key=lambda item: ranked(item, "river-diagnostic-v1:" + stratum))[:count]
        for identifier in chosen:
            selected.append({"originalPair": identifier, "stratum": stratum,
                             "outcomes": labels[identifier]})
        used.update(chosen)
    return selected, counts


def source_bindings():
    paths = [DATA / "CONTRACT.md", Path(__file__), RELEASE / "inputs-evaluation.json",
             RUN / "complete.json", RUN / "manifest.json"]
    paths += [RUN / f"evaluation/seed-{seed}.json" for seed in (17, 29, 41)]
    return {str(path.relative_to(ROOT)): digest(path) for path in paths}


def prepare():
    require(os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize >= 10 * 1024**3,
            "Less than 10 GiB free")
    reports = {str(seed): read(RUN / f"evaluation/seed-{seed}.json") for seed in (17, 29, 41)}
    selected, counts = select(reports)
    libraries = read(RELEASE / "inputs-evaluation.json")["libraries"]
    all_items = {item["id"]: item for library in libraries for item in library["items"]}
    aliases = {identifier: f"s{index:03d}" for index, identifier in
               enumerate(sorted(all_items, key=lambda item: ranked(item, "source-alias")), 1)}
    library_aliases = {library["id"]: f"b{index:02d}" for index, library in enumerate(libraries, 1)}
    pairs = {row["id"]: row for row in reports["17"]["predictions"]["hybrid"]}
    packet, selection = [], []
    for index, chosen in enumerate(sorted(selected, key=lambda item: ranked(item["originalPair"], "packet-order")), 1):
        row = pairs[chosen["originalPair"]]
        identifier = f"r{index:03d}"
        shown = {"id": identifier}
        for side in ("first", "second"):
            item = all_items[row[side]]
            shown[side] = {"id": aliases[item["id"]], "text": item["text"], "modality": item["modality"]}
        packet.append(shown)
        selection.append(chosen | {"id": identifier, "originalRelation": row["relation"],
                                   "library": row["library"]})
    publish(DATA / "packets/pairs.json", {"schemaVersion": 1, "phase": "pair", "pairs": packet})
    publish(DATA / "selection.json", {
        "schemaVersion": 1, "sources": source_bindings(), "items": selection,
        "availableAfterExcludingEarlierStrata": counts,
        "policy": "20 per union-of-all-three-seeds stratum; FP/FN/TP/TN precedence; SHA256 ordering; no duplicates",
        "packetSHA256": digest(DATA / "packets/pairs.json"), "sourceAliases": aliases,
        "libraryAliases": library_aliases, "diagnosticOnly": True,
        "oldQualificationChanged": False, "humanReviewed": False,
    })
    verify_selection()
    return {"prepared": True, "pairs": len(packet), "available": counts}


def verify_selection():
    selection = read(DATA / "selection.json")
    require(selection["sources"] == source_bindings(), "Frozen sampling sources changed")
    require(selection["packetSHA256"] == digest(DATA / "packets/pairs.json"), "Pair packet changed")
    return selection


def validate_review(review, packet, reviewer, phase):
    require(set(review) == {"schemaVersion", "reviewer", "phase", "packetSHA256", "judgments"}, "Invalid review keys")
    require(review["schemaVersion"] == 1 and review["reviewer"] == reviewer and review["phase"] == phase,
            "Wrong reviewer/phase")
    rows = review["judgments"]
    require(isinstance(rows, list), "Review judgments must be a list")
    ids = [row["id"] for row in rows]
    require(len(ids) == len(set(ids)) and set(ids) == {row["id"] for row in packet["pairs"]},
            "Missing/duplicate/extra review judgments")
    for row in rows:
        expected = {"id", "relation", "rationale", "pairSufficient"}
        if phase == "context":
            expected.add("evidenceIds")
        require(set(row) == expected and row["relation"] in RELATIONS, "Invalid judgment shape/relation")
        require(isinstance(row["rationale"], str) and len(row["rationale"].strip()) >= 20,
                "Rationale must explain evidence")
        require(type(row["pairSufficient"]) is bool, "pairSufficient must be boolean")
        if phase == "pair":
            require(row["pairSufficient"] == (row["relation"] != "uncertain"), "Pair sufficiency inconsistent")
        else:
            entry = next(item for item in packet["pairs"] if item["id"] == row["id"])
            allowed = {item["id"] for item in packet["libraries"][entry["contextId"]]}
            require(isinstance(row["evidenceIds"], list) and row["evidenceIds"]
                    and all(item in allowed for item in row["evidenceIds"]), "Invalid context evidence IDs")


def seal(reviewer, phase):
    verify_selection()
    packet_path = DATA / ("packets/pairs.json" if phase == "pair" else "packets/context.json")
    path = DATA / f"reviews/{reviewer}-{phase}.json"
    review, packet = read(path), read(packet_path)
    validate_review(review, packet, reviewer, phase)
    require(review["packetSHA256"] == digest(packet_path), "Review packet hash mismatch")
    if phase == "context":
        verify_pair_seals()
    receipt = {"reviewer": reviewer, "phase": phase, "reviewSHA256": digest(path),
               "packetSHA256": digest(packet_path), "contractSHA256": digest(DATA / "CONTRACT.md"),
               "judgments": len(review["judgments"])}
    publish(DATA / f"receipts/{reviewer}-{phase}.json", receipt)
    return receipt


def verify_pair_seals():
    for reviewer in REVIEWERS:
        path = DATA / f"receipts/{reviewer}-pair.json"
        require(path.exists(), "Both pair reviews must be sealed before context publication")
        require(read(path) == seal(reviewer, "pair"), "Pair seal changed")


def context():
    selection = verify_selection()
    verify_pair_seals()
    aliases = selection["sourceAliases"]
    libraries = read(RELEASE / "inputs-evaluation.json")["libraries"]
    contexts = {selection["libraryAliases"][library["id"]]: [
        {"id": aliases[item["id"]], "text": item["text"], "modality": item["modality"]}
        for item in library["items"]] for library in libraries}
    by_id = {item["id"]: item for item in selection["items"]}
    pairs = [item | {"contextId": selection["libraryAliases"][by_id[item["id"]]["library"]]}
             for item in read(DATA / "packets/pairs.json")["pairs"]]
    publish(DATA / "packets/context.json", {"schemaVersion": 1, "phase": "context",
                                            "pairs": pairs, "libraries": contexts,
                                            "retrospectiveContextNotOnlinePrefix": True})
    return {"contextPublished": True, "pairs": len(pairs), "libraries": len(contexts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify-selection", "seal", "context"))
    parser.add_argument("--reviewer", choices=REVIEWERS)
    parser.add_argument("--phase", choices=("pair", "context"))
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare()
    elif args.command == "verify-selection":
        verify_selection()
        result = {"selectionVerified": True}
    elif args.command == "context":
        result = context()
    else:
        require(args.reviewer and args.phase, "seal requires reviewer and phase")
        result = seal(args.reviewer, args.phase)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
