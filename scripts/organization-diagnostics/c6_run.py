#!/usr/bin/env python3
"""Bounded C6 inference and evaluation; never starts training or production work."""
import argparse
from contextlib import contextmanager
from pathlib import Path
import time

import c2_common as c
import c5_run
from c3_policy import accepted
from c5_metrics import evaluate as evaluate_predictions, validate_prediction

RUN = c.DATA / "runs/c6-01"
CURATED = c.DATA / "c6"
SCORERS = ("baseline", "17", "29", "41")
CANDIDATES = (*SCORERS, "scope-rules", *(s + "-gated" for s in SCORERS))


def pause():
    marker = RUN / "control/pause-requested.json"
    if not marker.exists():
        c.publish(marker, {"requestedAtUnix": time.time()})
    return {"pauseRequested": True, "safeToClose": False}


@contextmanager
def worker(resume=False):
    with c.worker():
        marker = RUN / "control/pause-requested.json"
        if resume and marker.exists():
            c.publish(RUN / f"resumptions/{time.time_ns()}.json", {"pauseRequestSHA256": c.digest(marker)})
            marker.unlink()
        yield


def boundary(phase):
    c.space(planned=4 * 1024**2)
    if c._pause_signal or (RUN / "control/pause-requested.json").exists() or (c.RUN / "control/pause-requested.json").exists():
        c.publish(RUN / f"pauses/{time.time_ns()}.json", {"phase": phase, "savedBoundary": True})
        raise c.Paused(phase)


def check_files(files, base):
    for name, sha in files.items():
        path = (base / name).resolve()
        c.require(path.is_relative_to(base) and c.digest(path) == sha, "C6 binding changed: " + name)


def packets():
    return c.read(c5_run.RUN / "release/inputs.json")["packets"]


def catalogue():
    texts, pairs = {}, {}
    for packet in packets():
        lookup = {s["id"]: s["text"] for s in packet["sources"]}
        a, b = (lookup[key] for key in packet["pair"])
        for text in (a, b):
            texts[c.text_sha(text)] = text
        first, second = sorted((c.text_sha(a), c.text_sha(b)))
        pairs[first + "--" + second] = {"first": first, "second": second}
    return {"texts": dict(sorted(texts.items())), "pairs": dict(sorted(pairs.items()))}


def freeze():
    if (RUN / "manifest.json").exists():
        verify_manifest()
        return {"frozen": True}
    c5_run.verify()
    inherited = c.verify_bindings()
    review = c.read(RUN / "review-complete.json")
    check_files(review["files"], RUN)
    c.require(review["expandedPackets"] == 160 and review["uniqueContextsPerReviewer"] == 112, "Incomplete semantic review")
    c.publish(RUN / "catalogue.json", catalogue())
    root = Path(__file__).parent
    files = list(root.glob("c6_*.py")) + list(root.glob("test_c6*.py"))
    files += [c.DATA / "C6_PROTOCOL.md", c.DATA / "C6_REVIEW_CONTRACT.md", CURATED / "SCOPE_PROTOTYPE.md", c5_run.CURATED / "complete.json",
              c5_run.RUN / "release/inputs.json", c5_run.RUN / "release/gold.json", RUN / "catalogue.json", RUN / "review-complete.json"]
    files += [RUN / name for name in review["files"]]
    files += list((RUN / "review-inputs").glob("*.json"))
    files += [c.ROOT / name for name in inherited["sources"]]
    files += [root / name for name in ("c3_policy.py", "c5_data.py", "c5_metrics.py", "c5_run.py")]
    c.publish(RUN / "manifest.json", {"runtime": c.runtime(), "thresholds": inherited["thresholds"], "candidates": list(CANDIDATES),
        "sources": {str(p.relative_to(c.ROOT)): c.digest(p) for p in sorted(set(files))}, "external": inherited["external"],
        "resource": c.space(), "trainingAllowed": False, "expectedPredictions": 1440})
    return {"frozen": True, "texts": len(catalogue()["texts"]), "pairs": len(catalogue()["pairs"])}


