"""Binary membership metrics; ambiguous examples never count as known negatives."""
import math
from collections import Counter
from sklearn.metrics import average_precision_score


def accepts(row,threshold):
    return threshold is not None and row.get("score") is not None and row["score"]>=threshold


def counts(rows,threshold=None,stored=False):
    decision=lambda r: bool(r["accepted"]) if stored else accepts(r,threshold)
    known=[r for r in rows if r["relation"]!="uncertain"]
    per={}
    for lib in sorted({r["library"] for r in rows}):
        subset=[r for r in known if r["library"]==lib]
        tp=sum(decision(r) and r["relation"]=="same" for r in subset)
        fp=sum(decision(r) and r["relation"]!="same" for r in subset)
        positive=sum(r["relation"]=="same" for r in subset)
        per[lib]={"tp":tp,"fp":fp,"fn":positive-tp,"recall":tp/positive if positive else None,
                  "precision":tp/(tp+fp) if tp+fp else None}
    tp,fp,fn=(sum(r[k] for r in per.values()) for k in ("tp","fp","fn"))
    recalls=[v["recall"] for v in per.values() if v["recall"] is not None]
    uncertain=[r for r in rows if r["relation"]=="uncertain"]
    scored=[r for r in known if r.get("score") is not None]
    return {"pairs":len(rows),"knownPairs":len(known),"uncertainPairs":len(uncertain),
        "tp":tp,"fp":fp,"fn":fn,"acceptedKnown":tp+fp,"precision":tp/(tp+fp) if tp+fp else None,
        "recall":tp/(tp+fn) if tp+fn else None,"macroRecall":sum(recalls)/len(recalls) if recalls else None,
        "falseRelated":sum(decision(r) and r["relation"]=="related" for r in rows),
        "falseUnrelated":sum(decision(r) and r["relation"]=="unrelated" for r in rows),
        "acceptedUncertain":sum(decision(r) for r in uncertain),
        "missingKnown":sum(r.get("score") is None for r in known),"perLibrary":per,
        "averagePrecision":float(average_precision_score([r["relation"]=="same" for r in scored],[r["score"] for r in scored]))
            if any(r["relation"]=="same" for r in scored) else None}


def select(rows):
    positives=Counter(r["library"] for r in rows if r["relation"]=="same")
    candidates=sorted([r for r in rows if r["relation"]!="uncertain" and r.get("score") is not None],key=lambda r:-r["score"])
    tp=fp=0;hits=Counter();best=None
    for i,row in enumerate(candidates):
        if row["relation"]=="same": tp+=1;hits[row["library"]]+=1
        else: fp+=1
        if i+1<len(candidates) and candidates[i+1]["score"]==row["score"]:continue
        precision=tp/(tp+fp)
        recall=sum(hits[lib]/n for lib,n in positives.items())/len(positives) if positives else 0
        rank=(recall,precision,row["score"])
        if tp+fp>=30 and precision>=.95 and (best is None or rank>best):best=rank
    return None if best is None else {"threshold":best[2],"metrics":counts(rows,best[2])}


def with_decisions(rows,threshold):
    for row in rows:
        score=row.get("score")
        if score is not None and not (math.isfinite(score) and 0<=score<=1):raise ValueError("invalid same score")
    return [r|{"accepted":accepts(r,threshold)} for r in rows]


def ranking(record,fallback=False):
    m=record["pooled"]
    value=lambda x: -1 if x is None else x
    if fallback:return (value(m["averagePrecision"]),)
    return (record["qualifyingFolds"],value(m["macroRecall"]),value(m["precision"]))
