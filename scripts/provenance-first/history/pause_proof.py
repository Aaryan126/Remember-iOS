"""Capture and verify immutable completed units across the explicit pause/resume."""
import argparse
import json

import control as c
import verify_coverage as coverage


def files(phase):
    paths = list((c.WORK / "units").glob("*/*.json"))
    if phase == "native":
        coverage.artifact_paths()
        paths += list((c.RUN / "output").glob("*.receipt.json"))
        paths += list((c.RUN / "output").glob("*.projection.json"))
        paths += list((c.RUN / "output").glob("*/ledger.json"))
        paths += list((c.RUN / "output").glob("*/synthetic-ledger.json"))
        paths += list((c.RUN / "output").glob("history-invariants.json"))
    return {str(path.relative_to(c.ROOT)): dict(sha256=c.digest(path), mtimeNS=path.stat().st_mtime_ns)
            for path in sorted(set(paths))}


def capture(phase):
    saved = files(phase)
    c.require(bool(saved), "no completed units to preserve")
    worker = c.load(c.WORK / "worker.json")
    c.require(worker["running"] is False, "worker must be stopped for pause proof")
    c.publish(c.WORK / f"{phase}-pause-before.json", dict(files=saved, workerStopped=True))


def verify(phase):
    prior = c.load(c.WORK / f"{phase}-pause-before.json")
    resumed = list(c.WORK.glob("pause-resumed-*.json"))
    c.require(bool(resumed), "no acknowledged pause/resume marker")
    current = files(phase)
    c.require(all(current.get(name) == record for name, record in prior["files"].items()),
              "completed artifact changed across resume")
    c.require(c.load(c.WORK / "worker.json")["running"] is False, "worker still running")
    result = dict(status="passed", preservedFiles=len(prior["files"]), workerStopped=True,
                  pauseBeforeSHA256=c.digest(c.WORK / f"{phase}-pause-before.json"),
                  acknowledgedMarkers={path.name: c.digest(path) for path in sorted(resumed)})
    c.publish(c.WORK / f"{phase}-pause-proof.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("capture", "verify"))
    parser.add_argument("phase", choices=("fixture", "native"))
    args = parser.parse_args()
    if args.command == "capture": capture(args.phase)
    else: print(json.dumps(verify(args.phase)))
