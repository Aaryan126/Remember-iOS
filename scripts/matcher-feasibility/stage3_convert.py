#!/usr/bin/env python3
"""Convert the frozen untrained reference, with no dataset tuning or training."""
import argparse
import json
import os
from pathlib import Path
import time

from stage3_common import *


def convert(run, workspace):
    receipt = run / "conversion.json"
    if receipt.exists():
        result = read(receipt)
        verify_files(workspace / result["package"], result["packageFiles"])
        return
    source_hashes = snapshot(run, "conversion", ["stage3_common.py", "stage3_convert.py"])
    boundary(run, "before-reference-load")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import numpy as np
    import torch
    import coremltools as ct
    from transformers import BertForSequenceClassification, BertModel
    torch.set_num_threads(4)
    torch.manual_seed(17)
    reference = workspace / "stage2/stage-2-attempt-01/reference"
    model = BertForSequenceClassification.from_pretrained(str(reference), local_files_only=True,
                trust_remote_code=False, weights_only=True, attn_implementation="eager").eval()

    class FiniteMaskBert(BertModel):
        def get_extended_attention_mask(self, attention_mask, input_shape, device=None, dtype=None):
            # FP32's minimum value becomes -inf in FP16; multiplying it by a
            # zero mask produces NaN. -10000 is finite in FP16 and still makes
            # excluded-token softmax weights underflow to zero. Verify every
            # frozen reference output before exporting this representation.
            return (1.0 - attention_mask[:, None, None, :].to(dtype or self.dtype)) * -10000.0

    safe_backbone = FiniteMaskBert(model.config)
    safe_backbone.load_state_dict(model.bert.state_dict(), strict=True)
    model.bert = safe_backbone
    model.eval()
    mask_checks = []
    for original_path in sorted((STAGE2 / "reference/cases").glob("*.json")):
        boundary(run, f"finite-mask-reference:{original_path.stem}")
        original = read(original_path)
        with torch.inference_mode():
            probabilities = model(**{k: torch.tensor(v) for k, v in original["inputs"].items()}).logits.softmax(-1)
        delta = float(np.max(np.abs(probabilities.numpy() - original["probabilities"])))
        require(delta <= 1e-7, f"finite mask changes original outputs: {original_path.stem}")
        mask_checks.append(delta)

    class Wrapper(torch.nn.Module):
        def __init__(self, network):
            super().__init__()
            self.network = network

        def forward(self, input_ids, attention_mask, token_type_ids):
            logits = self.network(input_ids=input_ids.long(), attention_mask=attention_mask.long(),
                                  token_type_ids=token_type_ids.long()).logits
            return logits, logits.softmax(dim=-1)

    wrapper = Wrapper(model).eval()
    example_path = STAGE2 / "reference/cases/mf01-i01--mf01-i02-256-forward.json"
    example = read(example_path)
    names = ["input_ids", "attention_mask", "token_type_ids"]
    tensors = tuple(torch.tensor(example["inputs"][name], dtype=torch.int32) for name in names)
    boundary(run, "before-torch-trace")
    started = time.monotonic()
    with torch.inference_mode():
        traced = torch.jit.trace(wrapper, tensors, strict=True)
    # Tracing at 256 must still preserve dynamic attention/position shapes at 512.
    trace_checks = []
    for length in (256, 512):
        original = read(STAGE2 / f"reference/cases/mf01-i01--mf01-i02-{length}-forward.json")
        with torch.inference_mode():
            logits, probabilities = traced(*(torch.tensor(original["inputs"][n], dtype=torch.int32) for n in names))
        delta = float(np.max(np.abs(probabilities.numpy() - original["probabilities"])))
        require(delta <= 1e-7, f"Torch trace differs at length {length}")
        trace_checks.append({"length": length, "maxProbabilityDifference": delta})
    trace_seconds = time.monotonic() - started
    boundary(run, "before-coreml-conversion")
    attempt = workspace / "stage3" / run.name / f"export-{time.time_ns()}"
    attempt.mkdir(parents=True)
    print(json.dumps({"phase": "conversion", "precision": "FP16", "lengths": [256, 512]}), flush=True)
    started = time.monotonic()
    converted = ct.convert(traced, convert_to="mlprogram", minimum_deployment_target=ct.target.iOS18,
        inputs=[ct.TensorType(name=name, shape=ct.EnumeratedShapes(shapes=[(1, 256), (1, 512)], default=(1, 256)), dtype=np.int32) for name in names],
        outputs=[ct.TensorType(name="logits", dtype=np.float32), ct.TensorType(name="probabilities", dtype=np.float32)],
        compute_precision=ct.precision.FLOAT16, compute_units=ct.ComputeUnit.CPU_ONLY, skip_model_load=True)
    converted.short_description = "Remember isolated MiniLM feasibility reference; classification head is untrained."
    converted.user_defined_metadata["class_order"] = json.dumps(["same", "related", "unrelated"])
    converted.user_defined_metadata["reference_weights_sha256"] = sha(reference / "model.safetensors")
    package = attempt / "MatcherReference.mlpackage"
    converted.save(str(package))
    result = {"schemaVersion": 1, "createdAt": now(), "status": "converted_not_yet_verified",
              "package": str(package.relative_to(workspace)), "packageFiles": files_in(package),
              "packageBytes": sum(p.stat().st_size for p in package.rglob("*") if p.is_file()),
              "traceSeconds": trace_seconds, "conversionSeconds": time.monotonic() - started,
              "traceChecks": trace_checks, "sourceSHA256": source_hashes, "precision": "float16",
              "finiteMaskReferenceCases": len(mask_checks), "finiteMaskMaxProbabilityDifference": max(mask_checks),
              "attentionMaskSentinel": -10000.0,
              "referenceWeightsSHA256": sha(reference / "model.safetensors"), "untrainedHead": True,
              "inputNames": names, "outputNames": ["logits", "probabilities"], "inputDtype": "int32",
              "enumeratedShapes": [[1, 256], [1, 512]], "classOrder": ["same", "related", "unrelated"]}
    save(receipt, result)
    print(json.dumps({"phase": "converted", "packageBytes": result["packageBytes"], "conversionSeconds": result["conversionSeconds"]}), flush=True)
    boundary(run, "conversion-saved")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--workspace", default=WORKSPACE)
    args = parser.parse_args()
    run, workspace = paths(args.run, args.workspace)
    setup_signals()
    try:
        initialize(run, workspace)
        convert(run, workspace)
    except Paused as error:
        print(json.dumps({"status": "paused", "safeBoundary": str(error)}), flush=True)
    except Exception as error:
        failure(run, error)
        raise


if __name__ == "__main__":
    main()
