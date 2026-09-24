#!/usr/bin/env python3
"""Second approved resource-only amendment; no inference or policy changes."""
from pathlib import Path
import runpy
import shutil
import sys
import time

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE.parent / "budget5"))
import approved_run as previous

c, runner = previous.c, previous.runner
GIB = 1024 ** 3
CAP, RESERVE = 8 * GIB, 10 * GIB
APPROVAL = runner.PUBLIC / "budget-8gib.json"
PEAK = 0


def accounting(free, initial, scoped, external):
    c.require(all(type(v) is int and v >= 0 for v in (free, initial, scoped, external)), "invalid resource accounting")
    growth = max(scoped + external, max(0, initial - free))
    c.require(free >= RESERVE, "free-space reserve below 10 GiB; stop, do not clean automatically")
    c.require(growth <= CAP, "approved new-write budget above 8 GiB; stop, do not clean automatically")
    return dict(freeBytes=free, scopedBytes=scoped, externalGrowthBytes=external,
                conservativeGrowthBytes=growth, capBytes=CAP, reserveBytes=RESERVE)


def resource_check(work=c.PF):
    global PEAK
    c.require(Path(work).resolve() == c.PF.resolve(), "budget approval is comparison-specific")
    info = c.read(c.PF / "resources.json")
    result = accounting(shutil.disk_usage(work).free, info["initialFreeBytes"],
                        c.pf1.allocated(work) + c.pf1.allocated(c.pf1.CODE),
                        sum(max(0, c.pf1.allocated(Path(p)) - start) for p, start in info["externalBaselines"].items()))
    PEAK = max(PEAK, result["conservativeGrowthBytes"])
    return result


def register():
    with c.worker():
        previous.verify()
        c.require(runner.verify_job("development")[3] == dict(embeddings=117, neural=501, pairs=501), "development stop changed")
        c.require(runner.verify_job("evaluation")[3] == dict(embeddings=109, neural=376, pairs=0), "evaluation stop changed")
        c.require(not (runner.RUN / "evaluation/predictions").exists(), "evaluation policy predictions already started")
        paths = [Path(__file__), CODE / "test_budget8.py", runner.PUBLIC / "BUDGET-AMENDMENT-8GIB.md",
                 previous.APPROVAL, c.PF / "resources.json", runner.PUBLIC / "selection.json"]
        saved = [p for split in ("development", "evaluation") for p in sorted((runner.RUN / split).rglob("*.json"))]
        c.publish(APPROVAL, {"approvedBy": "user", "approvalReply": "Yes u may", "capBytes": CAP,
                  "reserveBytes": RESERVE, "manifestSHA256": runner.verify_base(), "reference": runner.REFERENCE,
                  "baselineReset": False, "inferenceCodeChanged": False,
                  "hashes": {str(p): c.digest(p) for p in paths},
                  "savedUnits": {str(p): {"sha256": c.digest(p), "mtimeNS": p.stat().st_mtime_ns} for p in saved}})
        c.log(approvalSHA256=c.digest(APPROVAL), resources=resource_check(), preservedFiles=len(saved))


def verify():
    previous.verify()
    record = c.read(APPROVAL)
    c.require(record["capBytes"] == CAP and record["reserveBytes"] == RESERVE
              and record["manifestSHA256"] == runner.verify_base(), "approval scope changed")
    for path, expected in record["hashes"].items():
        c.require(c.digest(path) == expected, f"budget amendment binding changed: {path}")
    for path, expected in record["savedUnits"].items():
        c.require(c.digest(path) == expected["sha256"] and Path(path).stat().st_mtime_ns == expected["mtimeNS"], "pre-amendment saved file changed")
    return record


def main():
    c.require(len(sys.argv) >= 2, "use register, resources, model <command>, or ledger <command>")
    mode, arguments = sys.argv[1], sys.argv[2:]
    if mode == "register":
        c.require(not arguments, "unexpected register arguments")
        register()
        return
    c.require(mode in ("resources", "model", "ledger"), "invalid approved runner")
    verify()
    resource_check()
    if mode == "resources":
        c.log(resources=resource_check())
        return
    c.require(bool(arguments) and (mode != "model" or arguments[0] != "prepare"), "cannot refreeze comparison")
    path = CODE.parent / "comparison" / ("pc_runner.py" if mode == "model" else "pc_ledger.py")
    original_check, original_argv = c.pf1.resource_check, sys.argv
    attempt = runner.PUBLIC / "budget-runs" / f"{time.time_ns()}.json"
    failure = None
    try:
        c.pf1.resource_check = resource_check
        sys.argv = [str(path), *arguments]
        runpy.run_path(str(path), run_name="__main__")
    except BaseException as error:
        failure = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        c.pf1.resource_check, sys.argv = original_check, original_argv
        c.publish(attempt, {"mode": mode, "arguments": arguments, "approvalSHA256": c.digest(APPROVAL),
                  "peakPassingGrowthBytes": PEAK, "failure": failure})


if __name__ == "__main__": main()
