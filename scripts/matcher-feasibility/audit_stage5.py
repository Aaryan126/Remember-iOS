#!/usr/bin/env python3
"""Independent Stage 5 evidence audit; never selects on heldout outcomes."""
import argparse
from collections import Counter
from itertools import combinations
import json
import math
from pathlib import Path

import numpy as np

from stage5_common import DATA,ROOT,RELEASE,STAGE2,HERE,read,save,sha,require,paths,now


def gold(split,run=None):
    require(split in ["train","development","test"],"invalid audit split")
    if split=="test":
        from stage5_common import authorize_test
        require(run is not None,"test audit requires a selected run")
        authorize_test(run)
        require(read(run/"test-access.json")["selectionSHA256"]==sha(run/"selection.json"),"test access binding missing")
    inputs=read(RELEASE/f"inputs-{split}.json")
    labels={lib["id"]:lib for lib in read(RELEASE/f"labels-{split}.json")["libraries"]}
    result={}
    for library in inputs["libraries"]:
        label=labels[library["id"]]
        ambiguous={v["id"] for v in label["ambiguous"]}
        groups={item["id"]:{g["id"] for g in label["groups"] if item["id"] in g["members"]} for item in library["items"]}
        related={frozenset(pair) for pair in label["relatedGroupPairs"]}
        for a,b in combinations(sorted(groups),2):
            relation="uncertain" if a in ambiguous or b in ambiguous else "same" if groups[a]&groups[b] else (
                "related" if any(frozenset((x,y)) in related for x in groups[a] for y in groups[b]) else "unrelated")
            result[a+"--"+b]=(library["id"],a,b,relation)
    return result


def accepted(row,threshold):
    p=row.get("probabilities")
    return threshold is not None and p is not None and p[0] >= threshold and p.index(max(p))==0


def counts(rows,threshold):
    known=[r for r in rows if r["relation"]!="uncertain"]
    per={}
    for library in sorted({r["library"] for r in rows}):
        subset=[r for r in known if r["library"]==library]
        tp=sum(accepted(r,threshold) and r["relation"]=="same" for r in subset)
        fp=sum(accepted(r,threshold) and r["relation"]!="same" for r in subset)
        total=sum(r["relation"]=="same" for r in subset)
        per[library]={"tp":tp,"fp":fp,"fn":total-tp,"precision":tp/(tp+fp) if tp+fp else None,"recall":tp/total if total else None}
    tp,fp,fn=(sum(v[k] for v in per.values()) for k in ["tp","fp","fn"])
    recalls=[v["recall"] for v in per.values() if v["recall"] is not None]
    return {"tp":tp,"fp":fp,"fn":fn,"precision":tp/(tp+fp) if tp+fp else None,
            "recall":tp/(tp+fn) if tp+fn else None,"macroLibraryRecall":sum(recalls)/len(recalls) if recalls else None,
            "acceptedKnownPairs":tp+fp,"perLibrary":per}


def brute_threshold(rows):
    best=None
    for threshold in sorted({r["probabilities"][0] for r in rows if r["relation"]!="uncertain" and r.get("probabilities") is not None}):
        result=counts(rows,threshold)
        if result["acceptedKnownPairs"]>=30 and result["precision"]>=.95:
            candidate=(result["macroLibraryRecall"],result["precision"],threshold)
            if best is None or candidate>best:best=candidate
    return best


def near(actual,expected):
    if expected is None:require(actual is None,"undefined metric fabricated")
    else:require(actual is not None and math.isclose(actual,expected,abs_tol=1e-12,rel_tol=0),"metric mismatch")