def verify_manifest():
    manifest = c.read(RUN / "manifest.json")
    c.require(manifest["runtime"] == c.runtime(), "C6 runtime changed")
    check_files(manifest["sources"], c.ROOT)
    check_files(manifest["external"], c.WORKSPACE)
    return manifest


def legacy_prediction(packet, score, scorer, thresholds):
    verdict = "same_project" if accepted(score, scorer, thresholds) else "abstain"
    return {"queryID": packet["queryID"], "verdict": verdict, "evidence": [] if verdict == "abstain" else
            [{"sourceID": source["id"], "quote": source["text"]} for source in packet["sources"] if source["id"] in packet["pair"]]}


def assemble(scores, thresholds):
    from c6_scope import verify_packet
    output = {name: [] for name in CANDIDATES}
    for packet in packets():
        scope = verify_packet(packet)
        validate_prediction(packet, scope)
        output["scope-rules"].append(scope)
        texts = {s["id"]: s["text"] for s in packet["sources"]}
        score = scores[c.pair_key(*(texts[key] for key in packet["pair"]))]
        for scorer in SCORERS:
            legacy = legacy_prediction(packet, score, scorer, thresholds)
            validate_prediction(packet, legacy)
            output[scorer].append(legacy)
            output[scorer + "-gated"].append(scope if scope["verdict"] == "separate_projects" else legacy)
    return output


def parity_inputs():
    from c2_run import parity_inputs as original
    from c2_models import Features
    import numpy as np
    texts, embeddings, pairs = original()
    feature = Features(texts, embeddings)
    values = {p["id"]: feature.values(p["first"], p["second"]) for p in pairs}
    reference = {r["id"]: r["features"] for r in c.read(c.P2 / "features/evaluation.json")["rows"]}
    delta = max(float(np.max(np.abs(np.asarray(value) - reference[key]))) for key, value in values.items())
    c.require(delta <= 1e-12, "Reference feature regression")
    return texts, embeddings, pairs, feature, values, delta


