#!/usr/bin/env python3
"""Registered historical runtime controls. No benchmark/model/policy changes."""
import argparse
from collections import Counter
import math
from pathlib import Path
import re
import sys
import time

import common as c
import preflight

FOLDER = c.WORK / "runs/runtime-qualification-01"
PUBLIC = c.WORK / "runtime-qualification"
THRESHOLDS = (0.9804276486193665, 0.99, 0.995)
BOUNDS = {"savedFeatureDelta": 1e-12, "freshFeatureDelta": 1e-4,
          "directionalDelta": 1e-5, "combinedDelta": 1e-5,
          "minimumCosine": 0.99999, "relativeNormDelta": 0.001}


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def select(rows, original_ids, per_side=6):
    """Selection uses historical scores only; no current outputs or labels."""
    c.require(len({r["id"] for r in rows}) == len(rows), "duplicate historical pair ID")
    for row in rows:
        c.require(re.fullmatch(r"[A-Za-z0-9_-]+", row["id"]) is not None, "unsafe pair ID")
        c.require(finite(row["score"]) and 0 <= row["score"] <= 1, "invalid historical score")
    by_id = {r["id"]: r for r in rows}
    reasons = {}
    def retain(row, reason):
        reasons.setdefault(row["id"], []).append(reason)
    for key in original_ids:
        c.require(key in by_id, "missing original control")
        retain(by_id[key], "original-control")
    for library in sorted({r["library"] for r in rows}):
        group = [r for r in rows if r["library"] == library]
        for label, target in (("low", 0), ("middle", 0.5), ("high", 1)):
            retain(min(group, key=lambda r: (abs(r["score"]-target), r["id"])), f"library-{label}")
    for threshold in THRESHOLDS:
        for side in ("below", "at-or-above"):
            group = [r for r in rows if (r["score"] < threshold) == (side == "below")]
            c.require(len(group) >= per_side, f"insufficient controls {threshold}/{side}")
            for row in sorted(group, key=lambda r: (abs(r["score"]-threshold), r["id"]))[:per_side]:
                retain(row, f"threshold-{threshold}-{side}")
    return [{**{key: by_id[identifier][key] for key in ("id", "first", "second", "library", "score")},
             "reasons": reasons[identifier]} for identifier in sorted(reasons)]


def valid_vector(record, source_id, text):
    c.require(record["id"] == source_id and record["textSHA256"] == c.text_hash(text), "embedding input identity mismatch")
    c.require(record["status"] == "ok" and record["space"] == preflight.SPACE, "wrong embedding status/space")
    for channel in ("contextual", "sentence"):
        values = record[channel]
        c.require(len(values) == 512 and all(finite(v) for v in values), "invalid embedding dimension/value")
        c.require(sum(v*v for v in values) > 0, "zero embedding")


def valid_neural(record, pair_id, weights):
    c.require(record["id"] == pair_id and record["weightsSHA256"] == weights, "neural identity mismatch")
    values = record["directions"]
    c.require(len(values) == 2 and all(finite(v) and 0 <= v <= 1 for v in values), "invalid directional scores")
    c.require(finite(record["score"]) and abs(record["score"] - sum(values)/2) <= 1e-12, "invalid averaged score")


def prepare():
    c.boundary()
    # Also verifies the unchanged historical preflight runtime, weights and transforms.
    _, _, _, _, original, parent = preflight.inputs()
    old_report = c.P2 / "evaluation/seed-29.json"
    old_inputs = c.ROOT / "Evaluation/MatcherValidation/releases/v1/inputs-evaluation.json"
    controls = select(c.read(old_report)["predictions"]["hybrid"], [r["id"] for r in original])
    document = c.read(old_inputs)
    items = {item["id"]: (library["id"], item["text"])
             for library in document["libraries"] for item in library["items"]}
    source_ids = sorted({r[side] for r in controls for side in ("first", "second")})
    sources = {}
    paths = [old_report, old_inputs, PUBLIC / "PROTOCOL.md", Path(__file__),
             Path(__file__).with_name("test_qualification.py"), FOLDER.parent / "preflight/binding.json"]
    weights = c.read(c.P2 / "hybrid-29.json")["final"]["SHA256"]
    for key in source_ids:
        c.require(re.fullmatch(r"[A-Za-z0-9_-]+", key) is not None and key in items, "missing/unsafe source")
        library, text = items[key]
        old = c.P2 / f"embeddings/{key}.json"
        valid_vector(c.read(old), key, text)
        sources[key] = {"text": text, "textSHA256": c.text_hash(text), "library": library}
        paths.append(old)
    for pair in controls:
        c.require(all(sources[pair[side]]["library"] == pair["library"] for side in ("first", "second")), "pair library mismatch")
        old = c.P2 / f"predictions/seed-29-final/evaluation/{pair['id']}.json"
        valid_neural(c.read(old), pair["id"], weights)
        paths.append(old)
    manifest = {"schemaVersion": 1, "preflightBindingSHA256": parent, "weightsSHA256": weights,
                "thresholds": list(THRESHOLDS), "bounds": BOUNDS,
                "pairs": controls, "sources": sources, "benchmarkInputs": False,
                "hashes": {str(path): c.digest(path) for path in sorted(set(paths))}}
    c.publish(FOLDER / "manifest.json", manifest)
    c.publish(PUBLIC / "selection.json", {"pairs": controls, "sources": len(sources),
              "libraries": sorted({r["library"] for r in controls}), "manifestSHA256": c.digest(FOLDER / "manifest.json")})
    c.log(phase="registered", pairs=len(controls), sources=len(sources), libraries=len({r["library"] for r in controls}))
    return manifest


