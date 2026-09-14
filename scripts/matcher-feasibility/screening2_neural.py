"""Checkpointed binary MiniLM/MLP fits and resumable pair predictions."""
from __future__ import annotations

import gc
import json
import math
import numpy as np

from screening2_common import *
from screening2_data import task_id,matrix,partition
from stage5_common import save_state,load_state
from stage5_train import rng_state,restore_rng,cpu_tree
from stage5_data import batch_inputs,order_for


def seed_all(seed):
    import random
    import torch
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.mps.manual_seed(seed)


def make_model(trial,seed,width=None):
    import torch
    seed_all(seed)
    if trial.startswith("B"):
        require(width is not None,"missing MLP width")
        return torch.nn.Sequential(torch.nn.Linear(width,32 if trial=="B2" else 64),torch.nn.ReLU(),
                                   torch.nn.Dropout(.2),torch.nn.Linear(32 if trial=="B2" else 64,2))
    from transformers import BertForSequenceClassification
    directory=WORKSPACE/read(DATA/"model-manifest.json")["workspaceRelativeDirectory"]
    model,info=BertForSequenceClassification.from_pretrained(str(directory),num_labels=2,
        id2label={0:"not_same",1:"same"},label2id={"not_same":0,"same":1},local_files_only=True,
        trust_remote_code=False,weights_only=True,attn_implementation="eager",output_loading_info=True)
    require(set(info["missing_keys"])=={"classifier.weight","classifier.bias"} and not info.get("mismatched_keys")
            and not info.get("error_msgs"),"unexpected binary backbone initialization")
    for name,parameter in model.named_parameters():
        parameter.requires_grad_(trial=="C3" or name.startswith("classifier.") or
            (trial=="C2" and name.startswith(("bert.encoder.layer.10.","bert.encoder.layer.11."))))
    return model


def trainable_state(model):
    return {name:parameter.detach().cpu() for name,parameter in model.named_parameters() if parameter.requires_grad}


def restore_trainable(model,state):
    require(set(state)=={n for n,p in model.named_parameters() if p.requires_grad},"trainable state coverage mismatch")
    own=dict(model.named_parameters())
    import torch
    with torch.no_grad():
        for name,value in state.items():
            require(own[name].shape==value.shape,"trainable shape mismatch")
            own[name].copy_(value.to(own[name].device))


def schedule(step,total):
    warm=max(1,int(total*.1))
    return (step+1)/warm if step<warm else max(0,(total-step)/(total-warm))


def token_cache(split):
    require(split in ("train","development"),"heldout token access rejected")
    from safetensors.torch import load_file
    receipt=read(NEURAL/"tokens"/f"{split}.json")
    path=WORKSPACE/"stage5"/NEURAL.name/receipt["file"]
    require(sha(path)==receipt["SHA256"],"prior token cache changed")
    return load_file(str(path)),{r["id"]:i for i,r in enumerate(receipt["rows"])}


def checkpoint(run,external,key,model,optimizer,state,fingerprint):
    rows=[r for r in recovery_receipts(run) if r["task"]==key]
    if rows and rows[-1]["epoch"]==state["epoch"] and rows[-1]["offset"]==state["offset"]:
        require(sha(external/rows[-1]["file"])==rows[-1]["SHA256"],"current recovery changed")
        return rows[-1]
    estimate=sum(p.numel()*p.element_size()*3 for p in model.parameters() if p.requires_grad)+8*1024**2
    if not capacity(estimate):
        request_pause(run,"storage_before_checkpoint_latest_prior_state_retained")
        boundary(run,f"{key}:insufficient-save-space:latest-saved-step-{rows[-1]['step'] if rows else 'none'}")
    import torch
    torch.mps.synchronize()
    stamp=time.time_ns();path=external/"recovery"/f"{stamp}.pt.gz"
    save_state(path,{"task":key,"fingerprint":fingerprint,"model":trainable_state(model),
        "optimizer":cpu_tree(optimizer.state_dict()),"rng":rng_state(),"state":state})
    record={"stamp":stamp,"task":key,"step":state["step"],"epoch":state["epoch"],"offset":state["offset"],
            "file":str(path.relative_to(external)),"SHA256":sha(path),"bytes":path.stat().st_size,"at":now()}
    save(run/"recovery"/f"{stamp}.json",record);rotate(run,external)
    print(json.dumps({"phase":"checkpoint","task":key,"step":state["step"],"bytes":record["bytes"]}),flush=True)
    return record


