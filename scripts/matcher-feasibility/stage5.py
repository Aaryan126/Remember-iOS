#!/usr/bin/env python3
"""Checkpointed Stage 5 only. Explicit resume; never starts Stage 6."""
import argparse
import json
import sys

from stage5_common import *


class Tee:
    def __init__(self,stream,log): self.stream,self.log=stream,log
    def write(self,value):
        self.log.write(value);self.log.flush();return self.stream.write(value)
    def flush(self): self.log.flush();self.stream.flush()
    def isatty(self): return False


def verify(run, external):
    initialize(run, external)
    if (run / "complete.json").exists():
        value=read(run / "complete.json")
        verify_files(run,value["files"])
        verify_files(external,value["externalFiles"])
        return {"verified":True,"complete":True,"files":len(value["files"]),"externalFiles":len(value["externalFiles"]),
                "completeSHA256":sha(run / "complete.json")}
    return {"verified":True,"complete":False}


def complete(run, external):
    boundary(run,"completion")
    initialize(run, external)
    quality=read(run / "quality-report.json")
    require(len(list((run / "epochs").glob("*.json")))==9,"missing training candidates")
    for seed in [17,29,41]:
        for epoch in [1,2,3]:
            require((run / "evaluations" / f"seed-{seed}-epoch-{epoch}/development/summary.json").exists(),"missing development evaluation")
    history=read(DATA / "baseline-context.json")
    for key in ["artifacts","productionSources"]:
        require(all(sha(ROOT/name)==digest for name,digest in history[key].items()),"production or historical evidence changed")
    files={name:digest for name,digest in files_in(run).items() if name!="worker.lock" and not name.startswith("logs/")}
    save(run / "complete.json",{"schemaVersion":1,"stage":5,"completedAt":now(),"stageComplete":True,
        "qualityPassed":quality["passed"],"testResultsOpened":quality["testResultsOpened"],"stage6Started":False,
        "stopAfterStage":True,"files":files,"externalFiles":files_in(external)})


def run_all(run, external, resume=False, pause_after_steps=None):
    from stage5_data import prepare_tokens
    from stage5_train import train_epoch
    from stage5_evaluate import evaluate_candidate,select_candidate,final_report
    initialize(run,external)
    if (run / "complete.json").exists(): print(json.dumps(verify(run,external)));return
    marker=run / "control/pause-requested.json"
    if marker.exists() and resume: marker.rename(marker.parent / f"resumed-{time.time_ns()}.json")
    boundary(run,"initialized")
    for split in ["train","development"]: prepare_tokens(run,external,split)
    for seed in [17,29,41]:
        for epoch in range(3):
            train_epoch(run,external,seed,epoch,pause_after_steps=pause_after_steps)
            evaluate_candidate(run,external,seed,epoch+1)
            boundary(run,f"candidate-complete:{seed}:{epoch+1}")
    selected=select_candidate(run,external)
    print(json.dumps({"phase":"development-selection-frozen","selection":selected}),flush=True)
    if selected["status"]=="selected" and not (run / "test-access.json").exists():
        save(run / "test-access.json",{"at":now(),"selectionSHA256":sha(run / "selection.json"),
            "testFilesSHA256":{kind:sha(RELEASE / f"{kind}-test.json") for kind in ["inputs","labels"]},
            "policy":"one heldout evaluation of development-frozen neural winner and Stage2-frozen baseline; no test-driven tuning"})
    final_report(run,external)
    complete(run,external)
    print(json.dumps({"status":"complete","stage":5,"safeToCloseLaptop":True,"quality":read(run / "quality-report.json")}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["prepare","run","pause","verify","retention"])
    parser.add_argument("--run",required=True)
    parser.add_argument("--resume",action="store_true")
    parser.add_argument("--pause-after-steps",type=int)
    parser.add_argument("--policy",choices=["keep-all","latest-two"])
    parser.add_argument("--authorization")
    args=parser.parse_args(); run,external=paths(args.run)
    setup()
    if args.action=="pause": print(json.dumps({"status":request_pause(run)}));return
    if args.action=="retention":
        require((run/"manifest.json").exists() and not (run/"complete.json").exists(),"no active run")
        require(args.policy and args.authorization,"explicit user authorization required")
        save(run/"control/retention-policy.json",{"at":now(),"policy":args.policy,"explicitUserAuthorization":args.authorization})
        print('{"retentionPolicySaved":true}');return
    handle=lock(run)
    original_stdout,original_stderr=sys.stdout,sys.stderr
    log=None
    if args.action=="run":
        folder=run/"logs";folder.mkdir(exist_ok=True)
        log=(folder/f"driver-{time.time_ns()}.log").open("x")
        sys.stdout=Tee(sys.stdout,log);sys.stderr=Tee(sys.stderr,log)
    try:
        if args.action=="prepare": initialize(run,external);print('{"prepared":true}')
        elif args.action=="verify": print(json.dumps(verify(run,external)))
        else: run_all(run,external,args.resume,args.pause_after_steps)
    except Paused as error:
        print(json.dumps({"status":"paused","safeBoundary":str(error),"safeToCloseLaptop":True}),flush=True)
    except Exception as error:
        save(run / "failures" / f"{time.time_ns()}.json",{"at":now(),"errorType":type(error).__name__,"error":str(error)})
        raise
    finally:
        handle.close()
        sys.stdout,sys.stderr=original_stdout,original_stderr
        if log:log.close()


if __name__=="__main__": main()
