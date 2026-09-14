#!/usr/bin/env python3
"""Isolated local semantic-verifier diagnostic; no app, cloud, training or Git writes."""
import argparse
from collections import Counter
from contextlib import contextmanager
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import c2_common as c
import c5_run
from c5_data import validate_packet
from c5_metrics import validate_prediction
import c6_finalize
import c6_run

RUN = c.DATA / "runs/c7-01"
CURATED = c.DATA / "c7"
SCRIPT = Path(__file__).parent
BINARY = RUN / "build/semantic-probe"
PROMPT = CURATED / "prompt.txt"
LEGACY = ("baseline", "17", "29", "41")
CANDIDATES = (*LEGACY, "local", "always-abstain",
              *(s + "-veto" for s in LEGACY), *(s + "-confirm" for s in LEGACY))


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
            c.publish(RUN / f"resumptions/{time.time_ns()}.json", {"pauseSHA256": c.digest(marker)})
            marker.unlink()  # Only the saved request owned by this runner.
        yield


def boundary(phase):
    c.space(planned=4 * 1024**2)
    if c._pause_signal or (RUN / "control/pause-requested.json").exists() or (c.RUN / "control/pause-requested.json").exists():
        c.publish(RUN / f"pauses/{time.time_ns()}.json", {"savedBoundary": True, "phase": phase})
        raise c.Paused(phase)


def packets():
    return c6_run.packets()


def visible(packet):
    validate_packet(packet)
    return {"pair": packet["pair"], "sources": packet["sources"]}


def context_key(packet):
    return c.text_sha(json.dumps(visible(packet), sort_keys=True, ensure_ascii=False))


def request(packet):
    payload = json.dumps(visible(packet), sort_keys=True, ensure_ascii=False)
    c.require(len(payload) <= 16_000, "Input too long; refusing truncation")
    return {"instructions": PROMPT.read_text(), "packet": payload}


def catalogue():
    contexts, mapping = {}, {}
    for packet in packets():
        key = context_key(packet)
        contexts.setdefault(key, packet)
        mapping[packet["queryID"]] = key
    return {"contexts": dict(sorted(contexts.items())), "mapping": mapping}


