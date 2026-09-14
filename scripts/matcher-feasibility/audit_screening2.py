"""Independent binary counts, threshold sweep and fit/OOF evidence checks."""
import math
import numpy as np

from screening2_common import *
from audit_stage5 import gold as independent_gold
from screening2_data import matrix_key,source_data,matrix
from screening_ablation import fit_vocabulary
from screening2_models import portable_scores


def independent_counts(rows,threshold):
    per={};uncertain=0;related=unrelated=0
    for row in rows:
        accepted=threshold is not None and row["score"] is not None and row["score"]>=threshold
        lib=per.setdefault(row["library"],[0,0,0])
        if row["relation"]=="uncertain":uncertain+=int(accepted);continue
        if row["relation"]=="same":lib[2]+=1;lib[0]+=int(accepted)
        else:
            lib[1]+=int(accepted)
            related+=int(accepted and row["relation"]=="related")
            unrelated+=int(accepted and row["relation"]=="unrelated")
    tp=sum(v[0] for v in per.values());fp=sum(v[1] for v in per.values());positive=sum(v[2] for v in per.values())
    recalls=[v[0]/v[2] for v in per.values() if v[2]]
    return {"tp":tp,"fp":fp,"fn":positive-tp,"acceptedKnown":tp+fp,"precision":tp/(tp+fp) if tp+fp else None,
            "recall":tp/positive if positive else None,"macroRecall":sum(recalls)/len(recalls) if recalls else None,
            "acceptedUncertain":uncertain,"falseRelated":related,"falseUnrelated":unrelated}


def brute_threshold(rows):
    best=None
    for t in sorted({r["score"] for r in rows if r["relation"]!="uncertain" and r["score"] is not None}):
        m=independent_counts(rows,t)
        if m["acceptedKnown"]>=30 and m["precision"]>=.95:
            rank=(m["macroRecall"],m["precision"],t)
            if best is None or rank>best:best=rank
    return best[2] if best else None


def near(a,b):
    require(a is None and b is None or a is not None and b is not None and math.isclose(a,b,abs_tol=1e-12,rel_tol=0),"metric mismatch")


def check_rows(rows,truth,threshold,metric=None):
    require(len(rows)==len(truth) and {r["id"] for r in rows}==set(truth),"pair coverage mismatch")
    for row in rows:
        require(tuple(row[k] for k in ("library","first","second","relation"))==truth[row["id"]],"independent gold mismatch")
        score=row["score"]
        require(score is None or math.isfinite(score) and 0<=score<=1,"invalid score")
        if "directionScores" in row:near(score,sum(row["directionScores"])/len(row["directionScores"]))
        require(row["accepted"]==(threshold is not None and score is not None and score>=threshold),"saved decision mismatch")
    if metric:
        for key,value in independent_counts(rows,threshold).items():near(metric[key],value)


def check_provenance(run,model,fit_ids):
    require(model["fitLibraries"]==fit_ids,"wrong fit libraries")
    if model["trial"].startswith("D"):
        held=[];scores={}
        for entry in model["provenance"]["inner"]:
            require(set(entry["fitLibraries"])|set(entry["scoreLibraries"])==set(fit_ids)
                    and not set(entry["fitLibraries"])&set(entry["scoreLibraries"]),"hybrid library leakage")
            held+=entry["scoreLibraries"]
            fit=read(run/"fits"/entry["task"]/"complete.json")
            require(fit["SHA256"]==entry["modelSHA256"] and fit["fitLibraries"]==entry["fitLibraries"],"hybrid fit binding mismatch")
            for row in model["fitPairIDs"]:
                if row.split("-i")[0] not in entry["scoreLibraries"]:continue
                prediction=read(run/"predictions"/entry["task"]/f"{row}.json")
                require(prediction["weightsSHA256"]==entry["modelSHA256"],"hybrid score binding mismatch")
                scores[row]=prediction["score"]
        require(sorted(held)==sorted(fit_ids),"hybrid inner coverage mismatch")
        require(scores==model["trainingScores"],"hybrid combiner fitted non-OOF scores")


def average_precision(rows):
    known=sorted([r for r in rows if r["relation"]!="uncertain" and r["score"] is not None],key=lambda r:-r["score"])
    positive=sum(r["relation"]=="same" for r in known)
    if not positive:return None
    hits=previous=0;area=0.
    for i,row in enumerate(known):
        hits+=int(row["relation"]=="same")
        if i+1<len(known) and known[i+1]["score"]==row["score"]:continue
        area+=(hits-previous)/positive*hits/(i+1);previous=hits
    return area