def score(max_units=None):
    manifest = verify_manifest()
    from c2_models import Features, Neural
    from c6_probe import embedding_probe
    import numpy as np
    data = c.read(RUN / "catalogue.json")
    ref_texts, ref_emb, ref_pairs, ref_feature, ref_values, feature_delta = parity_inputs()
    if not (RUN / "native-parity.json").exists() or any(not (RUN / f"embeddings/{key}.json").exists() for key in data["texts"]):
        with embedding_probe(RUN) as query:
            if not (RUN / "native-parity.json").exists():
                comparisons = []
                for key in sorted(ref_texts)[:2]:
                    boundary("native-parity")
                    current = query(key, ref_texts[key])
                    delta = max(float(np.max(np.abs(np.asarray(current[k]) - ref_emb[key][k]))) for k in ("contextual", "sentence"))
                    c.require(delta <= 1e-6, "Native embedding parity changed")
                    c.unit(RUN / f"native-parity/{key}.json", current)
                    comparisons.append({"textSHA256": key, "maximumDelta": delta})
                c.publish(RUN / "native-parity.json", {"passed": True, "comparisons": comparisons})
            saved = 0
            for key, text in data["texts"].items():
                boundary("embedding:" + key)
                path = RUN / f"embeddings/{key}.json"
                if path.exists():
                    c.read_unit(path)
                    continue
                c.unit(path, query(key, text))
                saved += 1
                if max_units and saved >= max_units:
                    c.publish(RUN / f"pauses/{time.time_ns()}-bounded.json", {"phase": "embedding", "savedUnits": saved})
                    raise c.Paused("bounded-embedding-stop")
    features = Features(data["texts"], {key: c.read_unit(RUN / f"embeddings/{key}.json") for key in data["texts"]})
    values = {key: features.values(p["first"], p["second"]) for key, p in data["pairs"].items()}
    c.require(all(all(v is not None and np.isfinite(v) for v in row) for row in values.values()), "Incomplete model features")
    c.publish(RUN / "features.json", values)
    for seed in SCORERS[1:]:
        boundary("model-load:" + seed)
        missing_ref = [p for p in ref_pairs if not (RUN / f"parity/{seed}/{p['id']}.json").exists()]
        missing = [key for key in data["pairs"] if not (RUN / f"neural/{seed}/{key}.json").exists()]
        if missing_ref or missing:
            with Neural(seed) as model:
                for start in range(0, len(missing_ref), 8):
                    boundary("neural-reference:" + seed)
                    batch = missing_ref[start:start + 8]
                    result = model.predict([(ref_texts[p["first"]], ref_texts[p["second"]]) for p in batch])
                    for pair, record in zip(batch, result):
                        c.unit(RUN / f"parity/{seed}/{pair['id']}.json", record)
                for start in range(0, len(missing), 8):
                    boundary("neural-batch:" + seed + ":" + str(start))
                    keys = missing[start:start + 8]
                    result = model.predict([(data["texts"][data["pairs"][key]["first"]], data["texts"][data["pairs"][key]["second"]]) for key in keys])
                    for key, record in zip(keys, result):
                        c.unit(RUN / f"neural/{seed}/{key}.json", record)
        checks = []
        expected = c.read(c.P2 / f"evaluation/seed-{seed}.json")["predictions"]
        expected = {kind: {r["id"]: r for r in expected[kind]} for kind in ("baseline", "hybrid")}
        for pair in ref_pairs:
            key = pair["id"]
            current = c.read_unit(RUN / f"parity/{seed}/{key}.json")
            original = c.read(c.P2 / f"predictions/seed-{seed}-final/evaluation/{key}.json")
            c.require(current["weightsSHA256"] == original["weightsSHA256"], "Reference weights changed")
            delta = max(abs(a - b) for a, b in zip(current["directions"], original["directions"]))
            combined = ref_feature.scores(ref_values[key], {seed: current["score"]})
            hybrid_delta = abs(combined["hybrid"][seed] - expected["hybrid"][key]["score"])
            c.require(delta <= 1e-5 and hybrid_delta <= 1e-5 and
                      abs(combined["baseline"]["score"] - expected["baseline"][key]["score"]) <= 1e-12 and
                      combined["baseline"]["eligible"] == expected["baseline"][key]["eligible"], "Model probability parity failed")
            threshold = manifest["thresholds"]["hybrids"][seed]
            c.require((combined["hybrid"][seed] >= threshold) == (expected["hybrid"][key]["score"] >= threshold), "Reference threshold changed")
            checks.append({"id": key, "neuralDelta": delta, "hybridDelta": hybrid_delta})
        c.publish(RUN / f"parity/{seed}.json", {"passed": True, "featureDelta": feature_delta, "checks": checks})
        c.log("seed-saved", seed=seed, pairs=len(data["pairs"]), parityCases=len(checks))
    scores = {key: features.scores(values[key], {seed: c.read_unit(RUN / f"neural/{seed}/{key}.json")["score"] for seed in SCORERS[1:]})
              for key in data["pairs"]}
    c.require(all(row["baseline"]["score"] is not None and all(v is not None and np.isfinite(v) for v in row["hybrid"].values()) for row in scores.values()),
              "Invalid scores must not become abstentions")
    c.publish(RUN / "pair-scores.json", scores)
    for candidate, rows in assemble(scores, manifest["thresholds"]).items():
        c.unit(RUN / f"predictions/{candidate}.json", rows)
    paths = [p for folder in ("embeddings", "native-parity", "parity", "neural", "predictions") for p in (RUN / folder).rglob("*.json")]
    paths += [RUN / name for name in ("native-parity.json", "features.json", "pair-scores.json")]
    c.publish(RUN / "predictions-complete.json", {"manifestSHA256": c.digest(RUN / "manifest.json"),
        "files": {str(p.relative_to(RUN)): c.digest(p) for p in sorted(paths)}, "predictionCount": 1440})
    return {"predictionsFrozen": True, "count": 1440}


