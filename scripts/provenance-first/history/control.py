"""Checkpoint-1 history recovery controls; never launches inference or touches a vault."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE.parent))
import checkpoint as previous
from fixtures import encoded, load, require

ROOT, PF = previous.ROOT, previous.WORK
WORK = PF / "history-recovery"
RUN = PF / "runs/history-recovery"
GIB = 1024 ** 3
CAP, RESERVE = 18 * GIB, 10 * GIB
_pause_signal = False


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def checked(path):
    path = Path(path).absolute()
    require(path.resolve() == path, "history output path contains a symlink")
    require(any(path.is_relative_to(root) and path != root for root in (WORK, RUN)),
            "history output escapes its isolated workspace")
    return path


def publish(path, value):
    path = checked(path)
    if path.exists():
        require(path.read_bytes() == encoded(value), f"immutable artifact changed: {path.name}")
    else:
        previous.atomic(path, value)


def accounting(free, initial, scoped, external):
    require(all(type(v) is int and v >= 0 for v in (free, initial, scoped, external)),
            "invalid resource accounting")
    growth = max(scoped + external, max(0, initial - free))
    require(free >= RESERVE, "free-space reserve below 10 GiB; stop without cleanup")
    require(growth <= CAP, "approved growth above 18 GiB; stop without resetting baseline")
    return dict(freeBytes=free, scopedBytes=scoped, externalGrowthBytes=external,
                conservativeGrowthBytes=growth, capBytes=CAP, reserveBytes=RESERVE)


def resources():
    baseline = load(PF / "resources.json")
    return accounting(shutil.disk_usage(PF).free, baseline["initialFreeBytes"],
                      previous.allocated(PF) + previous.allocated(previous.CODE),
                      sum(max(0, previous.allocated(Path(p)) - start)
                          for p, start in baseline["externalBaselines"].items()))


def register():
    measure = resources()
    require((WORK / "BUDGET.md").is_file(), "approval documentation missing")
    target = WORK / "approval.json"
    if target.exists():
        verify_preserved()
        return load(target)
    # Bind old source/experiment documents without editing their frozen manifests.
    paths = [p for p in PF.rglob("*") if p.is_file() and not p.is_symlink()
             and not p.is_relative_to(WORK) and not p.is_relative_to(PF / "runs")
             and p.suffix in {".json", ".md"}]
    paths += [p for p in previous.CODE.rglob("*") if p.is_file()
              and not p.is_relative_to(CODE) and p.suffix in {".py", ".swift"}]
    paths += list((ROOT / "Remember/Remember").glob("*.swift"))
    record = dict(approvedBy="user", approvalReply="Yes approved", capBytes=CAP,
                  reserveBytes=RESERVE, baselineReset=False,
                  scope="history-recovery checkpoint 1 only", resources=measure,
                  budgetSHA256=digest(WORK / "BUDGET.md"),
                  preserved={str(p.relative_to(ROOT)): digest(p) for p in sorted(set(paths))})
    publish(target, record)
    return record


def verify_preserved():
    approval = load(WORK / "approval.json")
    require(approval["capBytes"] == CAP and approval["reserveBytes"] == RESERVE
            and approval["baselineReset"] is False, "resource approval changed")
    require(approval["budgetSHA256"] == digest(WORK / "BUDGET.md"), "budget document changed")
    for name, expected in approval["preserved"].items():
        path = ROOT / name
        require(path.resolve().is_relative_to(ROOT), "preservation path escaped repository")
        require(digest(path) == expected, f"preserved source/report changed: {name}")
    return approval


class Paused(Exception):
    pass


def boundary():
    if _pause_signal or (WORK / "pause.request.json").exists():
        raise Paused("saved unit boundary")
    return resources()


@contextmanager
def worker(resume=False):
    global _pause_signal
    WORK.mkdir(parents=True, exist_ok=True)
    with checked(WORK / "worker.lock").open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_preserved()
        marker = checked(WORK / "pause.request.json")
        if resume and marker.exists():
            marker.rename(WORK / f"pause-resumed-{time.time_ns()}.json")
        _pause_signal = False
        def requested(signum, frame):
            global _pause_signal
            _pause_signal = True
        old = {sig: signal.signal(sig, requested) for sig in (signal.SIGINT, signal.SIGTERM)}
        previous.atomic(checked(WORK / "worker.json"), dict(pid=os.getpid(), running=True))
        try:
            boundary()
            yield
        finally:
            previous.atomic(checked(WORK / "worker.json"), dict(pid=os.getpid(), running=False))
            for sig, handler in old.items():
                signal.signal(sig, handler)


def pause():
    previous.atomic(checked(WORK / "pause.request.json"), dict(reason="user-request"))
    # Native probe observes this second marker after a bounded library unit.
    previous.atomic(checked(RUN / "output/pause.request"), dict(reason="user-request"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("register", "resources", "verify", "pause"))
    args = parser.parse_args()
    if args.command == "register":
        result = register()
        print(json.dumps({"approvalSHA256": digest(WORK / "approval.json"),
                          "preservedFiles": len(result["preserved"]), "resources": result["resources"]}))
    elif args.command == "resources": print(json.dumps(resources()))
    elif args.command == "verify":
        print(json.dumps({"preservedFiles": len(verify_preserved()["preserved"])}))
    else:
        pause()
        print("Pause requested; safe-to-close requires worker/agent confirmation.")


if __name__ == "__main__":
    main()
