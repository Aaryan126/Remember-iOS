"""Portable small classifiers and cross-fitted hybrid orchestration."""
import warnings
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from screening2_common import *
from screening2_data import matrix,partition,task_id,matrix_key
from screening2_metrics import select,counts,with_decisions
import screening2_neural as neural


def sigmoid(values):
    values=np.asarray(values,dtype=np.float64)
    return np.exp(-np.logaddexp(0,-values))


def portable_scores(record,x):
    x=(np.asarray(x)-np.asarray(record["mean"]))/np.asarray(record["scale"])
    if record["kind"]=="logistic":return sigmoid(x@np.asarray(record["coefficient"])+record["intercept"])
    logits=np.full(len(x),record["initialLogOdds"],dtype=np.float64)
    for tree in record["trees"]:
        for i,row in enumerate(x):
            node=0
            while tree["left"][node]!=-1:
                # sklearn decision trees convert input to float32 before routing.
                node=tree["left"][node] if np.float32(row[tree["feature"][node]])<=tree["threshold"][node] else tree["right"][node]
            logits[i]+=record["learningRate"]*tree["value"][node]
    return sigmoid(logits)


def fit_portable(trial,x,y):
    scaler=StandardScaler().fit(x);scaled=scaler.transform(x)
    if trial=="A3":
        model=GradientBoostingClassifier(n_estimators=100,max_depth=2,learning_rate=.05,random_state=17)
    else:
        model=LogisticRegression(C=.1 if trial=="B1" else 1,solver="lbfgs",max_iter=2000,random_state=17)
    with warnings.catch_warnings():
        warnings.simplefilter("error",ConvergenceWarning);model.fit(scaled,y)
    require(model.classes_.tolist()==[0,1],"binary class order changed")
    record={"mean":scaler.mean_.tolist(),"scale":scaler.scale_.tolist(),"kind":"gradient_boosting" if trial=="A3" else "logistic"}
    if trial=="A3":
        probability=float(model.init_.class_prior_[1])
        record.update(initialLogOdds=float(np.log(probability/(1-probability))),learningRate=.05,
            trees=[{"left":t.tree_.children_left.tolist(),"right":t.tree_.children_right.tolist(),
                    "feature":t.tree_.feature.tolist(),"threshold":t.tree_.threshold.tolist(),
                    "value":t.tree_.value[:,0,0].tolist()} for t in model.estimators_[:,0]])
    else:record.update(coefficient=model.coef_[0].tolist(),intercept=float(model.intercept_[0]))
    require(np.max(np.abs(portable_scores(record,x)-model.predict_proba(scaled)[:,1]))<1e-10,"portable fit parity failed")
    return record,model,scaler


def simple(run,trial,fit_ids,seed,data,rows,embeddings=None):
    require(seed==17,"deterministic classifier seed must be17")
    require(trial in ("A1","A2","A3","B1"),"invalid simple classifier")
    key=task_id(trial,fit_ids,seed)
    folder=run/"fits"/key
    kind="six" if trial=="A1" else "vectors" if trial=="B1" else "expanded"
    known=[r for r in partition(data["rows"],fit_ids) if r["relation"]!="uncertain"]
    output=folder/"model.json"
    if output.exists():record=read(output)
    else:
        boundary(run,"simple-fit:"+key,planned=20*1024**2)
        x=matrix(known,kind,embeddings);y=np.array([int(r["relation"]=="same") for r in known])
        model,sklearn_model,scaler=fit_portable(trial,x,y)
        # Check export routing/probabilities on every requested evaluation row, too.
        values=matrix(rows,kind,embeddings)
        require(np.max(np.abs(portable_scores(model,values)-sklearn_model.predict_proba(scaler.transform(values))[:,1]))<1e-10,"portable evaluation parity failed")
        record={"trial":trial,"task":key,"fitLibraries":fit_ids,"fitPairIDs":[r["id"] for r in known],
                "kind":kind,"model":model,"manifestSHA256":sha(run/"manifest.json")}
        save(output,record)
        boundary(run,"simple-fit-saved:"+key)
    require(record["fitPairIDs"]==[r["id"] for r in known],"simple fit changed")
    scores=portable_scores(record["model"],matrix(rows,kind,embeddings))
    return [{k:r[k] for k in ("id","library","first","second","relation")}|{"score":float(score),"modelSHA256":sha(output)}
            for r,score in zip(rows,scores)]


