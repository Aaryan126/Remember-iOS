"""Development selection, frozen-baseline comparison and one-time heldout report."""
import gc
import json
import math
import selectors
import subprocess
import numpy as np

from stage5_common import *
from stage5_data import prepare_tokens, batch_inputs, inputs_for, gold_for
from stage2_metrics import metrics, select_threshold, bootstrap, retrieval_metrics


def evaluate_candidate(run, external, seed, epoch, split="development"):
    if split == "test":
        choice = authorize_test(run)
        require((seed, epoch) == (choice["seed"], choice["epoch"]), "test predictions restricted to frozen winner")
    else: require(split == "development", "unexpected evaluation split")
    output = run / "evaluations" / f"seed-{seed}-epoch-{epoch}" / split
    if (output / "summary.json").exists(): return read(output / "summary.json")
    boundary(run, f"evaluation:{seed}:{epoch}:{split}")
    import torch
    from transformers import BertForSequenceClassification
    from safetensors.torch import load_file
    torch.set_num_threads(4)
    epoch_result = read(run / "epochs" / f"seed-{seed}-epoch-{epoch}.json")
    weights = external / epoch_result["weights"]
    require(sha(weights) == epoch_result["weightsSHA256"], "candidate weights changed")
    cache = prepare_tokens(run, external, split)
    tokens = load_file(str(external / cache["file"]))
    model = BertForSequenceClassification.from_pretrained(str(weights.parent), local_files_only=True,
        trust_remote_code=False, weights_only=True, attn_implementation="eager").to("mps").eval()
    for index, pair in enumerate(cache["rows"]):
        boundary(run, f"evaluation:{seed}:{epoch}:{split}:{pair['id']}")
        file = output / "pairs" / f"{pair['id']}.json"
        if file.exists():
            prior = read(file)
            require(prior["weightsSHA256"] == epoch_result["weightsSHA256"] and prior["id"] == pair["id"], "evaluation record mismatch")
            continue
        with torch.inference_mode():
            values = batch_inputs(tokens, [index*2, index*2+1], "mps")
            logits = model(**values).logits
            probability = logits.softmax(-1).cpu().numpy()
        require(probability.shape == (2,3) and np.isfinite(probability).all(), "invalid evaluation outputs")
        save(file, {k:v for k,v in pair.items() if k != "untruncatedTokens"} | {
            "weightsSHA256": epoch_result["weightsSHA256"], "probabilities": probability.mean(axis=0, dtype=np.float64).tolist(),
            "directionProbabilities": probability.tolist(), "status": "ok", "maxLength": 512})
        if (index+1) % 200 == 0:
            print(json.dumps({"phase": "evaluation", "seed": seed, "epoch": epoch, "split": split,
                              "pairsCompleted": index+1, "total": len(cache["rows"])}), flush=True)
    del model; gc.collect(); torch.mps.empty_cache()
    truth = {r["id"]: r for r in gold_for(split, run)}
    rows = [read(output / "pairs" / f"{row['id']}.json") | {"relation": truth[row["id"]]["relation"]} for row in cache["rows"]]
    if split == "development":
        retrieved = {(r["first"], r["second"]): r["retrieved"] for r in read(STAGE2 / "features.json")["splits"][split]["pairs"]}
        selection = select_threshold(rows)
        threshold = selection["threshold"] if selection else None
    else:
        baseline = baseline_test(run, external)
        retrieved = {(r["first"],r["second"]):r["retrieved"] for r in baseline["rows"]}
        selection = None; threshold = authorize_test(run)["threshold"]
    for row in rows: row["retrieved"] = retrieved[row["first"],row["second"]]
    result = {"seed": seed, "epoch": epoch, "split": split, "weightsSHA256": epoch_result["weightsSHA256"],
        "selection": selection, "threshold": threshold, "rows": rows,
        "allPairs": metrics(rows, threshold), "candidateConditioned": metrics([r for r in rows if r["retrieved"]], threshold),
        "argmaxOperatingPoint": metrics(rows, 0), "maxLength": 512}
    save(output / "summary.json", result)
    print(json.dumps({"phase": "evaluation-complete", "seed": seed, "epoch": epoch, "split": split,
                      "selection": selection, "allPairs": result["allPairs"]}), flush=True)
    return result


def candidate_rank(candidate):
    selected = candidate["selection"]
    return (selected["metrics"]["macroLibraryRecall"], selected["metrics"]["precision"], selected["threshold"],
            -candidate["epoch"], -[17,29,41].index(candidate["seed"]))


