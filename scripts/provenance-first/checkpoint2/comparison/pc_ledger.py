#!/usr/bin/env python3
"""Replay frozen predicted actions in the existing fictional-only simulator app."""
import argparse
from pathlib import Path
import subprocess
import time

from pc_native import c
import pc_runner as runner
from pc_policy import ledger_run

DEVICE = "C530FCC2-DD67-4115-97D9-C4E34807EC57"
BUNDLE = "SimpleStudio.Remember.ProvenanceFirstProbe"
NATIVE = c.PF / "runs/current-runtime-comparison"
BINDINGS = c.PF / "runs/checkpoint1/ledger/project/Sources/bindings.json"


def batch():
    choice = runner.verify_selection()
    runs, aliases = [], {}
    for split in ("development","evaluation"):
        for key in ("A",choice["policyKey"]):
            for trace in runner.traces(split,key):
                value = ledger_run(trace)
                runs.append(value)
                if key == "A": aliases[value["id"].removesuffix("-A")+"-B"] = value["id"]
    c.require(len(runs)==96 and len({r["id"] for r in runs})==96,"expected 96 unique native runs")
    return {"schemaVersion":1,"runs":runs}, aliases


def prepare():
    c.boundary()
    c.pf1.verify_native(c.PF)
    value, aliases = batch()
    c.require(NATIVE.resolve().is_relative_to((c.PF/"runs").resolve()),"native output escape")
    path = NATIVE/"input.json"
    if path.exists(): c.require(c.read(path)==value,"native batch changed")
    else: c.pf1.atomic(path,value)
    receipt = {"batchSHA256":c.digest(path),"bindingsSHA256":c.digest(BINDINGS),
               "manifestSHA256":runner.verify_base(),"selectionSHA256":c.digest(runner.PUBLIC/"selection.json"),
               "nativeRuns":96,"BAliases":aliases,"reason":"B uses exactly A placements; only recovery results differ"}
    c.publish(runner.PUBLIC/"ledger-input.json",receipt)
    return receipt


def verify(complete=False):
    manifest = runner.verify_base()
    receipt = c.read(runner.PUBLIC/"ledger-input.json")
    c.require(receipt["manifestSHA256"] == manifest
              and receipt["selectionSHA256"] == c.digest(runner.PUBLIC/"selection.json"), "native comparison identity changed")
    c.require(receipt["batchSHA256"]==c.digest(NATIVE/"input.json") and receipt["bindingsSHA256"]==c.digest(BINDINGS),"native input binding changed")
    expected, aliases = batch()
    c.require(c.read(NATIVE/"input.json")==expected and receipt["BAliases"]==aliases,"native input differs from predictions")
    output = NATIVE/"output"
    c.pf1.verify_native_paths(output)
    done = []
    known = {c.text_hash(r["id"])+".receipt.json" for r in expected["runs"]}
    c.require(all(p.name in known or p.name=="invariants.receipt.json" for p in output.glob("*.receipt.json")),"unexpected native receipt")
    for run in expected["runs"]:
        path = output/(c.text_hash(run["id"])+".receipt.json")
        if not path.exists(): continue
        row = c.read(path)
        c.require(row["id"]==run["id"] and row["batchSHA256"]==receipt["batchSHA256"]
                  and row["bindingsSHA256"]==receipt["bindingsSHA256"],"native receipt identity changed")
        c.require(row["restartVerified"] and row["prefixCount"]==12 and row["historicalPrefixesVerified"]==12,"native state checks incomplete")
        c.require([r["id"] for r in row["prefixes"]]==[e["id"] for e in run["events"]],"native prefix identity mismatch")
        ledger = output/row["attempt"]/"ledger.json"
        c.require(ledger.resolve().is_relative_to(output.resolve()) and c.digest(ledger)==row["ledgerSHA256"],"native ledger mismatch")
        c.require(len(c.read(ledger))==row["ledgerCount"],"native ledger count mismatch")
        done.append({"id":run["id"],"receiptSHA256":c.digest(path)})
    if complete:
        state = c.read(output/"status.json")
        c.require(len(done)==96 and state["status"]=="complete" and int(state["completed"])==96
                  and state["batchSHA256"]==receipt["batchSHA256"]
                  and state["bindingsSHA256"]==receipt["bindingsSHA256"],"native replay incomplete")
        invariant = c.read(output/"invariants.receipt.json")
        binding = c.read(output/"invariant-execution.json")
        c.require(invariant["status"]=="passed" and int(invariant["checks"])>=31,"native invariants failed")
        c.require(binding["batchSHA256"]==receipt["batchSHA256"] and binding["bindingsSHA256"]==receipt["bindingsSHA256"]
                  and binding["invariantReceiptSHA256"]==c.digest(output/"invariants.receipt.json"),"invariant receipt is stale")
        ledger = output/invariant["attempt"]/"ledger.json"
        c.require(ledger.resolve().is_relative_to(output.resolve()) and c.digest(ledger)==invariant["ledgerSHA256"],"invariant ledger mismatch")
    return {"completed":len(done),"receipts":done,"batchSHA256":receipt["batchSHA256"]}


