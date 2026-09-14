#!/usr/bin/env python3
"""Post-run development error diagnostics; never changes official selection."""
import argparse
import json
from pathlib import Path

from audit_stage5 import counts,accepted
from stage5_common import read,save,sha,paths,RELEASE,STAGE2,now,require


def coverage_diagnostic(rows):
    best=None
    for threshold in sorted({r["probabilities"][0] for r in rows if r["relation"]!="uncertain" and r.get("probabilities") is not None}):
        value=counts(rows,threshold)
        if value["acceptedKnownPairs"]>=30:
            rank=(value["precision"],value["macroLibraryRecall"],threshold)
            if best is None or rank>best[0]:best=(rank,value)
    return None if best is None else {"threshold":best[0][2],"metrics":best[1],
        "purpose":"diagnostic precision at >=30 accepted pairs; NOT an approved operating point"}


def diagnose(run):
    require((run/"complete.json").exists(),"post-run diagnostics require completion")
    rows=[]
    reports=[]
    for seed in [17,29,41]:
        for epoch in [1,2,3]:
            file=run/"evaluations"/f"seed-{seed}-epoch-{epoch}/development/summary.json"
            report=read(file);reports.append(report)
            rows.append({"seed":seed,"epoch":epoch,"officialQualifies":report["selection"] is not None,
                "officialMetrics":report["allPairs"],"argmaxMetrics":report["argmaxOperatingPoint"],
                "bestPrecisionAtCoverage30":coverage_diagnostic(report["rows"]),"summarySHA256":sha(file)})
    available=[r for r in rows if r["bestPrecisionAtCoverage30"] is not None]
    examples={}
    if available:
        representative=max(available,key=lambda r:(r["bestPrecisionAtCoverage30"]["metrics"]["precision"],
            r["bestPrecisionAtCoverage30"]["metrics"]["macroLibraryRecall"],-r["epoch"],-r["seed"]))
        report=next(r for r in reports if (r["seed"],r["epoch"])==(representative["seed"],representative["epoch"]))
        threshold=representative["bestPrecisionAtCoverage30"]["threshold"]
        text={i["id"]:i["text"] for lib in read(RELEASE/"inputs-development.json")["libraries"] for i in lib["items"]}
        for name,predicate in {
            "falsePositive":lambda r: r["relation"] not in ["same","uncertain"] and accepted(r,threshold),
            "missedSame":lambda r:r["relation"]=="same" and not accepted(r,threshold),
            "acceptedAmbiguous":lambda r:r["relation"]=="uncertain" and accepted(r,threshold)}.items():
            subset=sorted([r for r in report["rows"] if predicate(r)],key=lambda r:-r["probabilities"][0])
            examples[name]={"count":len(subset),"examples":[{k:r[k] for k in ["library","first","second","relation","probabilities"]}
                | {"texts":[text[r["first"]],text[r["second"]]]} for r in subset[:8]]}
        examples["representative"]={"seed":representative["seed"],"epoch":representative["epoch"],"threshold":threshold,
            "diagnosticOnly":True,"doesNotChangeOfficialSelection":True}
    baseline=read(STAGE2/"baseline-summary.json")
    return {"at":now(),"runCompleteSHA256":sha(run/"complete.json"),"sourceSHA256":sha(Path(__file__)),
        "split":"development","testLabelsReadByThisDiagnostic":False,"candidates":rows,
        "frozenBaselineDevelopment":baseline["selectedMetrics"]["development"]["allPairs"],"errorExamples":examples,
        "limitation":"Post-run explanation of development errors, not a new operating-point selection or heldout comparison."}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--run",required=True);parser.add_argument("--output",required=True)
    args=parser.parse_args();run,_=paths(args.run);result=diagnose(run);save(args.output,result)
    print(json.dumps({"written":args.output,"candidates":[{"seed":r["seed"],"epoch":r["epoch"],
        "officialQualifies":r["officialQualifies"],"diagnostic":r["bestPrecisionAtCoverage30"]} for r in result["candidates"]]},indent=2))


if __name__=="__main__":main()
