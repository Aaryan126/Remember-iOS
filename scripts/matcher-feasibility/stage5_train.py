"""Resumable MPS fine-tuning. Selection and heldout labels are outside this module."""
import gc
import random
import numpy as np

from stage5_common import *
from stage5_data import prepare_tokens, training_examples, order_for, class_weights, batch_inputs


def rng_state():
    import torch
    state = np.random.get_state()
    return {"python": random.getstate(), "numpy": [state[0], state[1].tolist(), state[2], state[3], state[4]],
            "torch": torch.get_rng_state(), "mps": torch.mps.get_rng_state() if torch.backends.mps.is_available() else None}


def restore_rng(state):
    import torch
    random.setstate(state["python"])
    np_state = state["numpy"]
    np.random.set_state((np_state[0], np.array(np_state[1], dtype=np.uint32), *np_state[2:]))
    torch.set_rng_state(state["torch"])
    if state["mps"] is not None: torch.mps.set_rng_state(state["mps"])


def cpu_tree(value):
    import torch
    if isinstance(value, torch.Tensor): return value.detach().cpu()
    if isinstance(value, dict): return {k: cpu_tree(v) for k, v in value.items()}
    if isinstance(value, list): return [cpu_tree(v) for v in value]
    if isinstance(value, tuple): return tuple(cpu_tree(v) for v in value)
    return value


def new_model(seed):
    import torch
    from transformers import BertForSequenceClassification
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.mps.manual_seed(seed)
    directory = WORKSPACE / read(DATA / "model-manifest.json")["workspaceRelativeDirectory"]
    model, info = BertForSequenceClassification.from_pretrained(str(directory), num_labels=3,
        id2label=dict(enumerate(CLASSES)), label2id={v: i for i, v in enumerate(CLASSES)},
        local_files_only=True, trust_remote_code=False, weights_only=True, attn_implementation="eager", output_loading_info=True)
    require(set(info["missing_keys"]) == {"classifier.weight", "classifier.bias"}
            and not info.get("mismatched_keys") and not info.get("error_msgs"), "unexpected backbone initialization")
    return model


def recovery_receipts(run, seed):
    receipts = [read(path) | {"receipt": str(path)} for path in (run / "recovery" / f"seed-{seed}").glob("*.json")]
    return sorted(receipts, key=lambda r: (r["globalStep"], r["savedAtNS"]))


def apply_retention(run, external, seed):
    policy_path = run / "control/retention-policy.json"
    if not policy_path.exists(): return 0
    policy = read(policy_path)
    require(policy["policy"] in ["keep-all", "latest-two"] and policy.get("explicitUserAuthorization"), "invalid retention authority")
    if policy["policy"] == "keep-all": return 0
    receipts = recovery_receipts(run,seed)
    removed = 0
    for receipt in receipts[:-2]:
        file = (external / receipt["file"]).resolve()
        require(file.is_relative_to((external / "recovery" / f"seed-{seed}").resolve()) and file.name.endswith(".pt.gz"), "unsafe retention target")
        event = run / "retention-history" / f"{receipt['savedAtNS']}.json"
        if not file.exists():
            require(event.exists(), "unaccounted missing recovery checkpoint"); continue
        require(sha(file) == receipt["SHA256"], "retention target changed")
        if not event.exists():
            save(event,{"at":now(),"file":receipt["file"],"SHA256":receipt["SHA256"],"bytes":receipt["bytes"],
                "policySHA256":sha(policy_path),"keptRecoveryFiles":[r["file"] for r in receipts[-2:]],
                "action":"authorized removal of superseded recovery state; receipt and all epoch candidates retained"})
        file.unlink(); removed += 1
    return removed


