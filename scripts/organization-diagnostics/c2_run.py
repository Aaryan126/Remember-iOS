#!/usr/bin/env python3
"""Checkpoint-2 bounded inference/placement runner. Semantic scoring is separate."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
import time

import c2_common as c
from c2_policy import POLICY_IDS, run_stream


def parity_inputs():
    """Old published predictions are numerical references, not new scorer inputs."""
    report = c.read(c.P2 / "evaluation/seed-17.json")
    rows = report["predictions"]["hybrid"][:16]
    source = c.read(c.ROOT / "Evaluation/MatcherValidation/releases/v1/inputs-evaluation.json")
    items = {item["id"]: item for library in source["libraries"] for item in library["items"]}
    source_ids = sorted({row[side] for row in rows for side in ("first", "second")})
    texts = {c.text_sha(items[key]["text"]): items[key]["text"] for key in source_ids}
    embeddings = {c.text_sha(items[key]["text"]): c.read(c.P2 / f"embeddings/{key}.json") for key in source_ids}
    pairs = [{"id": row["id"], "first": c.text_sha(items[row["first"]]["text"]),
              "second": c.text_sha(items[row["second"]]["text"])} for row in rows]
    return texts, embeddings, pairs


def freeze():
    from c2_inputs import compile_inputs, catalogue
    if (c.RUN / "manifest.json").exists():
        return c.verify_bindings()
    c.boundary("prepare")
    # C1 verification performs no model or scorer execution.
    import finalize
    finalize.verify()
    streams, audit = compile_inputs()
    c.publish(c.RUN / "inputs.json", {"streams": streams})
    c.publish(c.RUN / "anchor-audit.json", audit)
    c.publish(c.RUN / "catalogue.json", catalogue(streams))
    from c2_reference import build
    build(c.RUN)  # Exact-verifies the native receipt if already built.
    root = Path(__file__).parent
    paths = list(root.glob("c2_*.py")) + list(root.glob("test_c2_*.py"))
    paths += [root / "checkpoint.py", root / "reference/C2ReferenceProbe.swift",
              c.DATA / "complete.json", c.DATA / "C2_PROTOCOL.md",
              c.ROOT / "Evaluation/MatcherFeasibility/model-manifest.json"]
    paths += list((c.DATA / "release").rglob("*.json"))
    paths += list(c.LEGACY.glob("*.py")) + list((c.ROOT / "scripts/matcher-validation").glob("*.py"))
    paths += [p for p in (root / "ledger").rglob("*") if p.is_file() and p.suffix in (".py", ".swift", ".md")]
    ready = c.read(c.RUN / "ledger/ready.json")
    ledger_binding_path = c.RUN / ready["bindingPath"]
    ledger_binding = c.read(ledger_binding_path)
    paths += [c.RUN / "ledger/ready.json", ledger_binding_path]
    paths += [c.ROOT / name for name in ledger_binding["production"]]
    for name, expected in ledger_binding["production"].items():
        c.require(c.digest(c.ROOT / name) == expected, "Ledger production source changed")
    paths += [c.RUN / name for name in ("inputs.json", "anchor-audit.json", "catalogue.json",
                                       "reference/build-receipt.json", "reference/C2ReferenceProbe")]
    reference = c.read(c.RUN / "reference/build-receipt.json")
    paths += [c.ROOT / name for name in reference["sources"]]
    paths += [c.P2 / name for name in ("complete.json", "manifest.json", "selection.json", "baseline.json",
                                      "hybrid-17.json", "hybrid-29.json", "hybrid-41.json", "tfidf.json", "probe.json",
                                      "features/evaluation.json", "evaluation/seed-17.json", "evaluation/seed-29.json",
                                      "evaluation/seed-41.json")]
    paths += [c.ROOT / "Evaluation/MatcherValidation/releases/v1/inputs-evaluation.json"]
    _, embeddings, pairs = parity_inputs()
    paths += [c.P2 / f"embeddings/{record['id']}.json" for record in embeddings.values()]
    paths += [c.P2 / f"predictions/seed-{seed}-final/evaluation/{pair['id']}.json"
              for seed in (17, 29, 41) for pair in pairs]
    selection = c.read(c.P2 / "selection.json")
    for name, expected in selection["artifacts"].items():
        c.require(c.digest(c.P2 / name) == expected, "P2 selection artifact changed: " + name)
    asset = c.read(c.ROOT / "Evaluation/MatcherFeasibility/model-manifest.json")
    external = [c.WORKSPACE / asset["workspaceRelativeDirectory"] / name for name in asset["assets"]]
    for path in external:
        c.require(c.digest(path) == asset["assets"][path.name]["sha256"], "Pinned asset changed")
    external += [c.EXTERNAL / "probe/EmbeddingProbe", c.EXTERNAL / "probe/EnglishEmbedding.swift"]
    external += [c.EXTERNAL / f"models/seed-{seed}-final.pt.gz" for seed in (17, 29, 41)]
    for path in external[-3:]:
        c.require(c.digest(path) == selection["weights"][str(path.relative_to(c.EXTERNAL))], "P2 final weight changed")
    receipt = {"schemaVersion": 1, "sources": {str(path.relative_to(c.ROOT)): c.digest(path) for path in sorted(set(paths))},
               "external": {str(path.relative_to(c.WORKSPACE)): c.digest(path) for path in external},
               "runtime": c.runtime(),
               "policies": list(POLICY_IDS), "thresholds": {key: selection[key] for key in ("baseline", "hybrids")},
               "parityIDs": [pair["id"] for pair in pairs], "modelBatchPairs": 8,
               "ledgerBindingSHA256": c.digest(ledger_binding_path),
               "scorerInputsContainGold": False, "diagnosticOnly": True, "resource": c.space()}
    c.publish(c.RUN / "manifest.json", receipt)
    return {"frozen": True, "streams": len(streams), "policies": len(POLICY_IDS)}


def parity():
    from c2_models import Features, Neural
    import numpy as np
    texts, embeddings, pairs = parity_inputs()
    features = Features(texts, embeddings)
    old_features = {row["id"]: row["features"] for row in c.read(c.P2 / "features/evaluation.json")["rows"]}
    values = {pair["id"]: features.values(pair["first"], pair["second"]) for pair in pairs}
    feature_delta = max(float(np.max(np.abs(np.array(values[key]) - old_features[key]))) for key in values)
    c.require(feature_delta <= 1e-12, "Frozen feature parity failed")
    for seed in ("17", "29", "41"):
        folder = c.RUN / f"parity/seed-{seed}"
        missing = [pair for pair in pairs if not (folder / f"{pair['id']}.json").exists()]
        if missing:
            c.boundary(f"parity-load-{seed}")
            with Neural(seed) as model:
                for offset in range(0, len(missing), 8):
                    c.boundary(f"parity-{seed}-{offset}")
                    batch = missing[offset:offset+8]
                    scores = model.predict([(texts[pair["first"]], texts[pair["second"]]) for pair in batch])
                    for pair, score in zip(batch, scores):
                        c.unit(folder / f"{pair['id']}.json", {"id": pair["id"], **score})
        report = c.read(c.P2 / f"evaluation/seed-{seed}.json")
        expected = {name: {row["id"]: row for row in report["predictions"][name]} for name in ("baseline", "hybrid")}
        checked = []
        for pair in pairs:
            key = pair["id"]
            current = c.read_unit(folder / f"{key}.json")
            original = c.read(c.P2 / f"predictions/seed-{seed}-final/evaluation/{key}.json")
            c.require(current["weightsSHA256"] == original["weightsSHA256"], "Parity weight binding changed")
            delta = max(abs(a-b) for a, b in zip(current["directions"], original["directions"]))
            c.require(delta <= 1e-5, f"Neural parity failed: {seed}/{key}: {delta}")
            scores = features.scores(values[key], {seed: current["score"]})
            baseline, hybrid = scores["baseline"], scores["hybrid"][seed]
            c.require(abs(baseline["score"] - expected["baseline"][key]["score"]) <= 1e-12
                      and baseline["eligible"] == expected["baseline"][key]["eligible"], "Baseline parity failed")
            c.require(abs(hybrid - expected["hybrid"][key]["score"]) <= 1e-5, "Hybrid probability parity failed")
            threshold = report["thresholds"]["hybrid"]
            c.require((hybrid >= threshold) == (expected["hybrid"][key]["score"] >= threshold), "Hybrid decision changed")
            checked.append({"id": key, "maximumDirectionalDelta": delta,
                            "hybridDelta": abs(hybrid - expected["hybrid"][key]["score"])})
        c.publish(c.RUN / f"parity/seed-{seed}.json", {"passed": True, "cases": checked, "featureDelta": feature_delta})
        c.log("parity", seed=seed, passed=True, maxDelta=max(row["maximumDirectionalDelta"] for row in checked))
    c.publish(c.RUN / "parity/complete.json", {"passed": True, "casesPerSeed": len(pairs), "manifestSHA256": c.digest(c.RUN / "manifest.json"),
        "reports": {str(seed): c.digest(c.RUN / f"parity/seed-{seed}.json") for seed in (17, 29, 41)}})
    return {"parityPassed": True}


def embeddings():
    from c2_models import embedding_probe, validate_embedding
    catalogue = c.read(c.RUN / "catalogue.json")
    with embedding_probe() as query:
        for index, (key, text) in enumerate(sorted(catalogue["texts"].items()), 1):
            c.boundary(f"embedding-{index}")
            path = c.RUN / f"embeddings/{key}.json"
            if not path.exists():
                c.unit(path, query(key, text))
            validate_embedding({"id": key, "text": text}, c.read_unit(path))
            if index % 20 == 0:
                c.log("embeddings", completed=index, total=len(catalogue["texts"]))
    records = [c.read_unit(c.RUN / f"embeddings/{key}.json") for key in catalogue["texts"]]
    c.publish(c.RUN / "embeddings-complete.json", {"status": dict(Counter(row["status"] for row in records)),
        "files": {key: c.digest(c.RUN / f"embeddings/{key}.json") for key in catalogue["texts"]}})


def verify_parity_receipt():
    complete = c.read(c.RUN / "parity/complete.json")
    c.require(complete.get("passed") is True and complete["casesPerSeed"] == 16,
              "Parity has not passed all reference cases")
    c.require(complete["manifestSHA256"] == c.digest(c.RUN / "manifest.json"), "Parity manifest changed")
    c.require(set(complete["reports"]) == {"17", "29", "41"}, "Parity seed coverage changed")
    for seed, expected in complete["reports"].items():
        path = c.RUN / f"parity/seed-{seed}.json"
        c.require(c.digest(path) == expected and c.read(path).get("passed") is True, "Parity report changed")
    return complete


def inference():
    from c2_models import Neural
    catalogue = c.read(c.RUN / "catalogue.json")
    texts, pairs = catalogue["texts"], catalogue["pairs"]
    for seed in ("17", "29", "41"):
        folder = c.RUN / f"neural/seed-{seed}"
        missing = [key for key in sorted(pairs) if not (folder / f"{key}.json").exists()]
        started = time.monotonic()
        if missing:
            c.boundary(f"neural-load-{seed}")
            with Neural(seed) as model:
                for offset in range(0, len(missing), 8):
                    c.boundary(f"neural-{seed}-{offset}")
                    batch = missing[offset:offset+8]
                    scores = model.predict([(texts[pairs[key]["first"]], texts[pairs[key]["second"]]) for key in batch])
                    for key, score in zip(batch, scores):
                        c.unit(folder / f"{key}.json", {"id": key, **score})
                    if offset % 80 == 0:
                        done = offset + len(batch)
                        elapsed = time.monotonic() - started
                        c.log("neural", seed=seed, completedThisInvocation=done, remaining=len(missing)-done,
                              elapsedSeconds=round(elapsed, 2), estimatedSeedSecondsRemaining=round(elapsed/done*(len(missing)-done)))
        record = c.read(c.P2 / f"hybrid-{seed}.json")["final"]
        for key in pairs:
            value = c.read_unit(folder / f"{key}.json")
            c.require(value["id"] == key and value["weightsSHA256"] == record["SHA256"], "Inference cache binding changed")
        c.publish(c.RUN / f"neural/seed-{seed}-complete.json", {"pairs": len(pairs), "weightsSHA256": record["SHA256"],
            "files": {key: c.digest(folder / f"{key}.json") for key in pairs}})


def traces():
    from c2_models import Features
    from c2_reference import build, ReferenceClient
    catalogue = c.read(c.RUN / "catalogue.json")
    embeddings = {key: c.read_unit(c.RUN / f"embeddings/{key}.json") for key in catalogue["texts"]}
    features = Features(catalogue["texts"], embeddings)
    paired = {}
    for key, pair in catalogue["pairs"].items():
        values = features.values(pair["first"], pair["second"])
        neural = {seed: c.read_unit(c.RUN / f"neural/seed-{seed}/{key}.json")["score"] for seed in ("17", "29", "41")}
        paired[key] = {"features": values, **features.scores(values, neural)}
    c.publish(c.RUN / "pair-scores.json", paired)
    def pair_score(a, b):
        value = paired[c.pair_key(a["text"], b["text"])]
        return {key: value[key] for key in ("baseline", "hybrid")}
    def retrieval(a, b):
        values = paired[c.pair_key(a["text"], b["text"])]["features"]
        return {"contextual": values[0], "lexical": values[2]}
    def embedding_for_text(text):
        result = embeddings[c.text_sha(text)]
        return {key: result[key] for key in ("contextual", "sentence", "space")} if result["status"] == "ok" else None
    streams = c.read(c.RUN / "inputs.json")["streams"]
    thresholds = c.read(c.RUN / "manifest.json")["thresholds"]
    paths = []
    with ReferenceClient(build(c.RUN), embedding_for_text) as reference:
        for policy in POLICY_IDS:
            for stream in streams:
                c.boundary(f"trace-{policy}-{stream['story']}-{stream['order']}")
                name = f"{policy}/{stream['story']}-{stream['order']}.json"
                path = c.RUN / "traces" / name
                if not path.exists():
                    trace = run_stream(stream, policy, pair_score, retrieval, thresholds, reference)
                    trace["id"] = f"{policy}:{stream['story']}:{stream['order']}"
                    c.unit(path, trace)
                trace = c.read_unit(path)
                c.require((trace["policy"], trace["story"], trace["order"]) == (policy, stream["story"], stream["order"]), "Trace binding changed")
                paths.append(path)
            c.log("policy", policy=policy, completedStreams=len(streams))
    # This is the information boundary: no metric/gold processing before all policies are frozen.
    c.publish(c.RUN / "predictions-complete.json", {"manifestSHA256": c.digest(c.RUN / "manifest.json"),
        "traces": {str(path.relative_to(c.RUN)): c.digest(path) for path in paths},
        "pairScoresSHA256": c.digest(c.RUN / "pair-scores.json"), "streams": len(paths),
        "prefixes": sum(len(c.read_unit(path)["events"]) for path in paths)})
    ledger_runs = []
    for path in paths:
        trace = c.read_unit(path)
        events = []
        for event in trace["events"]:
            command = {key: value for key, value in event.items() if key not in ("decision", "targetAnchors")}
            # The ledger fixture namespace maps localc01 and t:c01 to one UUID.
            # Preserve raw c01 identities in policy traces; rename only this transport projection.
            command["expectedState"] = {"local" + key: value for key, value in event["expectedState"].items()}
            if "source" in command:
                command["source"] = {**command["source"], "id": "local" + command["source"]["id"]}
            if "target" in command:
                command["target"] = "local" + command["target"]
            if event["kind"] in ("capture", "correct"):
                command["assignments"] = event["decision"]["assignedMemberships"]
            events.append(command)
        ledger_runs.append({"id": trace["id"], "events": events})
    c.publish(c.RUN / "ledger-input.json", {"schemaVersion": 1, "runs": ledger_runs})
    return {"streams": len(paths), "predictionsFrozen": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "parity", "score", "pause", "status"))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.phase == "pause":
        return c.log("pause", **c.request_pause())
    if args.phase == "status":
        return c.log("status", **c.space(), manifest=(c.RUN / "manifest.json").exists(),
                     parity=(c.RUN / "parity/complete.json").exists(), predictions=(c.RUN / "predictions-complete.json").exists(),
                     savedEmbeddings=len(list((c.RUN / "embeddings").glob("*.json"))),
                     savedNeuralPairs=len(list((c.RUN / "neural").glob("seed-*/*.json"))))
    try:
        with c.worker(args.resume):
            if args.phase == "prepare":
                result = freeze()
            else:
                c.verify_bindings()
                c.boundary(args.phase)
                if args.phase == "parity":
                    result = parity()
                else:
                    verify_parity_receipt()
                    embeddings()
                    inference()
                    result = traces()
            c.log("saved", **result)
    except c.Paused as pause:
        c.log("paused", boundary=str(pause), safeToClose=True)
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
