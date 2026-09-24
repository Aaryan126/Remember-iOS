"""Frozen original-model controls, kept separate from benchmark selection."""
import importlib.metadata
import platform
from pathlib import Path
import subprocess
import sys
import time

import common as c

SPACE = "apple-dual:en:5C45D94E-BAB4-4927-94B6-8B5745C46289:1:512:1:512:token64-sentence256-v3"


def legacy():
    # The historical modules are imported only for pure transforms and model loading.
    # Never call their runners, workers, writers or embedding_probe (old output path).
    override = c.ROOT / "Evaluation/iOS27/precision/build/python-overrides"
    c.require((override / "scipy").is_dir(), "existing local SciPy compatibility override missing")
    sys.path.insert(0, str(override))
    sys.path.insert(0, str(c.ROOT / "scripts/organization-diagnostics"))
    from c2_models import Features, Neural
    from c2_run import parity_inputs
    return Features, Neural, parity_inputs


def embedding(key, text):
    import json
    executable = c.EXTERNAL / "validation/validation-02/probe/EmbeddingProbe"
    start = time.monotonic()
    result = subprocess.run([str(executable)], input=json.dumps({"id": key, "text": text}) + "\n",
                            text=True, capture_output=True, timeout=65, check=True)
    lines = result.stdout.splitlines()
    c.require(len(lines) == 1, "embedding probe returned wrong response count")
    value = json.loads(lines[0])
    c.require(value.get("id") == key and value.get("status") == "ok", "embedding unavailable")
    c.require(value.get("space") == SPACE and value.get("expectedSpace") == SPACE, "embedding space changed")
    import math
    for channel in ("contextual", "sentence"):
        vector = value.get(channel, [])
        c.require(len(vector) == 512 and all(isinstance(v, (float, int)) and math.isfinite(v) for v in vector),
                  "invalid embedding vector")
        c.require(sum(v*v for v in vector) > 0, "zero embedding vector")
    return {**value, "textSHA256": c.text_hash(text), "seconds": time.monotonic() - start}


