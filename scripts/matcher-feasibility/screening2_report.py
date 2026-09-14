"""Frozen screen ranking, bounded development confirmation and final verdict."""
from screening2_common import *
from screening2_metrics import counts,select,with_decisions,ranking
from screening2_data import features,source_data,partition
from screening2_models import predict_trial


def summarize(run):
    output=run/"screen-summary.json"
    if output.exists():return read(output)
    result=[]
    folds=read(run/"folds.json")["folds"]
    for trial in read(run/"trials.json")["configurations"]:
        reports=[read(run/"screen"/fold["id"]/f"{trial['id']}.json") for fold in folds]
        rows=[row for record in reports for row in record["evaluation"]]
        require(len(rows)==3420 and len({r["id"] for r in rows})==3420,"screen OOF coverage failed")
        result.append({"trial":trial["id"],"family":trial["family"],"qualifyingFolds":sum(r["selection"] is not None for r in reports),
                       "pooled":counts(rows,stored=True),"folds":[r["metrics"] for r in reports]})
    control=[row|{"score":row["probabilities"][0]} for fold in folds
             for row in read(AUDIT/"ablations"/fold["id"]/"all_six.json")["partitions"]["evaluation"]]
    record={"trials":result,"control":{"trial":"all-six-C10","pooled":counts(control,stored=True)},
            "testAccess":False,"developmentAccess":False}
    save(output,record);return record


def choose(run):
    path=run/"selection.json"
    if path.exists():return read(path)
    report=summarize(run);fallback=all(r["qualifyingFolds"]==0 for r in report["trials"])
    # Stable ID ordering implements the proposed lower-family/ID tie break.
    ordered=sorted(sorted(report["trials"],key=lambda r:r["trial"]),key=lambda r:ranking(r,fallback),reverse=True)
    picked=[];families=set()
    for trial in ordered:
        if trial["family"] not in families:picked.append(trial["trial"]);families.add(trial["family"])
        if len(picked)==2:break
    result={"at":now(),"selectedTrials":picked,"ranking": [r["trial"] for r in ordered],"diagnosticFallback":fallback,
            "screenSummarySHA256":sha(run/"screen-summary.json"),"developmentUsedForSelection":False,
            "policy":"At most two families; confirmation is exploratory, not heldout. Every stochastic seed reported."}
    save(path,result);return result


def quality(metric,baseline):
    precision=metric["precision"];macro=metric["macroRecall"]
    return {"precision":precision is not None and precision>=.95,
            "acceptedCount":metric["acceptedKnown"]>=30,
            "macroRecallGain":macro is not None and macro+1e-12>=baseline["macroRecall"]+.05,
            "precisionDrop":precision is not None and baseline["precision"] is not None and precision+1e-12>=baseline["precision"]-.01,
            "coverage":metric["missingKnown"]==0}


def confirmation(run,external,pause_after_steps=None):
    chosen=choose(run)
    fit_ids=[f"mf{i:02}" for i in range(1,19)];dev_ids=[f"mf{i:02}" for i in range(19,25)]
    data=features(run,fit_ids,True);_,_,embeddings=source_data(True)
    dev=partition(data["rows"],dev_ids)
    inner=[fit_ids[i::3] for i in range(3)]
    baseline_rows=read(BASELINE/"baseline/C-10.json")["predictions"]["development"]
    from stage2_metrics import accepted
    threshold=read(BASELINE/"baseline-selected.json")["threshold"]
    baseline=counts([r|{"score":r["probabilities"][0],"accepted":accepted(r,threshold)} for r in baseline_rows],stored=True)
    results=[]
    for trial in chosen["selectedTrials"]:
        seeds=[17] if trial.startswith("A") or trial=="B1" else [17,29,41]
        for seed in seeds:
            output=run/"confirmation"/f"{trial}-seed-{seed}.json"
            if output.exists():results.append(read(output));continue
            boundary(run,f"confirmation:{trial}:{seed}")
            rows=predict_trial(run,external,trial,fit_ids,seed,data,dev,embeddings,inner,pause_after_steps)
            selected=select(rows);threshold=selected["threshold"] if selected else None
            metric=counts(rows,threshold);gates=quality(metric,baseline)
            record={"trial":trial,"seed":seed,"selectionSHA256":sha(run/"selection.json"),"threshold":threshold,
                    "thresholdSelection":selected,"rows":with_decisions(rows,threshold),"metrics":metric,"gates":gates,
                    "passed":all(gates.values()),"testAccess":False,"limitation":"Same inspected development libraries used to calibrate/report; not an independent test."}
            save(output,record);results.append(record)
            print(__import__('json').dumps({"phase":"confirmation-complete","trial":trial,"seed":seed,"passed":record["passed"],"metrics":metric}),flush=True)
    result={"selectedTrials":chosen["selectedTrials"],"baseline":baseline,"candidates":results,
            "familyPassed":{trial:all(r["passed"] for r in results if r["trial"]==trial) for trial in chosen["selectedTrials"]},
            "testAccess":False,"phoneUsed":False,"stopForUserReview":True}
    path=run/"confirmation-summary.json"
    if not path.exists():save(path,result)
    else:require(read(path)==result,"confirmation replay changed")
    return result
