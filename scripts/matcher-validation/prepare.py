"""Small resumable P0 preparation only; cannot train or open any previous dataset."""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Evaluation/MatcherValidation"
SOURCES = [DATA / "PLAN.md", DATA / "contract.json", DATA / "pilot.json", DATA / "pilot-review.md",
           Path(__file__), Path(__file__).with_name("validation_policy.py"),
           Path(__file__).with_name("test_validation.py")]
GIB = 1024 ** 3


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish(path, value):
    """Atomic no-overwrite publication; partial preparation can resume identical files."""
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if path.exists():
        require(path.read_bytes() == raw, f"refusing to replace changed artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".preparation-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            require(path.read_bytes() == raw, "concurrent publication differs")
    finally:
        os.unlink(temporary)


def shingles(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {tuple(words[i:i + 3]) for i in range(max(1, len(words) - 2))}


def validate_corpus(corpus, policy, release=False):
    require(corpus.get("schemaVersion") == 1, "unsupported schema")
    purpose = "qualification-release" if release else "development-pilot-only"
    require(corpus.get("purpose") == purpose, "pilot cannot become a qualification release implicitly")
    libraries = corpus.get("libraries", [])
    require(bool(libraries), "empty corpus")
    library_ids, item_ids, texts = set(), set(), set()
    families = {"storyFamily": {}, "templateFamily": {}}
    projected, gold = [], []
    counts, family_counts, indexed = {}, {}, []
    for library in libraries:
        lid = library["id"]
        require(isinstance(lid, str) and bool(lid) and lid not in library_ids, "invalid/duplicate library ID")
        library_ids.add(lid)
        split = library["split"]
        require(split in policy["requiredSplits"] if release else split == "pilot", "invalid split")
        counts[split] = counts.get(split, 0) + 1
        for field, assignments in families.items():
            group = library[field]
            require(isinstance(group, str) and bool(group), "missing family")
            require(group not in assignments or assignments[group] == split, f"{field} split leakage")
            assignments[group] = split
        family = library["storyFamily"]
        family_counts[family] = family_counts.get(family, 0) + 1
        threads = library["threads"]
        require(len(threads) >= 2 and all(isinstance(t, str) and t for t in threads)
                and len(threads) == len(set(threads)), "invalid threads")
        related = set()
        for pair in library["relatedThreads"]:
            require(len(pair) == 2 and pair[0] != pair[1] and set(pair) <= set(threads), "invalid related endpoints")
            key = frozenset(pair)
            require(key not in related, "duplicate related link")
            related.add(key)
        items = library["items"]
        require(len(items) >= 2, "not enough sources")
        if release:
            require(len(items) == policy["itemsPerLibrary"], "wrong source count")
        for item in items:
            iid = item["id"]
            require(isinstance(iid, str) and bool(iid) and iid not in item_ids, "invalid/duplicate source ID")
            item_ids.add(iid)
            require(isinstance(item.get("text"), str) and bool(item["text"].strip()), "empty source")
            normalized = " ".join(re.findall(r"\w+", item["text"].casefold()))
            require(normalized not in texts, "duplicate source text")
            texts.add(normalized)
            require(item.get("modality") in {"note", "image", "voice", "video", "file"}, "invalid modality")
            require(bool(item.get("rationale", "").strip()), "missing host-side rationale")
            memberships = item["memberships"]
            require(len(memberships) == len(set(memberships)) and set(memberships) <= set(threads), "invalid membership")
            indexed.append((split, iid, shingles(item["text"])))
        require(set().union(*(set(i["memberships"]) for i in items)) == set(threads), "empty thread")
        projected.append({"id": lid, "items": [{key: i[key] for key in ("id", "text", "modality")} for i in items]})
        for first, second in itertools.combinations(sorted(items, key=lambda i: i["id"]), 2):
            a, b = set(first["memberships"]), set(second["memberships"])
            relation = ("uncertain" if not a or not b else "same" if a & b else
                        "related" if any(frozenset((x, y)) in related for x in a for y in b) else "unrelated")
            gold.append({"id": first["id"] + "--" + second["id"], "library": lid, "split": split,
                         "first": first["id"], "second": second["id"], "relation": relation})
    require(len({r["id"] for r in gold}) == len(gold), "pair ID collision")
    for (split_a, id_a, a), (split_b, id_b, b) in itertools.combinations(indexed, 2):
        if split_a != split_b:
            similarity = len(a & b) / len(a | b) if a | b else 1
            require(similarity < policy["nearDuplicateJaccard"], f"cross-split near duplicate: {id_a}, {id_b}")
    if release:
        require(counts == policy["requiredSplits"], "split size differs from contract")
        require(all(n == policy["librariesPerStoryFamily"] for n in family_counts.values()), "wrong story family sizes")
        # This structural check is not a substitute for a review/adjudication freeze.
    summary = {"libraries": len(libraries), "sources": len(item_ids), "pairs": len(gold),
               "relations": {label: sum(r["relation"] == label for r in gold)
                             for label in ("same", "related", "unrelated", "uncertain")},
               "splits": counts, "qualificationReady": False}
    return {"schemaVersion": 1, "libraries": projected}, {"schemaVersion": 1, "pairs": gold}, summary


def bindings():
    return {str(path.relative_to(ROOT)): digest(path) for path in SOURCES}


def verify(run):
    manifest = read(run / "complete.json")
    require(manifest["sources"] == bindings(), "preparation sources changed; use a new attempt")
    require(set(manifest["artifacts"]) == {"pilot-inputs.json", "pilot-gold.json", "pilot-audit.json"}, "unexpected artifact list")
    for name, expected in manifest["artifacts"].items():
        require(digest(run / name) == expected, f"artifact changed: {name}")
    require(manifest["trainingStarted"] is False and manifest["stopForReview"] is True, "invalid checkpoint state")
    return manifest


def prepare(run):
    if (run / "complete.json").exists():
        return verify(run)
    policy = read(DATA / "contract.json")
    free = shutil.disk_usage(ROOT).free
    require(free - 1024 ** 2 >= policy["freeSpaceReserveGiB"] * GIB, "free-space reserve would be violated")
    current_bytes = sum(p.stat().st_size for p in DATA.rglob("*") if p.is_file())
    require(current_bytes + 1024 ** 2 <= policy["newStorageCapGiB"] * GIB, "preparation storage cap exceeded")
    source_hashes = bindings()
    inputs, labels, summary = validate_corpus(read(DATA / "pilot.json"), policy)
    for name, value in (("pilot-inputs.json", inputs), ("pilot-gold.json", labels), ("pilot-audit.json", summary)):
        publish(run / name, value)
    require(source_hashes == bindings(), "source changed while preparing")
    manifest = {"checkpoint": "P0", "sources": source_hashes,
                "artifacts": {name: digest(run / name) for name in ("pilot-inputs.json", "pilot-gold.json", "pilot-audit.json")},
                "trainingStarted": False, "benchmarkComplete": False, "stopForReview": True,
                "next": "P1: author, review and freeze full split-separated benchmark"}
    publish(run / "complete.json", manifest)
    return verify(run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify"))
    parser.add_argument("--run", type=Path, default=DATA / "runs/preparation-01")
    args = parser.parse_args()
    run = args.run.resolve()
    require(run.is_relative_to((DATA / "runs").resolve()) and run != (DATA / "runs").resolve(),
            "run must be a dedicated MatcherValidation/runs subdirectory")
    print(json.dumps(prepare(run) if args.command == "prepare" else verify(run), indent=2))


if __name__ == "__main__":
    main()