def checkpoint(run, external, model, optimizer, state, reason):
    import torch
    previous = recovery_receipts(run, state["seed"])
    if previous and all(previous[-1][key] == state[key] for key in ["epoch", "globalStep", "nextOffset", "microbatch"]):
        require((external / previous[-1]["file"]).exists(), "latest recovery file missing")
        return previous[-1]
    torch.mps.synchronize()
    stamp = time.time_ns()
    file = external / "recovery" / f"seed-{state['seed']}" / f"step-{state['globalStep']:05d}-{stamp}.pt.gz"
    started = time.monotonic()
    value = {"schemaVersion": 1, "manifestSHA256": sha(run / "manifest.json"),
             "model": cpu_tree(model.state_dict()), "optimizer": cpu_tree(optimizer.state_dict()),
             "position": dict(state), "rng": rng_state()}
    save_state(file, value)
    receipt = {"savedAtNS": stamp, "at": now(), "seed": state["seed"], "epoch": state["epoch"],
               "globalStep": state["globalStep"], "nextOffset": state["nextOffset"], "microbatch": state["microbatch"],
               "reason": reason, "file": str(file.relative_to(external)), "SHA256": sha(file), "bytes": file.stat().st_size,
               "saveSeconds": time.monotonic()-started, "manifestSHA256": sha(run / "manifest.json")}
    save(run / "recovery" / f"seed-{state['seed']}" / f"{stamp}.json", receipt)
    del value; gc.collect()
    removed = apply_retention(run,external,state["seed"])
    if removed: print(__import__('json').dumps({"phase":"approved-recovery-retention","removedSupersededCheckpoints":removed,"epochCandidatesPreserved":True}),flush=True)
    print(__import__('json').dumps({"phase": "recovery-checkpoint", **{k: receipt[k] for k in ['seed','epoch','globalStep','nextOffset','bytes','saveSeconds','reason']}}), flush=True)
    return receipt