def select_candidate(run, external):
    path = run / "selection.json"
    if path.exists():
        result = read(path)
        if result["status"] == "selected": authorize_test(run)
        return result
    boundary(run, "before-development-selection-freeze")
    candidates = [read(run / "evaluations" / f"seed-{seed}-epoch-{epoch}/development/summary.json")
                  for seed in [17,29,41] for epoch in [1,2,3]]
    qualifying = [r for r in candidates if r["selection"] is not None]
    result = {"createdAt": now(), "status": "selected" if qualifying else "no_qualifying_development_candidate",
        "testResultsOpened": False, "baselineSHA256": sha(STAGE2 / "baseline-selected.json"),
        "developmentCandidates": [{"seed": r["seed"], "epoch": r["epoch"], "selection": r["selection"],
                                   "weightsSHA256": r["weightsSHA256"]} for r in candidates]}
    if qualifying:
        winner = max(qualifying, key=candidate_rank)
        epoch = read(run / "epochs" / f"seed-{winner['seed']}-epoch-{winner['epoch']}.json")
        result.update(seed=winner["seed"], epoch=winner["epoch"], threshold=winner["selection"]["threshold"],
                      weights=str(external / epoch["weights"]), weightsSHA256=epoch["weightsSHA256"],
                      developmentMetrics=winner["allPairs"], evaluationLength=512)
    save(path, result)
    return result


