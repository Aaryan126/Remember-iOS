#!/usr/bin/env python3
"""One-shot execution of the second, exact A+B cleanup approval."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

spec = importlib.util.spec_from_file_location("audit", Path(__file__).with_name("inspect-cleanup.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
NAMES = [
    "search-handoff/edge-top.mp4.sb-61fc4779-9erjtv",
    "search-handoff/final-ui.mp4.sb-61fc4779-wpPM5Z",
    "search-overlay/overlay-motion.mp4.sb-61fc4779-rNnViX",
    "answer-support/native-build/Index.noindex",
    "search-handoff/top-dark.mp4",
    "search-handoff/stable-host-dark.mp4",
    "search-handoff/stable-layout-top.mp4",
    "search-overlay/scoped-full-suite.mp4",
    "search-overlay/scoped-removal.mp4",
]


def inventory(name):
    path = audit.RUN / name
    if not path.exists() or path.is_symlink() or path.resolve() != path:
        raise ValueError("Missing or redirected target: " + name)
    if not path.is_relative_to(audit.ROOT) or ".git" in path.parts:
        raise ValueError("Unsafe target")
    if path.is_dir() and any(p.name == ".git" for p in path.rglob("*")):
        raise ValueError("Git metadata in target")
    relative = str(path.relative_to(audit.ROOT))
    if subprocess.check_output(["git", "ls-files", "--", relative], cwd=audit.ROOT):
        raise ValueError("Tracked target")
    subprocess.run(["git", "check-ignore", "-q", relative], cwd=audit.ROOT, check=True)
    return {"path": relative, "bytes": int(subprocess.check_output(
        ["du", "-sk", str(path)], text=True).split()[0]) * 1024}


def verify():
    return {name: audit.verify_backup(name) for name in audit.PROTECTED}


def main():
    os.umask(0o077)
    proposal = audit.ROOT / "Evaluation/ProvenanceFirst/search-handoff/CLEANUP-PROPOSAL-2.md"
    if re.findall(r"^\| `([^`]+)` \|", proposal.read_text(), re.M) != NAMES:
        raise ValueError("Approved proposal differs")
    for command in subprocess.check_output(["ps", "-axo", "comm="], text=True).splitlines():
        if Path(command.strip()).name in {"xcodebuild", "simctl", "ffmpeg"}:
            raise ValueError("Build or recording worker running")
    before = verify()
    rows = [inventory(name) for name in NAMES]
    receipt = audit.RUN / "search-handoff/cleanup-approved-2.json"
    state = {"complete": False, "targets": rows, "deleted": [],
             "verifiedFilesBefore": {n: v[0] for n, v in before.items()},
             "freeBytesBefore": shutil.disk_usage(audit.ROOT).free}
    with receipt.open("x") as stream:
        json.dump(state, stream, indent=2)
    try:
        for name in NAMES:
            inventory(name)
            path = audit.RUN / name
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            state["deleted"].append(name)
            receipt.write_text(json.dumps(state, indent=2) + "\n")
        after = verify()
        if before != after:
            raise ValueError("Protected backup verification changed")
        state["verifiedFilesAfter"] = {n: v[0] for n, v in after.items()}
        state["complete"] = True
    finally:
        state["freeBytesAfter"] = shutil.disk_usage(audit.ROOT).free
        state["netRecoveredBytes"] = state["freeBytesAfter"] - state["freeBytesBefore"]
        receipt.write_text(json.dumps(state, indent=2) + "\n")
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
