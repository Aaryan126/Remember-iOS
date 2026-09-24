#!/usr/bin/env python3
"""Archive and summarize read-only motion traces from the fictional simulator."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "Evaluation/ProvenanceFirst/runs/search-handoff"
SIMULATOR = "C530FCC2-DD67-4115-97D9-C4E34807EC57"

def main():
    label = sys.argv[1]
    if not label.replace("-", "").isalnum():
        raise ValueError("Use an alphanumeric run label")
    mode = sys.argv[2] if len(sys.argv) > 2 else ""
    if mode not in {"", "top", "scrolled"}:
        raise ValueError("Trace mode must be top or scrolled")
    suffix = "-" + mode if mode else ""
    container = Path(subprocess.check_output([
        "xcrun", "simctl", "get_app_container", SIMULATOR,
        "SimpleStudio.Remember.SourceBrowserUI", "data"], text=True).strip())
    target = RUN / (label + "-trace.jsonl")
    if target.exists():
        raise ValueError("Do not overwrite a previous trace")
    shutil.copyfile(container / f"Documents/search-motion-trace{suffix}.jsonl", target)
    frames = [json.loads(line) for line in target.read_text().splitlines()]
    events = []
    previous = None
    for index, frame in enumerate(frames):
        field = next((v for v in frame["views"] if "queryLength" in v), None)
        if previous and field and ((previous["queryLength"] and not field["queryLength"])
                or (previous["editing"] and not field["editing"])):
            window = [f for f in frames[max(0, index - 1):]
                      if f["time"] < frame["time"] + 0.6]
            events.append(dict(time=frame["time"], before=previous, after=field, frames=window))
        previous = field
    report = dict(frameCount=len(frames), events=events)
    (RUN / (label + "-events.json")).write_text(json.dumps(report, indent=2) + "\n")
    for event in events:
        print(round(event["time"], 3), event["before"], "->", event["after"])
        for frame in event["frames"]:
            values = [dict(id=v["id"], offset=round(v["offset"], 2),
                           presentation=round(v["presentation"], 2), inset=v["inset"])
                      for v in frame["views"] if v.get("class") == "HostingScrollView"]
            print(round(frame["time"] - event["time"], 3), values,
                  [v for v in frame["views"] if v.get("handoff")])

if __name__ == "__main__":
    main()
