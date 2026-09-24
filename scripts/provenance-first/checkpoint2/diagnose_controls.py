#!/usr/bin/env python3
"""Explain a failed preflight using historical controls only; never authorizes a run.

This does not relax the preflight or inspect provenance benchmark predictions.
Every input is one of the already-exposed P2 numerical control pairs.
"""
import argparse
import time
import common as c
import preflight


def diagnose():
    import numpy as np
    Features, Neural, texts, old_embeddings, pairs, parent = preflight.inputs()
    folder = c.WORK / "runs/control-diagnostic"
    c.publish(folder / "binding.json", {"preflightBindingSHA256": parent,
              "scriptSHA256": c.digest(__file__), "controlsOnly": True,
              "canAuthorizeBenchmark": False})
    binding = c.digest(folder / "binding.json")
    current, vector_rows = {}, []
    for key, text in sorted(texts.items()):
        c.boundary()
        path = folder / f"embeddings/{key}.json"
        if not path.exists():
            prior = c.WORK / f"runs/preflight/embeddings/{key}.json"
            value = c.read_unit(prior, parent) if prior.exists() else preflight.embedding(key, text)
            c.unit(path, value, binding)
        current[key] = c.read_unit(path, binding)
        old = old_embeddings[key]
        c.require(old["textSHA256"] == c.text_hash(text), "historical embedding text mismatch")
        channels = {}
        for channel in ("contextual", "sentence"):
            a, b = np.array(current[key][channel]), np.array(old[channel])
            channels[channel] = {"maxComponentDelta": float(np.max(np.abs(a-b))),
                                 "cosine": float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))}
        vector_rows.append({"id": key, "channels": channels})
        c.log(phase="diagnostic-embeddings", complete=len(current), total=len(texts))
    fresh_features, saved_features = Features(texts, current), Features(texts, old_embeddings)
    old_feature_rows = {r["id"]: r["features"] for r in c.read(c.P2 / "features/evaluation.json")["rows"]}
    expected = {r["id"]: r for r in c.read(c.P2 / "evaluation/seed-29.json")["predictions"]["hybrid"]}
    missing = [p for p in pairs if not (folder / f"neural/{p['id']}.json").exists()]
    if missing:
        c.boundary()
        with Neural("29") as model:
            for offset in range(0, len(missing), 8):
                c.boundary()
                batch = missing[offset:offset+8]
                predictions = model.predict([(texts[p["first"]], texts[p["second"]]) for p in batch])
                for p, value in zip(batch, predictions):
                    c.unit(folder / f"neural/{p['id']}.json", {"id": p["id"], **value}, binding)
                c.log(phase="diagnostic-neural", complete=offset+len(batch), total=len(missing))
    results = []
    for p in pairs:
        old = c.read(c.P2 / f"predictions/seed-29-final/evaluation/{p['id']}.json")
        now = c.read_unit(folder / f"neural/{p['id']}.json", binding)
        c.require(now["weightsSHA256"] == old["weightsSHA256"], "neural weights differ")
        a, b = saved_features.values(p["first"], p["second"]), fresh_features.values(p["first"], p["second"])
        pure_delta = float(np.max(np.abs(np.asarray(a) - old_feature_rows[p["id"]])))
        c.require(pure_delta <= 1e-12, "feature implementation changed")
        score = fresh_features.scores(b, {"29": now["score"]})["hybrid"]["29"]
        old_score = expected[p["id"]]["score"]
        results.append({"id": p["id"], "savedFeatureDelta": pure_delta,
                        "freshFeatureDelta": float(np.max(np.abs(np.asarray(a)-b))),
                        "directionalDelta": max(abs(x-y) for x, y in zip(now["directions"], old["directions"])),
                        "combinedDelta": abs(score-old_score), "currentScore": score, "historicalScore": old_score,
                        "decisionChanged": (score >= 0.9804276486193665) != (old_score >= 0.9804276486193665)})
    report = {"status": "diagnostic-only-preflight-remains-failed", "bindingSHA256": binding,
              "embeddingSources": vector_rows, "pairs": results,
              "decisionChanges": sum(r["decisionChanged"] for r in results),
              "maximumCombinedDelta": max(r["combinedDelta"] for r in results),
              "maximumDirectionalDelta": max(r["directionalDelta"] for r in results),
              "maximumEmbeddingDelta": max(v["maxComponentDelta"] for r in vector_rows for v in r["channels"].values()),
              "benchmarkQualityMeasured": False, "phoneTested": False, "automaticApproval": False}
    c.publish(c.WORK / "control-diagnostic.json", report)
    return {key: value for key, value in report.items() if key not in ("pairs", "embeddingSources")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        with c.worker(resume=args.resume):
            c.log(result=diagnose())
    except c.Paused as error:
        c.log(status="paused", reason=str(error), workerStopped=True)
    except Exception as error:
        c.pf1.atomic(c.WORK / f"runs/failures/{time.time_ns()}.json",
                     {"type": type(error).__name__, "message": str(error), "phase": "control-diagnostic"})
        c.log(status="stopped", error=str(error))
        raise
