#!/usr/bin/env python3
"""Stage-1-only screening driver. Pause cooperatively; stop for user review."""
import argparse
import json
import sys

from screening_common import *
from stage5 import Tee


def verify_upstream():
    # Read-only verification, including all previously frozen external artifacts.
    from stage5 import verify
    result = verify(NEURAL,WORKSPACE/"stage5"/NEURAL.name)
    require(result["complete"],"prior feasibility incomplete")
    baseline = read(BASELINE/"complete.json")
    verify_files(BASELINE,baseline["files"])
    verify_files(WORKSPACE,baseline["workspaceFiles"])
    return {"at":now(),"neural":result,"baselineCompleteSHA256":sha(BASELINE/"complete.json")}


def verify(run,external):
    require((run/"manifest.json").exists(),"run not prepared")
    require(read(run/"manifest.json")["bindings"]==bindings(),"frozen source/input changed")
    if (run/"complete.json").exists():
        record = read(run/"complete.json")
        verify_files(run,record["files"]);verify_files(external,record["externalFiles"])
        return {"verified":True,"complete":True,"completeSHA256":sha(run/"complete.json")}
    return {"verified":True,"complete":False}


def report(run):
    ablation = read(run/"ablation-summary.json")["profiles"]
    review = read(run/"review-summary.json")
    sanity = read(run/"sanity/result.json")
    issues = review["labelAssessments"].get("possible_label_issue",0)+review["labelAssessments"].get("insufficient_evidence",0)
    return {"stage":1,"complete":True,"stage2Authorized":False,"stopForUserReview":True,
        "sanityPassed":sanity["passed"],"contextOrLabelConcerns":issues,
        "ablation":{k:{"qualifiedCalibrationFolds":v["qualifyingCalibrationFolds"],
                       "precision":v["pooledOOF"]["precision"],"macroRecall":v["pooledOOF"]["macroLibraryRecall"],
                       "acceptedKnown":v["pooledOOF"]["acceptedKnownPairs"],"averagePrecision":v["ranking"]["averagePrecision"]}
                    for k,v in ablation.items()},
        "decision":"Review evidence and any context/label concerns before authorizing Stage2; no automatic dataset edits or test opening.",
        "testAccess":False,"phoneUsed":False}


def run_all(run,external,resume=False,pause_after_steps=None):
    from screening_review import prepare_review,summarize_review
    from screening_ablation import run_ablation,summarize,PROFILES
    from screening_sanity import run_sanity
    from screening_diagnostics import run_diagnostics
    from audit_screening import audit
    initialize(run,external)
    if (run/"complete.json").exists(): print(json.dumps(verify(run,external)));return
    marker = run/"control/pause-requested.json"
    if resume and marker.exists(): marker.rename(marker.with_name(f"resumed-{time.time_ns()}.json"))
    boundary(run,external,"initialized")
    upstream = verify_upstream()
    save(run/"upstream-checks"/f"{time.time_ns()}.json",upstream)
    prepare_review(run)
    for fold in read(run/"folds.json")["folds"]:
        for profile in PROFILES: run_ablation(run,external,fold,profile)
    if not (run/"ablation-summary.json").exists(): summarize(run)
    run_sanity(run,external,pause_after_steps)
    run_diagnostics(run,external)
    cases = read(run/"review/selection.json")["cases"]
    if not all((run/"review/context"/f"{r['id']}.json").exists() for r in cases):
        request_pause(run,"awaiting_executing_agent_review")
        boundary(run,external,"compute-saved-awaiting-review")
    if not (run/"review-summary.json").exists(): save(run/"review-summary.json",summarize_review(run))
    boundary(run,external,"audit")
    if not (run/"audit.json").exists(): save(run/"audit.json",audit(run,external))
    else: require(audit(run,external)==read(run/"audit.json"),"audit replay changed")
    if not (run/"report.json").exists(): save(run/"report.json",report(run))
    initialize(run,external)
    files = {k:v for k,v in files_in(run).items() if k!="worker.lock" and not k.startswith("logs/")}
    save(run/"complete.json",{"at":now(),"stage":1,"stageComplete":True,"stage2Started":False,
        "testAccess":False,"files":files,"externalFiles":files_in(external),"stopForUserReview":True})
    print(json.dumps({"status":"complete","safeToCloseLaptop":True,"report":read(run/"report.json")}),flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["prepare","run","pause","verify","review"])
    parser.add_argument("--run",required=True)
    parser.add_argument("--stage",default="audit")
    parser.add_argument("--resume",action="store_true")
    parser.add_argument("--pause-after-sanity-steps",type=int)
    parser.add_argument("--file",type=Path)
    args = parser.parse_args();stage_guard(args.stage)
    run,external = locations(args.run);setup()
    if args.action=="pause": print(json.dumps({"status":request_pause(run)}));return
    handle = lock(run)
    stdout,stderr = sys.stdout,sys.stderr
    log = None
    try:
        if args.action=="run":
            (run/"logs").mkdir(exist_ok=True)
            log = (run/"logs"/f"driver-{time.time_ns()}.log").open("x")
            sys.stdout,sys.stderr = Tee(stdout,log),Tee(stderr,log)
            run_all(run,external,args.resume,args.pause_after_sanity_steps)
        elif args.action=="prepare":
            initialize(run,external)
            from screening_review import prepare_review
            prepare_review(run);print('{"prepared":true}')
        elif args.action=="verify": print(json.dumps(verify(run,external)))
        else:
            require(args.file is not None,"review file required")
            require(not (run/"complete.json").exists(),"completed review immutable")
            verify(run,external)
            from screening_review import import_reviews
            import_reviews(run,args.file);print('{"reviewImported":true}')
    except Paused as error:
        print(json.dumps({"status":"paused","phase":str(error),"safeToCloseLaptop":True}),flush=True)
    except Exception as error:
        save(run/"failures"/f"{time.time_ns()}.json",{"at":now(),"type":type(error).__name__,"error":str(error)})
        raise
    finally:
        handle.close();sys.stdout,sys.stderr = stdout,stderr
        if log: log.close()


if __name__=="__main__": main()
