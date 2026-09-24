#!/usr/bin/env python3
"""Stage fictional compiled inputs and run the existing isolated simulator probe."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

from checkpoint import WORK, atomic, resource_check, verify_units, verify_native_paths, writer
from fixtures import load, require, sha

DEVICE = "C530FCC2-DD67-4115-97D9-C4E34807EC57"
BUNDLE = "SimpleStudio.Remember.ProvenanceFirstProbe"


def call(*args):
    return subprocess.check_output(["xcrun", "simctl", *args], text=True).strip()


def execute(maximum=None, invariants=False):
    require(maximum is None or maximum > 0, "max-runs must be positive")
    with writer(WORK):
        require(len(verify_units(WORK)) == 24, "complete frozen compiler units required")
        resource_check(WORK)
        require(not (WORK / "pause.request.json").exists(), "pause requested; resume compiler first to acknowledge")
        root = WORK / "runs/checkpoint1"
        source = root / "input.json"
        expected = {"schemaVersion": 1, "runs": [load(WORK / "units" / key / "ledger.json")["runs"][0]
                    for key in verify_units(WORK)]}
        require(load(source) == expected, "compiled native input changed")
        container = Path(call("get_app_container", DEVICE, BUNDLE, "data")).resolve()
        allowed = Path.home() / "Library/Developer/CoreSimulator/Devices" / DEVICE / "data/Containers/Data/Application"
        require(container.parent == allowed and container.is_dir(), "unexpected simulator app container")
        private = container / "Documents/ProvenanceFirst"
        require(private.resolve().is_relative_to(container), "private input path escaped")
        private.mkdir(parents=True, exist_ok=True)
        target = private / (sha(source.read_bytes()) + ".json")
        if not target.exists():
            # Generated fixture staging, not source editing. Refuse to overwrite another input.
            with target.open("xb") as stream:
                stream.write(source.read_bytes())
        require(target.read_bytes() == source.read_bytes(), "staged input differs")
        output = root / "output"
        output.mkdir(parents=True, exist_ok=True)
        verify_native_paths(output)
        args = ["xcrun", "simctl", "launch", "--console", DEVICE, BUNDLE,
                "--input", str(target), "--output", str(output)]
        if maximum:
            args += ["--max-runs", str(maximum)]
        if invariants:
            args += ["--invariants"]
        attempt = str(time.time_ns())
        log = root / ("native-" + attempt + ".log")
        receipt = root / ("launch-" + attempt + ".json")
        atomic(receipt, {"status": "launching", "device": DEVICE, "bundle": BUNDLE,
                         "inputSHA256": sha(source.read_bytes()), "command": args, "log": log.name})
        with log.open("xb") as stream:
            process = subprocess.Popen(args, stdout=stream, stderr=subprocess.STDOUT)
            try:
                # Keep budget checks alive while native work runs. Pause stays library-bounded.
                while process.poll() is None:
                    time.sleep(1)
                    try:
                        resource_check(WORK)
                    except ValueError:
                        atomic(output / "pause.request", {"reason": "resource-limit"})
                        raise
                require(process.returncode == 0, f"native launch/replay failed; see {log}")
            except BaseException:
                atomic(output / "pause.request", {"reason": "coordinator-interrupted"})
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    # Only this experiment's app is in scope; preserve incomplete attempts.
                    subprocess.run(["xcrun", "simctl", "terminate", DEVICE, BUNDLE], check=False,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    process.terminate()
                    process.wait(timeout=10)
                atomic(receipt, {"status": "interrupted", "inputSHA256": sha(source.read_bytes()), "log": log.name})
                raise
        state = load(output / "status.json")
        require(state["batchSHA256"] == sha(source.read_bytes()) and state["status"] in {"paused", "complete"}, "native status mismatch")
        if invariants:
            verify_native_paths(output)
            invariant = load(output / "invariants.receipt.json")
            require(invariant["status"] == "passed", "native invariants not passed")
            binding_path = root / "ledger/project/Sources/bindings.json"
            atomic(output / "invariant-execution.json", {
                "batchSHA256": sha(source.read_bytes()), "bindingsSHA256": sha(binding_path.read_bytes()),
                "invariantReceiptSHA256": sha((output / "invariants.receipt.json").read_bytes()),
                "executedInvariants": True, "launchReceipt": receipt.name, "command": args})
        atomic(receipt, {"status": state["status"], "exitCode": process.returncode,
                         "device": DEVICE, "bundle": BUNDLE, "inputSHA256": sha(source.read_bytes()),
                         "command": args, "log": log.name, "completed": int(state["completed"])})
        return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-runs", type=int)
    parser.add_argument("--invariants", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(execute(arguments.max_runs, arguments.invariants), indent=2))