def validate_rows(rows,truth,threshold,recorded):
    require(len(rows)==len(truth) and {r["first"]+"--"+r["second"] for r in rows}==set(truth),"missing/duplicate pair coverage")
    for row in rows:
        expected=truth[row["first"]+"--"+row["second"]]
        require(tuple(row[k] for k in ["library","first","second","relation"])==expected,"independent gold join mismatch")
        p=row.get("probabilities")
        if p is not None:require(len(p)==3 and all(math.isfinite(v) and 0<=v<=1 for v in p) and abs(sum(p)-1)<1e-5,"invalid probability vector")
        if "directionProbabilities" in row:
            directions=row["directionProbabilities"]
            require(len(directions)==2 and all(len(v)==3 for v in directions),"missing direction")
            for i in range(3):near(p[i],(directions[0][i]+directions[1][i])/2)
    actual=counts(rows,threshold)
    for key in ["tp","fp","fn","precision","recall","macroLibraryRecall","acceptedKnownPairs"]:near(recorded[key],actual[key])
    for library,values in actual["perLibrary"].items():
        for key,value in values.items():near(recorded["perLibrary"][library][key],value)
    require(recorded["missingPredictionPairs"]==sum(r.get("probabilities") is None for r in rows),"missing coverage mismatch")
    require(recorded["acceptedUncertainPairs"]==sum(r["relation"]=="uncertain" and accepted(r,threshold) for r in rows),"ambiguous acceptance mismatch")
    near(recorded["automationFraction"],sum(accepted(r,threshold) for r in rows)/len(rows))
    classes=["same","related","unrelated"];confusion=[[0]*3 for _ in range(3)]
    for row in rows:
        if row["relation"]!="uncertain" and row.get("probabilities") is not None:
            confusion[classes.index(row["relation"])][row["probabilities"].index(max(row["probabilities"]))]+=1
    require(confusion==recorded["argmaxConfusionMatrix"],"confusion matrix mismatch")
    return actual


