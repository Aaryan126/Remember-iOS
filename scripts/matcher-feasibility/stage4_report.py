"""Strict Stage 4 device result validation. No semantic labels are read."""
import math
from pathlib import Path
import statistics

from experiment import DATA, read, save, require, sha
from stage3_common import now


def distribution(values):
    require(bool(values) and all(math.isfinite(v) and v >= 0 for v in values), "missing/nonfinite measurement")
    ordered = sorted(values)
    return {"count": len(values), "min": ordered[0], "median": statistics.median(ordered),
            "p95": ordered[math.ceil(.95 * len(ordered)) - 1], "max": ordered[-1],
            "mean": statistics.mean(ordered), "p95Method": "nearest rank"}


def validate_timing(value, length, index, fixtures):
    require(value["length"] == length and value["index"] == index and value["passes"] == 20, "timing identity/pass mismatch")
    require(len(value["pairs"]) == 10, "incomplete shortlist")
    expected = [fixtures[(index * 10 + offset) % len(fixtures)]["id"] for offset in range(10)]
    require([pair["fixtureID"] for pair in value["pairs"]] == expected, "wrong shortlist inputs")
    require(value["fullShortlistSeconds"] >= value["tokenizationSeconds"] + value["modelPredictionSeconds"], "invalid timing scope")
    distribution([value[k] for k in ["fullShortlistSeconds", "tokenizationSeconds", "modelPredictionSeconds"]])
    for pair in value["pairs"]:
        probabilities = pair["averagedProbabilities"]
        require(len(probabilities) == 3 and all(math.isfinite(p) and 0 <= p <= 1 for p in probabilities)
                and abs(sum(probabilities) - 1) <= .002, "invalid averaged probability")


