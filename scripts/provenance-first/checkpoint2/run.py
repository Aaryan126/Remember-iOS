#!/usr/bin/env python3
"""Checkpoint-2 entry point. Offline, pauseable, never changes production or Git."""
import argparse
import time
import common as c


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "pause"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-units", type=int)
    args = parser.parse_args()
    if args.command == "pause":
        c.pf1.atomic(c.WORK / "pause.request.json", {"requestedAtUnix": time.time()})
        c.log(pauseRequested=True, safeToClose=False)
        return
    try:
        with c.worker(resume=args.resume):
            c.boundary()
            from preflight import run
            c.log(result=run(args.max_units))
    except c.Paused as error:
        c.log(status="paused", reason=str(error), workerStopped=True)
    except Exception as error:
        c.pf1.atomic(c.WORK / f"runs/failures/{time.time_ns()}.json",
                     {"type": type(error).__name__, "message": str(error)})
        c.log(status="stopped", error=str(error))
        raise


if __name__ == "__main__":
    main()
