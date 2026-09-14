"""Original MiniLM outputs for conversion parity, never semantic quality scores."""
import json
import os
from pathlib import Path
import time

import numpy as np

from experiment import DATA, read, save, sha, require
from environment import verify_assets, publish_bytes


def fixtures(inputs):
    cases = []
    for document in inputs:
        for library in document["libraries"]:
            items = library["items"]
            for offset in range(0, 8, 2):
                first, second = items[offset:offset + 2]
                cases.append({"id": f"{first['id']}--{second['id']}", "first": first["text"], "second": second["text"],
                              "sourceIDs": [first["id"], second["id"]], "kind": "fictional-source-pair"})
    edges = [("empty", "", ""), ("empty-left", "", "A fictional workshop note."),
             ("empty-right", "A fictional workshop note.", ""),
             ("unicode", "Café façade — naïve notes 👩🏽‍🔬", "Cafe\u0301 and façade: résumé; 中文; العربية"),
             ("numbers-punctuation", "Ticket 07: 1.25 mm; version 2 != version 3?", "Ticket 70 — 12.5 mm. [SEP] [CLS]"),
             ("boundary-256", "alpha " * 252, "beta"),
             ("boundary-512", "alpha " * 508, "beta"),
             ("overflow-both", "alpha " * 700, "beta " * 700)]
    cases += [{"id": "edge-" + name, "first": a, "second": b, "sourceIDs": [], "kind": "tokenizer-edge"} for name, a, b in edges]
    return {"schemaVersion": 1, "selection": "first four disjoint source pairs per train/development library; no labels consulted",
            "fixtures": cases}


