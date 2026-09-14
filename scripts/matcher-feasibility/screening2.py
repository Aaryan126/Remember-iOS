#!/usr/bin/env python3
"""Execute only the authorized twelve-trial screening stage; never auto-deploy."""
import argparse
import json
import sys

from screening2_common import *
from stage5 import Tee


def verify(run,external):
    require((run/"manifest.json").exists(),"run not prepared")
    require(read(run/"manifest.json")["bindings"]==bindings(),"source/input binding changed")
    verify_files(run/"source-snapshots",{name:sha(HERE/name) for name in SOURCES})
    if (run/"complete.json").exists():
        result=read(run/"complete.json")
        verify_files(run,result["files"]);verify_files(external,result["externalFiles"])
        return {"verified":True,"complete":True,"completeSHA256":sha(run/"complete.json")}
    return {"verified":True,"complete":False}


def execute(run,external,resume=False,pause_after_steps=None):
    from screening2_data import features,partition,source_data
    from screening2_models import predict_trial,evaluate
    from screening2_report import summarize,choose,confirmation
    from audit_screening2 import audit
    initialize(run,external)
    if (run/"complete.json").exists():print(json.dumps(verify(run,external)));return
    marker=run/"control/pause-requested.json"
    if resume and marker.exists():marker.rename(marker.with_name(f"resumed-{time.time_ns()}.json"))
    boundary(run,"initialized")
    save(run/"upstream-checks"/f"{time.time_ns()}.json",verify_upstream())
    _,_,embeddings=source_data()
    for fold in read(run/"folds.json")["folds"]:
        data=features(run,fold["fit"])
        targets=partition(data["rows"],fold["calibration"]+fold["evaluation"])
        for config in read(run/"trials.json")["configurations"]:
            trial=config["id"];path=run/"screen"/fold["id"]/f"{trial}.json"
            if path.exists():continue
            boundary(run,f"screen:{fold['id']}:{trial}")
            rows=predict_trial(run,external,trial,fold["fit"],17,data,targets,embeddings,fold["hybridInnerValidation"],pause_after_steps)
            result=evaluate(rows,fold["calibration"],fold["evaluation"])|{"trial":trial,"fold":fold,
                "manifestSHA256":sha(run/"manifest.json"),"testAccess":False}
            save(path,result)
            print(json.dumps({"phase":"screen-trial-complete","trial":trial,"fold":fold["id"],"metrics":result["metrics"]}),flush=True)
    summarize(run);selected=choose(run)
    print(json.dumps({"phase":"screen-selection-frozen",**selected}),flush=True)
    result=confirmation(run,external,pause_after_steps)
    boundary(run,"final-audit")
    check=audit(run,external)
    if not (run/"audit.json").exists():save(run/"audit.json",check)
    else:require(read(run/"audit.json")==check,"audit replay changed")
    initialize(run,external)
    files={k:v for k,v in files_in(run).items() if k!="worker.lock" and not k.startswith("logs/")}
    save(run/"complete.json",{"at":now(),"stage":"screening-2","stageComplete":True,"testAccess":False,
         "phoneUsed":False,"productionIntegration":False,"stopForUserReview":True,
         "files":files,"externalFiles":files_in(external),"familyPassed":result["familyPassed"]})
    print(json.dumps({"status":"complete","safeToCloseLaptop":True,"familyPassed":result["familyPassed"]}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["prepare","run","pause","verify"])
    parser.add_argument("--run",required=True)
    parser.add_argument("--resume",action="store_true")
    parser.add_argument("--pause-after-steps",type=int)
    args=parser.parse_args();run,external=paths(args.run);setup()
    if args.action=="pause":print(json.dumps({"status":request_pause(run)}));return
    handle=lock(run);stdout,stderr=sys.stdout,sys.stderr;log=None
    try:
        if args.action=="prepare":initialize(run,external);print('{"prepared":true}')
        elif args.action=="verify":print(json.dumps(verify(run,external)))
        else:
            (run/"logs").mkdir(exist_ok=True);log=(run/"logs"/f"driver-{time.time_ns()}.log").open("x")
            sys.stdout,sys.stderr=Tee(stdout,log),Tee(stderr,log)
            execute(run,external,args.resume,args.pause_after_steps)
    except Paused as error:print(json.dumps({"status":"paused","phase":str(error),"safeToCloseLaptop":True}),flush=True)
    except Exception as error:
        save(run/"failures"/f"{time.time_ns()}.json",{"at":now(),"type":type(error).__name__,"error":str(error)})
        raise
    finally:
        handle.close();sys.stdout,sys.stderr=stdout,stderr
        if log:log.close()


if __name__=="__main__":main()