def build():
    if (RUN / "manifest.json").exists():
        raise ValueError("Already frozen; do not rebuild")
    c6_finalize.verify()
    c.space(planned=256 * 1024**2)
    source = SCRIPT / "c7_probe.swift"
    build_dir = BINARY.parent
    build_dir.mkdir(parents=True, exist_ok=True)
    receipt = RUN / "build.json"
    if receipt.exists():
        old = c.read(receipt)
        c.require(old["sourceSHA256"] == c.digest(source) and old["binarySHA256"] == c.digest(BINARY), "Build changed")
        return old
    c.require(not BINARY.exists(), "Unrecorded binary exists; preserve it and investigate")
    command = ["xcrun", "swiftc", "-parse-as-library", "-module-cache-path", str(build_dir / "module-cache"),
               str(source), "-o", str(BINARY)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    c.publish(RUN / "build-command.json", {"command": command, "stdout": result.stdout,
        "stderr": result.stderr, "returnCode": result.returncode})
    c.require(result.returncode == 0, "Swift build failed: " + result.stderr)
    native = subprocess.run([str(BINARY), "--availability"], capture_output=True, text=True, timeout=30)
    c.require(native.returncode == 0, "Availability process failed")
    state = json.loads(native.stdout)
    c.publish(RUN / "availability.json", {"response": state, "stderr": native.stderr})
    output = {"sourceSHA256": c.digest(source), "binarySHA256": c.digest(BINARY), "platform": platform.platform(),
        "toolchain": subprocess.run(["swift", "--version"], capture_output=True, text=True, check=True, timeout=30).stdout,
        "availability": state, "resource": c.space()}
    c.publish(receipt, output)
    c.require(state.get("availability") == "available", "Local model unavailable; stop without fallback")
    return output


def validate_output(packet, output):
    c.require(isinstance(output, dict) and set(output) == {"evidence", "verdict", "rationale"}, "Invalid output schema")
    c.require(isinstance(output["rationale"], str) and 0 < len(output["rationale"].strip()) <= 2000, "Invalid rationale")
    c.require(isinstance(output["evidence"], list) and len(output["evidence"]) <= 4, "Invalid evidence count")
    prediction = {"queryID": packet["queryID"], "verdict": output["verdict"], "evidence": output["evidence"]}
    validate_prediction(packet, prediction)
    if output["verdict"] != "abstain":
        cited = {item["sourceID"] for item in output["evidence"]}
        c.require(set(packet["pair"]) <= cited, "Decisive result must cite both queried sources")
    return prediction


def interpret(packet, raw):
    if raw["returnCode"] != 0:
        return {"status": "error", "errorKind": "timeout" if raw["timedOut"] else "process", "prediction": None}
    try:
        response = json.loads(raw["stdout"])
        c.require(isinstance(response, dict), "Invalid response envelope")
        if response.get("status") != "ok":
            return {"status": "error", "errorKind": "model:" + str(response.get("status")), "prediction": None}
        c.require(response.get("availability") == "available", "Availability mismatch")
        prediction = validate_output(packet, response["output"])
        return {"status": "ok", "prediction": prediction}
    except (ValueError, KeyError, TypeError) as error:
        return {"status": "error", "errorKind": "invalid-output", "detail": str(error), "prediction": None}


def tests():
    command = [sys.executable, "-m", "unittest", "discover", "-s", str(SCRIPT), "-p", "test_*.py"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    c.require(result.returncode == 0 and "skipped=" not in result.stderr, "Tests failed/skipped: " + result.stderr)
    c.publish(RUN / "validation/tests.json", {"command": command, "returnCode": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr, "runtime": c.runtime()})
    return {"passed": True, "output": result.stderr}


def freeze():
    if (RUN / "manifest.json").exists():
        verify_manifest()
        return {"frozen": True}
    c6_finalize.verify()
    built = c.read(RUN / "build.json")
    c.require(built["sourceSHA256"] == c.digest(SCRIPT / "c7_probe.swift") and built["binarySHA256"] == c.digest(BINARY), "Changed build")
    c.require(built["availability"]["availability"] == "available", "Model unavailable")
    c.require(c.read(RUN / "validation/tests.json")["returnCode"] == 0, "Tests required")
    data = catalogue()
    c.require(len(data["contexts"]) == 112 and len(data["mapping"]) == 160, "Context inventory changed")
    for packet in data["contexts"].values():
        request(packet)
    c.publish(RUN / "catalogue.json", data)
    paths = [SCRIPT / "c7_run.py", SCRIPT / "c7_probe.swift", SCRIPT / "test_c7.py", PROMPT,
             c.DATA / "C7_PROTOCOL.md", c6_run.CURATED / "complete.json", c5_run.RUN / "release/inputs.json",
             c5_run.RUN / "release/gold.json", c6_run.RUN / "adjudicated-gold.json",
             RUN / "catalogue.json", RUN / "build.json", RUN / "availability.json", BINARY,
             RUN / "validation/tests.json"]
    paths += [c6_run.RUN / f"predictions/{name}.json" for name in LEGACY]
    # Bind shared helpers as well; future amendments must not alter this attempt.
    paths += [SCRIPT / name for name in ("checkpoint.py", "c2_common.py", "c5_data.py", "c5_metrics.py", "c5_run.py", "c6_run.py", "c6_finalize.py")]
    c.publish(RUN / "manifest.json", {"sources": {str(p.relative_to(c.ROOT)): c.digest(p) for p in paths},
        "runtime": c.runtime(), "candidates": list(CANDIDATES), "model": "SystemLanguageModel.default",
        "sampling": "greedy", "maximumResponseTokens": 600, "timeoutSeconds": 60,
        "parentCompletionSHA256": c.digest(c6_run.CURATED / "complete.json"), "resource": c.space(),
        "exposedDiagnostic": True, "trainingAllowed": False})
    return {"frozen": True, "contexts": 112, "expandedPackets": 160}


def verify_manifest():
    manifest = c.read(RUN / "manifest.json")
    c.require(manifest["runtime"] == c.runtime(), "Runtime changed; preserve attempt")
    c6_run.check_files(manifest["sources"], c.ROOT)
    return manifest


def invoke(packet):
    started = time.monotonic()
    encoded = json.dumps(request(packet), ensure_ascii=False)
    try:
        result = subprocess.run([str(BINARY)], input=encoded, capture_output=True, text=True, timeout=60)
        raw = {"returnCode": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "timedOut": False}
    except subprocess.TimeoutExpired as error:
        # subprocess.run kills and reaps its child before raising TimeoutExpired.
        def decoded(value):
            return value.decode(errors="replace") if isinstance(value, bytes) else (value or "")
        raw = {"returnCode": -1, "stdout": decoded(error.stdout), "stderr": decoded(error.stderr), "timedOut": True}
    raw["elapsedSeconds"] = time.monotonic() - started
    return {"requestSHA256": c.text_sha(encoded), "raw": raw, "outcome": interpret(packet, raw)}


def predict(max_units=None):
    verify_manifest()
    data = c.read(RUN / "catalogue.json")
    consecutive_errors, created = 0, 0
    for index, (key, packet) in enumerate(data["contexts"].items(), 1):
        boundary("predict:" + key)
        path = RUN / f"units/{key}.json"
        if path.exists():
            c.read_unit(path)
            continue
        unit = invoke(packet)
        c.unit(path, unit)
        created += 1
        consecutive_errors = consecutive_errors + 1 if unit["outcome"]["status"] == "error" else 0
        c.log("predict", completed=index, total=len(data["contexts"]),
              status=unit["outcome"]["status"], seconds=unit["raw"]["elapsedSeconds"])
        if consecutive_errors >= 3:
            pause()
            boundary("three-consecutive-errors")
        if max_units is not None and created >= max_units:
            return {"savedUnits": index, "boundedStop": True, "safeToClose": True}
    paths = [RUN / f"units/{key}.json" for key in data["contexts"]]
    for path in paths:
        c.read_unit(path)
    c.publish(RUN / "outcomes-complete.json", {"manifestSHA256": c.digest(RUN / "manifest.json"),
        "files": {str(p.relative_to(RUN)): c.digest(p) for p in paths}})
    return {"outcomesComplete": True, "contexts": len(paths)}


def verify_outcomes():
    verify_manifest()
    record = c.read(RUN / "outcomes-complete.json")
    data = c.read(RUN / "catalogue.json")
    c.require(record["manifestSHA256"] == c.digest(RUN / "manifest.json"), "Outcome manifest changed")
    c.require(set(record["files"]) == {f"units/{key}.json" for key in data["contexts"]}, "Missing outcome units")
    c.require({p.name for p in (RUN / "units").glob("*.json")} == {key + ".json" for key in data["contexts"]}, "Unexpected units")
    c6_run.check_files(record["files"], RUN)
    return data


def combine(legacy, local, mode):
    if local["status"] != "ok":
        return {"status": "error", "errorKind": local["errorKind"], "prediction": None}
    prediction = local["prediction"]
    if prediction["verdict"] == "separate_projects":
        return {"status": "ok", "prediction": prediction}
    if mode == "veto":
        return {"status": "ok", "prediction": legacy}
    c.require(mode == "confirm", "Invalid combination mode")
    if prediction["verdict"] == legacy["verdict"] == "same_project":
        return {"status": "ok", "prediction": prediction}
    return {"status": "ok", "prediction": {"queryID": legacy["queryID"], "verdict": "abstain", "evidence": []}}


def assemble():
    data = verify_outcomes()
    old = {name: {p["queryID"]: p for p in c.read_unit(c6_run.RUN / f"predictions/{name}.json")} for name in LEGACY}
    output = {name: [] for name in CANDIDATES}
    for packet in packets():
        key = data["mapping"][packet["queryID"]]
        unit = c.read_unit(RUN / f"units/{key}.json")
        local = dict(unit["outcome"])
        if local["status"] == "ok":
            local["prediction"] = {**local["prediction"], "queryID": packet["queryID"]}
            validate_prediction(packet, local["prediction"])
        output["local"].append({"queryID": packet["queryID"], **local})
        output["always-abstain"].append({"queryID": packet["queryID"], "status": "ok",
            "prediction": {"queryID": packet["queryID"], "verdict": "abstain", "evidence": []}})
        for name in LEGACY:
            legacy = old[name][packet["queryID"]]
            output[name].append({"queryID": packet["queryID"], "status": "ok", "prediction": legacy})
            for mode in ("veto", "confirm"):
                output[name + "-" + mode].append({"queryID": packet["queryID"], **combine(legacy, local, mode)})
    return output


def rate(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "value": numerator / denominator if denominator else None}


def metrics(inputs, labels, predictions):
    ids = [p["queryID"] for p in inputs]
    gold = {p["queryID"]: p for p in labels}
    results = {p["queryID"]: p for p in predictions}
    c.require(len(ids) == len(set(ids)) and len(gold) == len(labels) and len(results) == len(predictions)
              and set(ids) == set(gold) == set(results), "Metric inventory mismatch")
    groups = {}
    for packet in inputs:
        truth, result = gold[packet["queryID"]], results[packet["queryID"]]
        c.require(result["status"] in {"ok", "error"}, "Invalid outcome status")
        if result["status"] == "ok":
            actual = validate_prediction(packet, result["prediction"])["verdict"]
        else:
            c.require(result["prediction"] is None and result.get("errorKind"), "Malformed error")
            actual = "error"
        target = truth["verdict"]
        scopes = ("all", "view:" + packet["view"], "family:" + truth["family"],
                  "partition:" + truth["partition"], "behavior:" + truth["behavior"])
        for scope in scopes:
            count = groups.setdefault(scope, Counter())
            count["queries"] += 1
            for name, condition in {
                "errors": actual == "error", "correct": actual == target,
                "decisive": actual in {"same_project", "separate_projects"},
                "knownSame": target == "same_project", "knownSeparate": target == "separate_projects",
                "unknown": target == "abstain", "predictedSame": actual == "same_project",
                "predictedSeparate": actual == "separate_projects", "abstained": actual == "abstain",
                "trueSame": actual == target == "same_project", "trueSeparate": actual == target == "separate_projects",
                "falseSameOnSeparate": actual == "same_project" and target == "separate_projects",
                "falseSeparateOnSame": actual == "separate_projects" and target == "same_project",
                "unsupportedDecisive": target == "abstain" and actual in {"same_project", "separate_projects"},
            }.items():
                count[name] += int(condition)
    output = {}
    for scope, count in sorted(groups.items()):
        output[scope] = {"counts": dict(count)}
        for name, numerator, denominator in (
            ("samePrecision", "trueSame", "predictedSame"), ("sameRecall", "trueSame", "knownSame"),
            ("conflictPrecision", "trueSeparate", "predictedSeparate"), ("conflictRecall", "trueSeparate", "knownSeparate"),
            ("coverage", "decisive", "queries"), ("correctness", "correct", "queries"),
            ("errorRate", "errors", "queries"), ("unsupportedAssertionRate", "unsupportedDecisive", "unknown"),
        ):
            output[scope][name] = rate(count[numerator], count[denominator])
    contrasts = {}
    for name, episodes, size in (("scopeContrast", {"scope-contrast", "continuation"}, 2),
                                 ("bridgeTriple", {"bridge"}, 3), ("referenceBeforeAfter", {"before", "after"}, 4)):
        for view in ("pair", "context"):
            correct, total = 0, 0
            for family in sorted({p["family"] for p in labels}):
                selected = [p["queryID"] for p in inputs if p["view"] == view
                            and gold[p["queryID"]]["family"] == family and gold[p["queryID"]]["episode"] in episodes]
                if len(selected) == size:
                    total += 1
                    correct += int(all(results[k]["status"] == "ok" and
                                       results[k]["prediction"]["verdict"] == gold[k]["verdict"] for k in selected))
            contrasts[name + ":" + view] = rate(correct, total)
    output["contrastChecks"] = contrasts
    return output


def exploration_gate(summary):
    context = summary["view:context"]
    checks = {}
    for name, threshold, lower_bound in (("conflictPrecision", .90, True), ("conflictRecall", .80, True),
                                         ("sameRecall", .75, True), ("unsupportedAssertionRate", .10, False),
                                         ("errorRate", .05, False)):
        value = context[name]["value"]
        checks[name] = {"value": value, "threshold": threshold,
            "passed": value is not None and (value >= threshold if lower_bound else value <= threshold)}
    return {"checks": checks, "passed": all(v["passed"] for v in checks.values()), "productionQualified": False}


def evaluate():
    output = assemble()
    for name, rows in output.items():
        c.unit(RUN / f"predictions/{name}.json", rows)
    c.publish(RUN / "predictions-complete.json", {"outcomesSHA256": c.digest(RUN / "outcomes-complete.json"),
        "files": {f"predictions/{name}.json": c.digest(RUN / f"predictions/{name}.json") for name in CANDIDATES}})
    summary = {"exposedDiagnostic": True}
    for kind, path in (("adjudicated", c6_run.RUN / "adjudicated-gold.json"), ("original", c5_run.RUN / "release/gold.json")):
        labels = c.read(path)["labels"]
        summary[kind] = {name: metrics(packets(), labels, rows) for name, rows in output.items()}
    summary["explorationGate"] = exploration_gate(summary["adjudicated"]["local"])
    c.publish(RUN / "summary.json", summary)
    c.publish(RUN / "metrics-complete.json", {"summarySHA256": c.digest(RUN / "summary.json"),
        "predictionsSHA256": c.digest(RUN / "predictions-complete.json")})
    return {"evaluated": True, "predictions": len(CANDIDATES) * len(packets()), "explorationGate": summary["explorationGate"]}


def proof_before():
    path = sorted((RUN / "units").glob("*.json"))[0]
    c.read_unit(path)
    c.publish(RUN / "resume-before.json", {"path": str(path.relative_to(RUN)), "SHA256": c.digest(path), "mtimeNS": path.stat().st_mtime_ns})
    return {"savedResumeBaseline": True}


def proof_after():
    before = c.read(RUN / "resume-before.json")
    path = RUN / before["path"]
    c.require(before["SHA256"] == c.digest(path) and before["mtimeNS"] == path.stat().st_mtime_ns, "Resumed unit changed")
    c.publish(RUN / "resume-after.json", {"passed": True, "beforeSHA256": c.digest(RUN / "resume-before.json"), **before})
    return {"resumeVerified": True}


def audit():
    c6_finalize.verify()
    data = verify_outcomes()
    for key, packet in data["contexts"].items():
        unit = c.read_unit(RUN / f"units/{key}.json")
        c.require(unit["requestSHA256"] == c.text_sha(json.dumps(request(packet), ensure_ascii=False)), "Request changed")
        c.require(unit["outcome"] == interpret(packet, unit["raw"]), "Native response replay mismatch")
    outputs = assemble()
    receipt = c.read(RUN / "predictions-complete.json")
    c.require(receipt["outcomesSHA256"] == c.digest(RUN / "outcomes-complete.json") and
              set(receipt["files"]) == {f"predictions/{name}.json" for name in CANDIDATES}, "Prediction inventory mismatch")
    c6_run.check_files(receipt["files"], RUN)
    for name, rows in outputs.items():
        c.require(rows == c.read_unit(RUN / f"predictions/{name}.json"), "Prediction replay mismatch")
    summary = c.read(RUN / "summary.json")
    metric_receipt = c.read(RUN / "metrics-complete.json")
    c.require(metric_receipt == {"summarySHA256": c.digest(RUN / "summary.json"),
              "predictionsSHA256": c.digest(RUN / "predictions-complete.json")}, "Metric receipt changed")
    for kind, path in (("adjudicated", c6_run.RUN / "adjudicated-gold.json"), ("original", c5_run.RUN / "release/gold.json")):
        for name, rows in outputs.items():
            c.require(summary[kind][name] == metrics(packets(), c.read(path)["labels"], rows), "Metric replay mismatch")
    c.require(summary["explorationGate"] == exploration_gate(summary["adjudicated"]["local"]), "Gate changed")
    proof_after()
    result = {"passed": True, "nativeResponses": len(data["contexts"]), "predictions": len(CANDIDATES) * len(packets()),
              "inferenceRepeated": False}
    c.publish(RUN / "validation/replay.json", result)
    return result


def complete():
    audit()
    c.require((CURATED / "REPORT.md").exists(), "Report required")
    c.publish(CURATED / "summary.json", c.read(RUN / "summary.json"))
    paths = [RUN / name for name in ("manifest.json", "outcomes-complete.json", "predictions-complete.json",
             "metrics-complete.json", "resume-before.json", "resume-after.json", "validation/tests.json", "validation/replay.json")]
    paths += [CURATED / "REPORT.md", CURATED / "summary.json"]
    c.publish(CURATED / "complete.json", {"complete": True, "checkpoint": 7, "productionQualified": False,
        "stopForUserReview": True, "nextExperimentStarted": False, "resource": c.space(),
        "sources": {str(p.relative_to(c.ROOT)): c.digest(p) for p in paths}})
    return {"complete": True, "stopForUserReview": True, "SHA256": c.digest(CURATED / "complete.json")}


def verify():
    result = c.read(CURATED / "complete.json")
    c.require(result["complete"] is True and result["productionQualified"] is False and result["stopForUserReview"] is True
              and result["nextExperimentStarted"] is False, "Invalid completion state")
    c6_run.check_files(result["sources"], c.ROOT)
    audit()
    return {"verified": True, "SHA256": c.digest(CURATED / "complete.json")}


def status():
    paths = list((RUN / "units").glob("*.json"))
    counts = Counter(c.read_unit(path)["outcome"]["status"] for path in paths)
    return {"savedUnits": len(paths), "total": 112, "outcomes": dict(counts),
            "pauseRequested": (RUN / "control/pause-requested.json").exists(), "complete": (CURATED / "complete.json").exists()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("build", "tests", "freeze", "predict", "pause", "status", "proof-before", "proof-after", "evaluate", "audit", "complete", "verify"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-units", type=int)
    args = parser.parse_args()
    if args.max_units is not None:
        c.require(args.max_units > 0, "Positive unit limit required")
    if args.phase in {"pause", "status", "tests"}:
        c.log(args.phase, **{"pause": pause, "status": status, "tests": tests}[args.phase]())
    else:
        try:
            with worker(args.resume):
                boundary(args.phase)
                action = {"build": build, "freeze": freeze, "predict": lambda: predict(args.max_units),
                          "proof-before": proof_before, "proof-after": proof_after, "evaluate": evaluate,
                          "audit": audit, "complete": complete, "verify": verify}[args.phase]
                c.log(args.phase, **action())
        except c.Paused as error:
            c.log("paused", boundary=str(error), safeToClose=True)
            raise SystemExit(75)
