"""Small known-label learning check, not model selection or quality evaluation."""
from __future__ import annotations

import gc
import json
import time

from screening_common import *
from stage5_common import save_state, load_state, publish_tensor_file
from stage5_train import new_model, cpu_tree, rng_state, restore_rng
from stage5_data import batch_inputs, order_for

# Executing-agent review of explicit H17/Loft L22/Q4/C8 references in mf01.
# Related pairs all include i04, which explicitly links Loft and Hearth's supplier.
SANITY_PAIRS = [(1,12,"same"),(2,16,"same"),(4,7,"same"),(8,11,"same"),
                (1,4,"related"),(4,12,"related"),(4,15,"related"),(4,18,"related"),
                (1,8,"unrelated"),(2,8,"unrelated"),(8,12,"unrelated"),(11,16,"unrelated")]


def sanity_inputs():
    inputs, _ = load_split("train")
    items = {i["id"]: i["text"] for lib in inputs["libraries"] for i in lib["items"]}
    truth = {r["id"]: r["relation"] for r in gold("train")}
    result = []
    for a,b,relation in SANITY_PAIRS:
        first,second = f"mf01-i{a:02}",f"mf01-i{b:02}"
        key = first+"--"+second
        require(truth[key] == relation, "reviewed sanity label mismatch")
        result.append({"id": key, "texts": [items[first],items[second]], "relation": relation})
    return result


def receipts(run):
    return sorted([read(p) for p in (run/"sanity/recovery").glob("*.json")],key=lambda r:r["stamp"])


def checkpoint(run, external, model, optimizer, state):
    previous = receipts(run)
    if previous and previous[-1]["step"] == state["step"]:
        require(sha(external/previous[-1]["file"]) == previous[-1]["SHA256"], "latest sanity state changed")
        return previous[-1]
    # A worst-case estimate leaves reserve before publication; actual blobs are ~280MB.
    boundary(run, external, "sanity-before-save", planned=450*1024**2) if not capacity(run,external,450*1024**2) else None
    import torch
    torch.mps.synchronize()
    stamp = time.time_ns()
    path = external / "recovery/sanity" / f"step-{state['step']:05}-{stamp}.pt.gz"
    save_state(path, {"manifestSHA256": sha(run/"manifest.json"), "model": cpu_tree(model.state_dict()),
                     "optimizer": cpu_tree(optimizer.state_dict()), "rng": rng_state(), "state": state})
    record = {"stamp": stamp, "step": state["step"], "file": str(path.relative_to(external)),
              "SHA256": sha(path), "bytes": path.stat().st_size, "at": now()}
    save(run/"sanity/recovery"/f"{stamp}.json",record)
    roll_recovery(run,external,receipts(run))
    print(json.dumps({"phase":"sanity-checkpoint","step":state["step"],"bytes":record["bytes"]}),flush=True)
    return record