def run_reference(run, workspace, boundary):
    if (run / "reference-summary.json").exists():
        return
    boundary(run, "reference-model-load")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch
    from transformers import AutoTokenizer, BertForSequenceClassification
    from safetensors.torch import save_file, load_file

    manifest = read(DATA / "model-manifest.json")
    verify_assets(workspace, manifest)
    model_directory = workspace / manifest["workspaceRelativeDirectory"]
    tokenizer = AutoTokenizer.from_pretrained(str(model_directory), local_files_only=True, trust_remote_code=False, use_fast=True)
    torch.manual_seed(17)
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    start = time.monotonic()
    model, loading = BertForSequenceClassification.from_pretrained(
        str(model_directory), num_labels=3, id2label={0: "same", 1: "related", 2: "unrelated"},
        label2id={"same": 0, "related": 1, "unrelated": 2},
        local_files_only=True, trust_remote_code=False, weights_only=True,
        attn_implementation="eager", output_loading_info=True)
    require(set(loading["missing_keys"]) == {"classifier.weight", "classifier.bias"},
            f"unexpected uninitialized weights: {loading['missing_keys']}")
    require(not loading.get("mismatched_keys") and not loading.get("error_msgs"), "backbone load was incomplete")
    model.eval()
    load_seconds = time.monotonic() - start
    external = workspace / "stage2" / run.name / "reference"
    external.mkdir(parents=True, exist_ok=True)
    weights = external / "model.safetensors"
    if weights.exists():
        previous = load_file(str(weights))
        require(set(previous) == set(model.state_dict()) and all(torch.equal(previous[k], v) for k, v in model.state_dict().items()),
                "seeded reference weights changed on resume")
    else:
        # Publish only a complete safe tensor file. Partial files remain clearly
        # marked and are never used as a checkpoint after interruption.
        pending = external / f"pending-{time.time_ns()}.safetensors"
        save_file({k: v.contiguous() for k, v in model.state_dict().items()}, str(pending))
        with pending.open("rb") as stream:
            os.fsync(stream.fileno())
        os.link(pending, weights)
        pending.unlink()
    publish_bytes(external / "config.json", model.config.to_json_string().encode())
    tokenizer_json = tokenizer.backend_tokenizer.to_str()
    publish_bytes(external / "tokenizer.json", tokenizer_json.encode())
    fixture_path = run / "reference/fixtures.json"
    if not fixture_path.exists():
        documents = [read(DATA / "releases/v1" / f"inputs-{split}.json") for split in ("train", "development")]
        save(fixture_path, fixtures(documents))
    cases = read(fixture_path)["fixtures"]
    weights_sha = sha(weights)
    completed = 0
    for case in cases:
        for length in (256, 512):
            for orientation in ("forward", "reverse"):
                boundary(run, f"reference:{case['id']}:{length}:{orientation}")
                path = run / "reference/cases" / f"{case['id']}-{length}-{orientation}.json"
                first, second = case["first"], case["second"]
                if orientation == "reverse":
                    first, second = second, first
                if path.exists():
                    previous = read(path)
                    require(previous["weightsSHA256"] == weights_sha and previous["fixturesSHA256"] == sha(fixture_path),
                            "reference case checkpoint changed")
                    completed += 1
                    continue
                tokens = tokenizer(first, second, padding="max_length", max_length=length, truncation="longest_first", return_tensors="pt")
                untruncated = len(tokenizer(first, second, truncation=False)["input_ids"])
                require(set(tokens) == {"input_ids", "attention_mask", "token_type_ids"}, "unexpected model input names")
                require(all(tuple(t.shape) == (1, length) for t in tokens.values()), "invalid token shape")
                started = time.monotonic()
                with torch.inference_mode():
                    logits = model(**tokens).logits
                    probabilities = logits.softmax(-1)
                require(torch.isfinite(logits).all().item() and torch.isfinite(probabilities).all().item(), "nonfinite reference output")
                save(path, {"id": case["id"], "length": length, "orientation": orientation,
                     "weightsSHA256": weights_sha, "fixturesSHA256": sha(fixture_path),
                     "inputs": {k: t.tolist() for k, t in tokens.items()}, "untruncatedPairTokens": untruncated,
                     "truncated": untruncated > length, "logits": logits.tolist(), "probabilities": probabilities.tolist(),
                     "classOrder": ["same", "related", "unrelated"], "cpuInferenceSeconds": time.monotonic() - started,
                     "untrainedHead": True, "notASemanticPrediction": True})
                completed += 1
        if completed % 40 == 0:
            print(json.dumps({"phase": "reference", "completed": completed, "total": len(cases) * 4}), flush=True)
    # Reload the persisted safe weights and check an independent forward pass.
    replica = BertForSequenceClassification(model.config)
    replica.load_state_dict(load_file(str(weights)), strict=True)
    replica.eval()
    first_path = run / "reference/cases" / f"{cases[0]['id']}-256-forward.json"
    record = read(first_path)
    with torch.inference_mode():
        repeated = replica(**{k: torch.tensor(v) for k, v in record["inputs"].items()}).logits.numpy()
    difference = float(np.max(np.abs(repeated - record["logits"])))
    require(difference <= 1e-7, "persisted reference reload parity failed")
    all_results = [read(p) for p in sorted((run / "reference/cases").glob("*.json"))]
    require(len(all_results) == len(cases) * 4, "reference case coverage mismatch")
    save(run / "reference-summary.json", {"status": "original_reference_complete", "fixturePairs": len(cases),
         "expectedCases": len(cases) * 4, "completedCases": len(all_results), "lengths": [256, 512],
         "orientations": ["forward", "reverse"], "truncatedCases": sum(r["truncated"] for r in all_results),
         "referenceHeadSeed": 17, "classOrder": ["same", "related", "unrelated"], "untrainedHead": True,
         "device": "cpu", "threads": 4, "attentionImplementation": "eager", "modelLoadSeconds": load_seconds,
         "reloadMaxLogitDifference": difference, "safeWeightsBytes": weights.stat().st_size,
         "weightsSHA256": weights_sha, "tokenizerSHA256": sha(external / "tokenizer.json"),
         "loadingInfo": loading, "neuralTrainingPerformed": False, "coreMLConversionPerformed": False,
         "limitation": "Random classification head is a numerical reference, not a trained semantic matcher or phone performance result."})
