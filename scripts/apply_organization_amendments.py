#!/usr/bin/env python3
"""Materialize a pre-prediction corpus revision without replacing draft or review evidence."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, default=Path("Evaluation/Organization/inputs.json"))
    p.add_argument("--amendments", type=Path, default=Path("Evaluation/Organization/amendments.json"))
    p.add_argument("--output", type=Path, default=Path("Evaluation/Organization/inputs-reviewed.json"))
    args = p.parse_args()
    if args.output.exists(): raise ValueError("refusing to overwrite corpus revision")
    amendment = json.loads(args.amendments.read_text())
    if amendment["baseInputsSHA256"] != hashlib.sha256(args.base.read_bytes()).hexdigest():
        raise ValueError("amendments reference a different base")
    raw = json.loads(args.base.read_text())
    by_id = {item["id"]: (library["id"], item) for library in raw["libraries"] for item in library["items"]}
    seen = set()
    for replacement in amendment["replacements"]:
        item_id = replacement["id"]
        if item_id in seen or item_id not in by_id: raise ValueError("duplicate/unknown amended item")
        seen.add(item_id)
        library, item = by_id[item_id]
        if library != replacement["libraryID"]: raise ValueError("amended library mismatch")
        item["text"] = replacement["text"]
    if len(seen) != 24: raise ValueError("expected24predeclared amendments")
    args.output.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"output": str(args.output), "inputsSHA256": hashlib.sha256(args.output.read_bytes()).hexdigest(), "replacements": len(seen)}))


if __name__ == "__main__": main()