def verify():
    c.verify_saved_preflight()
    c.require(FOLDER.resolve().is_relative_to(c.WORK.resolve()), "qualification directory escapes scope")
    path = FOLDER / "manifest.json"
    manifest = c.read(path)
    c.require(manifest["thresholds"] == list(THRESHOLDS) and manifest["bounds"] == BOUNDS, "criteria changed")
    c.require(manifest["preflightBindingSHA256"] == c.digest(FOLDER.parent / "preflight/binding.json"), "parent binding changed")
    for name, expected in manifest["hashes"].items():
        c.require(c.digest(name) == expected, f"qualification input/code changed: {name}")
    binding = c.digest(path)
    sources = manifest["sources"]
    expected = {"embeddings": {f"{s['textSHA256']}.json": key for key, s in sources.items()},
                "neural": {f"{p['id']}.json": p["id"] for p in manifest["pairs"]}}
    c.require(len(expected["embeddings"]) == len(sources), "duplicate source text requires explicit handling")
    completed = {}
    for kind, names in expected.items():
        paths = list((FOLDER / kind).glob("*"))
        c.require(all(p.name in names and p.is_file() and not p.is_symlink()
                      and p.resolve().is_relative_to(FOLDER.resolve()) for p in paths), "unexpected or escaped unit")
        for unit_path in paths:
            value = c.read_unit(unit_path, binding)
            key = names[unit_path.name]
            if kind == "embeddings":
                valid_vector(value, key, sources[key]["text"])
            else:
                valid_neural(value, key, manifest["weightsSHA256"])
        completed[kind] = len(paths)
    return manifest, binding, completed


def check_rows(vectors, pairs):
    failures = []
    for row in vectors:
        for channel, values in row["channels"].items():
            for metric, limit, lower in (("cosine", BOUNDS["minimumCosine"], True),
                                          ("relativeNormDelta", BOUNDS["relativeNormDelta"], False)):
                value = values[metric]
                if not finite(value) or (value < limit if lower else value > limit):
                    failures.append({"id": row["id"], "channel": channel, "metric": metric, "value": value, "limit": limit})
    for row in pairs:
        for metric in ("savedFeatureDelta", "freshFeatureDelta", "directionalDelta", "combinedDelta"):
            value = row[metric]
            if not finite(value) or value > BOUNDS[metric]:
                failures.append({"id": row["id"], "metric": metric, "value": value, "limit": BOUNDS[metric]})
        for threshold in THRESHOLDS:
            if (row["currentScore"] >= threshold) != (row["historicalScore"] >= threshold):
                failures.append({"id": row["id"], "metric": "threshold-decision", "threshold": threshold})
    return failures