def verify_predictions():
    verify_manifest()
    receipt = c.read(RUN / "predictions-complete.json")
    c.require(receipt["manifestSHA256"] == c.digest(RUN / "manifest.json") and receipt["predictionCount"] == 1440, "Prediction receipt changed")
    check_files(receipt["files"], RUN)
    from c2_run import parity_inputs as references
    ref_texts, _, ref_pairs = references()
    data = c.read(RUN / "catalogue.json")
    expected = {f"predictions/{candidate}.json" for candidate in CANDIDATES}
    expected |= {f"embeddings/{key}.json" for key in data["texts"]}
    expected |= {f"native-parity/{key}.json" for key in sorted(ref_texts)[:2]}
    expected |= {f"parity/{seed}/{p['id']}.json" for seed in SCORERS[1:] for p in ref_pairs}
    expected |= {f"neural/{seed}/{key}.json" for seed in SCORERS[1:] for key in data["pairs"]}
    expected |= {f"parity/{seed}.json" for seed in SCORERS[1:]}
    expected |= {"native-parity.json", "features.json", "pair-scores.json"}
    c.require(set(receipt["files"]) == expected, "Prediction inventory mismatch")
    for candidate in CANDIDATES:
        rows = c.read_unit(RUN / f"predictions/{candidate}.json")
        c.require(len(rows) == 160 and {r['queryID'] for r in rows} == {p['queryID'] for p in packets()}, "Prediction coverage mismatch")
    return receipt


def evaluate():
    verify_predictions()
    labels = c.read(RUN / "adjudicated-gold.json")["labels"]
    original = c.read(c5_run.RUN / "release/gold.json")["labels"]
    summary = {"adjudicated": {}, "original": {}, "diagnosticOnly": True}
    for candidate in CANDIDATES:
        boundary("evaluate:" + candidate)
        predictions = c.read_unit(RUN / f"predictions/{candidate}.json")
        summary["adjudicated"][candidate] = evaluate_predictions(packets(), labels, predictions)
        summary["original"][candidate] = evaluate_predictions(packets(), original, predictions)
        lookup = {p["queryID"]: p for p in predictions}
        c.publish(RUN / f"errors/{candidate}.json", [{"queryID": g["queryID"], "expected": g["verdict"],
            "prediction": lookup[g["queryID"]], "family": g["family"], "behavior": g["behavior"]}
            for g in labels if lookup[g["queryID"]]["verdict"] != g["verdict"]])
    c.publish(RUN / "summary.json", summary)
    c.publish(RUN / "metrics-complete.json", {"predictionReceiptSHA256": c.digest(RUN / "predictions-complete.json"),
        "summarySHA256": c.digest(RUN / "summary.json"), "files": {str(p.relative_to(RUN)): c.digest(p) for p in sorted((RUN / "errors").glob("*.json"))}})
    return {"metricsSaved": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "score", "evaluate", "pause", "status"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-units", type=int)
    args = parser.parse_args()
    c.require(args.max_units is None or args.max_units > 0, "max-units must be positive")
    if args.phase == "pause":
        c.log("pause", **pause()); return 0
    if args.phase == "status":
        c.log("status", **c.space(), embeddings=len(list((RUN / "embeddings").glob("*.json"))),
              predictions=(RUN / "predictions-complete.json").exists(), metrics=(RUN / "metrics-complete.json").exists()); return 0
    try:
        with worker(args.resume):
            boundary(args.phase)
            c.log("saved", **{"freeze": freeze, "score": lambda: score(args.max_units), "evaluate": evaluate}[args.phase]())
    except c.Paused as stopped:
        c.log("paused", boundary=str(stopped), safeToClose=True); return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