def predict_trial(run,external,trial,fit_ids,seed,data,rows,embeddings,inner=None,pause_after_steps=None):
    if trial in ("A1","A2","A3","B1"):
        return simple(run,trial,fit_ids,seed,data,rows,embeddings)
    if trial.startswith(("B","C")):
        record=neural.fit(run,external,trial,fit_ids,seed,data,embeddings,pause_after_steps)
        return neural.predict(run,external,record,rows,embeddings)
    require(trial in ("D1","D2","D3") and inner is not None,"invalid hybrid request")
    require(sorted(sum(inner,[]))==sorted(fit_ids) and len(set(sum(inner,[])))==len(fit_ids),"hybrid inner coverage/leakage")
    base="C"+trial[-1];scores={};provenance=[]
    for held in inner:
        fitting=[v for v in fit_ids if v not in held]
        record=neural.fit(run,external,base,fitting,seed,data,embeddings,pause_after_steps)
        targets=partition(data["rows"],held)
        result=neural.predict(run,external,record,targets)
        require(not set(fitting)&set(held),"hybrid inner leakage")
        scores.update({r["id"]:r["score"] for r in result})
        provenance.append({"fitLibraries":fitting,"scoreLibraries":held,"task":record["task"],"modelSHA256":record["SHA256"]})
    base_record=neural.fit(run,external,base,fit_ids,seed,data,embeddings,pause_after_steps)
    require(not set(fit_ids)&{r["library"] for r in rows},"hybrid output must not replace its training OOF scores")
    scores.update({r["id"]:r["score"] for r in neural.predict(run,external,base_record,rows)})
    # The deterministic combiner is repeated per neural seed; seed belongs to task identity.
    key=f"{trial}-seed-{seed}-fit-{matrix_key(fit_ids)}"
    known=[r for r in partition(data["rows"],fit_ids) if r["relation"]!="uncertain"]
    output=run/"fits"/key/"model.json"
    binding={"inner":provenance,"baseTask":base_record["task"],"baseSHA256":base_record["SHA256"]}
    if output.exists():record=read(output);require(record["provenance"]==binding,"hybrid provenance changed")
    else:
        boundary(run,"hybrid-combiner:"+key)
        x=matrix(known,"hybrid",extra=scores);y=np.array([int(r["relation"]=="same") for r in known])
        model,original,scaler=fit_portable("A2",x,y)
        values=matrix(rows,"hybrid",extra=scores)
        require(np.max(np.abs(portable_scores(model,values)-original.predict_proba(scaler.transform(values))[:,1]))<1e-10,"hybrid export parity failed")
        record={"trial":trial,"task":key,"fitLibraries":fit_ids,"fitPairIDs":[r["id"] for r in known],
                "kind":"hybrid","model":model,"provenance":binding,"trainingScores":{r["id"]:scores[r["id"]] for r in known}}
        save(output,record);boundary(run,"hybrid-combiner-saved:"+key)
    values=portable_scores(record["model"],matrix(rows,"hybrid",extra=scores))
    return [{k:r[k] for k in ("id","library","first","second","relation")}|
            {"score":float(score),"baseScore":scores[r["id"]],"modelSHA256":sha(output)} for r,score in zip(rows,values)]


def evaluate(rows,calibration_ids,evaluation_ids):
    require(not set(calibration_ids)&set(evaluation_ids),"calibration/evaluation overlap")
    calibration=partition(rows,calibration_ids);evaluation=partition(rows,evaluation_ids)
    selected=select(calibration);threshold=selected["threshold"] if selected else None
    return {"selection":selected,"threshold":threshold,"calibration":with_decisions(calibration,threshold),
            "evaluation":with_decisions(evaluation,threshold),"metrics":counts(evaluation,threshold)}
