#!/usr/bin/env python3
"""Post-hoc audio-only WER diagnostic; separate from frozen organization scores."""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re


SEMANTICS = {
    "status": "post-hoc; not preregistered with the organization benchmark",
    "normalization": "Casefold, then Unicode alphanumeric word runs ([^\\W_]+). Punctuation, apostrophes, hyphens and underscores separate tokens. Preserve accents and numeric forms; no stemming, number expansion or language-specific substitutions.",
    "metric": "Unit-cost word Levenshtein edit distance divided by reference word count; WER can exceed 1. Corpus WER pools edits and reference words; macro WER averages audio-item WER.",
    "failurePolicy": "Missing or non-completed run/extraction uses an empty hypothesis, contributing every reference word as a deletion. Completed extraction with empty text is also scored. No reference transcript fallback.",
    "scope": "Every audio item in the frozen inputs, one embedding/chronological/extracted run per library. Other media excluded. Reference text is the synthetic spoken-script diagnostic control.",
    "interpretation": "Transcript similarity diagnostic, not semantic correctness or organization accuracy. Device transcription uses Locale.current, not a per-file language. No quality threshold is asserted.",
}


def read(path):
    path = Path(path)
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def words(text):
    return re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE)


def distance(reference, hypothesis):
    previous = list(range(len(hypothesis) + 1))
    for i, expected in enumerate(reference, 1):
        current = [i]
        for j, observed in enumerate(hypothesis, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1,
                               previous[j - 1] + (expected != observed)))
        previous = current
    return previous[-1]


def verify_binding(inputs_path, corpus_freeze_path, results_path):
    inputs, frozen, results = read(inputs_path), read(corpus_freeze_path), read(results_path)
    require(inputs.get("schemaVersion") == results.get("schemaVersion") == frozen.get("schemaVersion") == 1,
            "unsupported schema")
    manifest = results.get("manifest", {})
    require(frozen.get("inputsSHA256") == sha(inputs_path) == manifest.get("inputsSHA256"),
            "frozen input/result hash mismatch")
    require(manifest.get("freezeSHA256") == sha(corpus_freeze_path), "result corpus freeze mismatch")
    require(manifest.get("mediaMode") == "extracted", "actual extracted results required")
    return inputs, results


def score(inputs, results):
    libraries = inputs["libraries"]
    require(len({l["id"] for l in libraries}) == len(libraries), "duplicate library")
    expected = {l["id"] + "-embedding-chronological-0" for l in libraries}
    requested = results["manifest"].get("expectedRunIDs", [])
    require(len(requested) == len(expected) and set(requested) == expected,
            "diagnostic requires exactly one embedding chronological run requested per library")
    runs = {}
    for run in results["runs"]:
        run_id = run["runID"]
        require(run_id in expected and run_id not in runs, "duplicate or unexpected run")
        require(run_id == run["libraryID"] + "-embedding-chronological-0"
                and run.get("mode") == "embedding" and run.get("order") == "chronological"
                and run.get("repeat") == 0 and run.get("mediaMode") == "extracted", "invalid run identity/mode")
        runs[run_id] = run
    rows, seen = [], set()
    for library in libraries:
        run_id = library["id"] + "-embedding-chronological-0"
        run = runs.get(run_id)
        extractions = {}
        for record in (run or {}).get("extractions", []):
            require(record["itemID"] not in extractions, "duplicate extraction")
            require(record["itemID"] in {item["id"] for item in library["items"]}, "unexpected extraction item")
            extractions[record["itemID"]] = record
        for item in library["items"]:
            if item["kind"] != "audio":
                continue
            require(item["id"] not in seen, "duplicate audio item")
            seen.add(item["id"])
            require(isinstance(item.get("referenceText"), str), "audio reference text required")
            reference = words(item["referenceText"])
            require(bool(reference), "audio reference must contain words")
            record = extractions.get(item["id"])
            run_status = run.get("status", "missing") if run else "missing"
            extraction_status = record.get("status", "missing") if record else "missing"
            usable = run_status == extraction_status == "completed"
            observed = record.get("text") if usable else ""
            require(isinstance(observed, str), "completed extraction text must be a string")
            hypothesis = words(observed)
            edits = distance(reference, hypothesis)
            rows.append({"itemID": item["id"], "libraryID": library["id"], "split": library["split"],
                         "runID": run_id, "runStatus": run_status, "extractionStatus": extraction_status,
                         "completedExtraction": usable, "nonemptyHypothesis": bool(hypothesis),
                         "referenceWords": len(reference), "hypothesisWords": len(hypothesis),
                         "wordEdits": edits, "wordErrorRate": edits / len(reference)})
    require(bool(rows), "no audio items")
    reference_total = sum(row["referenceWords"] for row in rows)
    edits_total = sum(row["wordEdits"] for row in rows)
    return {"schemaVersion": 1, "semantics": SEMANTICS, "items": rows,
            "coverage": {"expectedAudioItems": len(rows),
                         "completedExtractions": sum(r["completedExtraction"] for r in rows),
                         "nonemptyHypotheses": sum(r["nonemptyHypothesis"] for r in rows),
                         "extractionStatuses": dict(Counter(r["extractionStatus"] for r in rows)),
                         "missingOrFailedIDs": [r["itemID"] for r in rows if not r["completedExtraction"]]},
            "aggregate": {"referenceWords": reference_total, "wordEdits": edits_total,
                          "corpusWordErrorRate": edits_total / reference_total,
                          "macroItemWordErrorRate": sum(r["wordErrorRate"] for r in rows) / len(rows)}}


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["freeze", "score"])
    for name in ["inputs", "corpus-freeze", "results", "diagnostic-freeze"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    inputs, results = verify_binding(args.inputs, args.corpus_freeze, args.results)
    binding = {"schemaVersion": 1, "inputsSHA256": sha(args.inputs),
               "corpusFreezeSHA256": sha(args.corpus_freeze), "resultsSHA256": sha(args.results),
               "scorerSHA256": sha(__file__), "semantics": SEMANTICS}
    if args.command == "freeze":
        require(args.output is None, "freeze writes only --diagnostic-freeze")
        write_new(args.diagnostic_freeze, binding)
    else:
        require(args.output is not None, "score requires --output")
        require(read(args.diagnostic_freeze) == binding, "diagnostic semantics/code/input/result changed after freeze")
        result = score(inputs, results)
        result["binding"] = {**binding, "diagnosticFreezeSHA256": sha(args.diagnostic_freeze)}
        write_new(args.output, result)


if __name__ == "__main__":
    main()
