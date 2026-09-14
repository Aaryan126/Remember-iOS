"""Portable baseline/combiner fits and prospective held-out reporting."""
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score

import p2_common as c
import p2_data as data
import p2_train as neural
import validation_policy as policy
from stage2 import exported_probabilities, FEATURES
from stage2_metrics import CLASSES
from screening2_models import fit_portable, portable_scores


def usable(row):
    return all(v is not None and np.isfinite(v) for v in row["features"])


def baseline_score(model, rows):
    output = []
    for row in rows:
        p = exported_probabilities(model, [row["features"][:6]])[0] if usable(row) else None
        output.append({k:row[k] for k in ("id","library","split","first","second","relation")} |
                      {"score":float(p[0]) if p is not None else None,
                       "eligible":bool(np.argmax(p)==0) if p is not None else False})
    return output


def baseline():
    path = c.RUN / "baseline.json"
    if path.exists():
        return c.read(path)
    c.boundary("baseline")
    rows = data.features("train")
    known = [r for r in rows if r["relation"] != "uncertain"]
    c.require(all(usable(r) for r in known), "known training pairs missing compatible embeddings; no silent imputation/filtering")
    x = np.array([r["features"][:6] for r in known])
    y = [CLASSES.index(r["relation"]) for r in known]
    scaler = StandardScaler().fit(x)
    classifier = LogisticRegression(C=10, class_weight="balanced", solver="lbfgs", max_iter=2000, random_state=17)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        classifier.fit(scaler.transform(x),y)
    c.require(classifier.classes_.tolist()==[0,1,2], "baseline class order changed")
    model = {"C":10,"classOrder":CLASSES,"featureOrder":FEATURES,
             "scalerMean":scaler.mean_.tolist(),"scalerScale":scaler.scale_.tolist(),
             "coefficients":classifier.coef_.tolist(),"intercept":classifier.intercept_.tolist()}
    c.require(np.max(np.abs(exported_probabilities(model,x)-classifier.predict_proba(scaler.transform(x))))<1e-12, "baseline portable parity")
    calibration = baseline_score(model,data.features("calibration"))
    selected = policy.select_threshold(calibration,c.read(c.DATA / "contract.json"))
    result = {"model":model,"fitPairIDs":[r["id"] for r in known],"calibration":calibration,"selection":selected,
              "tfidfSHA256":c.digest(c.RUN / "tfidf.json")}
    c.publish(path,result)
    c.log("baseline-complete", selection=selected)
    return result


def hybrid_matrix(rows,scores):
    values = np.array([r["features"] for r in rows],dtype=float)
    probability = np.clip([scores[r["id"]] for r in rows],1e-6,1-1e-6)
    return np.column_stack((values,np.log(probability/(1-probability))))


def hybrid_score(model,rows,scores):
    output=[]
    for row in rows:
        score = float(portable_scores(model,hybrid_matrix([row],scores))[0]) if usable(row) else None
        output.append({k:row[k] for k in ("id","library","split","first","second","relation")} |
                      {"score":score,"baseScore":scores[row["id"]],"eligible":True})
    return output


