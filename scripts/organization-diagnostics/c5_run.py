#!/usr/bin/env python3
"""C5 preparation only. No training, model execution or production access."""
import argparse
from collections import Counter
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys
import time

import c2_common as c
from c5_data import validate_authoring, compile_family, validate_projection, novelty

RUN = c.DATA / "runs/c5-01"
CURATED = c.DATA / "c5"
AUTHORING = CURATED / "authored-families.json"


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
            marker.unlink()  # Only our recorded request, while holding the shared lock.
        yield


def boundary(phase):
    c.space(planned=2 * 1024**2)
    if c._pause_signal or (RUN / "control/pause-requested.json").exists() or (c.RUN / "control/pause-requested.json").exists():
        c.publish(RUN / f"pauses/{time.time_ns()}.json", {"phase": phase, "savedBoundary": True})
        raise c.Paused(phase)


def check_files(files, base):
    for name, sha in files.items():
        path = (base / name).resolve()
        c.require(path.is_relative_to(base) and c.digest(path) == sha, "C5 binding changed: " + name)


def verify_manifest():
    value = c.read(RUN / "manifest.json")
    c.require(value["runtime"] == c.runtime(), "C5 runtime changed")
    check_files(value["sources"], c.ROOT)
    return value


def freeze():
    if (RUN / "manifest.json").exists():
        verify_manifest()
        return {"frozen": True}
    import c4_finalize
    c4_finalize.verify()
    validate_authoring(c.read(AUTHORING))
    files = [AUTHORING, c.DATA / "C5_PROTOCOL.md", CURATED / "AUTHOR_REVIEW.md", c.DATA / "c4/complete.json",
             c.RUN / "catalogue.json"]
    files += list(Path(__file__).parent.glob("c5_*.py")) + list(Path(__file__).parent.glob("test_c5*.py"))
    # Reused utility closure is bound directly as well as through the C4 parent chain.
    files += [Path(__file__).parent / name for name in ("c2_common.py", "checkpoint.py")]
    c.publish(RUN / "manifest.json", {"schemaVersion": 1, "runtime": c.runtime(), "families": 8, "episodes": 48,
        "queries": 80, "packets": 160, "trainingAllowed": False, "modelScoringAllowed": False,
        "independentReviewPending": True, "sources": {str(p.relative_to(c.ROOT)): c.digest(p) for p in sorted(set(files))},
        "resource": c.space()})
    return {"frozen": True}


def prepare(max_units=None):
    verify_manifest()
    document = validate_authoring(c.read(AUTHORING))
    done, units = 0, []
    for family in document["families"]:
        boundary("family:" + family["id"])
        path = RUN / "families" / (family["id"] + ".json")
        expected = compile_family(family)
        if path.exists():
            c.require(c.read_unit(path) == expected, "Existing family differs from frozen projection")
        else:
            c.unit(path, expected)
            done += 1
            if max_units and done >= max_units:
                c.publish(RUN / f"pauses/{time.time_ns()}-bounded.json", {"savedFamilies": done, "phase": "prepare"})
                raise c.Paused("bounded-family-stop")
        units.append(c.read_unit(path))
    validate_projection(units)
    packets = [p for unit in units for p in unit["packets"]]
    gold = [row for unit in units for row in unit["gold"]]
    c.publish(RUN / "release/inputs.json", {"schemaVersion": 1, "packets": packets})
    c.publish(RUN / "release/gold.json", {"schemaVersion": 1, "labels": gold})
    c.publish(RUN / "release/splits.json", {partition: [p['queryID'] for p in gold if p['partition'] == partition]
        for partition in ("discovery", "diagnostic")})
    c.publish(RUN / "validation/novelty.json", novelty(document, list(c.read(c.RUN / "catalogue.json")["texts"].values())))
    counts = Counter((p["view"], row["verdict"]) for p, row in zip(packets, gold))
    c.publish(RUN / "summary.json", {"families": len(units), "episodes": 48, "queries": 80, "packets": len(packets),
        "labelCounts": {view: {label: counts[view, label] for label in ("same_project", "separate_projects", "abstain")}
                        for view in ("pair", "context")}, "modelPredictions": 0, "modelAccuracyMeasured": False,
        "independentReviewPending": True, "semanticQualification": False,
        "sourceTexts": 56, "familyPartitions": {p: [f["id"] for f in document["families"] if f["partition"] == p]
                                              for p in ("discovery", "diagnostic")}})
    paths = list((RUN / "families").glob("*.json")) + list((RUN / "release").glob("*.json"))
    paths += [RUN / "summary.json", RUN / "validation/novelty.json"]
    c.publish(RUN / "prepared.json", {"manifestSHA256": c.digest(RUN / "manifest.json"),
        "files": {str(p.relative_to(RUN)): c.digest(p) for p in sorted(paths)}, "readyForModelScoring": False})
    return {"prepared": True, "packets": len(packets), "independentReviewPending": True}