def check_predictions(run,trial,seed,fit_ids,rows,definitions,embeddings):
    key=f"{trial}-seed-{seed}-fit-{matrix_key(fit_ids)}"
    folder=run/"fits"/key
    if (folder/"model.json").exists():
        model=read(folder/"model.json");digest=sha(folder/"model.json")
        require(all(r["modelSHA256"]==digest for r in rows),"portable prediction binding mismatch")
        lookup={r["id"]:r for r in definitions[matrix_key(fit_ids)]["rows"]}
        extra=None
        if trial.startswith("D"):
            extra={}
            for row in rows:
                base=read(run/"predictions"/model["provenance"]["baseTask"]/f"{row['id']}.json")
                require(base["weightsSHA256"]==model["provenance"]["baseSHA256"],"hybrid base binding changed")
                near(base["score"],row["baseScore"]);extra[row["id"]]=base["score"]
        values=matrix([lookup[r["id"]] for r in rows],model["kind"],embeddings,extra)
        require(np.allclose(portable_scores(model["model"],values),[r["score"] for r in rows],atol=1e-12,rtol=0),"portable scores failed reconstruction")
    else:
        model=read(folder/"complete.json")
        for row in rows:
            raw=read(run/"predictions"/key/f"{row['id']}.json")
            require(raw["weightsSHA256"]==model["SHA256"]==row["weightsSHA256"],"neural prediction binding mismatch")
            near(raw["score"],row["score"])
            require(raw["directionScores"]==row["directionScores"],"direction scores changed")