def sim(*args):
    return subprocess.check_output(["xcrun","simctl",*args],text=True,timeout=60).strip()


def execute(maximum=None,invariants=False,resume=False):
    c.require(maximum is None or maximum>0,"max-runs must be positive")
    c.pf1.verify_native(c.PF)
    verify()
    output = NATIVE/"output"
    output.mkdir(parents=True,exist_ok=True)
    if resume:
        for marker in (c.WORK/"pause.request.json",output/"pause.request"):
            if marker.exists(): marker.rename(NATIVE/f"pause-resumed-{time.time_ns()}.json")
    c.boundary()
    devices = __import__("json").loads(sim("list","devices","--json"))
    device = next(d for values in devices["devices"].values() for d in values if d["udid"]==DEVICE)
    if device["state"]=="Shutdown": sim("boot",DEVICE)
    sim("bootstatus",DEVICE,"-b")
    c.boundary()
    container = Path(sim("get_app_container",DEVICE,BUNDLE,"data")).resolve()
    allowed = Path.home()/"Library/Developer/CoreSimulator/Devices"/DEVICE/"data/Containers/Data/Application"
    c.require(container.parent==allowed and container.is_dir(),"unexpected simulator data container")
    installed = Path(sim("get_app_container",DEVICE,BUNDLE,"app"))
    built = c.PF/"runs/checkpoint1/ledger/build/Build/Products/Debug-iphonesimulator/ProvenanceFirstProbe.app"
    c.require(c.digest(installed/"ProvenanceFirstProbe")==c.digest(built/"ProvenanceFirstProbe"),"installed probe differs from recorded build")
    c.require(c.digest(installed/"bindings.json")==c.digest(BINDINGS),"installed probe bindings differ")
    private = container/"Documents/ProvenanceFirst"
    c.require(private.resolve().is_relative_to(container),"private input path escaped")
    private.mkdir(parents=True,exist_ok=True)
    source = NATIVE/"input.json"
    target = private/(c.digest(source)+".json")
    if not target.exists():
        with target.open("xb") as stream: stream.write(source.read_bytes())
    c.require(target.read_bytes()==source.read_bytes(),"staged fictional input differs")
    command = ["xcrun","simctl","launch","--console",DEVICE,BUNDLE,"--input",str(target),"--output",str(output)]
    if maximum: command += ["--max-runs",str(maximum)]
    if invariants:
        c.require(not (output/"invariants.receipt.json").exists(),"do not overwrite invariant receipt")
        command.append("--invariants")
    attempt = str(time.time_ns())
    log = NATIVE/f"launch-{attempt}.log"
    c.pf1.atomic(NATIVE/f"launch-{attempt}.json",{"command":command,"inputSHA256":c.digest(source)})
    with log.open("xb") as stream:
        process = subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                time.sleep(1)
                c.pf1.resource_check()
                if c._paused or (c.WORK/"pause.request.json").exists():
                    c.pf1.atomic(output/"pause.request",{"reason":"requested"})
            c.require(process.returncode==0,f"native replay failed; see {log}")
        except BaseException:
            c.pf1.atomic(output/"pause.request",{"reason":"coordinator-stop"})
            try: process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                subprocess.run(["xcrun","simctl","terminate",DEVICE,BUNDLE],capture_output=True,timeout=15)
                process.terminate()
                process.wait(timeout=10)
            raise
    if invariants:
        c.pf1.verify_native_paths(output)
        record = c.read(output/"invariants.receipt.json")
        c.require(record["status"]=="passed","invariants failed")
        c.pf1.atomic(output/"invariant-execution.json",{"batchSHA256":c.digest(source),"bindingsSHA256":c.digest(BINDINGS),
                    "invariantReceiptSHA256":c.digest(output/"invariants.receipt.json"),"command":command})
    state = c.read(output/"status.json")
    result = verify(complete=state["status"]=="complete")
    if state["status"]=="complete": c.publish(runner.PUBLIC/"native-verification.json",result)
    c.log(phase="native-ledger",status=state["status"],completed=result["completed"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("prepare","run","verify"))
    parser.add_argument("--max-runs",type=int)
    parser.add_argument("--invariants",action="store_true")
    parser.add_argument("--resume",action="store_true")
    args = parser.parse_args()
    try:
        with c.worker(resume=False):
            if args.command=="prepare": prepare()
            elif args.command=="run": execute(args.max_runs,args.invariants,args.resume)
            else: c.log(result=verify(complete=True))
    except c.Paused as error:
        c.log(status="paused",reason=str(error),workerStopped=True)