def verify_prepared():
    verify_manifest()
    receipt = c.read(RUN / "prepared.json")
    c.require(receipt["manifestSHA256"] == c.digest(RUN / "manifest.json") and receipt["readyForModelScoring"] is False,
              "Invalid preparation receipt")
    expected = {f"families/f{i:02d}.json" for i in range(1, 9)} | {"release/inputs.json", "release/gold.json",
        "release/splits.json", "summary.json", "validation/novelty.json"}
    c.require(set(receipt["files"]) == expected, "Release inventory mismatch")
    check_files(receipt["files"], RUN)
    units = [compile_family(f) for f in validate_authoring(c.read(AUTHORING))["families"]]
    validate_projection(units)
    for unit in units:
        c.require(c.read_unit(RUN / f"families/{unit['family']}.json") == unit, "Family reconstruction mismatch")
    c.require(c.read(RUN / "release/inputs.json")["packets"] == [p for u in units for p in u["packets"]], "Packet reconstruction mismatch")
    c.require(c.read(RUN / "release/gold.json")["labels"] == [g for u in units for g in u["gold"]], "Gold reconstruction mismatch")
    return {"preparedVerified": True, "packetsReconstructed": 160}


def proof_before():
    path = RUN / "families/f01.json"
    c.read_unit(path)
    c.publish(RUN / "resume-before.json", {"path": "families/f01.json", "SHA256": c.digest(path), "mtimeNS": path.stat().st_mtime_ns})
    return {"resumeBaselineSaved": True}


def proof_after():
    verify_prepared()
    before = c.read(RUN / "resume-before.json")
    path = RUN / before["path"]
    c.require(before["SHA256"] == c.digest(path) and before["mtimeNS"] == path.stat().st_mtime_ns, "Resume changed saved family")
    c.publish(RUN / "resume-after.json", {"passed": True, "beforeSHA256": c.digest(RUN / "resume-before.json"),
        "SHA256": c.digest(path), "mtimeNS": path.stat().st_mtime_ns})
    return {"resumeVerified": True}


def tests():
    command = [sys.executable, "-m", "unittest", "discover", "-s", "scripts/organization-diagnostics", "-p", "test_*.py"]
    result = subprocess.run(command, cwd=c.ROOT, capture_output=True, text=True, timeout=60,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    c.require(result.returncode == 0 and "skipped=" not in result.stderr, "Failed/skipped tests: " + result.stderr)
    c.publish(RUN / "validation/tests.json", {"command": command, "returnCode": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr, "runtime": c.runtime()})
    return {"passed": True, "output": result.stderr}


def evidence():
    import c4_finalize
    c4_finalize.verify()
    verify_prepared()
    before, after = c.read(RUN / "resume-before.json"), c.read(RUN / "resume-after.json")
    first = RUN / before["path"]
    c.require(after["passed"] is True and after["beforeSHA256"] == c.digest(RUN / "resume-before.json")
              and before["SHA256"] == after["SHA256"] == c.digest(first)
              and before["mtimeNS"] == after["mtimeNS"] == first.stat().st_mtime_ns, "Invalid resume proof")
    checks = c.read(RUN / "validation/tests.json")
    c.require(checks["returnCode"] == 0 and checks["runtime"] == c.runtime(), "Missing/failed tests")


def complete():
    evidence()
    c.require((CURATED / "REPORT.md").exists(), "Report required before completion")
    c.publish(CURATED / "summary.json", c.read(RUN / "summary.json"))
    paths = [RUN / name for name in ("manifest.json", "prepared.json", "resume-before.json", "resume-after.json", "validation/tests.json")]
    paths += [CURATED / "summary.json", CURATED / "REPORT.md"]
    c.publish(CURATED / "complete.json", {"checkpoint": 5, "complete": True, "stopForUserReview": True,
        "readyForModelScoring": False, "independentReviewPending": True, "modelPredictions": 0,
        "productionQualified": False, "nextExperimentStarted": False,
        "parentCompletionSHA256": c.digest(c.DATA / "c4/complete.json"),
        "sources": {str(p.relative_to(c.ROOT)): c.digest(p) for p in paths}, "resource": c.space()})
    return {"complete": True, "stopForUserReview": True, "completeSHA256": c.digest(CURATED / "complete.json")}


def verify():
    receipt = c.read(CURATED / "complete.json")
    c.require(receipt["complete"] is True and receipt["readyForModelScoring"] is False and receipt["modelPredictions"] == 0
              and receipt["independentReviewPending"] is True and receipt["productionQualified"] is False
              and receipt["nextExperimentStarted"] is False and receipt["stopForUserReview"] is True, "Invalid completion")
    c.require(receipt["parentCompletionSHA256"] == c.digest(c.DATA / "c4/complete.json"), "Parent changed")
    check_files(receipt["sources"], c.ROOT)
    evidence()
    return {"verified": True, "completeSHA256": c.digest(CURATED / "complete.json"), "stopForUserReview": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "prepare", "proof-before", "proof-after", "tests", "complete", "verify", "pause", "status"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-units", type=int)
    args = parser.parse_args()
    c.require(args.max_units is None or args.max_units > 0, "max-units must be positive")
    if args.phase == "pause":
        c.log("pause", **pause())
        return 0
    if args.phase == "status":
        c.log("status", **c.space(), families=len(list((RUN / "families").glob("*.json"))),
              prepared=(RUN / "prepared.json").exists(), complete=(CURATED / "complete.json").exists())
        return 0
    if args.phase == "tests":
        c.log("tests", **tests())  # Tests acquire the worker lock in their own fixtures.
        return 0
    try:
        with worker(args.resume):
            boundary(args.phase)
            result = {"freeze": freeze, "prepare": lambda: prepare(args.max_units), "proof-before": proof_before,
                      "proof-after": proof_after, "complete": complete, "verify": verify}[args.phase]()
            c.log("saved", **result)
    except c.Paused as stopped:
        c.log("paused", boundary=str(stopped), safeToClose=True)
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
