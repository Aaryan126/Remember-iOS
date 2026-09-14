#!/usr/bin/env python3
"""C6 numerical replay audit and completion publication."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

import c2_common as c
import c5_run
import c6_run as run
from c5_metrics import evaluate


def proof_before():
    first = sorted((run.RUN / "embeddings").glob("*.json"))[0]
    c.read_unit(first)
    c.publish(run.RUN / "resume-before.json", {"path": str(first.relative_to(run.RUN)), "SHA256": c.digest(first), "mtimeNS": first.stat().st_mtime_ns})
    return {"resumeBaselineSaved": True}


def proof_after():
    run.verify_predictions()
    before = c.read(run.RUN / "resume-before.json")
    first = run.RUN / before["path"]
    c.require(c.digest(first) == before["SHA256"] and first.stat().st_mtime_ns == before["mtimeNS"], "Saved embedding changed on resume")
    c.publish(run.RUN / "resume-after.json", {"passed": True, "beforeSHA256": c.digest(run.RUN / "resume-before.json"),
        "SHA256": c.digest(first), "mtimeNS": first.stat().st_mtime_ns})
    return {"resumeVerified": True}


def tests():
    command = [sys.executable, "-m", "unittest", "discover", "-s", "scripts/organization-diagnostics", "-p", "test_*.py"]
    result = subprocess.run(command, cwd=c.ROOT, capture_output=True, text=True, timeout=60,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    c.require(result.returncode == 0 and "skipped=" not in result.stderr, "Failed/skipped tests: " + result.stderr)
    c.publish(run.RUN / "validation/tests.json", {"command": command, "returnCode": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr, "runtime": c.runtime()})
    return {"passed": True, "output": result.stderr}


def evidence():
    c5_run.verify()
    run.verify_predictions()
    metrics = c.read(run.RUN / "metrics-complete.json")
    c.require(metrics["predictionReceiptSHA256"] == c.digest(run.RUN / "predictions-complete.json") and
              metrics["summarySHA256"] == c.digest(run.RUN / "summary.json"), "Metric freeze changed")
    c.require(set(metrics["files"]) == {f"errors/{name}.json" for name in run.CANDIDATES}, "Missing error files")
    run.check_files(metrics["files"], run.RUN)
    before, after = c.read(run.RUN / "resume-before.json"), c.read(run.RUN / "resume-after.json")
    first = run.RUN / before["path"]
    c.require(after["passed"] is True and after["beforeSHA256"] == c.digest(run.RUN / "resume-before.json") and
              before["SHA256"] == after["SHA256"] == c.digest(first) and
              before["mtimeNS"] == after["mtimeNS"] == first.stat().st_mtime_ns, "Resume proof changed")


def audit():
    evidence()
    from c2_models import Features
    data = c.read(run.RUN / "catalogue.json")
    feature = Features(data["texts"], {k: c.read_unit(run.RUN / f"embeddings/{k}.json") for k in data["texts"]})
    values = {key: feature.values(p["first"], p["second"]) for key, p in data["pairs"].items()}
    c.require(values == c.read(run.RUN / "features.json"), "Feature replay mismatch")
    scores = {key: feature.scores(values[key], {seed: c.read_unit(run.RUN / f"neural/{seed}/{key}.json")["score"] for seed in run.SCORERS[1:]})
              for key in data["pairs"]}
    c.require(scores == c.read(run.RUN / "pair-scores.json"), "Probability reconstruction mismatch")
    predictions = run.assemble(scores, c.read(run.RUN / "manifest.json")["thresholds"])
    summary = c.read(run.RUN / "summary.json")
    for candidate, rows in predictions.items():
        run.boundary("audit:" + candidate)
        c.require(rows == c.read_unit(run.RUN / f"predictions/{candidate}.json"), "Prediction replay mismatch")
        for kind, path in (("adjudicated", run.RUN / "adjudicated-gold.json"), ("original", c5_run.RUN / "release/gold.json")):
            c.require(evaluate(run.packets(), c.read(path)["labels"], rows) == summary[kind][candidate], "Metric replay mismatch")
    c.publish(run.RUN / "validation/replay.json", {"passed": True, "reconstructedPredictions": 1440, "summaryVariants": 18,
        "featurePairs": len(values), "neuralInferenceRepeated": False})
    return {"replayPassed": True, "predictions": 1440}


def complete():
    evidence()
    checks = c.read(run.RUN / "validation/tests.json")
    c.require(checks["returnCode"] == 0 and checks["runtime"] == c.runtime() and c.read(run.RUN / "validation/replay.json")["passed"], "Validation missing")
    c.require((run.CURATED / "REPORT.md").exists(), "Report required")
    c.publish(run.CURATED / "summary.json", c.read(run.RUN / "summary.json"))
    paths = [run.RUN / name for name in ("manifest.json", "review-complete.json", "predictions-complete.json", "metrics-complete.json",
        "resume-before.json", "resume-after.json", "validation/tests.json", "validation/replay.json")]
    paths += [run.CURATED / "REPORT.md", run.CURATED / "summary.json"]
    c.publish(run.CURATED / "complete.json", {"checkpoint": 6, "complete": True, "productionQualified": False,
        "stopForUserReview": True, "nextExperimentStarted": False, "parentCompletionSHA256": c.digest(c5_run.CURATED / "complete.json"),
        "sources": {str(p.relative_to(c.ROOT)): c.digest(p) for p in paths}, "resource": c.space()})
    return {"complete": True, "stopForUserReview": True, "completeSHA256": c.digest(run.CURATED / "complete.json")}


def verify():
    record = c.read(run.CURATED / "complete.json")
    c.require(record["complete"] is True and record["productionQualified"] is False and record["stopForUserReview"] is True
              and record["nextExperimentStarted"] is False and record["parentCompletionSHA256"] == c.digest(c5_run.CURATED / "complete.json"),
              "Invalid completion")
    run.check_files(record["sources"], c.ROOT)
    evidence()
    return {"verified": True, "completeSHA256": c.digest(run.CURATED / "complete.json"), "stopForUserReview": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("proof-before", "proof-after", "tests", "audit", "complete", "verify"))
    args = parser.parse_args()
    if args.phase == "tests":
        c.log("tests", **tests())
    else:
        try:
            with run.worker():
                run.boundary(args.phase)
                c.log("finalize", **{"proof-before": proof_before, "proof-after": proof_after, "audit": audit,
                                     "complete": complete, "verify": verify}[args.phase]())
        except c.Paused as stopped:
            c.log("paused", boundary=str(stopped), safeToClose=True)
            raise SystemExit(75)
