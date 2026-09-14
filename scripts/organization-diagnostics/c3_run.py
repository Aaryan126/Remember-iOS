#!/usr/bin/env python3
"""Cached-score C3 experiment; no inference, training or production access."""
import argparse
from contextlib import contextmanager
import fcntl
from pathlib import Path
import time

import c2_common as c
from c3_policy import POLICIES, NEW, run_stream, fixed_trace

RUN = c.DATA / "runs/c3-01"
CURATED = c.DATA / "c3"


def pause():
    path = RUN / "control/pause-requested.json"
    if not path.exists():
        c.publish(path, {"requestedAtUnix": time.time()})
    return {"pauseRequested": True, "safeToClose": False}


@contextmanager
def worker(resume=False):
    RUN.mkdir(parents=True, exist_ok=True)
    with c.worker(), (RUN / "worker.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another C3 worker is active") from error
        marker = RUN / "control/pause-requested.json"
        if resume and marker.exists():
            c.publish(RUN / f"resumptions/{time.time_ns()}.json", {"requestSHA256": c.digest(marker)})
            marker.unlink()  # Only C3's own acknowledged request, not C2 artifacts.
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def boundary(phase):
    c.space(planned=2 * 1024**2)
    if c._pause_signal or (RUN / "control/pause-requested.json").exists() or (c.RUN / "control/pause-requested.json").exists():
        c.publish(RUN / f"pauses/{time.time_ns()}.json", {"phase": phase, "savedBoundary": True})
        raise c.Paused(phase)


def verify_manifest():
    manifest = c.read(RUN / "manifest.json")
    c.require(manifest["runtime"] == c.runtime(), "C3 runtime changed")
    for relative, sha in manifest["sources"].items():
        path = (c.ROOT / relative).resolve()
        c.require(path.is_relative_to(c.ROOT) and c.digest(path) == sha, "C3 binding changed: " + relative)
    return manifest


def prepare():
    if (RUN / "manifest.json").exists():
        verify_manifest()
        return {"prepared": True}
    import c2_finalize
    c2_finalize.verify()
    files = list(Path(__file__).parent.glob("c3_*.py")) + list(Path(__file__).parent.glob("test_c3_*.py"))
    files += [c.DATA / "C3_PROTOCOL.md", c.CURATED / "complete.json", c.RUN / "manifest.json",
              c.RUN / "inputs.json", c.RUN / "pair-scores.json", c.RUN / "predictions-complete.json",
              c.RUN / "metrics-summary.json", c.RUN / "metrics-complete.json"]
    # Bind the complete reused C2 source closure and every input/gold/trace used here.
    files += [c.ROOT / path for path in c.read(c.RUN / "manifest.json")["sources"]]
    files += [c.RUN / path for path in c.read(c.RUN / "predictions-complete.json")["traces"]]
    c.publish(RUN / "manifest.json", {"schemaVersion": 1, "runtime": c.runtime(), "policies": list(POLICIES),
        "thresholds": c.read(c.RUN / "manifest.json")["thresholds"],
        "sources": {str(path.relative_to(c.ROOT)): c.digest(path) for path in sorted(set(files))},
        "fixedAnchorPolicies": list(POLICIES), "newOnlineStreams": 36, "fixedContexts": 3456,
        "counterfactualDecisions": 27648, "diagnosticOnly": True, "resource": c.space()})
    return {"prepared": True}


def callbacks():
    cache = c.read(c.RUN / "pair-scores.json")
    def pairs(a, b):
        value = cache[c.pair_key(a["text"], b["text"])]
        return {key: value[key] for key in ("baseline", "hybrid")}
    def retrieval(a, b):
        values = cache[c.pair_key(a["text"], b["text"])]["features"]
        return {"contextual": values[0], "lexical": values[2]}
    return pairs, retrieval


def online_path(policy, stream):
    root = RUN / "online" if policy == NEW else c.RUN / "traces" / policy
    return root / f"{stream['story']}-{stream['order']}.json"


def prediction_files():
    streams = c.read(c.RUN / "inputs.json")["streams"]
    return [online_path(NEW, stream) for stream in streams] + [RUN / "fixed" / policy /
        f"{stream['story']}-{stream['order']}.json" for policy in POLICIES for stream in streams]


