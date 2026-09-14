"""Recompute screening evidence using independent gold, counts and threshold code."""
import numpy as np

from screening_common import *
from audit_stage5 import gold as independent_gold, validate_rows, brute_threshold, near, accepted
from screening_ablation import PROFILES, fit_vocabulary
from stage2 import exported_probabilities


def audit(run, external):
    require(read(run/"manifest.json")["bindings"]==bindings(),"frozen source mismatch")
    truth = independent_gold("train")
    fold_plan = read(run/"folds.json")["folds"]
    pooled = {profile:[] for profile in PROFILES}
    checked = 0
    libraries,_ = load_split("train")
    for fold in fold_plan:
        validate_fold(fold)
        data = read(run/"ablations"/fold["id"]/"features.json")
        _,vocabulary = fit_vocabulary(libraries["libraries"],fold["fit"])
        require(data["tfidf"]==vocabulary,"fit-only vocabulary reconstruction failed")
        for profile,columns in PROFILES.items():
            result = read(run/"ablations"/fold["id"]/f"{profile}.json")
            require(result["featureFileSHA256"]==sha(run/"ablations"/fold["id"]/"features.json"),"feature binding failed")
            model = result["model"]
            fit = [r for r in data["partitions"]["fit"] if r["relation"]!="uncertain"
                   and all(r["features"][i] is not None for i in columns)]
            require(model["columns"]==columns and model["fitPairIDs"]==[r["id"] for r in fit],"wrong fitting pairs")
            x = np.array([[r["features"][i] for i in columns] for r in fit])
            require(np.allclose(x.mean(0),model["scalerMean"],atol=1e-12,rtol=0),"scaler fit leakage")
            scale = x.std(0);scale[scale==0]=1
            require(np.allclose(scale,model["scalerScale"],atol=1e-12,rtol=0),"scaler variance mismatch")
            expected_threshold = brute_threshold(result["partitions"]["calibration"])
            near(result["threshold"],expected_threshold[2] if expected_threshold else None)
            for partition,rows in result["partitions"].items():
                subset = {key:value for key,value in truth.items() if value[0] in fold[partition]}
                validate_rows(rows,subset,result["threshold"],result["metrics"][partition])
                features = {r["id"]:r["features"] for r in data["partitions"][partition]}
                for row in rows:
                    require(row["accepted"]==accepted(row,result["threshold"]),"stored decision mismatch")
                    require(row["features"]==features[row["id"]],"prediction feature mutation")
                    if row["probabilities"] is not None:
                        p = exported_probabilities(model,[[row["features"][i] for i in columns]])[0]
                        require(np.allclose(p,row["probabilities"],atol=1e-12,rtol=0),"exported prediction mismatch")
                checked += len(rows)
            pooled[profile].extend(result["partitions"]["evaluation"])
    summary = read(run/"ablation-summary.json")
    for profile,rows in pooled.items():
        require(len(rows)==len(truth) and {r["id"] for r in rows}==set(truth),"OOF coverage failed")
        known = [r for r in rows if r["relation"]!="uncertain"]
        tp = sum(r["accepted"] and r["relation"]=="same" for r in known)
        fp = sum(r["accepted"] and r["relation"]!="same" for r in known)
        metric = summary["profiles"][profile]["pooledOOF"]
        near(metric["tp"],tp);near(metric["fp"],fp)
        near(metric["precision"],tp/(tp+fp) if tp+fp else None)
        recalls = [sum(r["accepted"] and r["relation"]=="same" for r in known if r["library"]==lib)/
                   sum(r["relation"]=="same" for r in known if r["library"]==lib)
                   for lib in sorted({r["library"] for r in known})]
        near(metric["macroLibraryRecall"],sum(recalls)/len(recalls))
    context = read(run/"review/context-inputs.json")
    for case in context["cases"]:
        pair = run/"review/pair"/f"{case['id']}.json"
        require(sha(pair)==context["pairReviewHashes"][case["id"]],"pair review changed after context release")
        require(read(pair)["recordedAt"]<=context["releasedAt"],"review chronology invalid")
        require((run/"review/context"/f"{case['id']}.json").exists(),"missing contextual review")
    require(len(context["cases"])==60,"review coverage failed")
    from screening_sanity import receipts
    recovery = receipts(run)
    for row in recovery:
        path = external/row["file"]
        if path.exists(): require(sha(path)==row["SHA256"],"recovery digest failed")
        else:
            event = read(run/"retention"/f"{row['stamp']}.json")
            require(event["file"]==row["file"] and event["SHA256"]==row["SHA256"],"unaccounted rotation")
    require(sum((external/r["file"]).exists() for r in recovery)==min(2,len(recovery)),"rolling retention failed")
    sanity = read(run/"sanity/result.json")
    require(sha(external/sanity["weights"])==sanity["weightsSHA256"],"sanity export changed")
    checks = [read(p) for p in (run/"sanity/checks").glob("*.json")]
    recent = sorted(checks,key=lambda r:r["step"])[-2:]
    passed = len(recent)==2 and all(r["correctDirections"]==24 and r["crossEntropy"]<.1 for r in recent)
    require(sanity["passed"]==passed,"sanity pass rule mismatch")
    diagnostics = read(run/"diagnostics/summary.json")
    rows = [read(run/"diagnostics/train"/f"{key}.json") | {"relation":value[3]} for key,value in truth.items()]
    m = diagnostics["neural"]["train"]
    validate_rows(rows,truth,m["fixedThreshold"],m["fixedThresholdMetrics"])
    dev_truth = independent_gold("development")
    rows = read(NEURAL/"evaluations/seed-17-epoch-3/development/summary.json")["rows"]
    m = diagnostics["neural"]["development"]
    validate_rows(rows,dev_truth,m["fixedThreshold"],m["fixedThresholdMetrics"])
    require(not (run/"test-access.json").exists() and not read(run/"stage2-trials.json")["authorizedToExecute"],"stage boundary violation")
    require(list((run/"sanity/resumptions").glob("*.json")),"live recovery exercise missing")
    return {"passed":True,"predictionRowsRecounted":checked+len(truth)+len(dev_truth),
            "reviewPairs":60,"heldoutAccess":False,"stage2Started":False,
            "checks":["independent gold and metrics","brute-force calibration thresholds","fit-only vocabulary and scaler",
                      "portable prediction reconstruction","OOF coverage","review chronology","recovery receipts and rotation",
                      "live resume receipt","sanity pass rule","training/development diagnostic counts"],
            "limitation":"Separate implementation of counting/integrity checks, not an independent human or agent review."}
