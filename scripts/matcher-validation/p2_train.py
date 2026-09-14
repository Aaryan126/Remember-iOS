"""Three fixed-epoch MiniLM fits, with full-state effective-batch recovery."""
import gc
import math
import time

import p2_common as c
import p2_data as data
from screening2_neural import make_model, schedule
from stage5_train import rng_state, restore_rng, cpu_tree
from stage5_data import order_for, batch_inputs


def optimizer_for(model):
    import torch
    groups = [{"params": [p for n,p in model.named_parameters() if n.startswith("classifier.")], "base_lr": .001},
              {"params": [p for n,p in model.named_parameters() if not n.startswith("classifier.")], "base_lr": .000005}]
    for group in groups:
        group["lr"] = group["base_lr"]
    return torch.optim.AdamW(groups, weight_decay=.01)


def train_loop(model, optimizer, examples, forward, task, fingerprint, seed, epochs=3, batch=16, micro=8, pause_after=None):
    import torch
    device = next(model.parameters()).device.type
    previous = c.latest_recovery(task)
    if previous:
        payload = c.load_state(c.EXTERNAL / previous["file"], previous["SHA256"])
        c.require(payload["fingerprint"] == fingerprint, "recovery fit binding mismatch")
        model.load_state_dict(payload["model"], strict=True)
        optimizer.load_state_dict(payload["optimizer"])
        restore_rng(payload["rng"])
        position = payload["position"]
        c.publish(c.RUN / "resumptions" / f"{time.time_ns()}.json", {"task":task, "from":previous, "fullStateRestored":True})
        del payload
    else:
        position = {"epoch":0, "offset":0, "step":0, "seconds":0., "lossSum":0., "batches":0}

    def checkpoint():
        if device == "mps":
            torch.mps.synchronize()
        return c.save_recovery(task, {"fingerprint":fingerprint, "position":dict(position),
                                     "model":cpu_tree(model.state_dict()), "optimizer":cpu_tree(optimizer.state_dict()), "rng":rng_state()})

    checkpoint()
    invocation = position["step"]
    total = epochs * math.ceil(len(examples) / batch)
    # Preflight room for the next checkpoint, not just its small JSON receipt.
    reserve = sum(p.numel()*p.element_size() for p in model.parameters()) * 3 + 16*c.MIB
    while position["epoch"] < epochs:
        order = order_for(seed, position["epoch"], len(examples))
        model.train()
        while position["offset"] < len(order):
            if c.wants_pause():
                checkpoint()
                c.boundary("training-saved:" + task)
            c.check_space(reserve)
            chosen = [examples[i] for i in order[position["offset"]:position["offset"]+batch]]
            started = time.monotonic()
            optimizer.zero_grad(set_to_none=True)
            for group in optimizer.param_groups:
                group["lr"] = group["base_lr"] * schedule(position["step"], total)
            loss_sum = 0.
            for start in range(0, len(chosen), micro):
                chunk = chosen[start:start+micro]
                logits = forward(model, [i for i,_ in chunk], [i for i,_ in chosen])
                targets = torch.tensor([y for _,y in chunk], device=device)
                loss = torch.nn.functional.cross_entropy(logits, targets, reduction="sum") / len(chosen)
                c.require(bool(torch.isfinite(loss)), "nonfinite training loss")
                loss.backward()
                loss_sum += loss.item()
            norm = torch.stack([p.grad.norm() for p in model.parameters() if p.grad is not None]).norm()
            c.require(bool(torch.isfinite(norm)), "nonfinite training gradient")
            optimizer.step()
            if device == "mps":
                torch.mps.synchronize()
            position["offset"] += len(chosen)
            position["step"] += 1
            position["seconds"] += time.monotonic() - started
            position["lossSum"] += loss_sum
            position["batches"] += 1
            exercise_pause = pause_after is not None and position["step"]-invocation >= pause_after
            if position["step"] % 50 == 0 or c.wants_pause() or exercise_pause:
                checkpoint()
                if exercise_pause:
                    raise c.Paused("exercise saved:" + task)
                c.boundary("checkpoint:" + task)
            if position["step"] % 25 == 0:
                c.log("training", task=task, step=position["step"], totalSteps=total,
                      epoch=position["epoch"]+1, meanLoss=position["lossSum"]/position["batches"],
                      secondsPerStep=position["seconds"]/position["step"])
        position["epoch"] += 1
        position["offset"] = 0
        checkpoint()
    return position


