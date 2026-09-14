"""Reproduce input handling and measure in-sample versus development behavior."""
import gc
import json
import numpy as np

from screening_common import *
from screening_ablation import diagnostic_curve
from stage2_metrics import metrics
from stage5_data import pair_inputs, batch_inputs, training_examples

DIAGNOSTIC_THRESHOLD = .9831428229808807


def run_diagnostics(run, external):
    path = run/"diagnostics/summary.json"
    if path.exists(): return read(path)
    boundary(run,external,"diagnostics-start")
    import torch
    from transformers import AutoTokenizer, BertForSequenceClassification
    from safetensors.torch import load_file
    torch.set_num_threads(4)
    old_external = WORKSPACE/"stage5"/NEURAL.name
    candidate = read(NEURAL/"epochs/seed-17-epoch-3.json")
    weights = old_external/candidate["weights"]
    require(sha(weights)==candidate["weightsSHA256"],"old diagnostic weights changed")
    model_dir = WORKSPACE/read(DATA/"model-manifest.json")["workspaceRelativeDirectory"]
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir),local_files_only=True,trust_remote_code=False)
    model = BertForSequenceClassification.from_pretrained(str(weights.parent),local_files_only=True,
        trust_remote_code=False,weights_only=True,attn_implementation="eager").to("mps").eval()
    require(model.config.id2label == {0:"same",1:"related",2:"unrelated"},"class mapping changed")
    checks = {}
    for split in ("train","development"):
        boundary(run,external,"diagnostics-cache:"+split)
        cache = read(NEURAL/"tokens"/f"{split}.json")
        require(sha(old_external/cache["file"])==cache["SHA256"],"old token cache changed")
        require(cache["sourceSHA256"]==sha(RELEASE/f"inputs-{split}.json"),"token input hash mismatch")
        tokens = load_file(str(old_external/cache["file"]))
        inputs,_ = load_split(split)
        pairs = pair_inputs(inputs)
        require([p["id"] for p in pairs]==[r["id"] for r in cache["rows"]],"token pair order mismatch")
        # Re-tokenize two pairs per library, both directions, without labels as input.
        indices = [i for i in range(len(pairs)) if i%190 in (0,189)]
        for i in indices:
            for direction in (0,1):
                texts = pairs[i]["texts"][::1 if direction==0 else -1]
                encoded = tokenizer(*texts,padding="max_length",max_length=512,truncation="longest_first")
                require(all(encoded[k]==tokens[k][i*2+direction].tolist() for k in encoded),"fresh token mismatch")
        if split=="train":
            labels = {r["id"]:r["relation"] for r in gold(split)}
            expected = [(i*2+d,["same","related","unrelated"].index(labels[p["id"]]))
                        for i,p in enumerate(pairs) if labels[p["id"]]!="uncertain" for d in (0,1)]
            require(training_examples(NEURAL,cache)==expected,"training label/direction indexing mismatch")
        checks[split] = {"freshTokenDirections":len(indices)*2,"tokenCacheSHA256":cache["SHA256"],
                         "totalPairs":len(pairs),"truncatedDirections":cache["truncatedDirections"]}
        scoring_indices = range(len(pairs)) if split=="train" else indices
        for i in scoring_indices:
            boundary(run,external,f"diagnostic:{split}:{i}")
            output = run/"diagnostics"/split/f"{pairs[i]['id']}.json"
            if output.exists():
                require(read(output)["weightsSHA256"]==candidate["weightsSHA256"],"diagnostic binding mismatch")
                continue
            with torch.inference_mode():
                probabilities = model(**batch_inputs(tokens,[i*2,i*2+1],"mps")).logits.softmax(-1).cpu().numpy()
                padding_delta = None
                if i in indices:
                    padded = model(**batch_inputs(tokens,[i*2,i*2+1],"mps",512)).logits.softmax(-1).cpu().numpy()
                    padding_delta = float(np.max(np.abs(probabilities-padded)))
                    require(padding_delta<.002,"dynamic-padding parity failed")
            require(np.isfinite(probabilities).all(),"nonfinite diagnostic output")
            save(output,{k:v for k,v in pairs[i].items() if k!="texts"} | {
                "weightsSHA256":candidate["weightsSHA256"],"probabilities":probabilities.mean(axis=0,dtype=np.float64).tolist(),
                "directionProbabilities":probabilities.tolist(),"paddingMaxAbsoluteDelta":padding_delta})
            if (i+1)%200==0: print(json.dumps({"phase":"training-diagnostic","pairs":i+1,"total":len(pairs)}),flush=True)
    development = read(NEURAL/"evaluations/seed-17-epoch-3/development/summary.json")["rows"]
    lookup = {r["id"]:r for r in development}
    deltas = [max(abs(a-b) for a,b in zip(read(p)["probabilities"],lookup[p.stem]["probabilities"]))
              for p in (run/"diagnostics/development").glob("*.json")]
    require(len(deltas)==12 and max(deltas)<.002,"old-development reproduction failed")
    training = [read(run/"diagnostics/train"/f"{r['id']}.json") | {"relation":r["relation"]} for r in gold("train")]
    baseline = read(BASELINE/"baseline/C-10.json")
    threshold = read(BASELINE/"baseline-selected.json")["threshold"]
    def summary(rows,t):
        return {"fixedThreshold":t,"fixedThresholdMetrics":metrics(rows,t),"argmaxMetrics":metrics(rows,0),
                "ranking":diagnostic_curve(rows)}
    result = {"inputChecks":checks,"developmentReproductionMaxDelta":max(deltas),
              "weightsSHA256":candidate["weightsSHA256"],"trainingExamples":5654,
              "neural":{split:summary(rows,DIAGNOSTIC_THRESHOLD) for split,rows in (("train",training),("development",development))},
              "baseline":{split:summary(baseline["predictions"][split],threshold) for split in ("train","development")},
              "policy":"Fixed post-hoc diagnostic candidate/threshold, not a qualifying model. Training is in-sample; development was already inspected. No selection or test access.",
              "testAccess":False}
    save(path,result)
    del model;gc.collect();torch.mps.empty_cache()
    return result
