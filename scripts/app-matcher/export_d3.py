#!/usr/bin/env python3
"""Export frozen P2 seed 29 for the app. No fitting, downloads or historical writes."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/organization-diagnostics"))
import c2_common as c

OUT = ROOT / "Evaluation/AppMatcher"
RESOURCES = ROOT / "Remember/Remember/MatcherAssets"


def main():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    c.space(planned=512 * 1024**2)
    record = c.read(c.P2 / "hybrid-29.json")
    weights = c.EXTERNAL / record["final"]["file"]
    c.require(c.digest(weights) == record["final"]["SHA256"], "Frozen trained weights changed")
    asset_manifest = c.read(ROOT / "Evaluation/MatcherFeasibility/model-manifest.json")
    assets = c.WORKSPACE / asset_manifest["workspaceRelativeDirectory"]
    config = c.read(c.P2 / "tfidf.json")
    parameters = {"version": "d3-p2-seed29-corroborated-v1", "threshold": 0.9804276486193665,
                  "weightsSHA256": record["final"]["SHA256"], "combiner": record["model"], "tfidf": config}
    c.publish(RESOURCES / "D3Parameters.json", parameters)
    vocabulary = RESOURCES / "D3Vocabulary.txt"
    if vocabulary.exists():
        c.require(c.digest(vocabulary) == c.digest(assets / "vocab.txt"), "Vocabulary changed")
    else:
        shutil.copyfile(assets / "vocab.txt", vocabulary)
    c.publish(OUT / "inputs.json", {"sources": {str(p.relative_to(ROOT)): c.digest(p) for p in
              (c.P2 / "hybrid-29.json", c.P2 / "tfidf.json", ROOT / "scripts/app-matcher/export_d3.py")},
              "weightsSHA256": c.digest(weights), "engineeringCandidate": 29, "productionQualified": False})
    if (OUT / "conversion.json").exists():
        print("Conversion already saved; preserving original export.", flush=True)
        return
    import numpy as np
    import torch
    import coremltools as ct
    from transformers import AutoTokenizer, BertConfig, BertForSequenceClassification, BertModel
    torch.set_num_threads(4)
    model_config = BertConfig.from_pretrained(str(assets), local_files_only=True, num_labels=2)
    model_config._attn_implementation = "eager"
    model = BertForSequenceClassification(model_config).eval()
    with gzip.open(weights, "rb") as stream:
        saved = torch.load(stream, map_location="cpu", weights_only=True)
    c.require(saved["fingerprint"] == record["final"]["fingerprint"], "Wrong checkpoint fingerprint")
    model.load_state_dict(saved["model"], strict=True)
    del saved
    tokenizer = AutoTokenizer.from_pretrained(str(assets), local_files_only=True, trust_remote_code=False)
    from c2_run import parity_inputs
    texts, embeddings, pairs = parity_inputs()
    fixtures = []
    for pair in pairs:
        a, b = texts[pair["first"]], texts[pair["second"]]
        directions = []
        for left, right in ((a, b), (b, a)):
            tokens = tokenizer(left, right, padding="max_length", truncation="longest_first", max_length=512, return_tensors="pt")
            with torch.inference_mode():
                probability = model(**tokens).logits.softmax(-1)[0, 1].item()
            directions.append({"tokens": {k: v.tolist() for k, v in tokens.items()}, "probability": probability})
        fixtures.append({"id": pair["id"], "first": a, "second": b, "directions": directions,
                         "embeddingA": embeddings[pair["first"]], "embeddingB": embeddings[pair["second"]]})

    class FiniteMaskBert(BertModel):
        def get_extended_attention_mask(self, attention_mask, input_shape, device=None, dtype=None):
            return (1.0 - attention_mask[:, None, None, :].to(dtype or self.dtype)) * -10000.0
    backbone = FiniteMaskBert(model.config)
    backbone.load_state_dict(model.bert.state_dict(), strict=True)
    model.bert = backbone
    model.eval()

    class Wrapper(torch.nn.Module):
        def __init__(self, model):
            super().__init__(); self.model = model
        def forward(self, input_ids, attention_mask, token_type_ids):
            return self.model(input_ids=input_ids.long(), attention_mask=attention_mask.long(),
                              token_type_ids=token_type_ids.long()).logits.softmax(-1)
    names = ("input_ids", "attention_mask", "token_type_ids")
    tensors = tuple(torch.tensor(fixtures[0]["directions"][0]["tokens"][key], dtype=torch.int32) for key in names)
    with torch.inference_mode():
        traced = torch.jit.trace(Wrapper(model).eval(), tensors)
    package = RESOURCES / "D3Matcher.mlpackage"
    c.require(not package.exists(), "Unrecorded package exists; preserve and inspect it")
    print("Converting trained seed-29 model to FP16 Core ML", flush=True)
    converted = ct.convert(traced, convert_to="mlprogram", minimum_deployment_target=ct.target.iOS18,
        inputs=[ct.TensorType(name=name, shape=(1, 512), dtype=np.int32) for name in names],
        outputs=[ct.TensorType(name="probabilities", dtype=np.float32)],
        compute_precision=ct.precision.FLOAT16, compute_units=ct.ComputeUnit.CPU_ONLY)
    converted.short_description = "Remember D3 P2 seed-29 binary pair matcher; experimental organization candidate."
    converted.user_defined_metadata["class_order"] = '["not_same", "same"]'
    converted.user_defined_metadata["weights_sha256"] = c.digest(weights)
    converted.save(str(package))
    maximum_delta = 0
    from c2_models import Features
    features = Features(texts, embeddings)
    from screening2_models import portable_scores
    for fixture, pair in zip(fixtures, pairs):
        actual = []
        for direction in fixture["directions"]:
            result = converted.predict({key: np.asarray(direction["tokens"][key], dtype=np.int32) for key in names})
            value = float(result["probabilities"][0, 1])
            maximum_delta = max(maximum_delta, abs(value - direction["probability"]))
            actual.append(value)
        values = features.values(pair["first"], pair["second"])
        def combined(p):
            p = float(np.clip(p, 1e-6, 1-1e-6))
            return float(portable_scores(record["model"], [values + [float(np.log(p/(1-p)))]])[0])
        expected = combined(sum(d["probability"] for d in fixture["directions"]) / 2)
        observed = combined(sum(actual) / 2)
        c.require((expected >= parameters["threshold"]) == (observed >= parameters["threshold"]), "Decision parity failure")
        fixture.update(features=values, expectedScore=expected, coreMLScore=observed)
    c.require(maximum_delta <= 0.002, "Core ML probability drift exceeds conversion tolerance")
    c.publish(OUT / "parity-inputs.json", {"fixtures": fixtures})
    c.publish(OUT / "conversion.json", {"passed": True, "pairs": len(fixtures), "directions": 2*len(fixtures),
        "maximumProbabilityDelta": maximum_delta, "decisionParity": True,
        "packageBytes": sum(p.stat().st_size for p in package.rglob("*") if p.is_file()),
        "files": {str(p.relative_to(RESOURCES)): c.digest(p) for p in RESOURCES.rglob("*") if p.is_file()}})
    print(json.dumps(c.read(OUT / "conversion.json")), flush=True)


if __name__ == "__main__":
    main()
