#!/usr/bin/env python3
"""Pin a separately scored BANKING77 diagnostic; no dataset code or Git execution."""
import argparse
import csv
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path
import urllib.request


REVISION = "57ec275d8078af65b7731c2a98be812d844a6d6b"
URL = f"https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/{REVISION}/banking_data/test.csv"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
SOURCE_SHA256 = "d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d"


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, help="optional offline copy of the pinned test.csv")
    p.add_argument("--output", type=Path, default=Path("Evaluation/Organization/public"))
    args = p.parse_args()
    targets = [args.output / n for n in ("inputs.json", "labels.json", "provenance.json", "freeze.json")]
    if any(p.exists() for p in targets): raise ValueError("refusing to overwrite existing dataset artifacts")
    if args.source:
        data = args.source.read_bytes()
    else:
        with urllib.request.urlopen(URL, timeout=60) as response:
            data = response.read(4_000_001)
        if len(data) > 4_000_000: raise ValueError("unexpectedly large public source")
    if sha(data) != SOURCE_SHA256: raise ValueError("public source does not match the pinned release hash")
    grouped = defaultdict(list)
    for row, value in enumerate(csv.DictReader(io.StringIO(data.decode("utf-8-sig")))):
        if set(value) != {"text", "category"} or not value["text"].strip(): raise ValueError("invalid source schema")
        grouped[value["category"]].append((row, value["text"]))
    if len(grouped) != 77: raise ValueError("expected 77 source categories")
    categories = sorted(grouped, key=lambda c: sha(("remember-public-1729:" + c).encode()))[:20]
    items, membership, attribution = [], {}, []
    for category in categories:
        seen = set()
        rows = []
        for row, text in sorted(grouped[category], key=lambda r: sha(("1729:" + r[1]).encode())):
            normalized = " ".join(text.casefold().split())
            if normalized not in seen:
                seen.add(normalized)
                rows.append((row, text))
            if len(rows) == 10: break
        if len(rows) != 10: raise ValueError("category has insufficient unique examples")
        for row, text in rows:
            item = f"p-{len(items) + 1:03d}"
            items.append({"id": item, "text": text, "kind": "text", "timestamp": 1_800_000_000 + len(items)})
            membership[item] = [category]
            attribution.append({"itemID": item, "sourceRow": row, "category": category})
    inputs = {"schemaVersion": 1, "libraries": [{"id": "public-banking77", "split": "public", "slice": "public", "items": items}]}
    labels = {"schemaVersion": 1, "libraries": [{"id": "public-banking77", "memberships": membership,
                "ambiguous": [], "relationships": []}]}
    provenance = {"source": URL, "revision": REVISION, "sourceSHA256": sha(data), "license": "CC-BY-4.0",
                  "licenseURL": LICENSE, "authors": "Iñigo Casanueva, Tadas Temčinas, Daniela Gerz, Matthew Henderson, Ivan Vulić / PolyAI",
                  "citation": "Efficient Intent Detection with Dual Sentence Encoders, NLP for ConvAI 2020",
                  "selection": "SHA256 seed1729 selects20categories,10 unique test examples each; no relabeling",
                  "adaptation": "200-example subset; original text unchanged, opaque IDs added; not a standard BANKING77 score",
                  "rows": attribution}
    args.output.mkdir(parents=True, exist_ok=True)
    for path, value in zip(targets, [inputs, labels, provenance]):
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    freeze = {"schemaVersion": 1, "inputsSHA256": sha(targets[0].read_bytes()), "labelsSHA256": sha(targets[1].read_bytes()),
              "provenanceSHA256": sha(targets[2].read_bytes()), "claim": "original public intent labels, not project-identity truth"}
    targets[3].write_text(json.dumps(freeze, indent=2) + "\n")
    print(json.dumps({"items": len(items), "categories": len(categories), "inputs": str(targets[0]), "sourceSHA256": sha(data)}))


if __name__ == "__main__": main()
