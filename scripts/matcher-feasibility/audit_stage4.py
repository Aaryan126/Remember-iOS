#!/usr/bin/env python3
"""Independent device-evidence audit and immutable Stage 4 completion receipt."""
import argparse
import json
import math
from pathlib import Path
import statistics

from experiment import DATA, ROOT, read, save, sha, require
from stage3_common import HERE, WORKSPACE, files_in, verify_files, now
from stage4 import verify as verify_inputs, run_path


def audit(run, report_path):
    from stage3 import verify as verify_stage3
    verify_stage3(DATA / "runs/stage-3-attempt-03", WORKSPACE)
    manifest = verify_inputs(run)
    report = read(report_path)
    require(report_path.parent == run / "reports", "report outside run")
    require(report["candidateID"] == manifest["candidateID"], "report candidate mismatch")
    device = run / "device"
    fixtures = read(Path(manifest["project"]) / "Sources/fixtures.json")["fixtures"]
    require(all(set(f) == {"id", "first", "second"} for f in fixtures), "phone payload must be input-only")
    refs = DATA / "runs/stage-2-attempt-01/reference/cases"
    parity_deltas, agreements, averaged_agreements = [], [], []
    timing_deltas = []
    reference_averages = {}
    for fixture in fixtures:
        for length in [256, 512]:
            original_vectors, phone_vectors = [], []
            for orientation in ["forward", "reverse"]:
                identifier = f"{fixture['id']}-{length}-{orientation}"
                original = read(refs / f"{identifier}.json")
                phone = read(device / "parity/records" / f"{identifier}.json")
                require(phone["fixtureID"] == fixture["id"] and phone["orientation"] == orientation
                        and phone["length"] == length and phone["id"] == identifier, "parity identity mismatch")
                prediction = phone["prediction"]
                require(prediction["inputs"] == original["inputs"], "token mismatch")
                require(len(prediction["logits"]) == 3 and all(math.isfinite(p) for p in prediction["logits"]), "nonfinite logits")
                p, q = prediction["probabilities"], original["probabilities"][0]
                require(len(p) == 3 and all(math.isfinite(v) and 0 <= v <= 1 for v in p)
                        and abs(sum(p)-1) < .002, "invalid probability vector")
                parity_deltas.append(max(abs(p[i]-q[i]) for i in range(3)))
                agreements.append(p.index(max(p)) == q.index(max(q)))
                original_vectors.append(q); phone_vectors.append(p)
            original_average = [sum(v[i] for v in original_vectors)/2 for i in range(3)]
            phone_average = [sum(v[i] for v in phone_vectors)/2 for i in range(3)]
            reference_averages[(fixture["id"], length)] = original_average
            averaged_agreements.append(original_average.index(max(original_average)) == phone_average.index(max(phone_average)))
    require(len(parity_deltas) == 416 and len(averaged_agreements) == 208, "incomplete parity")
    require(max(parity_deltas) == report["parity"]["maxProbabilityDifference"], "reported parity mismatch")
    require(sum(agreements)/416 == report["parity"]["classAgreement"], "reported agreement mismatch")

    for path in device.glob("*/records/*.json"):
        if path.parent.parent.name == "parity": continue
        timing = read(path)
        require(timing["passes"] == 20 and len(timing["pairs"]) == 10, "shortlist omitted directions")
        root = path.parent.parent / "launches" / timing["launchID"]
        start = read(root / "start.json")
        require(start["candidateID"] == manifest["candidateID"] and start["length"] == timing["length"], "timing from wrong launch")
        expected_ids = [fixtures[(timing["index"]*10+i) % 104]["id"] for i in range(10)]
        require([p["fixtureID"] for p in timing["pairs"]] == expected_ids, "shortlist fixture order changed")
        for pair in timing["pairs"]:
            ref = reference_averages[(pair["fixtureID"], timing["length"])]
            require(len(pair["averagedProbabilities"]) == 3, "averaging output missing")
            timing_deltas.append(max(abs(pair["averagedProbabilities"][i]-ref[i]) for i in range(3)))
    require(len(timing_deltas) == 3100, "missing cold/warm/interruption pairs")
    require(all(math.isfinite(v) and v <= .01 for v in timing_deltas), "timed decision path differs from original")

    for length in [256, 512]:
        rows = [read(device / f"warm-{length}/records/{i}.json") for i in range(100)]
        measured = sorted(row["fullShortlistSeconds"] for row in rows)
        require(all(math.isfinite(v) and v > 0 for v in measured), "invalid latency")
        require(measured[94] == report["warmShortlistSeconds"][str(length)]["p95"], "p95 incorrect")
        require(statistics.median(measured) == report["warmShortlistSeconds"][str(length)]["median"], "median incorrect")
        for launch_id in {row["launchID"] for row in rows}:
            warmups = list((device / f"warm-{length}/launches/{launch_id}").glob("warmup-*.json"))
            require(len(warmups) == 3, "warmup coverage missing")

    starts = sorted([read(p) for p in device.glob("*/launches/*/start.json")], key=lambda p: p["recordedAt"])
    require(len(starts) == 15, "unexpected accepted-run process count")
    ends = [read(device / s["job"] / "launches" / s["launchID"] / "end.json") for s in starts]
    require(sum(e["status"] == "complete" for e in ends) == 14 and sum(e["status"] == "paused" for e in ends) == 1,
            "missing/failed launch receipt")
    require(all(e["memory"]["failedSamples"] == 0 for e in ends), "memory sampling failure")
    samples = [v for e in ends for v in e["memory"]["samples"]]
    peak = max(v["footprintBytes"] for v in samples)
    require(peak == report["memory"]["peakSampledFootprintBytes"], "peak footprint incorrectly reported")
    require(all(s["storage"]["bundleLogicalBytes"] == report["storage"]["first"]["bundleLogicalBytes"] for s in starts), "on-phone app size changed")
    require(starts[0]["storage"] == report["storage"]["first"] and ends[-1]["storage"] == report["storage"]["last"], "storage chronology incorrect")
    require(read(run / "build.json")["appLogicalBytes"] == starts[0]["storage"]["bundleLogicalBytes"], "phone bundle differs in size from signed build")

    # Every byte copied from the phone must remain identical across collection snapshots.
    exported = 0
    for folder in (run / "exports").iterdir():
        for path in folder.rglob("*.json"):
            require(sha(path) == sha(device / path.relative_to(folder)), "previously collected phone evidence changed")
            exported += 1
    preserved = [p for p in (device / "interruption/records").glob("*.json")
                 if read(device / "interruption/launches" / read(p)["launchID"] / "end.json")["status"] == "paused"]
    require(len(preserved) == report["interruption"]["completedRecordsPreservedFromPausedLaunch"] == 6,
            "pause/resume record preservation mismatch")

    # First installation/preflight is diagnostic evidence, not silently discarded or pooled.
    preliminary = DATA / "runs/stage-4-attempt-01"
    prior = read(preliminary / "manifest.json")
    verify_files(preliminary / "source-snapshots", prior["sourceHashes"])
    for name in ["Stage4ProbeApp.swift", "MatcherRuntime.swift", "MatcherTokenizer.swift"]:
        require(prior["sourceHashes"][name] == manifest["sourceHashes"][name], "preflight used different model path")
    require(prior["candidateID"] == manifest["candidateID"], "preflight candidate changed")
    first_load = read(next((preliminary / "device/cold-00").glob("launches/*/load.json")))
    restarted = [read(device / s["job"] / "launches" / s["launchID"] / "load.json")["modelAndTokenizerLoadSeconds"]
                 for s in starts if s["mode"] == "cold"]
    require(len(restarted) == 10 and restarted[0] == report["firstObservedColdLoadSeconds"], "cold chronology mismatch")
    gates = {"warm256Latency": report["warmShortlistSeconds"]["256"]["p95"] <= 1,
             "sampledProcessMemory": peak <= 500_000_000,
             "deviceParity": max(parity_deltas) <= .01 and sum(agreements)/416 >= .99,
             "coverageAndInterruption": len(preserved) == 6}
    require(gates == report["gates"] and all(gates.values()) == report["passed"], "gate verdict mismatch")
    historical = read(DATA / "baseline-context.json")
    for key in ("artifacts", "productionSources"):
        require(all(sha(ROOT / name) == expected for name, expected in historical[key].items()), "historical/production source changed")
    result = {"at": now(), "audited": True, "gates": gates, "passed": all(gates.values()),
        "reportSHA256": sha(report_path), "auditSourceSHA256": sha(Path(__file__)),
        "timedPairsComparedWithOriginalAverages": len(timing_deltas), "maxTimedPairProbabilityDifference": max(timing_deltas),
        "averagedPairClassAgreement": sum(averaged_agreements)/len(averaged_agreements),
        "byteIdenticalExportedFilesChecked": exported,
        "preflightFirstObservedModelLoadSeconds": first_load["modelAndTokenizerLoadSeconds"],
        "acceptedFirstLoadSeconds": restarted[0], "subsequentNineLoadsMedianSeconds": statistics.median(restarted[1:]),
        "lowPowerModeObserved": any(s["lowPowerMode"] for s in starts),
        "deviceOS": sorted({s["operatingSystem"] for s in starts}),
        "upstreamStagesVerified": [1, 2, 3], "productionAppTouched": False, "testLabelsOpened": False,
        "historicalArtifactsUnchanged": len(historical["artifacts"]),
        "productionSourcesUnchanged": len(historical["productionSources"])}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["audit", "finalize", "verify"])
    parser.add_argument("--run", required=True)
    parser.add_argument("--report")
    args = parser.parse_args(); run = run_path(args.run)
    if args.action == "verify":
        complete = read(run / "complete.json")
        verify_files(run, complete["files"])
        verify_files(HERE, complete["auditSources"])
        verify_files(DATA / "runs/stage-4-attempt-01", complete["preflightFiles"])
        verify_inputs(run)
        from stage3 import verify as verify_stage3
        verify_stage3(DATA / "runs/stage-3-attempt-03", WORKSPACE)
        print(json.dumps({"verified": True, "files": len(complete["files"]), "completeSHA256": sha(run / "complete.json")})); return
    require(bool(args.report), "--report required")
    report_path = Path(args.report).resolve()
    result = audit(run, report_path)
    if args.action == "finalize":
        require(not (run / "complete.json").exists(), "completion is immutable")
        require(not (run / "control/pause-requested.json").exists(), "pending pause request")
        save(run / "audit.json", result)
        # Worker lock is operational, not evidence. No jobs may be added after this checkpoint.
        files = {name: digest for name, digest in files_in(run).items() if name != "worker.lock"}
        prior = DATA / "runs/stage-4-attempt-01"
        save(run / "complete.json", {"schemaVersion": 1, "stage": 4, "completedAt": now(),
            "stageComplete": True, "feasibilityPassed": result["passed"], "stopAfterStage": True,
            "report": str(report_path.relative_to(run)), "files": files,
            "auditSources": {Path(__file__).name: sha(Path(__file__))},
            "preflightFiles": {name: digest for name, digest in files_in(prior).items() if name != "worker.lock"}})
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