def baseline_test(run, external):
    authorize_test(run)
    path = run / "test-baseline.json"
    if path.exists(): return read(path)
    from stage2 import validate_embedding, pair_features, top_candidates, exported_probabilities, content_sha
    from sklearn.feature_extraction.text import TfidfVectorizer
    document = inputs_for("test", run)
    items = [item for lib in document["libraries"] for item in lib["items"]]
    executable = WORKSPACE / "stage2/stage-2-attempt-01/probe/EmbeddingProbe"
    frozen = read(STAGE2 / "complete.json")["workspaceFiles"]
    require(sha(executable) == frozen[str(executable.relative_to(WORKSPACE))], "embedding executable changed")
    process = None; log = None
    try:
        for item in items:
            boundary(run, f"test-embedding:{item['id']}")
            target = run / "test-embeddings" / f"{item['id']}.json"
            if target.exists(): validate_embedding(item, read(target)); continue
            if process is None:
                log_path = run / "logs" / f"embedding-{time.time_ns()}.log"; log_path.parent.mkdir(exist_ok=True)
                log = log_path.open("x")
                process = subprocess.Popen([str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True, bufsize=1)
            process.stdin.write(json.dumps(item)+"\n"); process.stdin.flush()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                require(selector.select(120), "test embedding timeout")
            line = process.stdout.readline(); require(bool(line), "embedding process exited")
            row = json.loads(line) | {"textSHA256": content_sha(item["text"]), "recordedAt": now()}
            validate_embedding(item,row)
            if row["status"] == "ok":
                require(row["space"] in read(STAGE2 / "embedding-summary.json")["spaces"], "Mac embedding model space changed since baseline fit")
            save(target,row)
    finally:
        if process:
            process.stdin.close()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.terminate(); process.wait(timeout=10)
            process.stdout.close(); log.close()
    baseline = read(STAGE2 / "baseline-selected.json")
    tfidf = baseline["tfidf"]
    vectorizer = TfidfVectorizer(vocabulary=tfidf["vocabulary"], lowercase=True, ngram_range=(1,2), dtype=np.float64)
    vectorizer.idf_ = np.asarray(tfidf["idf"])
    require(vectorizer.vocabulary == tfidf["vocabulary"], "TF-IDF vocabulary changed")
    gold = gold_for("test",run)
    by_library = {lib["id"]:[r for r in gold if r["library"] == lib["id"]] for lib in document["libraries"]}
    candidates, rows = {}, []
    for lib in document["libraries"]:
        items = lib["items"]; index = {item["id"]:i for i,item in enumerate(items)}
        embeddings = [read(run / "test-embeddings" / f"{item['id']}.json") for item in items]
        lexical_vectors = vectorizer.transform([item["text"] for item in items]); lexical = (lexical_vectors @ lexical_vectors.T).toarray()
        contextual = [[None]*len(items) for _ in items]
        for pair in by_library[lib["id"]]:
            a,b = index[pair["first"]],index[pair["second"]]
            features = pair_features(items[a],items[b],embeddings[a],embeddings[b],lexical[a,b])
            contextual[a][b] = contextual[b][a] = features[0]
            probability = exported_probabilities(baseline["model"],[features])[0].tolist() if all(v is not None for v in features) else None
            rows.append(pair | {"features":features,"probabilities":probability,"status":"ok" if probability is not None else "missing_embedding"})
        candidates.update(top_candidates([item["id"] for item in items],contextual,lexical))
    for row in rows: row["retrieved"] = row["second"] in candidates[row["first"]] or row["first"] in candidates[row["second"]]
    result = {"baselineSHA256":sha(STAGE2 / "baseline-selected.json"),"threshold":baseline["threshold"],"rows":rows,
        "allPairs":metrics(rows,baseline["threshold"]),"candidateConditioned":metrics([r for r in rows if r["retrieved"]],baseline["threshold"]),
        "retrieval":retrieval_metrics(document["libraries"],by_library,candidates),"candidates":candidates,"fitPerformed":False}
    save(path,result); return result


def quality_gates(neural, baseline, retrieval):
    n,b = neural["allPairs"],baseline["allPairs"]
    def at_least(value, limit):
        # Exact percentage-point boundaries can round down by one binary ULP.
        return value >= limit or math.isclose(value,limit,rel_tol=0,abs_tol=1e-12)
    return {"neuralPrecision": n["precision"] is not None and n["precision"] >= .95,
        "minimumAccepted":n["acceptedKnownPairs"] >=30,
        "macroRecallImprovement": n["macroLibraryRecall"] is not None and b["macroLibraryRecall"] is not None and at_least(n["macroLibraryRecall"]-b["macroLibraryRecall"],.05),
        "precisionDrop":n["precision"] is not None and b["precision"] is not None and at_least(n["precision"]-b["precision"],-.01),
        "retrieval":retrieval["atLeastOneRecallAt10"] is not None and retrieval["atLeastOneRecallAt10"] >= .90,
        "coverage":n["missingPredictionPairs"] == b["missingPredictionPairs"] == 0}


def paired_bootstrap(neural, baseline, count=2000):
    a,b = neural["perLibrary"],baseline["perLibrary"]
    require(set(a)==set(b), "paired bootstrap library coverage mismatch")
    libraries=sorted(a); rng=np.random.default_rng(1729)
    values={"precisionDifference":[],"macroRecallDifference":[]}
    for _ in range(count):
        keys=[libraries[i] for i in rng.integers(0,len(libraries),len(libraries))]
        def summary(rows):
            tp=sum(rows[k]["tp"] for k in keys); fp=sum(rows[k]["fp"] for k in keys)
            recalls=[rows[k]["recall"] for k in keys if rows[k]["recall"] is not None]
            return (tp/(tp+fp) if tp+fp else None, float(np.mean(recalls)) if recalls else None)
        first,second=summary(a),summary(b)
        for i,name in enumerate(values):
            if first[i] is not None and second[i] is not None: values[name].append(first[i]-second[i])
    return {"resamples":count,"seed":1729,"unit":"paired library", "intervals":{
        key:{"lower":float(np.quantile(v,.025)) if v else None,"upper":float(np.quantile(v,.975)) if v else None,
             "definedResamples":len(v)} for key,v in values.items()},
        "limitation":"Six synthetic test libraries; resampling cannot establish production reliability."}


def final_report(run, external):
    path=run / "quality-report.json"
    if path.exists(): return read(path)
    choice=read(run / "selection.json")
    if choice["status"] != "selected":
        result={"status":"no_qualifying_development_candidate","passed":False,"testResultsOpened":False,
                "stage6Recommended":False,"selectionSHA256":sha(run / "selection.json")}
    else:
        neural=evaluate_candidate(run,external,choice["seed"],choice["epoch"],"test")
        baseline=baseline_test(run,external); gates=quality_gates(neural,baseline,baseline["retrieval"])
        result={"status":"heldout_evaluation_complete","passed":all(gates.values()),"gates":gates,
            "testResultsOpened":True,"selectionSHA256":sha(run / "selection.json"),
            "neural":{"allPairs":neural["allPairs"],"candidateConditioned":neural["candidateConditioned"]},
            "baseline":{"allPairs":baseline["allPairs"],"candidateConditioned":baseline["candidateConditioned"]},
            "retrieval":baseline["retrieval"],"pairedBootstrap":paired_bootstrap(neural["allPairs"],baseline["allPairs"]),
            "stage6Recommended":all(gates.values()),
            "limitations":["Agent-reviewed synthetic data, not human validation or production traffic.",
                "All-pair final-library relations, not chronological attachment or automatic merge safety.",
                "Test release consumed; any test-driven tuning requires a new independent test set.",
                "Quality scored at maximum512 tokens; trained256/512 truncation and Core ML/phone quality need Stage6."]}
        for name,source in [("neural",neural),("baseline",baseline)]:
            intervals=bootstrap(source["rows"],source["threshold"])
            intervals["limitation"]="Heldout synthetic libraries after frozen development selection; six-library sampling uncertainty."
            result[name]["bootstrap"]=intervals
        from stage2_metrics import accepted
        inputs={i["id"]:i["text"] for lib in inputs_for("test",run)["libraries"] for i in lib["items"]}
        errors={}
        for label,predicate in {
            "falsePositive":lambda r: r["relation"] not in ["same","uncertain"] and accepted(r,choice["threshold"]),
            "missedSame":lambda r:r["relation"]=="same" and not accepted(r,choice["threshold"]),
            "acceptedAmbiguous":lambda r:r["relation"]=="uncertain" and accepted(r,choice["threshold"])}.items():
            rows=sorted([r for r in neural["rows"] if predicate(r)],key=lambda r:-r["probabilities"][0])
            errors[label]={"count":len(rows),"examples":[r | {"texts":[inputs[r["first"]],inputs[r["second"]]]} for r in rows[:12]]}
        save(run / "error-analysis.json",errors)
    save(path,result); return result
