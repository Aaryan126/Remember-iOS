#!/usr/bin/env python3
"""Check intermediate rendered grid positions in fictional simulator traces.

Unlike settled UI assertions, this catches a container animating from its old
local origin after reparenting. It does not claim to measure perceived smoothness.
"""
import json
from pathlib import Path
import sys


def evaluate(report):
    measurements = []
    for event in report["events"]:
        if event["after"]["queryLength"] != 0:
            continue
        prior = event["frames"][0]
        grid = next(v for v in prior["views"] if v.get("class") == "HostingScrollView")
        samples = [v for frame in event["frames"] if frame["time"] >= event["time"]
                   for v in frame["views"] if v.get("id") == grid["id"]]
        if len(samples) < 3 or any("renderedY" not in v for v in samples):
            raise ValueError("Insufficient intermediate-frame geometry")
        error = max(abs(v["renderedY"] - v["frameY"]) for v in samples)
        measurements.append({"queryLengthBefore": event["before"]["queryLength"],
                             "samples": len(samples), "maxContainerDisplacement": error})
    filled = sum(m["queryLengthBefore"] > 0 for m in measurements)
    empty = len(measurements) - filled
    if filled < 4 or empty < 2:
        raise ValueError("Need all four filled dismissals/clears and empty controls")
    return {"passed": all(m["maxContainerDisplacement"] <= 1 for m in measurements),
            "filled": filled, "empty": empty, "measurements": measurements}


if __name__ == "__main__":
    result = evaluate(json.loads(Path(sys.argv[1]).read_text()))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
