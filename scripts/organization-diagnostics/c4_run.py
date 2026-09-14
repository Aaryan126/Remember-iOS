#!/usr/bin/env python3
"""C4 isolated checkpoint runner. Pause at immutable stream boundaries."""
import argparse
from contextlib import contextmanager
from pathlib import Path
import time

import c2_common as c
import c3_run
from c4_policy import ANCHORS, fixed_stream

RUN = c.DATA / "runs/c4-01"
CURATED = c.DATA / "c4"


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
            c.publish(RUN / f"resumptions/{time.time_ns()}.json", {"requestSHA256": c.digest(marker)})
            marker.unlink()  # Only this checkpoint's request, after acquiring exclusive lock.
        yield


def boundary(phase):
    c.space(planned=4 * 1024**2)
    if c._pause_signal or (RUN / "control/pause-requested.json").exists() or (c.RUN / "control/pause-requested.json").exists():
        c.publish(RUN / f"pauses/{time.time_ns()}.json", {"phase": phase, "savedBoundary": True})
        raise c.Paused(phase)


def checked_files(files, base):
    for relative, sha in files.items():
        path = (base / relative).resolve()
        c.require(path.is_relative_to(base) and c.digest(path) == sha, "C4 binding changed: " + relative)


def verify_manifest():
    manifest = c.read(RUN / "manifest.json")
    c.require(manifest["runtime"] == c.runtime(), "C4 runtime changed")
    checked_files(manifest["sources"], c.ROOT)
    return manifest


def prepare():
    if (RUN / "manifest.json").exists():
        verify_manifest()
        return {"prepared": True}
    import c3_finalize
    c3_finalize.verify()
    paths = list(Path(__file__).parent.glob("c4_*.py")) + list(Path(__file__).parent.glob("test_c4_*.py"))
    paths += [c.DATA / "C4_PROTOCOL.md", c3_run.CURATED / "complete.json"]
    for receipt in (c3_run.RUN / "manifest.json", c3_run.CURATED / "complete.json"):
        paths += [receipt] + [c.ROOT / name for name in c.read(receipt)["sources"]]
    for stream in c.read(c.RUN / "inputs.json")["streams"]:
        paths += [c3_run.online_path(anchor, stream) for anchor in ANCHORS]
    c.publish(RUN / "manifest.json", {"schemaVersion": 1, "runtime": c.runtime(), "anchors": list(ANCHORS),
        "thresholds": c.read(c.RUN / "manifest.json")["thresholds"], "streamUnits": 144, "scorerContexts": 9264,
        "sources": {str(p.relative_to(c.ROOT)): c.digest(p) for p in sorted(set(paths))}, "resource": c.space()})
    return {"prepared": True}


def paths_for(phase):
    return [RUN / phase / anchor / f"{s['story']}-{s['order']}.json" for anchor in ANCHORS
            for s in c.read(c.RUN / "inputs.json")["streams"]]


def predict(max_units=None):
    manifest = verify_manifest()
    pairs, _ = c3_run.callbacks()
    done = 0
    for anchor in ANCHORS:
        for stream in c.read(c.RUN / "inputs.json")["streams"]:
            path = RUN / "proposals" / anchor / f"{stream['story']}-{stream['order']}.json"
            boundary("predict:" + path.name)
            if path.exists():
                c.read_unit(path)
                continue
            trace = c.read_unit(c3_run.online_path(anchor, stream))
            value = fixed_stream(trace, pairs, manifest["thresholds"])
            c.unit(path, value)
            done += 1
            if max_units and done >= max_units:
                c.publish(RUN / f"pauses/{time.time_ns()}-bounded.json", {"savedUnits": done, "phase": "predict"})
                raise c.Paused("bounded-unit-stop")
        c.log("proposal-anchor", anchor=anchor, savedStreams=36)
    files = paths_for("proposals")
    contexts = sum(len(c.read_unit(p)["prefixes"]) * 4 for p in files)
    c.require(contexts == manifest["scorerContexts"], "C4 context coverage mismatch")
    c.publish(RUN / "predictions-complete.json", {"manifestSHA256": c.digest(RUN / "manifest.json"),
        "scorerContexts": contexts, "files": {str(p.relative_to(RUN)): c.digest(p) for p in files}})
    return {"predictionsFrozen": True, "scorerContexts": contexts}


def verify_predictions():
    verify_manifest()
    receipt = c.read(RUN / "predictions-complete.json")
    c.require(receipt["manifestSHA256"] == c.digest(RUN / "manifest.json"), "C4 manifest receipt mismatch")
    c.require(set(receipt["files"]) == {str(p.relative_to(RUN)) for p in paths_for("proposals")}, "C4 prediction inventory mismatch")
    checked_files(receipt["files"], RUN)
    return receipt


def evaluate():
    verify_predictions()
    from c4_metrics import score_stream, summarize
    units = []
    for source, path in zip(paths_for("proposals"), paths_for("metrics")):
        boundary("evaluate:" + path.name)
        if not path.exists():
            value = c.read_unit(source)
            gold = c.read(c.DATA / f"release/gold/{value['story']}-{value['order']}.json")
            result = score_stream(value, gold)
            # Exact final no-repair parity against C3, independent of repaired outcomes.
            from c2_metrics import score_trace
            trace = c.read_unit(c3_run.online_path(value["anchor"], value))
            expected = score_trace(trace, gold)["final"]
            c.require(result["prefixes"][-1]["before"] == {k: expected[k] for k in ("pairs", "structure")},
                      "No-repair anchor parity failed")
            c.unit(path, result)
        units.append(c.read_unit(path))
    c.publish(RUN / "summary.json", summarize(units))
    c.publish(RUN / "metrics-complete.json", {"predictionReceiptSHA256": c.digest(RUN / "predictions-complete.json"),
        "summarySHA256": c.digest(RUN / "summary.json"), "files": {str(p.relative_to(RUN)): c.digest(p) for p in paths_for("metrics")}})
    return {"metricsSaved": True, "noRepairFinalParityChecks": len(units)}


def verify_metrics():
    verify_predictions()
    receipt = c.read(RUN / "metrics-complete.json")
    c.require(receipt["predictionReceiptSHA256"] == c.digest(RUN / "predictions-complete.json") and
              receipt["summarySHA256"] == c.digest(RUN / "summary.json"), "C4 metric receipt mismatch")
    c.require(set(receipt["files"]) == {str(p.relative_to(RUN)) for p in paths_for("metrics")}, "C4 metric inventory mismatch")
    checked_files(receipt["files"], RUN)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "predict", "evaluate", "pause", "status"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-units", type=int)
    args = parser.parse_args()
    c.require(args.max_units is None or args.max_units > 0, "max-units must be positive")
    if args.phase == "pause":
        c.log("pause", **pause())
        return 0
    if args.phase == "status":
        c.log("status", **c.space(), predictionUnits=sum(p.exists() for p in paths_for("proposals")),
              metricUnits=sum(p.exists() for p in paths_for("metrics")), complete=(CURATED / "complete.json").exists())
        return 0
    try:
        with worker(args.resume):
            boundary(args.phase)
            c.log("saved", **{"prepare": prepare, "predict": lambda: predict(args.max_units), "evaluate": evaluate}[args.phase]())
    except c.Paused as error:
        c.log("paused", boundary=str(error), safeToClose=True)
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