def train_epoch(run, external, seed, epoch, pause_after_steps=None):
    import torch
    import torch.nn.functional as F
    from safetensors.torch import load_file, save_file
    require(seed in [17,29,41] and epoch in [0,1,2], "unplanned training candidate")
    done = run / "epochs" / f"seed-{seed}-epoch-{epoch+1}.json"
    if done.exists():
        record = read(done); require(sha(external / record["weights"]) == record["weightsSHA256"], "epoch weights changed")
        return record
    boundary(run, f"before-training:{seed}:{epoch+1}")
    torch.set_num_threads(4)
    require(torch.backends.mps.is_available(), "MPS unavailable; no silent backend change")
    receipt = prepare_tokens(run, external, "train")
    tokens = load_file(str(external / receipt["file"]))
    examples = training_examples(run, receipt)
    weights = torch.tensor(class_weights([label for _,label in examples]), device="mps")
    model = new_model(seed).to("mps")
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=.01)
    previous = recovery_receipts(run, seed)
    if previous:
        latest = previous[-1]
        state_file = external / latest["file"]
        recovered = load_state(state_file, latest["SHA256"])
        require(recovered["manifestSHA256"] == sha(run / "manifest.json"), "recovery config changed")
        model.load_state_dict(recovered["model"], strict=True)
        optimizer.load_state_dict(recovered["optimizer"])
        state = recovered["position"]
        restore_rng(recovered["rng"])
        require(state["seed"] == seed, "wrong recovery seed")
        if state["epoch"] == epoch-1:
            require(state["nextOffset"] == len(examples), "previous epoch incomplete")
            state.update(epoch=epoch, nextOffset=0, lossSum=0.0, lossSteps=0)
        require(state["epoch"] == epoch, "recovery epoch mismatch")
        del recovered; gc.collect(); torch.mps.empty_cache()
        save(run / "resumptions" / f"{time.time_ns()}.json", {"at": now(), "seed": seed,
             "epoch": epoch, "globalStep": state["globalStep"], "nextOffset": state["nextOffset"],
             "checkpointSHA256": latest["SHA256"], "restoredModelOptimizerCPUAndMPSRandomStates": True})
    else:
        require(epoch == 0, "no checkpoint for previous epoch")
        state = {"seed": seed, "epoch": epoch, "globalStep": 0, "nextOffset": 0,
                 "microbatch": 8, "lossSum": 0.0, "lossSteps": 0, "trainingSeconds": 0.0}
        checkpoint(run, external, model, optimizer, state, "initialized")
    model.train()
    order = order_for(seed, epoch, len(examples))
    invocation_step = state["globalStep"]
    step_times = []
    while state["nextOffset"] < len(order):
        if wants_pause(run):
            checkpoint(run, external, model, optimizer, state, "pause")
            boundary(run, f"training-saved:{seed}:{epoch}:{state['globalStep']}")
        if shutil.disk_usage(run).free < 11 * 1024**3:
            checkpoint(run, external, model, optimizer, state, "low-disk-safe-stop")
            request_pause(run); boundary(run, "low-disk-checkpoint-saved")
        started = time.monotonic()
        chosen = [examples[i] for i in order[state["nextOffset"]:state["nextOffset"]+16]]
        indices, labels = zip(*chosen)
        longest = int(tokens["attention_mask"][list(indices)].sum(-1).max())
        length = min(512, ((longest+31)//32)*32)
        denominator = sum(float(weights[label].item()) * .5 for label in labels)
        prior_rng = rng_state()
        while True:
            optimizer.zero_grad(set_to_none=True)
            loss_sum = 0.0
            try:
                for offset in range(0, len(chosen), state["microbatch"]):
                    batch = chosen[offset:offset+state["microbatch"]]
                    values = batch_inputs(tokens, [i for i,_ in batch], "mps", length)
                    targets = torch.tensor([label for _,label in batch], dtype=torch.long, device="mps")
                    logits = model(**values).logits
                    loss = (F.cross_entropy(logits, targets, weight=weights, reduction="none") * .5).sum() / denominator
                    require(bool(torch.isfinite(loss).item()), "nonfinite training loss")
                    loss.backward(); loss_sum += loss.detach().item()
                    del values, targets, logits, loss
                grad_norm = torch.stack([parameter.grad.detach().norm() for parameter in model.parameters() if parameter.grad is not None]).norm()
                require(bool(torch.isfinite(grad_norm).item()), "nonfinite training gradient")
                del grad_norm
                break
            except RuntimeError as error:
                if "out of memory" not in str(error).lower() or state["microbatch"] == 1: raise
                old = state["microbatch"]; state["microbatch"] //= 2
                values = targets = logits = loss = None
                optimizer.zero_grad(set_to_none=True); gc.collect(); torch.mps.empty_cache(); restore_rng(prior_rng)
                save(run / "memory-adjustments" / f"{time.time_ns()}.json", {"seed": seed, "epoch": epoch,
                    "globalStep": state["globalStep"], "fromMicrobatch": old, "toMicrobatch": state["microbatch"],
                    "effectiveBatchUnchanged": 16, "reason": "MPS out of memory during forward/backward; entire uncommitted batch retried"})
        optimizer.step(); torch.mps.synchronize()
        seconds = time.monotonic()-started
        state["nextOffset"] += len(chosen); state["globalStep"] += 1
        state["lossSum"] += loss_sum; state["lossSteps"] += 1; state["trainingSeconds"] += seconds
        step_times.append(seconds)
        if state["globalStep"] % 10 == 0:
            print(__import__('json').dumps({"phase": "training", "seed": seed, "epoch": epoch+1,
                "globalStep": state["globalStep"], "directionsCompleted": state["nextOffset"], "directionsPerEpoch": len(order),
                "meanStepSecondsThisInvocation": sum(step_times)/len(step_times),
                "meanLossThisEpoch": state["lossSum"]/state["lossSteps"], "microbatch": state["microbatch"],
                "mpsDriverBytes": torch.mps.driver_allocated_memory()}), flush=True)
        if pause_after_steps is not None and state["globalStep"]-invocation_step >= pause_after_steps: request_pause(run)
        if state["globalStep"] % 50 == 0 or wants_pause(run):
            checkpoint(run, external, model, optimizer, state, "pause" if wants_pause(run) else "periodic")
            boundary(run, f"training-saved:{seed}:{epoch}:{state['globalStep']}")
    recovery = checkpoint(run, external, model, optimizer, state, "epoch-complete")
    candidate = external / "candidates" / f"seed-{seed}-epoch-{epoch+1}"
    file = candidate / "model.safetensors"
    if file.exists():
        prior = load_file(str(file))
        require(all(torch.equal(prior[k], v.detach().cpu()) for k,v in model.state_dict().items()), "unreceipted candidate differs")
    else: publish_tensor_file(file, lambda pending: save_file(cpu_tree(model.state_dict()), str(pending)))
    from environment import publish_bytes
    publish_bytes(candidate / "config.json", model.config.to_json_string().encode())
    result = {"seed": seed, "epoch": epoch+1, "weights": str(file.relative_to(external)), "weightsSHA256": sha(file),
        "configSHA256": sha(candidate / "config.json"), "recoverySHA256": recovery["SHA256"],
        "globalStep": state["globalStep"], "meanLoss": state["lossSum"]/state["lossSteps"],
        "trainingSecondsCumulative": state["trainingSeconds"], "trainingDirections": len(order), "microbatch": state["microbatch"],
        "truncatedTrainingDirections": sum(receipt["rows"][index//2]["untruncatedTokens"][index%2] > 512 for index,_ in examples)}
    save(done, result)
    del model, optimizer; gc.collect(); torch.mps.empty_cache()
    return result