def run_sanity(run, external, pause_after_steps=None):
    if (run/"sanity/result.json").exists():
        return read(run/"sanity/result.json")
    boundary(run, external, "sanity-initialize",planned=700*1024**2)
    import torch
    from transformers import AutoTokenizer
    from safetensors.torch import save_file
    torch.set_num_threads(4)
    require(torch.backends.mps.is_available(), "MPS unavailable; no implicit backend change")
    model_dir = WORKSPACE / read(DATA/"model-manifest.json")["workspaceRelativeDirectory"]
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir),local_files_only=True,trust_remote_code=False)
    examples = sanity_inputs()
    pairs = [texts for row in examples for texts in (row["texts"],row["texts"][::-1])]
    encoded = tokenizer([p[0] for p in pairs],[p[1] for p in pairs],padding="max_length",max_length=512,
                        truncation="longest_first",return_tensors="pt")
    targets = torch.tensor([index for row in examples for index in (["same","related","unrelated"].index(row["relation"]),)*2],dtype=torch.long)
    if not (run/"sanity/inputs.json").exists():
        save(run/"sanity/inputs.json",{"examples":examples,"directions":24,"goldReviewed":True,
             "purpose":"memorization/optimization sanity only; not generalization", "maxSteps":200,
             "passRule":"24/24 directional predictions correct and CE<0.1 on two successive 10-step checks",
             "optimizer":"AdamW all weights, lr2e-5 weight_decay0.01; unweighted 3-class loss"})
    model = new_model(17).to("mps")
    optimizer = torch.optim.AdamW(model.parameters(),lr=2e-5,weight_decay=.01)
    prior = receipts(run)
    if prior:
        saved = load_state(external/prior[-1]["file"],prior[-1]["SHA256"])
        require(saved["manifestSHA256"] == sha(run/"manifest.json"), "wrong recovery manifest")
        model.load_state_dict(saved["model"],strict=True)
        optimizer.load_state_dict(saved["optimizer"])
        restore_rng(saved["rng"])
        state = saved["state"]
        save(run/"sanity/resumptions"/f"{time.time_ns()}.json",{"at":now(),"step":state["step"],
             "recoverySHA256":prior[-1]["SHA256"],"modelOptimizerAndRNGRestored":True})
        del saved; gc.collect()
    else:
        state = {"step":0,"consecutivePasses":0,"trainingSeconds":0.0}
        checkpoint(run,external,model,optimizer,state)
    invocation_start = state["step"]
    while state["step"] < 200 and state["consecutivePasses"] < 2:
        if wants_pause(run) or not capacity(run,external,700*1024**2):
            checkpoint(run,external,model,optimizer,state)
            if not wants_pause(run): request_pause(run,"storage_budget_after_sanity_save")
            boundary(run,external,f"sanity-saved-step:{state['step']}")
        started = time.monotonic()
        step = state["step"]
        order = order_for(17,step//2,len(pairs))
        indices = order[(step%2)*16:(step%2)*16+16]
        model.train(); optimizer.zero_grad(set_to_none=True)
        loss = torch.nn.functional.cross_entropy(model(**batch_inputs(encoded,indices,"mps")).logits,targets[indices].to("mps"))
        require(bool(torch.isfinite(loss)),"nonfinite sanity loss")
        loss.backward()
        require(all(bool(torch.isfinite(p.grad).all()) for p in model.parameters() if p.grad is not None),"nonfinite sanity gradient")
        optimizer.step(); torch.mps.synchronize()
        state["step"] += 1;state["trainingSeconds"] += time.monotonic()-started
        del loss
        if state["step"] % 10 == 0:
            model.eval()
            with torch.inference_mode():
                logits = torch.cat([model(**batch_inputs(encoded,list(range(i,min(i+8,len(pairs)))),"mps")).logits.cpu()
                                    for i in range(0,len(pairs),8)])
                correct = int((logits.argmax(-1)==targets).sum())
                ce = float(torch.nn.functional.cross_entropy(logits,targets))
            passed = correct == len(pairs) and ce < .1
            state["consecutivePasses"] = state["consecutivePasses"]+1 if passed else 0
            record = {"step":state["step"],"correctDirections":correct,"totalDirections":len(pairs),"crossEntropy":ce,
                      "probabilities":logits.softmax(-1).tolist(),"consecutivePasses":state["consecutivePasses"]}
            path = run/"sanity/checks"/f"step-{state['step']:04}.json"
            # Interrupted unsaved steps may replay with MPS numerical variation: preserve both receipts.
            if path.exists(): path = path.with_name(f"step-{state['step']:04}-replay-{time.time_ns()}.json")
            save(path,record)
            print(json.dumps({k:v for k,v in record.items() if k!="probabilities"}),flush=True)
        if pause_after_steps is not None and state["step"]-invocation_start >= pause_after_steps:
            request_pause(run,"live_sanity_pause_exercise")
        if state["step"]%50 == 0 or wants_pause(run):
            checkpoint(run,external,model,optimizer,state)
            boundary(run,external,f"sanity-saved-step:{state['step']}")
    last = checkpoint(run,external,model,optimizer,state)
    path = external/"sanity/model.safetensors"
    if not path.exists():
        publish_tensor_file(path,lambda pending:save_file(cpu_tree(model.state_dict()),str(pending)))
    else:
        from safetensors.torch import load_file
        exported = load_file(str(path))
        require(all(torch.equal(v.detach().cpu(),exported[k]) for k,v in model.state_dict().items()),"orphan sanity export differs")
        del exported
    result = {"passed":state["consecutivePasses"]>=2,"steps":state["step"],"trainingSeconds":state["trainingSeconds"],
              "recoverySHA256":last["SHA256"],"weightsSHA256":sha(path),"weights":str(path.relative_to(external)),
              "generalizationClaim":False,"testAccess":False}
    save(run/"sanity/result.json",result)
    del model,optimizer;gc.collect();torch.mps.empty_cache()
    return result