def hybrid(seed,pause_after=None):
    path = c.RUN / f"hybrid-{seed}.json"
    if path.exists():
        return c.read(path)
    base = baseline()
    splits = c.read(c.RELEASE / "splits.json")
    scores,provenance = {},[]
    for fold in splits["innerFolds"]:
        record = neural.fit(seed,fold["id"],pause_after)
        values = neural.predict(record,"train",fold["scoreLibraries"])
        c.require(not set(values)&set(scores), "OOF pair overlap")
        scores.update(values)
        provenance.append(record | {"scoreLibraries":fold["scoreLibraries"]})
    rows = data.features("train")
    c.require(set(scores)=={r["id"] for r in rows}, "incomplete OOF coverage")
    known = [r for r in rows if r["relation"]!="uncertain"]
    c.require(all(usable(r) for r in known), "hybrid training missing features")
    c.boundary("combiner:" + str(seed))
    x = hybrid_matrix(known,scores)
    model,original,scaler = fit_portable("A2",x,np.array([int(r["relation"]=="same") for r in known]))
    final = neural.fit(seed,"final",pause_after)
    calibration_rows = data.features("calibration")
    calibration_scores = neural.predict(final,"calibration",splits["libraries"]["calibration"])
    valid = [r for r in calibration_rows if usable(r)]
    matrix = hybrid_matrix(valid,calibration_scores)
    c.require(np.max(np.abs(portable_scores(model,matrix)-original.predict_proba(scaler.transform(matrix))[:,1]))<1e-10, "combiner portable parity")
    calibration = hybrid_score(model,calibration_rows,calibration_scores)
    selected = policy.select_threshold(calibration,c.read(c.DATA / "contract.json"),
                                        base["selection"]["metrics"] if base["selection"] else None,hybrid=True)
    result = {"seed":seed,"model":model,"final":final,"OOFFits":provenance,"OOFScores":scores,
              "fitPairIDs":[r["id"] for r in known],"calibration":calibration,"selection":selected}
    c.publish(path,result)
    c.log("hybrid-calibration-complete", seed=seed, selection=selected)
    return result


def freeze_selection():
    if (c.RUN / "selection.json").exists():
        return c.verify_selection()
    baseline_result = c.read(c.RUN / "baseline.json")
    candidates = {str(seed):c.read(c.RUN / f"hybrid-{seed}.json") for seed in (17,29,41)}
    representations = []
    token_files = []
    for split in ("train","calibration"):
        libraries,_ = c.split_data(split)
        representations += [c.RUN / "embeddings" / f"{i['id']}.json" for l in libraries for i in l["items"]]
        representations += [c.RUN / "features" / f"{split}.json",c.RUN / "tokens" / f"{split}.json"]
        token_files.append(c.EXTERNAL / c.read(c.RUN / "tokens" / f"{split}.json")["file"])
    c.publish(c.RUN / "representations.json",{"run":{str(p.relative_to(c.RUN)):c.digest(p) for p in representations},
                                              "external":{str(p.relative_to(c.EXTERNAL)):c.digest(p) for p in token_files}})
    artifact_paths = [c.RUN / "baseline.json",c.RUN / "tfidf.json",c.RUN / "representations.json"] + [c.RUN / f"hybrid-{s}.json" for s in (17,29,41)]
    weights = {}
    for candidate in candidates.values():
        for record in candidate["OOFFits"]+[candidate["final"]]:
            c.require(c.digest(c.EXTERNAL / record["file"])==record["SHA256"], "weight changed before selection")
            weights[record["file"]]=record["SHA256"]
    selection = {"manifestSHA256":c.digest(c.RUN / "manifest.json"),
                 "baseline":baseline_result["selection"]["threshold"] if baseline_result["selection"] else None,
                 "hybrids":{s:v["selection"]["threshold"] if v["selection"] else None for s,v in candidates.items()},
                 "artifacts":{str(p.relative_to(c.RUN)):c.digest(p) for p in artifact_paths},"weights":weights}
    c.publish(c.RUN / "selection.json",selection)
    return c.verify_selection()


