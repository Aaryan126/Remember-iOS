#!/usr/bin/env python3
"""C4 replay verification and immutable completion publication."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

import c2_common as c
import c3_run
import c4_run as run
from c4_policy import fixed_stream, SCORERS
from c4_metrics import score_stream, summarize


def proof_before():
    path = run.paths_for("proposals")[0]
    c.read_unit(path)
    c.publish(run.RUN / "resume-before.json", {"path": str(path.relative_to(run.RUN)),
        "SHA256": c.digest(path), "mtimeNS": path.stat().st_mtime_ns})
    return {"resumeBaselineSaved": True}


def proof_after():
    before = c.read(run.RUN / "resume-before.json")
    path = run.RUN / before["path"]
    c.require(c.digest(path) == before["SHA256"] and path.stat().st_mtime_ns == before["mtimeNS"], "Resume changed completed unit")
    c.require((run.RUN / "predictions-complete.json").exists(), "Resume has not finished predictions")
    c.publish(run.RUN / "resume-after.json", {"passed": True, "beforeSHA256": c.digest(run.RUN / "resume-before.json"),
        "SHA256": c.digest(path), "mtimeNS": path.stat().st_mtime_ns})
    return {"resumeVerified": True}


def tests():
    command = [sys.executable, "-m", "unittest", "discover", "-s", "scripts/organization-diagnostics", "-p", "test_*.py"]
    result = subprocess.run(command, cwd=c.ROOT, capture_output=True, text=True, timeout=60,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    c.require(result.returncode == 0 and "skipped=" not in result.stderr, "Failed/skipped tests: " + result.stderr)
    c.publish(run.RUN / "validation/tests.json", {"command": command, "returnCode": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr, "runtime": c.runtime()})
    return {"testsPassed": True, "output": result.stderr}


def audit():
    import c3_finalize
    c3_finalize.verify()
    run.verify_metrics()
    pairs, _ = c3_run.callbacks()
    thresholds = run.verify_manifest()["thresholds"]
    units = []
    for source, metric in zip(run.paths_for("proposals"), run.paths_for("metrics")):
        run.boundary("audit:" + source.name)
        saved = c.read_unit(source)
        trace = c.read_unit(c3_run.online_path(saved["anchor"], saved))
        c.require(saved == fixed_stream(trace, pairs, thresholds), "Proposal replay mismatch")
        gold = c.read(c.DATA / f"release/gold/{saved['story']}-{saved['order']}.json")
        result = score_stream(saved, gold)
        c.require(c.read_unit(metric) == result, "Metric replay mismatch")
        units.append(result)
    c.require(summarize(units) == c.read(run.RUN / "summary.json"), "Summary reconstruction mismatch")
    summary = c.read(run.RUN / "summary.json")
    c.require(all(summary["pooled"][s]["allPrefixes"]["counts"]["contexts"] == 2316 for s in SCORERS), "Context coverage mismatch")
    before, after = c.read(run.RUN / "resume-before.json"), c.read(run.RUN / "resume-after.json")
    first = run.RUN / before["path"]
    c.require(after["passed"] is True and after["beforeSHA256"] == c.digest(run.RUN / "resume-before.json")
              and before["SHA256"] == after["SHA256"] == c.digest(first)
              and before["mtimeNS"] == after["mtimeNS"] == first.stat().st_mtime_ns, "Resume proof changed")
    result = {"passed": True, "reconstructedProposalUnits": 144, "reconstructedMetricUnits": 144,
              "scorerContexts": 9264, "parentC3Verified": True, "summaryReproduced": True}
    c.publish(run.RUN / "validation/replay-audit.json", result)
    return result


def complete():
    run.verify_metrics()
    checks = c.read(run.RUN / "validation/tests.json")
    replay = c.read(run.RUN / "validation/replay-audit.json")
    c.require(checks["returnCode"] == 0 and checks["runtime"] == c.runtime() and replay["passed"] is True,
              "Validation missing or failed")
    c.require((run.CURATED / "REPORT.md").exists(), "Report is required")
    c.publish(run.CURATED / "summary.json", c.read(run.RUN / "summary.json"))
    paths = [run.RUN / name for name in ("manifest.json", "predictions-complete.json", "metrics-complete.json", "summary.json",
        "resume-before.json", "resume-after.json", "validation/tests.json", "validation/replay-audit.json")]
    paths += [run.CURATED / "REPORT.md", run.CURATED / "summary.json", Path(__file__).resolve()]
    c.publish(run.CURATED / "complete.json", {"checkpoint": 4, "complete": True, "productionQualified": False,
        "stopForUserReview": True, "nextExperimentStarted": False,
        "parentCompletionSHA256": c.digest(c3_run.CURATED / "complete.json"),
        "sources": {str(p.relative_to(c.ROOT)): c.digest(p) for p in paths}, "resource": c.space()})
    return {"complete": True, "stopForUserReview": True, "completeSHA256": c.digest(run.CURATED / "complete.json")}


def verify():
    receipt = c.read(run.CURATED / "complete.json")
    c.require(receipt["complete"] is True and receipt["productionQualified"] is False and
              receipt["nextExperimentStarted"] is False and receipt["stopForUserReview"] is True, "Invalid completion")
    c.require(receipt["parentCompletionSHA256"] == c.digest(c3_run.CURATED / "complete.json"), "Parent completion changed")
    run.checked_files(receipt["sources"], c.ROOT)
    run.verify_metrics()
    import c3_finalize
    c3_finalize.verify()
    return {"verified": True, "stopForUserReview": True, "completeSHA256": c.digest(run.CURATED / "complete.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("proof-before", "proof-after", "tests", "audit", "complete", "verify"))
    args = parser.parse_args()
    if args.phase == "tests":
        c.log("tests", **tests())  # Tests exercise the shared worker lock themselves.
    else:
        try:
            with run.worker():
                run.boundary(args.phase)
                c.log("finalize", **{"proof-before": proof_before, "proof-after": proof_after, "audit": audit,
                                     "complete": complete, "verify": verify}[args.phase]())
        except c.Paused as stopped:
            c.log("paused", boundary=str(stopped), safeToClose=True)
            raise SystemExit(75)
