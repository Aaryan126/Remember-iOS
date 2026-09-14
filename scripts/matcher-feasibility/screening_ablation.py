"""Four feature ablations with separate library fitting, calibration and scoring."""
from __future__ import annotations

import json
import time
import warnings
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.preprocessing import StandardScaler

from screening_common import BASELINE, read, save, sha, require, gold, load_split, boundary, validate_fold
from stage2 import FEATURES, pair_features, validate_embedding, exported_probabilities
from stage2_metrics import CLASSES, accepted, metrics, select_threshold

PROFILES = {"embeddings": [0,1], "lexical": [2,3,4,5], "all_six": [0,1,2,3,4,5], "without_numbers": [0,1,2,3,5]}


def fit_vocabulary(libraries, fitting_ids):
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1,2), dtype=np.float64)
    items = [item for lib in libraries if lib["id"] in fitting_ids for item in lib["items"]]
    vectorizer.fit([item["text"] for item in items])
    return vectorizer, {"fitSourceIDs": [i["id"] for i in items],
                        "vocabulary": {k: int(v) for k,v in vectorizer.vocabulary_.items()},
                        "idf": vectorizer.idf_.tolist(), "lowercase": True, "ngramRange": [1,2],
                        "tokenPattern": vectorizer.token_pattern, "norm": "l2"}


def fold_features(run, external, fold):
    validate_fold(fold)
    path = run / "ablations" / fold["id"] / "features.json"
    if path.exists():
        return read(path)
    boundary(run, external, "features:" + fold["id"])
    inputs, _ = load_split("train")
    libraries = inputs["libraries"]
    vectorizer, vocabulary = fit_vocabulary(libraries, fold["fit"])
    truth = gold("train")
    partitions = {}
    for partition in ("fit", "calibration", "evaluation"):
        rows = []
        for lib in libraries:
            if lib["id"] not in fold[partition]:
                continue
            boundary(run, external, "features:" + fold["id"] + ":" + lib["id"])
            items = lib["items"]
            index = {item["id"]: i for i,item in enumerate(items)}
            embeddings = [read(BASELINE / "embeddings" / f"{item['id']}.json") for item in items]
            for item, embedding in zip(items, embeddings):
                validate_embedding(item, embedding)
            matrix = vectorizer.transform([item["text"] for item in items])
            lexical = (matrix @ matrix.T).toarray()
            for pair in [r for r in truth if r["library"] == lib["id"]]:
                a,b = index[pair["first"]],index[pair["second"]]
                values = pair_features(items[a],items[b],embeddings[a],embeddings[b],lexical[a,b])
                rows.append(pair | {"features": values})
        partitions[partition] = rows
    result = {"fold": fold, "tfidf": vocabulary, "featureOrder": FEATURES, "partitions": partitions}
    save(path, result)
    return result


def usable(row, columns):
    return all(row["features"][i] is not None and np.isfinite(row["features"][i]) for i in columns)


def diagnostic_curve(rows):
    known = [r for r in rows if r["relation"] != "uncertain" and r.get("probabilities") is not None]
    if not known:
        return {"averagePrecision": None, "curve": [], "knownScoredPairs": 0}
    truth = np.array([r["relation"] == "same" for r in known])
    scores = np.array([r["probabilities"][0] for r in known])
    precision, recall, thresholds = precision_recall_curve(truth, scores)
    return {"averagePrecision": float(average_precision_score(truth,scores)) if truth.any() else None,
            "knownScoredPairs": len(known), "missingKnownPairs": sum(r["relation"] != "uncertain" for r in rows)-len(known),
            "curve": [{"threshold": float(t), "precision": float(p), "recall": float(r)}
                      for p,r,t in zip(precision,recall,thresholds)],
            "policy": "ranking diagnostic on P(same), not a newly approved threshold; class-winning constraint not applied"}