def predict(max_units=None):
    manifest = verify_manifest()
    pairs, retrieval = callbacks()
    streams = c.read(c.RUN / "inputs.json")["streams"]
    thresholds = manifest["thresholds"]
    completed = 0
    def tick(phase):
        nonlocal completed
        completed += 1
        if max_units and completed >= max_units:
            c.publish(RUN / f"pauses/{time.time_ns()}-bounded.json", {"phase": phase, "savedUnits": completed})
            raise c.Paused("bounded-unit-stop:" + phase)
    for stream in streams:
        boundary("online:" + stream["story"] + stream["order"])
        path = online_path(NEW, stream)
        if path.exists():
            c.read_unit(path)
            continue
        checked = []
        for policy in POLICIES:
            if policy == NEW:
                continue
            reproduced = run_stream(stream, policy, pairs, retrieval, thresholds)
            original = c.read_unit(online_path(policy, stream))
            c.require(reproduced == original, "C2 decision/state parity failed: " + policy + stream["story"] + stream["order"])
            checked.append(policy)
        trace = run_stream(stream, NEW, pairs, retrieval, thresholds)
        c.unit(RUN / "parity" / path.name, {"story": stream["story"], "order": stream["order"], "matchedPolicies": checked})
        c.unit(path, trace)
        tick("online:" + path.name)
    for policy in POLICIES:
        for stream in streams:
            boundary("fixed:" + policy + stream["story"] + stream["order"])
            path = RUN / "fixed" / policy / f"{stream['story']}-{stream['order']}.json"
            if path.exists():
                c.read_unit(path)
                continue
            anchor = c.read_unit(online_path(policy, stream))
            result = fixed_trace(anchor, pairs, retrieval, thresholds)
            c.require(len(result["contexts"]) == 12, "Expected twelve capture contexts per stream")
            # Each lineage's own counterfactual must reproduce its saved online decision.
            expected = {event["id"]: event["decision"] for event in anchor["events"] if event["kind"] == "capture"}
            for context in result["contexts"]:
                own = context["decisions"][policy]
                comparable = {key: value for key, value in expected[context["event"]].items()
                              if key not in ("retrieval", "pairEvidence", "assignedMemberships")}
                c.require(own == comparable, "Own-lineage fixed-state parity failed")
            c.unit(path, result)
            tick("fixed:" + policy + ":" + path.name)
        c.log("fixed-anchor", anchor=policy, streams=36)
    paths = prediction_files() + list((RUN / "parity").glob("*.json"))
    c.require(len(list((RUN / "parity").glob("*.json"))) == 36, "Missing parity receipts")
    for path in paths:
        c.read_unit(path)
    c.publish(RUN / "predictions-complete.json", {"manifestSHA256": c.digest(RUN / "manifest.json"),
        "files": {str(path.relative_to(RUN)): c.digest(path) for path in sorted(paths)},
        "legacyParityStreams": 252, "fixedOwnLineageChecks": 3456, "counterfactualDecisions": 27648})
    return {"predictionsFrozen": True, "counterfactualDecisions": 27648}


def verify_predictions():
    verify_manifest()
    receipt = c.read(RUN / "predictions-complete.json")
    c.require(receipt["manifestSHA256"] == c.digest(RUN / "manifest.json"), "Prediction freeze changed")
    expected = {str(path.relative_to(RUN)) for path in prediction_files()} | {
        "parity/" + path.name for path in prediction_files()[:36]}
    c.require(set(receipt["files"]) == expected, "Incomplete prediction inventory")
    for name, sha in receipt["files"].items():
        c.require(c.digest(RUN / name) == sha, "Prediction artifact changed: " + name)
    return receipt


def evaluate():
    verify_predictions()  # Gold is opened only after this succeeds.
    from c2_metrics import score_trace
    from c2_report import summarize, order_sensitivity
    from c3_metrics import score_fixed, combine
    thresholds = c.read(RUN / "manifest.json")["thresholds"]
    streams = c.read(c.RUN / "inputs.json")["streams"]
    online, fixed = {policy: [] for policy in POLICIES}, []
    for policy in POLICIES:
        for stream in streams:
            boundary("metrics:" + policy + stream["story"] + stream["order"])
            gold = c.read(c.DATA / f"release/gold/{stream['story']}-{stream['order']}.json")
            online[policy].append(score_trace(c.read_unit(online_path(policy, stream)), gold))
            path = RUN / "metrics/fixed" / policy / f"{stream['story']}-{stream['order']}.json"
            if not path.exists():
                value = score_fixed(c.read_unit(RUN / "fixed" / policy / path.name), gold, thresholds)
                c.unit(path, value)
            fixed.append(c.read_unit(path))
        c.log("metrics-anchor", anchor=policy)
    old = c.read(c.RUN / "metrics-summary.json")["policy"]
    summary = {"diagnosticOnly": True, "online": {}, "fixed": {}}
    for policy, rows in online.items():
        value = summarize(rows)
        if policy != NEW:
            c.require(value == old[policy]["allOrders"], "C2 semantic metric parity failed")
        summary["online"][policy] = {"allOrders": value,
            "byStory": {story: summarize([row for row in rows if row["story"] == story]) for story in sorted({r['story'] for r in rows})},
            "byOrder": {order: summarize([row for row in rows if row["order"] == order]) for order in sorted({r['order'] for r in rows})},
            "orderSensitivity": order_sensitivity([c.read_unit(online_path(policy, stream)) for stream in streams])}
    for dimension, keys in (("anchor", POLICIES), ("story", sorted({r['story'] for r in fixed})),
                            ("order", sorted({r['order'] for r in fixed}))):
        summary["fixed"]["by" + dimension.title()] = {key: {"counts": combine([row for row in fixed if row[dimension] == key]),
            "pairClassification": combine([row for row in fixed if row[dimension] == key], "pairClassification")} for key in keys}
    summary["fixed"]["pooled"] = {"counts": combine(fixed), "pairClassification": combine(fixed, "pairClassification")}
    c.publish(RUN / "summary.json", summary)
    c.publish(RUN / "metrics-complete.json", {"predictionReceiptSHA256": c.digest(RUN / "predictions-complete.json"),
        "summarySHA256": c.digest(RUN / "summary.json"),
        "files": {str(path.relative_to(RUN)): c.digest(path) for path in sorted((RUN / "metrics").rglob("*.json"))}})
    return {"metricsSaved": True}


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
        c.log("status", **c.space(), predictions=(RUN / "predictions-complete.json").exists(),
              metrics=(RUN / "metrics-complete.json").exists(), onlineUnits=len(list((RUN / "online").glob("*.json"))),
              fixedUnits=len(list((RUN / "fixed").glob("*/*.json"))))
        return 0
    try:
        with worker(args.resume):
            boundary(args.phase)
            result = {"prepare": prepare, "predict": lambda: predict(args.max_units), "evaluate": evaluate}[args.phase]()
            c.log("saved", **result)
    except c.Paused as stopped:
        c.log("paused", boundary=str(stopped), safeToClose=True)
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
