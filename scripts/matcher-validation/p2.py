"""P2 CLI. Every long phase is resumable; no phone or production operations."""
import argparse
import time

import p2_common as c
import p2_data as data
import p2_models as models
import p2_train as training


def prepare():
    if (c.RUN / "manifest.json").exists():
        return c.verify()
    c.p1_release.verify()
    from screening2_common import verify_environment
    verify_environment()
    asset=c.read(c.ROOT / "Evaluation/MatcherFeasibility/model-manifest.json")
    assets={asset["workspaceRelativeDirectory"]+"/"+name:record["sha256"] for name,record in asset["assets"].items()}
    for relative,expected in assets.items():
        c.require(c.digest(c.WORKSPACE / relative)==expected,"pinned asset mismatch")
    # Twelve FP32 exports plus two retained AdamW states and one temporary state.
    # Source model file size is slightly larger than the classifier parameter tensors.
    estimated_peak=21*asset["assets"]["pytorch_model.bin"]["bytes"]+384*c.MIB
    snapshot=c.check_space(estimated_peak)
    manifest={"stage":"P2","authorizedBy":"user: cary on after P1 checkpoint report",
              "sources":c.source_bindings(),"environment":c.environment(),"assets":assets,
              "p1SHA256":c.digest(c.DATA / "runs/p1-01/complete.json"),
              "model":asset["model"],"revision":asset["revision"],"seeds":[17,29,41],
              "estimatedPeakAdditionalBytes":estimated_peak,"storageAtPreparation":snapshot,
              "epochs":3,"effectiveBatch":16,"microbatch":8,"maxTokens":512,
              "headLR":.001,"backboneLR":.000005,"weightDecay":.01,"warmupFraction":.1,
              "neuralClassOrder":["not_same","same"],"loss":"unweighted directional cross entropy",
              "combiner":"ten existing features + clipped logit of mean directional probability; C1 logistic",
              "retention":"all twelve final exports; latest two global verified recovery states; receipt before removal",
              "oldTestOpened":False,"phoneRequired":False,"productionChanges":False}
    c.publish(c.RUN / "manifest.json",manifest)
    return manifest


def exercise(pause_after):
    import torch
    from screening2_neural import seed_all
    c.require(torch.backends.mps.is_available(),"MPS exercise unavailable")
    if (c.RUN / "pause-exercise.json").exists():
        return c.read(c.RUN / "pause-exercise.json")
    seed_all(17)
    model=torch.nn.Sequential(torch.nn.Linear(4,8),torch.nn.ReLU(),torch.nn.Dropout(.2),torch.nn.Linear(8,2)).to("mps")
    optimizer=torch.optim.AdamW([{"params":list(model.parameters()),"lr":.001,"base_lr":.001}],weight_decay=.01)
    x=torch.arange(128,dtype=torch.float32).reshape(32,4).to("mps")/128
    examples=[(n,n%2) for n in range(32)]
    result=training.train_loop(model,optimizer,examples,lambda m,i,all_i:m(x[i]),"pause-exercise",
                               c.digest(c.RUN / "manifest.json"),17,epochs=2,batch=8,micro=4,pause_after=pause_after)
    resumptions=[c.read(p) for p in (c.RUN / "resumptions").glob("*.json")]
    c.require(any(r["task"]=="pause-exercise" and r["fullStateRestored"] for r in resumptions),"exercise must resume across process invocations")
    report={"passed":True,"device":"mps","position":result,"restoredModelOptimizerRNGAndOffset":True,
            "crossProcess":True,"bitwiseMPSClaim":False,"fixture":"tiny dropout classifier, same checkpoint/training engine"}
    c.publish(c.RUN / "pause-exercise.json",report)
    return report


def evidence_paths():
    return [p for p in c.RUN.rglob("*.json") if p.name!="complete.json" or p.parent!=c.RUN
            if not str(p.relative_to(c.RUN)).startswith(("control/","pauses/","failures/"))]


