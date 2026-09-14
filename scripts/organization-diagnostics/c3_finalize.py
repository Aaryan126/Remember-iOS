#!/usr/bin/env python3
"""Post-run C3 curation/verification, separately bound by the completion receipt."""
import argparse
from pathlib import Path
import os
import subprocess
import sys

import c2_common as c
import c3_run as run
from c3_policy import POLICIES, NEW


def evidence():
    import c2_finalize
    c2_finalize.verify()
    run.verify_predictions()
    metrics = c.read(run.RUN / "metrics-complete.json")
    c.require(metrics["predictionReceiptSHA256"] == c.digest(run.RUN / "predictions-complete.json")
              and metrics["summarySHA256"] == c.digest(run.RUN / "summary.json"), "C3 metric binding changed")
    c.require(len(metrics["files"]) == 288, "Missing fixed metric units")
    for name, sha in metrics["files"].items():
        path = (run.RUN / name).resolve()
        c.require(path.is_relative_to(run.RUN) and c.digest(path) == sha, "Metric unit changed")
        c.read_unit(path)
    before, after = c.read(run.RUN / "resume-proof-before.json"), c.read(run.RUN / "resume-proof-after.json")
    first = run.RUN / before["path"]
    c.require(after["passed"] is True and after["beforeSHA256"] == c.digest(run.RUN / "resume-proof-before.json")
              and before["SHA256"] == after["unitSHA256"] == c.digest(first)
              and before["mtimeNS"] == after["unchangedMtimeNS"] == first.stat().st_mtime_ns, "Resume evidence changed")
    summary = c.read(run.RUN / "summary.json")
    c.require(set(summary["online"]) == set(POLICIES)
              and set(summary["fixed"]["byAnchor"]) == set(POLICIES), "Missing policy/anchor")
    # Pair retrieval ignores lineage memberships. It must not acquire fake replication
    # by counting the identical pair-classification evidence eight times in the report.
    direct = summary["fixed"]["byAnchor"][POLICIES[0]]["pairClassification"]
    c.require(all(row["pairClassification"] == direct for row in summary["fixed"]["byAnchor"].values()),
              "Pair inputs unexpectedly depend on lineage")
    for value in summary["fixed"]["pooled"]["counts"].values():
        c.require(value["contexts"] == 3456 and value["eligibleWrongEvents"] == 2880
                  and value["eligibleMissedEvents"] == 2232, "Unexpected fixed-state coverage")
    return summary, direct


def tests():
    path = run.RUN / "validation/tests.json"
    if path.exists():
        saved = c.read(path)
        c.require(all(row["returnCode"] == 0 for row in saved["checks"]), "Failed saved tests")
        return
    command = [sys.executable, "-m", "unittest", "discover", "-s", "scripts/organization-diagnostics", "-p", "test_*.py"]
    # The full suite itself checks worker locking. Don't hold the shared lock here.
    result = subprocess.run(command, cwd=c.ROOT, capture_output=True, text=True, timeout=60,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    c.require(result.returncode == 0 and "skipped=" not in result.stderr, "Tests failed/skipped: " + result.stderr)
    c.publish(path, {"checks": [{"command": command, "returnCode": result.returncode,
                                "stdout": result.stdout, "stderr": result.stderr}], "runtime": c.runtime()})


def complete():
    if (run.CURATED / "complete.json").exists():
        return verify()
    summary, direct = evidence()
    from c2_metrics import score_trace
    online_metrics = []
    for stream in c.read(c.RUN / "inputs.json")["streams"]:
        trace = c.read_unit(run.online_path(NEW, stream))
        gold = c.read(c.DATA / f"release/gold/{stream['story']}-{stream['order']}.json")
        result = score_trace(trace, gold)
        path = run.RUN / "metrics/online-baseline-corroborated" / f"{stream['story']}-{stream['order']}.json"
        c.publish(path, result)
        online_metrics.append(path)
    from c2_report import summarize
    c.require(summarize([c.read(path) for path in online_metrics]) == summary["online"][NEW]["allOrders"],
              "New baseline prefix metrics disagree with summary")
    c.publish(run.CURATED / "summary.json", {"diagnosticOnly": True,
        "online": {key: value["allOrders"] for key, value in summary["online"].items()},
        "fixed": summary["fixed"], "retrievedPairClassificationUniqueContexts": direct})
    c.publish(run.CURATED / "tests.json", c.read(run.RUN / "validation/tests.json"))
    c.publish(run.CURATED / "resume-proof.json", {"before": c.read(run.RUN / "resume-proof-before.json"),
                                               "after": c.read(run.RUN / "resume-proof-after.json")})
    paths = [run.RUN / name for name in ("manifest.json", "predictions-complete.json", "metrics-complete.json",
                                        "summary.json", "resume-proof-before.json", "resume-proof-after.json", "validation/tests.json")]
    paths += online_metrics + list(run.CURATED.glob("*.md")) + [run.CURATED / name for name in ("summary.json", "tests.json", "resume-proof.json")]
    paths += [Path(__file__).resolve()]
    c.require((run.CURATED / "REPORT.md").exists(), "Report required before completion")
    c.publish(run.CURATED / "complete.json", {"complete": True, "productionQualified": False, "stopForUserReview": True,
        "checkpoint": 3, "parentCompletionSHA256": c.digest(c.CURATED / "complete.json"),
        "sources": {str(path.relative_to(c.ROOT)): c.digest(path) for path in paths},
        "newOnlineStreams": 36, "newOnlinePrefixes": 579, "legacyParityStreams": 252,
        "fixedContexts": 3456, "fixedOwnLineageChecks": 3456, "counterfactualDecisions": 27648,
        "resourceAtCompletion": c.space(), "nextExperimentStarted": False})
    return {"complete": True, "stopForUserReview": True, "completeSHA256": c.digest(run.CURATED / "complete.json")}


def verify():
    receipt = c.read(run.CURATED / "complete.json")
    c.require(receipt["complete"] is True and receipt["productionQualified"] is False
              and receipt["nextExperimentStarted"] is False, "Invalid C3 completion status")
    for name, sha in receipt["sources"].items():
        path = (c.ROOT / name).resolve()
        c.require(path.is_relative_to(c.ROOT) and c.digest(path) == sha, "C3 completed evidence changed: " + name)
    evidence()
    return {"verified": True, "stopForUserReview": True, "completeSHA256": c.digest(run.CURATED / "complete.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("complete", "verify"))
    args = parser.parse_args()
    if args.phase == "complete" and not (run.CURATED / "complete.json").exists():
        tests()
    with run.worker():
        run.boundary("finalize")
        c.log("finalize", **({"complete": complete, "verify": verify}[args.phase]()))