def audit(run,external):
    require(read(run/"manifest.json")["bindings"]==bindings(),"source freeze mismatch")
    truth=independent_gold("train");development=independent_gold("development")
    libraries,_,embeddings=source_data(True)
    definitions={}
    for file in (run/"features").glob("*.json"):
        data=read(file);_,vocabulary=fit_vocabulary(libraries,data["fitLibraries"])
        require(data["tfidf"]==vocabulary,"fit-only TF-IDF mismatch")
        definitions[matrix_key(data["fitLibraries"])]=data
    checked=0
    for fold in read(run/"folds.json")["folds"]:
        for config in read(run/"trials.json")["configurations"]:
            boundary(run,f"audit:{fold['id']}:{config['id']}")
            record=read(run/"screen"/fold["id"]/f"{config['id']}.json")
            require(record["fold"]==fold,"screen fold changed")
            near(record["threshold"],brute_threshold(record["calibration"]))
            for part in ("calibration","evaluation"):
                subset={k:v for k,v in truth.items() if v[0] in fold[part]}
                check_rows(record[part],subset,record["threshold"],record["metrics"] if part=="evaluation" else None)
                checked+=len(record[part])
            check_predictions(run,config["id"],17,fold["fit"],record["calibration"]+record["evaluation"],definitions,embeddings)
    for file in (run/"fits").glob("*/model.json"):
        model=read(file);fit_ids=model["fitLibraries"];check_provenance(run,model,fit_ids)
        expected={key for key,row in truth.items() if row[0] in fit_ids and row[3]!="uncertain"}
        require(set(model["fitPairIDs"])==expected and len(model["fitPairIDs"])==len(expected),"simple fitting pair leak/coverage")
        data=definitions[matrix_key(fit_ids)];lookup={r["id"]:r for r in data["rows"]}
        rows=[lookup[key] for key in model["fitPairIDs"]]
        x=matrix(rows,model["kind"],embeddings,model.get("trainingScores"))
        require(np.allclose(x.mean(0),model["model"]["mean"],atol=1e-12,rtol=0),"simple scaler fitting mismatch")
        scale=x.std(0);scale[scale==0]=1
        require(np.allclose(scale,model["model"]["scale"],atol=1e-12,rtol=0),"simple scaler variance mismatch")
    for file in (run/"fits").glob("*/complete.json"):
        boundary(run,"audit-neural:"+file.parent.name)
        record=read(file);spec=read(file.parent/"spec.json")
        require(sha(file.parent/"spec.json")==record["fingerprint"],"neural spec hash mismatch")
        require(sha(external/record["file"])==record["SHA256"],"final neural model corrupted")
        expected={k for k,v in truth.items() if v[0] in record["fitLibraries"] and v[3]!="uncertain"}
        require(set(spec["fitPairIDs"])==expected and len(spec["fitPairIDs"])==len(expected),"neural fit coverage/leakage")
        require(spec["directions"]==len(expected)*(2 if record["trial"].startswith("C") else 1),"neural direction count mismatch")
        require(record["steps"]==math.ceil(spec["directions"]/spec["batch"])*spec["epochs"],"incomplete fit steps")
    selection=read(run/"selection.json")
    require(selection["screenSummarySHA256"]==sha(run/"screen-summary.json") and not selection["developmentUsedForSelection"],"selection binding mismatch")
    summary=read(run/"confirmation-summary.json")
    screening=read(run/"screen-summary.json")
    for report in screening["trials"]:
        records=[read(run/"screen"/fold["id"]/f"{report['trial']}.json") for fold in read(run/"folds.json")["folds"]]
        rows=[r for record in records for r in record["evaluation"]]
        require(len(rows)==len(truth) and {r["id"] for r in rows}==set(truth),"pooled OOF coverage mismatch")
        decisions=[r|{"score":1. if r["accepted"] else 0.} for r in rows]
        for key,value in independent_counts(decisions,1.).items():near(report["pooled"][key],value)
        near(report["pooled"]["averagePrecision"],average_precision(rows))
        require(report["qualifyingFolds"]==sum(r["selection"] is not None for r in records),"qualifying fold count mismatch")
    fallback=all(r["qualifyingFolds"]==0 for r in screening["trials"])
    def rank(r):
        m=r["pooled"]
        return ((m["averagePrecision"] if m["averagePrecision"] is not None else -1),) if fallback else (r["qualifyingFolds"],m["macroRecall"] or 0,m["precision"] if m["precision"] is not None else -1)
    ordered=sorted(sorted(screening["trials"],key=lambda r:r["trial"]),key=rank,reverse=True)
    picked=[];families=set()
    for row in ordered:
        if row["family"] not in families:picked.append(row["trial"]);families.add(row["family"])
        if len(picked)==2:break
    require(selection["selectedTrials"]==picked and selection["diagnosticFallback"]==fallback,"selection ranking mismatch")
    for trial in selection["selectedTrials"]:
        expected=[17] if trial.startswith("A") or trial=="B1" else [17,29,41]
        records=[r for r in summary["candidates"] if r["trial"]==trial]
        require(sorted(r["seed"] for r in records)==expected,"confirmation seed cherry-picking")
        for record in records:
            near(record["threshold"],brute_threshold(record["rows"]))
            check_rows(record["rows"],development,record["threshold"],record["metrics"]);checked+=len(record["rows"])
            check_predictions(run,trial,record["seed"],[f"mf{i:02}" for i in range(1,19)],record["rows"],definitions,embeddings)
            m=record["metrics"];b=summary["baseline"]
            passed=m["precision"] is not None and m["precision"]>=.95 and m["acceptedKnown"]>=30 and m["macroRecall"]+1e-12>=b["macroRecall"]+.05 and m["precision"]+1e-12>=b["precision"]-.01 and m["missingKnown"]==0
            require(record["passed"]==passed,"confirmation quality gate mismatch")
        require(summary["familyPassed"][trial]==all(r["passed"] for r in records),"family seed stability mismatch")
    recovery=recovery_receipts(run)
    for row in recovery:
        path=external/row["file"]
        if path.exists():require(sha(path)==row["SHA256"],"recovery hash failed")
        else:
            removed=read(run/"retention"/f"{row['stamp']}.json")
            require(removed["file"]==row["file"] and removed["SHA256"]==row["SHA256"],"unrecorded recovery deletion")
    require(sum((external/r["file"]).exists() for r in recovery)==min(2,len(recovery)),"rolling retention mismatch")
    require(not (run/"test-access.json").exists(),"test access prohibited")
    require(list((run/"fits").glob("*/resumptions/*.json")),"live pause/resume exercise missing")
    return {"passed":True,"predictionRowsRecounted":checked,"screenTrials":36,
            "confirmationRuns":len(summary["candidates"]),"testAccess":False,
            "checks":["independent gold and binary counts","brute-force calibration thresholds","fit-only transforms",
                      "library-disjoint hybrid score provenance","fit pair coverage and steps","all confirmation seeds",
                      "frozen selection","lossless export hashes","recovery retention receipts"]}