def completed():
    c.verify()
    manifest=c.read(c.RUN / "complete.json")
    c.require(manifest["stage"]=="P2" and manifest["complete"] is True and manifest["stopForUserReview"] is True,"invalid P2 completion")
    c.require(set(manifest["artifacts"])=={str(p.relative_to(c.RUN)) for p in evidence_paths()},"P2 evidence inventory changed")
    for relative,expected in manifest["artifacts"].items():
        target=(c.RUN / relative).resolve()
        c.require(target.is_relative_to(c.RUN.resolve()) and c.digest(target)==expected,"completed evidence changed")
    required={"report.json","selection.json","baseline.json","pause-exercise.json"}
    required|={f"evaluation/seed-{s}.json" for s in (17,29,41)}
    required|={f"fits/seed-{s}-{f}/complete.json" for s in (17,29,41) for f in (0,1,2,"final")}
    c.require(required.issubset(manifest["artifacts"]),"incomplete P2 evidence inventory")
    c.require(set(manifest["externalArtifacts"])=={str(p.relative_to(c.EXTERNAL)) for p in c.EXTERNAL.rglob("*") if p.is_file()},"external inventory changed")
    for relative,expected in manifest["externalArtifacts"].items():
        target=(c.EXTERNAL / relative).resolve()
        c.require(target.is_relative_to(c.EXTERNAL.resolve()) and c.digest(target)==expected,"external evidence changed")
    c.verify_selection()
    return {"complete":True,"completeSHA256":c.digest(c.RUN / "complete.json"),"allSeedsPassed":c.read(c.RUN / "report.json")["allSeedsPassed"]}


def run(pause_after=None):
    if (c.RUN / "complete.json").exists():
        return completed()
    c.require(c.read(c.RUN / "pause-exercise.json")["passed"] is True,"pause exercise required before long fits")
    data.tokens("train")
    models.baseline()
    for seed in (17,29,41):
        models.hybrid(seed,pause_after)
    models.freeze_selection()
    models.evaluate()
    c.verify()
    evidence={str(p.relative_to(c.RUN)):c.digest(p) for p in evidence_paths()}
    external={str(p.relative_to(c.EXTERNAL)):c.digest(p) for p in c.EXTERNAL.rglob("*") if p.is_file()}
    c.publish(c.RUN / "complete.json",{"stage":"P2","complete":True,"stopForUserReview":True,
                                      "productionQualified":False,"oldTestOpened":False,"artifacts":evidence,"externalArtifacts":external})
    return completed()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("prepare","exercise","run","pause","verify","status"))
    parser.add_argument("--resume",action="store_true")
    parser.add_argument("--pause-after-steps",type=int)
    args=parser.parse_args()
    if args.pause_after_steps is not None:
        c.require(args.pause_after_steps>0,"pause steps must be positive")
    c.setup()
    if args.command=="pause":
        c.pause()
        c.log("pause-requested",safeToCloseLaptop=False)
        return
    handle=c.lock()
    try:
        if args.command=="prepare":
            c.log("prepared",manifest=prepare())
            return
        c.verify()
        if args.command in ("status","verify"):
            result=completed() if (c.RUN / "complete.json").exists() else {"complete":False,
                   "fits":len(list((c.RUN / "fits").glob("*/complete.json"))),"recoveries":c.recoveries()[-2:]}
            c.log(args.command,**result)
            return
        if args.resume:
            c.resume_control()
        c.boundary("start")
        result=exercise(args.pause_after_steps) if args.command=="exercise" else run(args.pause_after_steps)
        c.log("finished",result=result,safeToCloseLaptop=True)
    except c.Paused as error:
        c.log("paused",reason=str(error),safeToCloseLaptop=True)
    except Exception as error:
        c.publish(c.RUN / "failures" / f"{time.time_ns()}.json",{"type":type(error).__name__,"message":str(error)})
        raise
    finally:
        handle.close()


if __name__=="__main__":
    main()