def bootstrap(baseline_rows,hybrid_rows,thresholds,family_by_library,samples=2000):
    """Resample families jointly; duplicate draws get distinct library/source IDs."""
    policy.align_predictions(baseline_rows,hybrid_rows,"evaluation")
    families=sorted({family_by_library[r["library"]] for r in baseline_rows})
    rng=np.random.default_rng(1729)
    deltas={"precision":[],"macroRecall":[]}
    per_library=[policy.metrics(rows,thresholds[key])["perLibrary"]
                 for rows,key in ((baseline_rows,"baseline"),(hybrid_rows,"hybrid"))]
    for _ in range(samples):
        chosen=rng.choice(families,len(families),replace=True)
        summaries=[]
        for per in per_library:
            selected=[v for family in chosen for lid,v in per.items() if family_by_library[lid]==family]
            tp=sum(v["tp"] for v in selected)
            fp=sum(v["fp"] for v in selected)
            recalls=[v["recall"] for v in selected if v["recall"] is not None]
            summaries.append({"precision":tp/(tp+fp) if tp+fp else None,
                              "macroRecall":sum(recalls)/len(recalls) if recalls else None})
        a,b=summaries
        for key in deltas:
            if a[key] is not None and b[key] is not None:
                deltas[key].append(b[key]-a[key])
    return {"families":len(families),"samples":samples,"seed":1729,"descriptiveOnly":True,
            "differences":{k:{"defined":len(v),"undefined":samples-len(v),
                              "percentile95":np.quantile(v,[.025,.975]).tolist() if v else None} for k,v in deltas.items()}}


def ranking(rows):
    known=[r for r in rows if r["relation"]!="uncertain" and r["score"] is not None]
    return {"averagePrecision":float(average_precision_score([r["relation"]=="same" for r in known],[r["score"] for r in known])) if any(r["relation"]=="same" for r in known) else None,
            "scoredKnown":len(known),"policy":"ranking only; baseline argmax eligibility not applied"}


def diagnostic_slices(rows, threshold, feature_rows, source_items):
    """Descriptive fixed slices, never a threshold-selection input."""
    features={r["id"]:r for r in feature_rows}
    def challenge(row):
        short=any(len(source_items[key]["text"].split())<=8 for key in (row["first"],row["second"]))
        return short or features[row["id"]]["features"][7]==1 or row["relation"]=="related"
    difficult=[r for r in rows if challenge(r)]
    routine=[r for r in rows if not challenge(r)]
    return {name:{"pairs":len(part),"metrics":policy.metrics(part,threshold),"ranking":ranking(part)}
            for name,part in (("challenge",difficult),("routine",routine))}


def evaluate():
    selection=c.verify_selection()
    rows=data.features("evaluation")
    libraries,_=c.split_data("evaluation")
    items={i["id"]:i for l in libraries for i in l["items"]}
    splits=c.read(c.RELEASE / "splits.json")
    baseline_result=c.read(c.RUN / "baseline.json")
    control=baseline_score(baseline_result["model"],rows)
    reports={}
    for seed in (17,29,41):
        c.boundary("evaluation:"+str(seed))
        result=c.read(c.RUN / f"hybrid-{seed}.json")
        scores=neural.predict(result["final"],"evaluation",splits["libraries"]["evaluation"])
        candidate=hybrid_score(result["model"],rows,scores)
        thresholds={"baseline":selection["baseline"],"hybrid":selection["hybrids"][str(seed)]}
        report=policy.evaluate_frozen(control,candidate,thresholds,c.read(c.DATA / "contract.json"))
        report.update(seed=seed,thresholds=thresholds,baselineRanking=ranking(control),hybridRanking=ranking(candidate),
                      bootstrap=bootstrap(control,candidate,thresholds,splits["familyByLibrary"]),
                      predictions={"baseline":control,"hybrid":candidate})
        report["diagnosticSlices"]={"baseline":diagnostic_slices(control,thresholds["baseline"],rows,items),
                                    "hybrid":diagnostic_slices(candidate,thresholds["hybrid"],rows,items)}
        c.publish(c.RUN / "evaluation" / f"seed-{seed}.json",report)
        reports[str(seed)]={k:v for k,v in report.items() if k!="predictions"}
        c.log("evaluation-complete",seed=seed,qualification=report["qualification"])
    c.publish(c.RUN / "report.json",{"seeds":reports,"allSeedsPassed":all(r["qualification"]["passed"] for r in reports.values()),
                                     "oldTestOpened":False,"productionQualified":False,"productionReplayRun":False})
