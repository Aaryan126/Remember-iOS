#!/usr/bin/env python3
"""Recompute Stage 3 parity and safety checks from immutable artifacts."""
import argparse
import json
import plistlib
from pathlib import Path
import shutil

import numpy as np

from stage3_common import *
import stage3


def independent_score(actual, expected):
    actual, expected = np.asarray(actual, dtype=float).reshape(-1), np.asarray(expected, dtype=float).reshape(-1)
    require(actual.shape == expected.shape == (3,) and np.isfinite(actual).all() and np.isfinite(expected).all(), "nonfinite/invalid audited output")
    return float(np.abs(actual - expected).max()), int(actual.argmax()) == int(expected.argmax())


def audit(run, workspace):
    verified = stage3.verify(run, workspace)
    originals = {p.stem: read(p) for p in sorted((STAGE2 / "reference/cases").glob("*.json"))}
    require(len(originals) == 416, "reference coverage changed")
    for key, original in originals.items():
        token = read(run / "tokenizer-cases" / f"{key}.json")
        require(token["passed"] and token["inputs"] == original["inputs"], "token/shape/segment/padding mismatch")
    build = read(run / "app-build.json")
    results = {}
    for backend, folder in [("cpu_only", run / "parity/cpu_only"), ("all", run / "parity/all"),
                            ("native_swift", run / build["nativeCasesDirectory"])]:
        require({p.stem for p in folder.glob("*.json")} == set(originals), "missing/extra conversion cases")
        differences, agreements, grouped = [], [], {}
        for key, original in originals.items():
            row = read(folder / f"{key}.json")
            require(row["referenceSHA256"] == sha(STAGE2 / "reference/cases" / f"{key}.json"), "reference binding mismatch")
            probabilities = row["prediction"]["probabilities"] if backend == "native_swift" else row["probabilities"]
            if backend == "native_swift":
                require(row["prediction"]["inputs"] == original["inputs"], "native runtime token mismatch")
            delta, agrees = independent_score(probabilities, original["probabilities"])
            require(delta == row["maxProbabilityDifference"] and agrees == row["classAgreement"], "stored parity score differs")
            differences.append(delta); agreements.append(agrees)
            group = (original["id"], original["length"])
            grouped.setdefault(group, []).append((np.asarray(probabilities).reshape(3), np.asarray(original["probabilities"]).reshape(3)))
        mean_differences, mean_agreements = [], []
        for group in grouped.values():
            require(len(group) == 2, "missing pair orientation")
            delta, agrees = independent_score(np.mean([r[0] for r in group], axis=0), np.mean([r[1] for r in group], axis=0))
            mean_differences.append(delta); mean_agreements.append(agrees)
        require(max(differences) <= .01 and sum(agreements) / len(agreements) >= .99, "individual conversion gate fails")
        require(max(mean_differences) <= .01 and sum(mean_agreements) / len(mean_agreements) >= .99, "averaged-orientation conversion gate fails")
        results[backend] = {"cases": len(differences), "maxProbabilityDifference": max(differences),
                            "classAgreement": sum(agreements) / len(agreements),
                            "orientationAveragedPairs": len(mean_differences),
                            "meanOrientationMaxProbabilityDifference": max(mean_differences),
                            "meanOrientationClassAgreement": sum(mean_agreements) / len(mean_agreements)}
    app = workspace / build["app"]
    payload = read(app / "fixtures.json")
    require(set(payload) == {"schemaVersion", "fixtures"} and payload["schemaVersion"] == 1, "unexpected phone payload root")
    require(len(payload["fixtures"]) == 104 and all(set(f) == {"id", "first", "second"} for f in payload["fixtures"]), "labels/metadata leaked to phone fixtures")
    info = plistlib.loads((app / "Info.plist").read_bytes())
    require(info["CFBundleIdentifier"] == "SimpleStudio.Remember.MatcherProbe", "wrong app identity")
    require(not (app / "_CodeSignature").exists(), "unexpected signed bundle")
    require(not list((workspace / build["project"]).rglob("*.entitlements")), "unexpected probe entitlements")
    require(not any(key.endswith("UsageDescription") for key in info), "private-data permission requested")
    historical = read(DATA / "baseline-context.json")
    for key in ("artifacts", "productionSources"):
        require(all(sha(ROOT / name) == expected for name, expected in historical[key].items()), "historical or production snapshot changed")
    pauses = [read(p) for p in (run / "pauses").glob("*.json")]
    conversion = read(run / "conversion.json")
    require(conversion["finiteMaskReferenceCases"] == 416 and conversion["finiteMaskMaxProbabilityDifference"] <= 1e-7,
            "finite mask not verified against original")
    return {"schemaVersion": 1, "auditedAt": now(), "passed": True, "stage3": verified,
            "auditorSHA256": sha(__file__), "parityRecomputed": results, "tokenChecks": 428,
            "phoneFixturePairs": 104, "phoneFixturesLabelFree": True, "unsignedProbeIdentityVerified": True,
            "privateDataPermissionsRequested": False, "productionEntitlementsShared": False,
            "pauseBoundaries": [p["phase"] for p in pauses], "completedArtifactsVerifiedAfterResume": True,
            "pauseTestScope": "driver stopped at initialization boundary with converted/parity/build receipts already saved; not an in-flight export cancellation test",
            "historicalArtifactsUnchanged": len(historical["artifacts"]), "productionSourcesUnchanged": len(historical["productionSources"]),
            "freeBytes": shutil.disk_usage(workspace).free, "phoneTestingPerformed": False, "testResultsOpened": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--workspace", default=WORKSPACE)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run, workspace = paths(args.run, args.workspace)
    result = audit(run, workspace)
    save(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