def run_ablation(run, external, fold, profile):
    output = run / "ablations" / fold["id"] / f"{profile}.json"
    if output.exists():
        return read(output)
    boundary(run, external, f"fit:{fold['id']}:{profile}", planned=8*1024**2)
    data = fold_features(run, external, fold)
    columns = PROFILES[profile]
    fitting = [r for r in data["partitions"]["fit"] if r["relation"] != "uncertain" and usable(r, columns)]
    x = np.array([[r["features"][i] for i in columns] for r in fitting])
    y = np.array([CLASSES.index(r["relation"]) for r in fitting])
    require(set(y) == {0,1,2}, "fitting partition missing a class")
    scaler = StandardScaler().fit(x)
    classifier = LogisticRegression(C=10, class_weight="balanced", solver="lbfgs", max_iter=2000, random_state=17)
    started = time.monotonic()
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        classifier.fit(scaler.transform(x), y)
    model = {"C": 10, "classOrder": CLASSES, "columns": columns, "featureOrder": [FEATURES[i] for i in columns],
             "scalerMean": scaler.mean_.tolist(), "scalerScale": scaler.scale_.tolist(),
             "coefficients": classifier.coef_.tolist(), "intercept": classifier.intercept_.tolist(),
             "fitPairIDs": [r["id"] for r in fitting], "fitLibraries": fold["fit"]}
    partitions = {}
    for name, rows in data["partitions"].items():
        scored = []
        for row in rows:
            p = None
            if usable(row, columns):
                values = [[row["features"][i] for i in columns]]
                p = exported_probabilities(model, values)[0].tolist()
                original = classifier.predict_proba(scaler.transform(values))[0]
                require(np.max(np.abs(original-p)) < 1e-12, "portable classifier parity failed")
            scored.append(row | {"probabilities": p, "status": "ok" if p is not None else "missing_features"})
        partitions[name] = scored
    selected = select_threshold(partitions["calibration"])
    threshold = selected["threshold"] if selected else None
    for rows in partitions.values():
        for row in rows:
            row["accepted"] = accepted(row, threshold)
    result = {"fold": fold["id"], "profile": profile, "featureFileSHA256": sha(run/"ablations"/fold["id"]/"features.json"),
              "model": model, "calibrationSelection": selected, "threshold": threshold,
              "partitions": partitions, "seconds": time.monotonic()-started,
              "metrics": {name: metrics(rows,threshold) for name,rows in partitions.items()},
              "evaluationRanking": diagnostic_curve(partitions["evaluation"])}
    save(output, result)
    print(json.dumps({"phase": "ablation-complete", "fold": fold["id"], "profile": profile,
                      "calibrationQualified": selected is not None, "evaluation": result["metrics"]["evaluation"]}),flush=True)
    boundary(run, external, f"saved-fit:{fold['id']}:{profile}")
    return result


def policy_metrics(rows):
    """Pool heldout decisions made with different independently calibrated thresholds."""
    result = metrics(rows, None)
    per = {}
    for library in sorted({r["library"] for r in rows}):
        subset = [r for r in rows if r["library"] == library and r["relation"] != "uncertain"]
        tp = sum(r["accepted"] and r["relation"] == "same" for r in subset)
        fp = sum(r["accepted"] and r["relation"] != "same" for r in subset)
        positive = sum(r["relation"] == "same" for r in subset)
        per[library] = {"tp": tp, "fp": fp, "fn": positive-tp,
                        "precision": tp/(tp+fp) if tp+fp else None, "recall": tp/positive if positive else None}
    tp,fp,fn = (sum(v[key] for v in per.values()) for key in ("tp","fp","fn"))
    recalls = [r["recall"] for r in per.values() if r["recall"] is not None]
    ambiguous = [r for r in rows if r["relation"] == "uncertain"]
    result.update(tp=tp, fp=fp, fn=fn, acceptedKnownPairs=tp+fp, precision=tp/(tp+fp) if tp+fp else None,
                  recall=tp/(tp+fn) if tp+fn else None, macroLibraryRecall=float(np.mean(recalls)) if recalls else None,
                  automationFraction=sum(r["accepted"] for r in rows)/len(rows),
                  acceptedUncertainPairs=sum(r["accepted"] for r in ambiguous),
                  acceptedUncertainFraction=sum(r["accepted"] for r in ambiguous)/len(ambiguous) if ambiguous else None,
                  perLibrary=per)
    return result


def summarize(run):
    summaries = {}
    folds = read(run / "folds.json")["folds"]
    for profile in PROFILES:
        reports = [read(run / "ablations" / fold["id"] / f"{profile}.json") for fold in folds]
        rows = [row for report in reports for row in report["partitions"]["evaluation"]]
        require(len(rows) == 3420 and len({r["id"] for r in rows}) == 3420, "incomplete OOF pair coverage")
        summaries[profile] = {"qualifyingCalibrationFolds": sum(r["calibrationSelection"] is not None for r in reports),
                              "pooledOOF": policy_metrics(rows), "perFold": [r["metrics"]["evaluation"] for r in reports],
                              "ranking": diagnostic_curve(rows)}
    result = {"profiles": summaries, "testAccess": False,
              "interpretation": "Training-library OOF diagnostic with separate calibration; not the six-library development score or final heldout test. Only 18 synthetic libraries."}
    save(run / "ablation-summary.json", result)
    return result
