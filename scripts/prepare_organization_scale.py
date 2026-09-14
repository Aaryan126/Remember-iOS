#!/usr/bin/env python3
"""Create bounded performance-only libraries from development sources, not new semantic evidence."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", type=Path, default=Path("Evaluation/Organization/inputs-reviewed.json"))
    p.add_argument("--output", type=Path, default=Path("Evaluation/Organization/scale"))
    args = p.parse_args()
    if args.output.exists(): raise ValueError("refusing to overwrite scale release")
    original = json.loads(args.inputs.read_text())
    source = [item for library in original["libraries"] if library["split"] == "development" and library["slice"] == "english"
              for item in library["items"]]
    if not source: raise ValueError("no development sources")
    libraries = []
    for count in [100, 500, 1000]:
        items = [{"id": f"s{count}-{i:04d}", "text": source[i % len(source)]["text"], "kind": "text", "timestamp": 1_800_000_000 + i}
                 for i in range(count)]
        libraries.append({"id": f"scale-{count}", "split": "development", "slice": "scale", "items": items})
    args.output.mkdir(parents=True)
    path = args.output / "inputs.json"
    path.write_text(json.dumps({"schemaVersion": 1, "libraries": libraries}, indent=2, ensure_ascii=False) + "\n")
    (args.output / "freeze.json").write_text(json.dumps({"schemaVersion": 1,
        "inputsSHA256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "sourceSHA256": hashlib.sha256(args.inputs.read_bytes()).hexdigest(),
        "claim": "performance-only repeated development documents; no semantic generalization claim",
        "counts": [100, 500, 1000], "scenarioTimeoutSeconds": 600}, indent=2) + "\n")
    print(path)


if __name__ == "__main__": main()