def report(run):
    run = Path(run)
    manifest = read(run / "manifest.json")
    fixtures = read(Path(manifest["project"]) / "Sources/fixtures.json")["fixtures"]
    device = run / "device"
    required = [(f"cold-{i:02d}", "cold", 256, 1) for i in range(10)] + [
        ("warm-256", "warm", 256, 100), ("warm-512", "warm", 512, 100),
        ("parity", "parity", 256, 1), ("interruption", "interrupt", 256, 100)]
    for job, mode, length, count in required:
        require(read(run / "jobs" / f"{job}.json") == {"job": job, "mode": mode, "length": length, "count": count}, "unexpected job config")
        require((run / "jobs" / f"{job}-complete.json").exists(), f"job incomplete: {job}")
        paths = list((device / job / "records").glob("*.json"))
        require(len(paths) == (416 if mode == "parity" else count), f"wrong measurement coverage: {job}")
        if mode != "parity":
            for index in range(count): validate_timing(read(device / job / "records" / f"{index}.json"), length, index, fixtures)

    launches = []
    for path in sorted((run / "launches").glob("*.json")):
        if path.stem.endswith("-host-end"): continue
        host = read(path)
        root = device / host["job"] / "launches" / host["launchID"]
        require((root / "end.json").exists(), "unaccounted device launch; investigate interruption/crash")
        start, end = read(root / "start.json"), read(root / "end.json")
        require(start["candidateID"] == manifest["candidateID"] and start["runID"] == run.name
                and start["launchID"] == end["launchID"] == host["launchID"], "device candidate/run changed")
        require(start["computeUnits"] == "all", "compute policy changed")
        require(end["status"] in ["complete", "paused"], "failed device launch")
        require(end["memory"]["samples"] and end["memory"]["failedSamples"] == 0, "memory sampling unavailable")
        require(read(run / "launches" / f"{host['launchID']}-host-end.json")["returncode"] == 0, "host launch failure")
        launches.append((host, start, end, read(root / "load.json")))
    launches.sort(key=lambda entry: entry[0]["at"])
    cold = [entry for entry in launches if entry[0]["mode"] == "cold" and entry[2]["status"] == "complete"]
    require(len(cold) == 10 and len({entry[1]["processID"] for entry in cold}) == 10, "cold loads are not ten distinct processes")
    require(all(entry[0]["command"].count("--terminate-existing") == 1 for entry in cold), "process-cold launch option missing")

    # Model reference outputs are non-test, untrained-head conversion fixtures, not gold labels.
    deltas, agreements, averages = [], [], {}
    for fixture in fixtures:
        for length in [256, 512]:
            directional = []
            for orientation in ["forward", "reverse"]:
                identifier = f"{fixture['id']}-{length}-{orientation}"
                actual = read(device / "parity/records" / f"{identifier}.json")
                original = read(DATA / "runs/stage-2-attempt-01/reference/cases" / f"{identifier}.json")
                require(actual["id"] == identifier and actual["prediction"]["inputs"] == original["inputs"], "phone token mismatch")
                a, b = actual["prediction"]["probabilities"], original["probabilities"][0]
                require(len(a) == 3 and all(math.isfinite(p) for p in a), "nonfinite phone probabilities")
                deltas.append(max(abs(x - y) for x, y in zip(a, b)))
                agreements.append(max(range(3), key=a.__getitem__) == max(range(3), key=b.__getitem__))
                directional.append((a, b))
            averaged = [[sum(direction[column][i] for direction in directional) / 2 for i in range(3)] for column in [0, 1]]
            averages[f"{fixture['id']}-{length}"] = max(abs(x-y) for x, y in zip(*averaged))
    parity = {"cases": len(deltas), "exactTokenCases": len(deltas), "maxProbabilityDifference": max(deltas),
              "classAgreement": sum(agreements) / len(agreements), "averagedPairs": len(averages),
              "maxAveragedProbabilityDifference": max(averages.values())}
    warm = {str(length): distribution([read(device / f"warm-{length}/records/{i}.json")["fullShortlistSeconds"] for i in range(100)])
            for length in [256, 512]}
    memory = [sample for _, _, end, _ in launches for sample in end["memory"]["samples"]]
    gaps = [b["uptime"] - a["uptime"] for _, _, end, _ in launches
            for a, b in zip(end["memory"]["samples"], end["memory"]["samples"][1:])]
    interrupted = [entry for entry in launches if entry[0]["job"] == "interruption" and entry[2]["status"] == "paused"]
    require(interrupted, "interruption exercise missing")
    retained = set()
    for export in sorted((run / "exports").iterdir()):
        for path in (export / "interruption/records").glob("*.json"):
            require(sha(path) == sha(device / "interruption/records" / path.name), "completed record changed after interruption")
            retained.add(path.name)
    require(len(retained) == 100, "incomplete interruption recovery")
    paused_ids = {entry[0]["launchID"] for entry in interrupted}
    reused = [path for path in (device / "interruption/records").glob("*.json") if read(path)["launchID"] in paused_ids]
    require(reused, "pause exercise did not retain completed records from the interrupted process")
    peak = max(s["footprintBytes"] for s in memory)
    gates = {"warm256Latency": warm["256"]["p95"] <= manifest["gates"]["warm256P95Seconds"],
             "sampledProcessMemory": peak <= manifest["gates"]["peakFootprintBytes"],
             "deviceParity": parity["maxProbabilityDifference"] <= .01 and parity["classAgreement"] >= .99,
             "coverageAndInterruption": True}
    result = {"stage": 4, "createdAt": now(), "candidateID": manifest["candidateID"], "gates": gates,
        "passed": all(gates.values()), "warmShortlistSeconds": warm, "parity": parity,
        "coldModelAndTokenizerLoadSeconds": distribution([entry[3]["modelAndTokenizerLoadSeconds"] for entry in cold]),
        "coldFirstShortlistSeconds": distribution([read(device / f"cold-{i:02d}/records/0.json")["fullShortlistSeconds"] for i in range(10)]),
        "firstObservedColdLoadSeconds": cold[0][3]["modelAndTokenizerLoadSeconds"],
        "memory": {"peakSampledFootprintBytes": peak, "peakSampledResidentBytes": max(s["residentBytes"] for s in memory),
            "samples": len(memory), "requestedIntervalSeconds": .02, "observedIntervalSeconds": distribution(gaps),
            "thermalStatesObserved": sorted({s["thermalState"] for s in memory})},
        "storage": {"first": launches[0][1]["storage"], "last": launches[-1][2]["storage"]},
        "interruption": {"pausedLaunches": len(interrupted), "totalRecoveredRecords": 100,
                         "completedRecordsPreservedFromPausedLaunch": len(reused)},
        "limitations": ["Untrained head: not a semantic quality test.", "Single iPhone, fictional fixture workload, no app-integration performance claim.",
            "Process-cold does not mean reboot-cold or purged OS/accelerator caches; first observed load kept separately.",
            "Model+tokenizer load excludes pre-main app startup; host launch overhead is not reported as app startup.",
            "20ms process footprint sampling can miss short peaks and excludes separately-accounted system/accelerator memory.",
            "Storage is logical file bytes visible in probe bundle/container, not Settings installation allocation or system caches.",
            "ComputeUnits.all permits CPU/GPU/ANE; it does not prove Neural Engine execution.",
            "Cooperative pause/resume tested; no deliberate cable removal, device reboot, or OS jetsam test."]}
    path = run / "reports" / f"{__import__('time').time_ns()}.json"
    save(path, result)
    print(__import__('json').dumps({"report": str(path), **result}, indent=2))
    return result