def fit(run,external,trial,fit_ids,seed,data,embeddings=None,pause_after_steps=None):
    import torch
    from sklearn.preprocessing import StandardScaler
    torch.set_num_threads(4);require(torch.backends.mps.is_available(),"MPS unavailable")
    key=task_id(trial,fit_ids,seed);folder=run/"fits"/key
    final=folder/"complete.json"
    if final.exists():
        record=read(final);require(sha(external/record["file"])==record["SHA256"],"fit export changed");return record
    boundary(run,"fit-start:"+key,planned=64*1024**2)
    known=[r for r in partition(data["rows"],fit_ids) if r["relation"]!="uncertain"]
    require({r["relation"]=="same" for r in known}=={False,True},"binary fit needs both classes")
    scaler=None;features=None;tokens=None
    if trial.startswith("B"):
        values=matrix(known,"vectors",embeddings)
        transform=StandardScaler().fit(values)
        scaler={"mean":transform.mean_.tolist(),"scale":transform.scale_.tolist()}
        features=torch.tensor(transform.transform(values),dtype=torch.float32)
        examples=[(i,int(r["relation"]=="same")) for i,r in enumerate(known)]
        epochs,batch=20,64
    else:
        tokens,index=token_cache("train")
        examples=[(index[r["id"]]*2+d,int(r["relation"]=="same")) for r in known for d in (0,1)]
        epochs,batch=3,16
    definition={"task":key,"trial":trial,"fitLibraries":fit_ids,"seed":seed,"fitPairIDs":[r["id"] for r in known],
                "scaler":scaler,"epochs":epochs,"batch":batch,"directions":len(examples),"classOrder":["not_same","same"],
                "manifestSHA256":sha(run/"manifest.json")}
    spec=folder/"spec.json"
    if spec.exists():require(read(spec)==definition,"fit definition changed")
    else:save(spec,definition)
    fingerprint=sha(spec)
    model=make_model(trial,seed,features.shape[1] if features is not None else None).to("mps")
    if trial.startswith("C"):
        backbone=[p for n,p in model.named_parameters() if p.requires_grad and not n.startswith("classifier.")]
        head=[p for n,p in model.named_parameters() if n.startswith("classifier.")]
        groups=[{"params":head,"lr":.001,"base_lr":.001}]
        if backbone:groups.append({"params":backbone,"lr":1e-5 if trial=="C2" else 5e-6,"base_lr":1e-5 if trial=="C2" else 5e-6})
    else:groups=[{"params":list(model.parameters()),"lr":.001,"base_lr":.001}]
    optimizer=torch.optim.AdamW(groups,weight_decay=.01)
    prior=[r for r in recovery_receipts(run) if r["task"]==key]
    if prior:
        saved=load_state(external/prior[-1]["file"],prior[-1]["SHA256"])
        require(saved["fingerprint"]==fingerprint,"recovery definition mismatch")
        restore_trainable(model,saved["model"]);optimizer.load_state_dict(saved["optimizer"]);restore_rng(saved["rng"])
        state=saved["state"]
        save(folder/"resumptions"/f"{time.time_ns()}.json",{"at":now(),"step":state["step"],"recoverySHA256":prior[-1]["SHA256"],"restoredOptimizerAndRNG":True})
        del saved;gc.collect()
    else:
        state={"epoch":0,"offset":0,"step":0,"lossSum":0.,"batches":0,"seconds":0.}
        checkpoint(run,external,key,model,optimizer,state,fingerprint)
    invocation=state["step"];total=epochs*math.ceil(len(examples)/batch)
    estimate=sum(p.numel()*p.element_size()*3 for p in model.parameters() if p.requires_grad)+16*1024**2
    while state["epoch"]<epochs:
        order=order_for(seed,state["epoch"],len(examples))
        model.train()
        if trial=="C1":model.bert.eval()
        while state["offset"]<len(order):
            if wants_pause(run) or not capacity(estimate):
                checkpoint(run,external,key,model,optimizer,state,fingerprint)
                if not wants_pause(run):request_pause(run,"storage_after_checkpoint")
                boundary(run,"saved-training:"+key)
            start=time.monotonic();chosen=[examples[i] for i in order[state["offset"]:state["offset"]+batch]]
            optimizer.zero_grad(set_to_none=True)
            for group in optimizer.param_groups:group["lr"]=group["base_lr"]*(schedule(state["step"],total) if trial.startswith("C") else 1)
            loss_sum=0.
            micro=8 if trial.startswith("C") else batch
            longest=None
            if tokens is not None:
                length=int(tokens["attention_mask"][[i for i,_ in chosen]].sum(-1).max())
                longest=min(512,((length+31)//32)*32)
            for offset in range(0,len(chosen),micro):
                chunk=chosen[offset:offset+micro];indices=[i for i,_ in chunk]
                logits=model(**batch_inputs(tokens,indices,"mps",longest)).logits if tokens is not None else model(features[indices].to("mps"))
                targets=torch.tensor([v for _,v in chunk],device="mps")
                loss=torch.nn.functional.cross_entropy(logits,targets,reduction="sum")/len(chosen)
                require(bool(torch.isfinite(loss)),"nonfinite training loss")
                loss.backward();loss_sum+=loss.item()
                del logits,targets,loss
            norm=torch.stack([p.grad.norm() for p in model.parameters() if p.grad is not None]).norm()
            require(bool(torch.isfinite(norm)),"nonfinite training gradient")
            optimizer.step();torch.mps.synchronize()
            state["offset"]+=len(chosen);state["step"]+=1;state["batches"]+=1
            state["lossSum"]+=loss_sum;state["seconds"]+=time.monotonic()-start
            if pause_after_steps is not None and state["step"]-invocation>=pause_after_steps:request_pause(run,"live_stage2_recovery_exercise")
            if state["step"]%50==0 or wants_pause(run):
                checkpoint(run,external,key,model,optimizer,state,fingerprint);boundary(run,"checkpoint:"+key)
            if state["step"]%25==0:print(json.dumps({"phase":"training","task":key,"epoch":state["epoch"]+1,"step":state["step"],"totalSteps":total,"meanLoss":state["lossSum"]/state["batches"]}),flush=True)
        epoch_record={"epoch":state["epoch"]+1,"step":state["step"],"meanLoss":state["lossSum"]/state["batches"],"trainingSeconds":state["seconds"]}
        # Preserve replay evidence after an unexpected interruption, never overwrite.
        save(folder/"epochs"/f"epoch-{state['epoch']+1}-{time.time_ns()}.json",epoch_record)
        state["epoch"]+=1;state["offset"]=0;state["lossSum"]=0.;state["batches"]=0
        checkpoint(run,external,key,model,optimizer,state,fingerprint)
    path=external/"models"/f"{key}.pt.gz"
    boundary(run,"before-final-export:"+key,planned=sum(p.numel()*p.element_size() for p in model.parameters() if p.requires_grad)+8*1024**2)
    weights=trainable_state(model)
    if not path.exists():save_state(path,{"fingerprint":fingerprint,"model":weights})
    else:
        prior_export=load_state(path,sha(path));require(prior_export["fingerprint"]==fingerprint,"orphan export binding mismatch")
        require(all(torch.equal(weights[n],prior_export["model"][n]) for n in weights),"orphan weights differ")
    record={"task":key,"trial":trial,"seed":seed,"fitLibraries":fit_ids,"fingerprint":fingerprint,
            "file":str(path.relative_to(external)),"SHA256":sha(path),"bytes":path.stat().st_size,
            "trainableParameters":sum(p.numel() for p in model.parameters() if p.requires_grad),
            "steps":state["step"],"trainingSeconds":state["seconds"],"lossless":True}
    save(final,record)
    del model,optimizer,features,tokens;gc.collect();torch.mps.empty_cache()
    print(json.dumps({"phase":"fit-complete",**record}),flush=True)
    return record


def predict(run,external,record,rows,embeddings=None):
    import torch
    key=record["task"];folder=run/"predictions"/key
    missing=[r for r in rows if not (folder/f"{r['id']}.json").exists()]
    if missing:
        boundary(run,"predict:"+key)
        spec=read(run/"fits"/key/"spec.json")
        require(sha(run/"fits"/key/"spec.json")==record["fingerprint"],"fit spec changed")
        saved=load_state(external/record["file"],record["SHA256"])
        require(saved["fingerprint"]==record["fingerprint"],"export fingerprint mismatch")
        trial=record["trial"];scaler=spec["scaler"]
        model=make_model(trial,record["seed"],len(scaler["mean"]) if scaler else None).to("mps")
        restore_trainable(model,saved["model"]);model.eval();del saved
        caches={}
        if trial.startswith("C"):
            for split in sorted({"development" if int(r["library"][2:])>18 else "train" for r in missing}):
                if split=="development":require((run/"selection.json").exists(),"development prediction before selection")
                caches[split]=token_cache(split)
        for start in range(0,len(missing),8):
            boundary(run,f"predict:{key}:{start}")
            batch=missing[start:start+8]
            with torch.inference_mode():
                if scaler:
                    x=(matrix(batch,"vectors",embeddings)-np.array(scaler["mean"]))/np.array(scaler["scale"])
                    values=model(torch.tensor(x,dtype=torch.float32,device="mps")).softmax(-1)[:,1].cpu().tolist()
                    directions=[[v] for v in values]
                else:
                    directions=[]
                    # Partition to avoid mixing train/development token cache indices.
                    for split in ("train","development"):
                        part=[r for r in batch if (int(r["library"][2:])>18)==(split=="development")]
                        if not part:continue
                        tokens,index=caches[split]
                        indices=[index[r["id"]]*2+d for r in part for d in (0,1)]
                        values=model(**batch_inputs(tokens,indices,"mps")).logits.softmax(-1)[:,1].cpu().tolist()
                        directions.extend(zip([r["id"] for r in part],[values[i:i+2] for i in range(0,len(values),2)]))
                    by_id=dict(directions);directions=[by_id[r["id"]] for r in batch]
            for row,values in zip(batch,directions):
                require(all(math.isfinite(v) and 0<=v<=1 for v in values),"invalid inference probability")
                save(folder/f"{row['id']}.json",{k:row[k] for k in ("id","library","first","second")}|
                     {"score":sum(values)/len(values),"directionScores":values,"weightsSHA256":record["SHA256"]})
        del model,caches;gc.collect();torch.mps.empty_cache()
    output=[]
    for row in rows:
        value=read(folder/f"{row['id']}.json")
        require(value["weightsSHA256"]==record["SHA256"],"prediction weights changed")
        output.append(value|{"relation":row["relation"]})
    return output