def inputs():
    c.pf1.verify_manifest(c.PF)
    Features, Neural, parity_inputs = legacy()
    texts, embeddings, pairs = parity_inputs()
    record = c.read(c.P2 / "hybrid-29.json")
    assets = c.read(c.ROOT / "Evaluation/MatcherFeasibility/model-manifest.json")
    paths = [c.EXTERNAL / assets["workspaceRelativeDirectory"] / name for name in assets["assets"]]
    for path in paths:
        c.require(c.digest(path) == assets["assets"][path.name]["sha256"], f"model/tokenizer asset changed: {path.name}")
    weights = c.EXTERNAL / "validation/validation-02" / record["final"]["file"]
    c.require(c.digest(weights) == record["final"]["SHA256"], "seed-29 weight hash changed")
    probe = c.EXTERNAL / "validation/validation-02/probe/EmbeddingProbe"
    c.require(c.digest(probe) == c.read(c.P2 / "probe.json")["SHA256"], "embedding probe changed")
    parameters = c.read(c.ROOT / "Remember/Remember/MatcherAssets/D3Parameters.json")
    c.require(parameters["combiner"] == record["model"] and parameters["tfidf"] == c.read(c.P2 / "tfidf.json"),
              "app and frozen P2 transforms differ")
    c.require(parameters["threshold"] == record["selection"]["threshold"] == 0.9804276486193665,
              "production threshold changed")
    c.require(parameters["weightsSHA256"] == record["final"]["SHA256"], "app weights identity changed")
    paths += [weights, probe, c.PF / "frozen.json", c.WORK / "README.md"]
    paths += [c.CODE / name for name in ("common.py", "preflight.py", "run.py")]
    paths += [c.P2 / name for name in ("tfidf.json", "baseline.json", "hybrid-17.json", "hybrid-29.json", "hybrid-41.json",
                                     "features/evaluation.json", "evaluation/seed-29.json")]
    paths += [c.P2 / f"embeddings/{v['id']}.json" for v in embeddings.values()]
    paths += [c.P2 / f"predictions/seed-29-final/evaluation/{p['id']}.json" for p in pairs]
    paths += [c.ROOT / "Remember/Remember" / name for name in
              ("D3OrganizationPolicy.swift", "D3Features.swift", "D3PairMatcher.swift", "MatcherAssets/D3Parameters.json")]
    paths += [c.ROOT / "scripts/organization-diagnostics" / name for name in
              ("c2_models.py", "c2_common.py", "c2_run.py", "checkpoint.py")]
    paths += list((c.ROOT / "scripts/matcher-feasibility").glob("*.py"))
    override = c.ROOT / "Evaluation/iOS27/precision/build/python-overrides"
    paths += [p for p in override.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    import scipy
    c.require(scipy.__version__ == "1.17.1" and Path(scipy.__file__).resolve().is_relative_to(override.resolve()),
              "unexpected SciPy runtime")
    manifest = {"schemaVersion": 1, "hashes": {str(p): c.digest(p) for p in sorted(set(paths))},
                "runtime": {"python": sys.version, "platform": platform.platform(),
                            "packages": {name: importlib.metadata.version(name) for name in
                                         ("torch", "transformers", "numpy", "scipy", "scikit-learn", "tokenizers")},
                            "scipyOverride": str(override)},
                "controls": pairs, "embeddingSpace": SPACE, "neuralTolerance": 1e-5,
                "embeddingTolerance": 1e-5, "featureTolerance": 1e-12}
    c.publish(c.WORK / "runs/preflight/binding.json", manifest)
    return Features, Neural, texts, embeddings, pairs, c.digest(c.WORK / "runs/preflight/binding.json")


def run(max_units=None):
    import numpy as np
    Features, Neural, texts, old_embeddings, pairs, binding = inputs()
    base = c.WORK / "runs/preflight"
    units = 0
    fresh = {}
    for key, text in sorted(texts.items()):
        c.boundary()
        path = base / f"embeddings/{key}.json"
        if not path.exists():
            c.unit(path, embedding(key, text), binding)
            units += 1
        value = c.read_unit(path, binding)
        c.require(value["textSHA256"] == c.text_hash(text), "control text changed")
        delta = max(abs(a-b) for channel in ("contextual", "sentence")
                    for a, b in zip(value[channel], old_embeddings[key][channel]))
        c.require(delta <= 1e-5, f"embedding numerical parity failed: {key}, delta={delta}")
        fresh[key] = value
        c.log(phase="control-embeddings", complete=len(fresh), total=len(texts), maxDelta=delta)
        if max_units and units >= max_units:
            raise c.Paused("bounded preflight unit limit")
    old_features = {row["id"]: row["features"] for row in c.read(c.P2 / "features/evaluation.json")["rows"]}
    saved_features, features = Features(texts, old_embeddings), Features(texts, fresh)
    feature_delta = max(float(np.max(np.abs(np.array(saved_features.values(p["first"], p["second"])) - old_features[p["id"]]))) for p in pairs)
    c.require(feature_delta <= 1e-12, f"frozen feature parity failed: {feature_delta}")
    missing = [p for p in pairs if not (base / f"neural/{p['id']}.json").exists()]
    if missing:
        c.boundary()
        with Neural("29") as model:
            for offset in range(0, len(missing), 8):
                c.boundary()
                batch = missing[offset:offset+8]
                values = model.predict([(texts[p["first"]], texts[p["second"]]) for p in batch])
                for p, value in zip(batch, values):
                    c.unit(base / f"neural/{p['id']}.json", {"id": p["id"], **value}, binding)
                c.log(phase="control-neural", complete=offset + len(batch), total=len(missing))
    expected = {r["id"]: r for r in c.read(c.P2 / "evaluation/seed-29.json")["predictions"]["hybrid"]}
    checked = []
    for p in pairs:
        current = c.read_unit(base / f"neural/{p['id']}.json", binding)
        old = c.read(c.P2 / f"predictions/seed-29-final/evaluation/{p['id']}.json")
        delta = max(abs(a-b) for a, b in zip(current["directions"], old["directions"]))
        c.require(delta <= 1e-5, f"neural numerical parity failed: {p['id']}, delta={delta}")
        score = features.scores(features.values(p["first"], p["second"]), {"29": current["score"]})["hybrid"]["29"]
        score_delta = abs(score - expected[p["id"]]["score"])
        c.require(score_delta <= 1e-5, f"combined score parity failed: {p['id']}, delta={score_delta}")
        c.require((score >= 0.9804276486193665) == (expected[p["id"]]["score"] >= 0.9804276486193665), "control decision changed")
        checked.append({"id": p["id"], "directionalDelta": delta, "combinedDelta": score_delta})
    report = {"passed": True, "bindingSHA256": binding, "controlPairs": checked,
              "featureDelta": feature_delta, "embeddingSources": len(fresh), "phoneTested": False,
              "benchmarkQualityMeasured": False}
    c.publish(c.WORK / "preflight.json", report)
    return report
