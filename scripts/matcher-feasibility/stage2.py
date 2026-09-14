#!/usr/bin/env python3
"""Resumable Mac-only Stage 2. Never reads heldout labels or changes production."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import subprocess
import sys
import time
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from experiment import ROOT, DATA, read, save, sha, require, validate_inputs, validate_labels, pair_rows, verify_freeze
from environment import publish_bytes, verify_assets
from stage2_metrics import CLASSES, metrics, select_threshold, bootstrap, retrieval_metrics

HERE = Path(__file__).resolve().parent
RELEASE = DATA / "releases/v1"
FEATURES = ["contextual_cosine", "sentence_cosine", "word_tfidf_cosine",
            "character_trigram_jaccard", "number_token_jaccard", "text_length_ratio"]
pause_requested = False


class Paused(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def on_signal(signum, frame):
    global pause_requested
    pause_requested = True


def boundary(run, phase):
    require(shutil.disk_usage(run).free >= 10 * 1024**3, "less than 10 GiB free; stop heavyweight work")
    if pause_requested or (run / "control/pause-requested.json").exists():
        save(run / "pauses" / f"{time.time_ns()}.json", {"at": now(), "phase": phase,
             "status": "paused", "completedEmbeddingItems": len(list((run / "embeddings").glob("*.json"))),
             "completedReferenceCases": len(list((run / "reference/cases").glob("*.json")))})
        raise Paused(phase)


def content_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def load_split(split):
    require(split in ("train", "development"), "Stage 2 cannot load heldout test labels or inputs")
    inputs = read(RELEASE / f"inputs-{split}.json")
    validate_inputs(inputs, complete=False)
    require(all(r["split"] == split for r in inputs["libraries"]), "mixed input split")
    return inputs


def source_bindings():
    paths = [HERE / name for name in ["stage2.py", "stage2_metrics.py", "stage2_reference.py", "Stage2EmbeddingProbe.swift", "test_stage2.py"]]
    paths += [RELEASE / f"{kind}-{split}.json" for kind in ("inputs", "labels") for split in ("train", "development")]
    paths += [ROOT / "Remember/Remember/ProjectIntelligence.swift"]
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}


def initialize(run, workspace):
    require(run.is_relative_to((DATA / "runs").resolve()), "run must be under experiment runs directory")
    require(workspace.name == "v1" and workspace.parent.name == "RememberMatcherFeasibility", "unexpected workspace")
    require(re.fullmatch(r"stage-2-attempt-\d+", run.name), "invalid run name")
    verified = verify_freeze(DATA / "freeze.json")
    verify_assets(workspace, read(DATA / "model-manifest.json"))
    current = source_bindings()
    path = run / "manifest.json"
    if path.exists():
        previous = read(path)
        require(previous["sourceSHA256"] == current, "Stage 2 code/input changed; preserve this attempt and create a new one")
        require(previous["stage1FreezeSHA256"] == verified["freezeSHA256"], "Stage 1 freeze changed")
    else:
        save(path, {"schemaVersion": 1, "stage": 2, "authorizedBy": "user: go ahead with stage 2",
                   "createdAt": now(), "stage1FreezeSHA256": verified["freezeSHA256"],
                   "sourceSHA256": current, "splits": ["train", "development"], "testResultsOpened": False,
                   "featureOrder": FEATURES, "characterNormalization": "lowercase and collapse whitespace",
                   "numberTokenPattern": r"\d+(?:[.,]\d+)*", "lengthUnit": "Python Unicode code points in original text",
                   "candidateTieBreak": "source ID", "missingEvidencePolicy": "no probability; counted in coverage and positive recall denominator",
                   "stopAfterStage": True, "noPhone": True})


def build_probe(run, workspace):
    boundary(run, "before-embedding-probe-build")
    generated = workspace / "stage2" / run.name / "probe"
    source = (ROOT / "Remember/Remember/ProjectIntelligence.swift").read_text()
    provider = source.split("nonisolated struct ProjectEmbedding:", 1)[1].split("nonisolated enum ProjectMath", 1)[0]
    normalization = source.split("    static func normalized(_ vector:", 1)[1].split("    static func cosine(", 1)[0]
    body = "import Foundation\nimport NaturalLanguage\nnonisolated struct ProjectEmbedding:" + provider
    body += "nonisolated enum ProjectMath {\n    static func normalized(_ vector:" + normalization + "}\n"
    publish_bytes(generated / "ProductionEmbedding.swift", body.encode())
    executable = generated / "EmbeddingProbe"
    if not executable.exists():
        result = subprocess.run(["xcrun", "swiftc", "-parse-as-library", "-O", "-target", "arm64-apple-macos26.0",
                                 str(generated / "ProductionEmbedding.swift"), str(HERE / "Stage2EmbeddingProbe.swift"),
                                 "-o", str(executable)], capture_output=True, text=True, timeout=180)
        save(run / "probe-build.json", {"at": now(), "returncode": result.returncode,
             "stdout": result.stdout, "stderr": result.stderr, "generatedSourceSHA256": sha(generated / "ProductionEmbedding.swift"),
             "productionSourceSHA256": sha(ROOT / "Remember/Remember/ProjectIntelligence.swift")})
        require(result.returncode == 0, "Swift probe compilation failed; see probe-build.json")
    return executable


def validate_embedding(item, record):
    require(record["id"] == item["id"] and record["textSHA256"] == content_sha(item["text"]), "embedding source mismatch")
    require(record["status"] in ("ok", "unavailable", "error"), "invalid embedding status")
    if record["status"] == "ok":
        require(record.get("space") and record["space"] == record.get("expectedSpace"), "embedding space mismatch")
        for key in ("contextual", "sentence"):
            vector = np.asarray(record.get(key, []), dtype=float)
            require(vector.ndim == 1 and len(vector) > 0 and np.isfinite(vector).all()
                    and abs(np.linalg.norm(vector) - 1) < 1e-4, "invalid embedding vector")


def collect_embeddings(run, workspace):
    executable = build_probe(run, workspace)
    items = [i for split in ("train", "development") for lib in load_split(split)["libraries"] for i in lib["items"]]
    start = time.monotonic()
    process = None
    log = None
    try:
        for index, item in enumerate(items):
            boundary(run, f"embedding:{item['id']}")
            path = run / "embeddings" / f"{item['id']}.json"
            if path.exists():
                validate_embedding(item, read(path))
                continue
            if process is None:
                log = (run / f"probe-stderr-{time.time_ns()}.log").open("w")
                process = subprocess.Popen([str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=log, text=True, bufsize=1)
            process.stdin.write(json.dumps(item) + "\n")
            process.stdin.flush()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                require(bool(selector.select(timeout=120)), "embedding response timed out")
                line = process.stdout.readline()
            require(bool(line), "embedding probe exited without a response")
            record = {**json.loads(line), "textSHA256": content_sha(item["text"]), "recordedAt": now()}
            validate_embedding(item, record)
            save(path, record)
            if (index + 1) % 20 == 0:
                print(json.dumps({"phase": "embeddings", "completed": index + 1, "total": len(items),
                                  "elapsedSecondsThisInvocation": round(time.monotonic() - start, 2)}), flush=True)
    finally:
        if process is not None:
            process.stdin.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            process.stdout.close()
            log.close()
    path = run / "embedding-summary.json"
    if not path.exists():
        records = [read(run / "embeddings" / f"{i['id']}.json") for i in items]
        save(path, {"items": len(records), "statusCounts": dict(Counter(r["status"] for r in records)),
             "languages": dict(Counter(r.get("language", "unknown") for r in records)),
             "spaces": dict(Counter(r.get("space", "unavailable") for r in records)),
             "extractionSeconds": sum(r["seconds"] for r in records), "macOnly": True,
             "manifestSHA256": sha(run / "manifest.json")})


def jaccard(a, b):
    return len(a & b) / len(a | b) if a or b else 0.0


def trigrams(text):
    text = " ".join(text.lower().split())
    return {text[i:i + 3] for i in range(len(text) - 2)}


def cosine(a, b):
    if a is None or b is None or len(a) != len(b) or not len(a):
        return None
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if not np.isfinite(a).all() or not np.isfinite(b).all() or denominator == 0:
        return None
    return float(np.clip(a @ b / denominator, -1, 1))


def pair_features(first, second, a, b, lexical):
    compatible = a["status"] == b["status"] == "ok" and a.get("space") == b.get("space")
    contextual = cosine(a.get("contextual"), b.get("contextual")) if compatible else None
    sentence = cosine(a.get("sentence"), b.get("sentence")) if compatible else None
    text_a, text_b = first["text"], second["text"]
    return [contextual, sentence, float(lexical), jaccard(trigrams(text_a), trigrams(text_b)),
            jaccard(set(re.findall(r"\d+(?:[.,]\d+)*", text_a)), set(re.findall(r"\d+(?:[.,]\d+)*", text_b))),
            min(len(text_a), len(text_b)) / max(len(text_a), len(text_b)) if text_a or text_b else 0.0]


def top_candidates(ids, contextual, lexical, k=5):
    output = {}
    for index, item in enumerate(ids):
        semantic = sorted([j for j in range(len(ids)) if j != index and contextual[index][j] is not None],
                          key=lambda j: (-contextual[index][j], ids[j]))[:k]
        words = sorted([j for j in range(len(ids)) if j != index], key=lambda j: (-lexical[index][j], ids[j]))[:k]
        output[item] = sorted({ids[j] for j in semantic + words})
    return output


def prepare_features(run):
    if (run / "features.json").exists():
        return read(run / "features.json")
    boundary(run, "features")
    train = load_split("train")
    texts = [i["text"] for lib in train["libraries"] for i in lib["items"]]
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), dtype=np.float64)
    vectorizer.fit(texts)
    results = {"featureOrder": FEATURES, "splits": {}, "tfidf": {"vocabulary": {k: int(v) for k, v in vectorizer.vocabulary_.items()},
               "idf": vectorizer.idf_.tolist(), "ngramRange": [1, 2], "lowercase": True,
               "tokenPattern": vectorizer.token_pattern, "norm": "l2", "fitSplit": "train", "fitDocuments": len(texts)}}
    for split in ("train", "development"):
        inputs = load_split(split)
        labels = read(RELEASE / f"labels-{split}.json")
        validate_labels(inputs, labels)
        label_map = {r["id"]: r for r in labels["libraries"]}
        rows, candidates, gold = [], {}, {}
        for lib in inputs["libraries"]:
            boundary(run, f"features:{lib['id']}")
            items = lib["items"]
            embeddings = [read(run / "embeddings" / f"{i['id']}.json") for i in items]
            for item, record in zip(items, embeddings):
                validate_embedding(item, record)
            lexical = (vectorizer.transform([i["text"] for i in items]) @ vectorizer.transform([i["text"] for i in items]).T).toarray()
            index = {i["id"]: n for n, i in enumerate(items)}
            contextual = [[None] * len(items) for _ in items]
            gold[lib["id"]] = pair_rows(lib, label_map[lib["id"]])
            for pair in gold[lib["id"]]:
                a, b = index[pair["first"]], index[pair["second"]]
                feature = pair_features(items[a], items[b], embeddings[a], embeddings[b], lexical[a, b])
                contextual[a][b] = contextual[b][a] = feature[0]
                rows.append({**pair, "library": lib["id"], "features": feature,
                             "status": "ok" if all(v is not None for v in feature) else "missing_embedding"})
            candidates.update(top_candidates([i["id"] for i in items], contextual, lexical))
        for row in rows:
            row["retrieved"] = row["second"] in candidates[row["first"]] or row["first"] in candidates[row["second"]]
        results["splits"][split] = {"pairs": rows, "candidates": candidates,
                                    "retrieval": retrieval_metrics(inputs["libraries"], gold, candidates)}
    save(run / "features.json", results)
    return results


def exported_probabilities(model, features):
    scaled = (np.asarray(features) - model["scalerMean"]) / model["scalerScale"]
    logits = scaled @ np.asarray(model["coefficients"]).T + model["intercept"]
    logits -= logits.max(axis=1, keepdims=True)
    probabilities = np.exp(logits)
    return probabilities / probabilities.sum(axis=1, keepdims=True)


def run_baseline(run):
    if (run / "baseline-summary.json").exists():
        return
    data = prepare_features(run)
    train = data["splits"]["train"]["pairs"]
    fitting = [r for r in train if r["relation"] != "uncertain" and r["status"] == "ok"]
    require({r["relation"] for r in fitting} == set(CLASSES), "available training data lacks a class")
    x = np.array([r["features"] for r in fitting])
    y = np.array([CLASSES.index(r["relation"]) for r in fitting])
    scaler = StandardScaler().fit(x)
    candidates = []
    for c in (.1, 1., 10.):
        boundary(run, f"baseline:C={c}")
        path = run / "baseline" / f"C-{c:g}.json"
        if path.exists():
            result = read(path)
            candidates.append(result)
            continue
        classifier = LogisticRegression(C=c, class_weight="balanced", max_iter=2000, random_state=17, solver="lbfgs")
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            classifier.fit(scaler.transform(x), y)
        require(list(classifier.classes_) == [0, 1, 2], "unexpected classifier class order")
        model = {"C": c, "classOrder": CLASSES, "featureOrder": FEATURES, "fitSplit": "train",
                 "scalerMean": scaler.mean_.tolist(), "scalerScale": scaler.scale_.tolist(),
                 "coefficients": classifier.coef_.tolist(), "intercept": classifier.intercept_.tolist(),
                 "iterations": classifier.n_iter_.tolist()}
        require(np.max(np.abs(exported_probabilities(model, x) - classifier.predict_proba(scaler.transform(x)))) < 1e-12,
                "portable baseline export differs from sklearn")
        predictions = {}
        for split, content in data["splits"].items():
            rows = [{**r, "probabilities": None} for r in content["pairs"]]
            valid = [r for r in rows if r["status"] == "ok"]
            if valid:
                values = classifier.predict_proba(scaler.transform([r["features"] for r in valid]))
                for row, probabilities in zip(valid, values):
                    row["probabilities"] = probabilities.tolist()
            predictions[split] = rows
        selected = select_threshold(predictions["development"])
        threshold = selected["threshold"] if selected else None
        result = {"model": model, "selection": selected, "predictions": predictions,
                  "metrics": {split: {"allPairs": metrics(rows, threshold),
                                      "candidateConditioned": metrics([r for r in rows if r["retrieved"]], threshold),
                                      "argmaxOperatingPoint": metrics(rows, 0.0)} for split, rows in predictions.items()}}
        save(path, result)
        candidates.append(result)
        print(json.dumps({"phase": "baseline", "C": c, "qualifyingOperatingPoint": selected}), flush=True)
    qualifying = [r for r in candidates if r["selection"] is not None]
    winner = max(qualifying, key=lambda r: (r["selection"]["metrics"]["macroLibraryRecall"],
                 r["selection"]["metrics"]["precision"], r["selection"]["threshold"], -r["model"]["C"])) if qualifying else None
    summary = {"status": "qualified_on_development" if winner else "no_qualifying_development_baseline",
               "testResultsOpened": False, "fitPairs": len(fitting), "trainingKnownPairs": sum(r["relation"] != "uncertain" for r in train),
               "retrieval": {s: d["retrieval"] for s, d in data["splits"].items()},
               "selectedC": winner["model"]["C"] if winner else None,
               "threshold": winner["selection"]["threshold"] if winner else None,
               "selectedMetrics": winner["metrics"] if winner else None,
               "developmentBootstrap": bootstrap(winner["predictions"]["development"], winner["selection"]["threshold"]) if winner else None,
               "semanticNeuralTrainingPerformed": False,
               "limitations": ["Development is used for selection, not unbiased validation.", "No chronological grouping or merge replay.",
                               "Pair automation includes ambiguous pairs; known precision excludes them and reports their acceptance separately."]}
    if winner:
        save(run / "baseline-selected.json", {"model": winner["model"], "threshold": summary["threshold"], "tfidf": data["tfidf"]})
    save(run / "baseline-summary.json", summary)


def complete(run, workspace):
    boundary(run, "final-integrity-check")
    verify_freeze(DATA / "freeze.json")
    require(read(run / "manifest.json")["sourceSHA256"] == source_bindings(), "code changed while running")
    references = read(run / "reference-summary.json")
    baseline = read(run / "baseline-summary.json")
    require(references["completedCases"] == references["expectedCases"], "incomplete reference coverage")
    files = [p for p in run.rglob("*.json") if "control" not in p.parts and p.name != "complete.json"]
    assets = workspace / "stage2" / run.name
    external = [p for p in assets.rglob("*") if p.is_file()]
    save(run / "complete.json", {"schemaVersion": 1, "stage": 2, "completedAt": now(),
         "status": "completed_not_integrated", "baselineStatus": baseline["status"], "testResultsOpened": False,
         "stage3Started": False, "files": {str(p.relative_to(run)): sha(p) for p in sorted(files)},
         "workspaceFiles": {str(p.relative_to(workspace)): sha(p) for p in sorted(external)}})


def verify_run(run, workspace):
    result = read(run / "complete.json")
    for root, entries in ((run, result["files"]), (workspace, result["workspaceFiles"])):
        for name, expected in entries.items():
            path = (root / name).resolve()
            require(path.is_relative_to(root) and path.is_file() and sha(path) == expected, f"Stage 2 artifact mismatch: {name}")
    require(read(run / "manifest.json")["sourceSHA256"] == source_bindings(), "Stage 2 source bindings changed")
    return {"verified": True, "files": len(result["files"]), "workspaceFiles": len(result["workspaceFiles"]),
            "completeSHA256": sha(run / "complete.json")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "pause", "verify"])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, default=Path.home() / "Library/Application Support/RememberMatcherFeasibility/v1")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    run, workspace = args.run.resolve(), args.workspace.resolve()
    require(run.is_relative_to((DATA / "runs").resolve()), "invalid run location")
    marker = run / "control/pause-requested.json"
    if args.command == "pause":
        require((run / "manifest.json").is_file(), "no initialized run to pause")
        if not marker.exists():
            save(marker, {"requestedAt": now(), "reason": "user pause request"})
        print("Pause requested; wait for the running process to confirm a saved boundary.")
        return
    if args.command == "verify":
        print(json.dumps(verify_run(run, workspace)))
        return
    initialize(run, workspace)
    if (run / "complete.json").exists():
        print(json.dumps(verify_run(run, workspace)))
        return
    if args.resume and marker.exists():
        marker.rename(run / "control" / f"resumed-request-{time.time_ns()}.json")
    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    try:
        collect_embeddings(run, workspace)
        run_baseline(run)
        from stage2_reference import run_reference
        run_reference(run, workspace, boundary)
        complete(run, workspace)
        print(json.dumps(verify_run(run, workspace)), flush=True)
    except Paused as error:
        print(json.dumps({"status": "paused", "safeBoundary": str(error), "resumeWith": "same run command plus --resume"}), flush=True)
    except Exception as error:
        save(run / "failures" / f"{time.time_ns()}.json", {"at": now(), "type": type(error).__name__, "error": str(error)})
        raise


if __name__ == "__main__":
    main()