def analyze(manifest, binding):
    import numpy as np
    Features, _, _ = preflight.legacy()
    sources = manifest["sources"]
    fresh, saved, vectors = {}, {}, []
    for key, source in sources.items():
        fresh[key] = c.read_unit(FOLDER / f"embeddings/{source['textSHA256']}.json", binding)
        saved[key] = c.read(c.P2 / f"embeddings/{key}.json")
        channels = {}
        for channel in ("contextual", "sentence"):
            a, b = np.asarray(fresh[key][channel]), np.asarray(saved[key][channel])
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            channels[channel] = {"maxComponentDelta": float(np.max(np.abs(a-b))),
                                 "cosine": float(a @ b / (na * nb)), "relativeNormDelta": float(abs(na-nb)/nb)}
        vectors.append({"id": key, "library": source["library"], "channels": channels})
    texts = {key: value["text"] for key, value in sources.items()}
    current_features, old_features = Features(texts, fresh), Features(texts, saved)
    reference_features = {r["id"]: r["features"] for r in c.read(c.P2 / "features/evaluation.json")["rows"]}
    pairs = []
    for pair in manifest["pairs"]:
        key = pair["id"]
        now = c.read_unit(FOLDER / f"neural/{key}.json", binding)
        old = c.read(c.P2 / f"predictions/seed-29-final/evaluation/{key}.json")
        a, b = old_features.values(pair["first"], pair["second"]), current_features.values(pair["first"], pair["second"])
        score = current_features.scores(b, {"29": now["score"]})["hybrid"]["29"]
        pairs.append({"id": key, "library": pair["library"], "reasons": pair["reasons"],
                      "savedFeatureDelta": float(np.max(np.abs(np.asarray(a) - reference_features[key]))),
                      "freshFeatureDelta": float(np.max(np.abs(np.asarray(a)-b))),
                      "directionalDelta": max(abs(x-y) for x, y in zip(now["directions"], old["directions"])),
                      "combinedDelta": abs(score-pair["score"]), "currentScore": score, "historicalScore": pair["score"]})
    failures = check_rows(vectors, pairs)
    thresholds = [{"threshold": t, "changes": sum((r["currentScore"] >= t) != (r["historicalScore"] >= t) for r in pairs),
                   "historicalAbove": sum(r["historicalScore"] >= t for r in pairs),
                   "closestBelow": min(t-r["historicalScore"] for r in pairs if r["historicalScore"] < t),
                   "closestAbove": min(r["historicalScore"]-t for r in pairs if r["historicalScore"] >= t)} for t in THRESHOLDS]
    report = {"status": "passed" if not failures else "failed", "offlineComparisonCompatible": not failures,
              "priorVectorIdentityPreflightPassed": False, "appOrDeviceQualified": False,
              "benchmarkQualityMeasured": False, "manifestSHA256": binding,
              "pairs": pairs, "embeddings": vectors, "failures": failures, "thresholds": thresholds,
              "pairsByLibrary": dict(sorted(Counter(p["library"] for p in pairs).items())),
              "maximumCombinedDelta": max(p["combinedDelta"] for p in pairs),
              "maximumDirectionalDelta": max(p["directionalDelta"] for p in pairs),
              "maximumFeatureDelta": max(p["freshFeatureDelta"] for p in pairs),
              "maximumEmbeddingComponentDelta": max(v["maxComponentDelta"] for r in vectors for v in r["channels"].values()),
              "minimumEmbeddingCosine": min(v["cosine"] for r in vectors for v in r["channels"].values()),
              "maximumRelativeNormDelta": max(v["relativeNormDelta"] for r in vectors for v in r["channels"].values())}
    c.publish(PUBLIC / "result.json", report)
    return report


def run(max_units=None):
    manifest, binding, completed = verify()
    # Exact-verifies package/runtime versions too; no prior fresh vectors are reused.
    _, Neural, _, _, _, _ = preflight.inputs()
    made = 0
    for key, source in sorted(manifest["sources"].items()):
        c.boundary()
        path = FOLDER / f"embeddings/{source['textSHA256']}.json"
        if not path.exists():
            c.unit(path, preflight.embedding(key, source["text"]), binding)
            made += 1
            completed["embeddings"] += 1
            c.log(phase="qualification-embeddings", completed=completed["embeddings"], total=len(manifest["sources"]))
        if max_units and made >= max_units:
            raise c.Paused("qualification unit limit")
    missing = [p for p in manifest["pairs"] if not (FOLDER / f"neural/{p['id']}.json").exists()]
    if missing:
        c.boundary()
        with Neural("29") as model:
            for start in range(0, len(missing), 8):
                c.boundary()
                batch = missing[start:start + (min(8, max_units-made) if max_units else 8)]
                values = model.predict([(manifest["sources"][p["first"]]["text"], manifest["sources"][p["second"]]["text"]) for p in batch])
                for pair, value in zip(batch, values):
                    c.unit(FOLDER / f"neural/{pair['id']}.json", {"id": pair["id"], **value}, binding)
                    made += 1
                    completed["neural"] += 1
                c.log(phase="qualification-neural", completed=completed["neural"], total=len(manifest["pairs"]))
                if max_units and made >= max_units:
                    raise c.Paused("qualification unit limit")
    c.boundary()
    manifest, binding, completed = verify()
    c.require(completed == {"embeddings": len(manifest["sources"]), "neural": len(manifest["pairs"])}, "incomplete qualification")
    report = analyze(manifest, binding)
    c.log(status=report["status"], failures=report["failures"], thresholds=report["thresholds"],
          maximumCombinedDelta=report["maximumCombinedDelta"], pairs=len(report["pairs"]))
    return 0 if report["offlineComparisonCompatible"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run", "verify"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-units", type=int)
    args = parser.parse_args()
    c.require(args.max_units is None or args.max_units > 0, "max-units must be positive")
    try:
        # Hold the shared lock; verify this new run before clearing a pause marker.
        with c.worker(resume=False):
            if args.command == "prepare":
                c.require(not args.resume, "prepare does not clear a pause request")
                prepare()
            else:
                manifest, binding, completed = verify()
                if args.command == "verify":
                    c.log(verified=True, completed=completed, manifestSHA256=binding)
                else:
                    preflight.inputs()  # Verify active runtime before allowing resume.
                    marker = c.WORK / "pause.request.json"
                    if args.resume and marker.exists():
                        marker.rename(FOLDER / f"pause-resumed-{time.time_ns()}.json")
                    return run(args.max_units)
    except c.Paused as error:
        c.log(status="paused", reason=str(error), workerStopped=True)
    except Exception as error:
        c.pf1.atomic(c.WORK / f"runs/failures/{time.time_ns()}.json",
                     {"type": type(error).__name__, "message": str(error), "phase": "runtime-qualification"})
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
