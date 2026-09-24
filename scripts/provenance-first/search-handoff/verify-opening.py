#!/usr/bin/env python3
"""Compare native bar/content movement in fictional per-frame search traces."""
import json
from pathlib import Path
import sys


def evaluate(frames):
    measurements = []
    previous = None
    for index, frame in enumerate(frames):
        field = next((row for row in frame["views"] if "queryLength" in row), None)
        if field is None:
            continue
        if (previous is not None and not previous[1]["editing"] and field["editing"]
                and not previous[1]["queryLength"] and not field["queryLength"]):
            before, old_field = previous
            grid = next(row for row in before["views"] if row.get("class") == "HostingScrollView")
            start_gap = grid["renderedY"] - grid["presentation"] - old_field["renderedY"]
            errors = []
            intermediate = 0
            for sample in frames[index:]:
                if sample["time"] > frame["time"] + 0.6:
                    break
                bar = next((row for row in sample["views"] if "queryLength" in row), None)
                content = next((row for row in sample["views"] if row.get("id") == grid["id"]), None)
                if bar is None or content is None or bar["queryLength"]:
                    break
                gap = content["renderedY"] - content["presentation"] - bar["renderedY"]
                errors.append(abs(gap - start_gap))
                if 2 < abs(bar["renderedY"] - bar["frameY"]) < 52:
                    intermediate += 1
            measurements.append({"time": frame["time"], "samples": len(errors),
                                 "intermediate": intermediate, "maxGapError": max(errors, default=0)})
        previous = (frame, field)
    if len(measurements) < 4 or sum(row["intermediate"] > 0 for row in measurements) < 3:
        raise ValueError("Insufficient opening transitions with intermediate frames")
    return {"passed": all(row["maxGapError"] <= 2 for row in measurements),
            "measurements": measurements}


if __name__ == "__main__":
    report = evaluate([json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()])
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