def fit(seed, fold, pause_after=None):
    import torch
    c.require(seed in (17,29,41) and fold in (0,1,2,"final"), "unplanned fit")
    task = f"seed-{seed}-{fold}"
    folder = c.RUN / "fits" / task
    final_path = folder / "complete.json"
    if final_path.exists():
        record = c.read(final_path)
        c.require(c.digest(c.EXTERNAL / record["file"]) == record["SHA256"], "fit export changed")
        c.require(c.digest(folder / "spec.json") == record["fingerprint"], "fit spec changed")
        return record
    c.boundary("fit:" + task)
    torch.set_num_threads(4)
    c.require(torch.backends.mps.is_available(), "MPS unavailable; no silent backend switch")
    splits = c.read(c.RELEASE / "splits.json")
    fitting = splits["libraries"]["train"] if fold == "final" else splits["innerFolds"][fold]["fitLibraries"]
    _, gold = c.split_data("train")
    known = [r for r in gold if r["library"] in fitting and r["relation"] != "uncertain"]
    c.require({r["relation"] == "same" for r in known} == {False, True}, "missing binary class")
    tokens, index = data.tokens("train")
    examples = [(index[r["id"]]*2+d, int(r["relation"] == "same")) for r in known for d in (0,1)]
    definition = {"task":task, "seed":seed, "fitLibraries":fitting, "fitPairIDs":[r["id"] for r in known],
                  "manifestSHA256":c.digest(c.RUN / "manifest.json"), "tokenSHA256":c.digest(c.RUN / "tokens/train.json"),
                  "epochs":3, "batch":16, "microbatch":8, "directions":len(examples)}
    c.publish(folder / "spec.json", definition)
    fingerprint = c.digest(folder / "spec.json")
    model = make_model("C3", seed).to("mps")
    optimizer = optimizer_for(model)
    def forward(model, indices, chosen):
        length = min(512, ((int(tokens["attention_mask"][chosen].sum(-1).max())+31)//32)*32)
        return model(**batch_inputs(tokens, indices, "mps", length)).logits
    position = train_loop(model, optimizer, examples, forward, task, fingerprint, seed, pause_after=pause_after)
    target = c.EXTERNAL / "models" / f"{task}.pt.gz"
    c.boundary("export:" + task, 150*c.MIB)
    payload = {"fingerprint":fingerprint, "model":cpu_tree(model.state_dict())}
    if target.exists():
        old = c.load_state(target, c.digest(target))
        c.require(old["fingerprint"] == fingerprint and set(old["model"]) == set(payload["model"])
                  and all(torch.equal(old["model"][n],v) for n,v in payload["model"].items()), "orphan model differs")
    else:
        c.save_state(target, payload)
    record = {"task":task, "seed":seed, "fold":fold, "file":str(target.relative_to(c.EXTERNAL)),
              "SHA256":c.digest(target), "fingerprint":fingerprint, "fitLibraries":fitting, "position":position}
    c.publish(final_path, record)
    del model, optimizer, tokens, payload
    gc.collect()
    torch.mps.empty_cache()
    c.log("fit-complete", **record)
    return record


def predict(record, split, library_ids):
    import torch
    _, gold = c.split_data(split)
    c.require(not set(library_ids) & set(record["fitLibraries"]), "in-sample neural scores forbidden")
    rows = [r for r in gold if r["library"] in library_ids]
    c.require({r["library"] for r in rows} == set(library_ids), "prediction libraries missing/wrong split")
    folder = c.RUN / "predictions" / record["task"] / split
    missing = [r for r in rows if not (folder / f"{r['id']}.json").exists()]
    if missing:
        c.boundary("predict:" + record["task"])
        tokens,index = data.tokens(split)
        model = make_model("C3", record["seed"]).to("mps")
        saved = c.load_state(c.EXTERNAL / record["file"], record["SHA256"])
        c.require(saved["fingerprint"] == record["fingerprint"], "prediction fit binding")
        model.load_state_dict(saved["model"], strict=True)
        del saved
        model.eval()
        for start in range(0,len(missing),8):
            c.boundary("predict:" + record["task"])
            batch = missing[start:start+8]
            indices = [index[r["id"]]*2+d for r in batch for d in (0,1)]
            with torch.inference_mode():
                values = model(**batch_inputs(tokens,indices,"mps")).logits.softmax(-1)[:,1].cpu().tolist()
            for n,row in enumerate(batch):
                directions = values[n*2:n*2+2]
                c.require(all(math.isfinite(v) and 0<=v<=1 for v in directions), "nonfinite prediction")
                c.publish(folder / f"{row['id']}.json", {"id":row["id"], "score":sum(directions)/2,
                          "directions":directions, "weightsSHA256":record["SHA256"]})
            if start % 200 == 0:
                c.log("prediction", task=record["task"], split=split, completed=start+len(batch), remaining=len(missing)-start-len(batch))
        del model,tokens
        gc.collect()
        torch.mps.empty_cache()
    result = {}
    for r in rows:
        value = c.read(folder / f"{r['id']}.json")
        c.require(value["id"] == r["id"] and value["weightsSHA256"] == record["SHA256"], "prediction changed")
        result[r["id"]] = value["score"]
    return result