def audit(run,external):
    require((run/"complete.json").exists(),"training/evaluation not complete; do not audit partial outcomes as final")
    from stage5 import verify
    verified=verify(run,external)
    manifest=read(run/"manifest.json")
    development_gold=gold("development");training_gold=gold("train")
    training_counts=Counter(row[3] for row in training_gold.values())
    require(sum(n for key,n in training_counts.items() if key!="uncertain")==2827,"training coverage mismatch")
    evaluations=[]
    candidates=[]
    for seed in [17,29,41]:
        receipts=[read(p) for p in (run/"recovery"/f"seed-{seed}").glob("*.json")]
        require(set(range(50,1063,50)).issubset({r["globalStep"] for r in receipts}),"missing periodic recovery checkpoint")
        for epoch in [1,2,3]:
            record=read(run/"epochs"/f"seed-{seed}-epoch-{epoch}.json")
            require(record["globalStep"]==354*epoch and record["trainingDirections"]==5654,"epoch steps/coverage mismatch")
            require(any(r["SHA256"]==record["recoverySHA256"] and r["nextOffset"]==5654 for r in receipts),"epoch recovery missing")
            output=run/"evaluations"/f"seed-{seed}-epoch-{epoch}/development"
            report=read(output/"summary.json")
            require(report["weightsSHA256"]==record["weightsSHA256"],"evaluation weights mismatch")
            require(len(list((output/"pairs").glob("*.json")))==1140,"missing per-pair files")
            for row in report["rows"]:
                saved=read(output/"pairs"/f"{row['id']}.json")
                require(all(row[k]==v for k,v in saved.items()),"summary changed saved prediction")
            validate_rows(report["rows"],development_gold,report["threshold"],report["allPairs"])
            subset=[r for r in report["rows"] if r["retrieved"]]
            for key,value in counts(subset,report["threshold"]).items():
                if key!="perLibrary":near(report["candidateConditioned"][key],value)
            best=brute_threshold(report["rows"])
            if best is None:require(report["selection"] is None,"nonqualifying threshold selected")
            else:
                near(report["selection"]["threshold"],best[2])
                candidates.append(((*best,-epoch,-[17,29,41].index(seed)),seed,epoch))
            evaluations.append({"seed":seed,"epoch":epoch,"qualifies":best is not None,"independentRank":best})
    choice=read(run/"selection.json");result=read(run/"quality-report.json")
    require(result["selectionSHA256"]==sha(run/"selection.json"),"quality selection binding changed")
    if not candidates:
        require(choice["status"]=="no_qualifying_development_candidate" and not result["testResultsOpened"]
                and not (run/"test-access.json").exists(),"test release despite no qualifying model")
    else:
        winner=max(candidates)
        require((choice["seed"],choice["epoch"])==(winner[1],winner[2]),"candidate rank/tie break mismatch")
        near(choice["threshold"],winner[0][2])
        require(sha(Path(choice["weights"]))==choice["weightsSHA256"],"winning weights changed")
        access=read(run/"test-access.json")
        require(access["selectionSHA256"]==sha(run/"selection.json") and access["at"]>=choice["createdAt"],"test access precedes selection")
        test_gold=gold("test",run)
        neural=read(run/"evaluations"/f"seed-{choice['seed']}-epoch-{choice['epoch']}/test/summary.json")
        baseline=read(run/"test-baseline.json")
        require(neural["weightsSHA256"]==choice["weightsSHA256"] and neural["threshold"]==choice["threshold"],"test candidate changed")
        frozen=read(STAGE2/"baseline-selected.json")
        require(baseline["baselineSHA256"]==sha(STAGE2/"baseline-selected.json") and baseline["threshold"]==frozen["threshold"] and not baseline["fitPerformed"],"test baseline refit/retuned")
        for source in [neural,baseline]:validate_rows(source["rows"],test_gold,source["threshold"],source["allPairs"])
        near(neural["allPairs"]["precision"],result["neural"]["allPairs"]["precision"])
        near(baseline["allPairs"]["precision"],result["baseline"]["allPairs"]["precision"])
        # Independently reconstruct directed retrieval recall and enforce no self/cross-library edges.
        positives={}
        libraries={}
        for library,a,b,relation in test_gold.values():
            libraries[a]=libraries[b]=library
            positives.setdefault(a,set());positives.setdefault(b,set())
            if relation=="same":positives[a].add(b);positives[b].add(a)
        hits=eligible=found=total=0
        for item,relevant in positives.items():
            retrieved=baseline["candidates"][item]
            require(len(retrieved)<=10 and len(set(retrieved))==len(retrieved) and item not in retrieved
                    and all(libraries[other]==libraries[item] for other in retrieved),"invalid retrieval candidates")
            if relevant:
                eligible+=1;overlap=set(retrieved)&relevant;hits+=bool(overlap);found+=len(overlap);total+=len(relevant)
        near(result["retrieval"]["atLeastOneRecallAt10"],hits/eligible)
        near(result["retrieval"]["allRelevantRecall"],found/total)
        n,b=counts(neural["rows"],choice["threshold"]),counts(baseline["rows"],baseline["threshold"])
        passed=(n["precision"] is not None and n["precision"]>=.95 and n["acceptedKnownPairs"]>=30
                and n["macroLibraryRecall"]-b["macroLibraryRecall"]>=.05-1e-12 and b["precision"] is not None
                and n["precision"]-b["precision"]>=-.01-1e-12 and hits/eligible>=.9
                and all(r.get("probabilities") is not None for source in [neural,baseline] for r in source["rows"]))
        require(result["passed"]==passed and result["stage6Recommended"]==passed,"quality verdict mismatch")
    resumptions=[read(p) for p in (run/"resumptions").glob("*.json")]
    require(any(r["globalStep"]==2 and r["nextOffset"]==32 and r["restoredModelOptimizerCPUAndMPSRandomStates"] for r in resumptions),"live pause recovery missing")
    retained=0;rotated=0
    for path in (run/"recovery").glob("*/*.json"):
        recovery=read(path);file=external/recovery["file"]
        if file.exists():
            require(recovery["SHA256"]==read(run/"complete.json")["externalFiles"][recovery["file"]],"recovery digest not frozen")
            retained+=1
        else:
            event=read(run/"retention-history"/f"{recovery['savedAtNS']}.json")
            policy=read(run/"control/retention-policy.json")
            require(policy["policy"]=="latest-two" and policy["explicitUserAuthorization"]
                    and event["SHA256"]==recovery["SHA256"] and event["policySHA256"]==sha(run/"control/retention-policy.json"),"unauthorized/unrecorded missing checkpoint")
            rotated+=1
    return {"at":now(),"audited":True,"stage5":verified,"auditorSHA256":sha(Path(__file__)),
        "developmentThresholdsIndependentlyRecomputed":9,"developmentEvaluations":evaluations,
        "trainingPairsByClass":dict(training_counts),"testResultsOpened":result["testResultsOpened"],
        "qualityPassed":result["passed"],"recoveryFilesRetained":retained,"authorizedRecoveryFilesRotated":rotated,
        "livePauseRestoredAtStep":2,"testDrivenTuningPerformed":False,
        "limitations":["Source/metric/integrity audit, not an independent human validation of synthetic labels.",
                       "MPS continuation was exercised; exact bitwise training replay is not claimed."]}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--run",required=True);parser.add_argument("--output",required=True)
    args=parser.parse_args();run,external=paths(args.run)
    result=audit(run,external);save(args.output,result);print(json.dumps(result,indent=2))


if __name__=="__main__":main()
