#!/usr/bin/env python3
"""Swift tokenization and FP16 Core ML parity against frozen Stage 2 cases."""
import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

import numpy as np

from stage3_common import *


def comparison(actual, reference):
    actual, reference = np.asarray(actual, dtype=float), np.asarray(reference, dtype=float)
    require(actual.shape == reference.shape == (1, 3), "unexpected probability shape")
    require(np.isfinite(actual).all() and np.isfinite(reference).all(), "nonfinite probability output")
    require(np.all(actual >= 0) and np.all(actual <= 1) and abs(float(actual.sum()) - 1) < .002, "invalid probability vector")
    return {"maxProbabilityDifference": float(np.max(np.abs(actual - reference))),
            "classAgreement": int(actual.argmax(-1)[0]) == int(reference.argmax(-1)[0])}


def summarize(rows):
    require(bool(rows), "empty parity results")
    delta = max(r["maxProbabilityDifference"] for r in rows)
    agreement = sum(r["classAgreement"] for r in rows) / len(rows)
    return {"cases": len(rows), "maxProbabilityDifference": delta, "classAgreement": agreement,
            "passed": delta <= .01 and agreement >= .99}


def fixture_requests():
    requests = []
    for fixture in read(STAGE2 / "reference/fixtures.json")["fixtures"]:
        for length in (256, 512):
            for orientation in ("forward", "reverse"):
                a, b = fixture["first"], fixture["second"]
                if orientation == "reverse":
                    a, b = b, a
                key = f"{fixture['id']}-{length}-{orientation}"
                requests.append({"id": key, "first": a, "second": b, "length": length})
    return requests


def tokenizer_checks(run, workspace):
    receipt = run / "tokenizer-summary.json"
    if receipt.exists():
        require(read(receipt)["passed"], "saved tokenizer checks failed")
        return
    source_hashes = snapshot(run, "tokenizer", ["MatcherTokenizer.swift", "Stage3TokenizerProbe.swift", "stage3_common.py", "stage3_parity.py"])
    folder = workspace / "stage3" / run.name / "tokenizer"
    folder.mkdir(parents=True, exist_ok=True)
    executable = folder / "TokenizerProbe"
    if not executable.exists():
        boundary(run, "before-tokenizer-build")
        built = subprocess.run(["xcrun", "swiftc", "-parse-as-library", "-O", str(HERE / "MatcherTokenizer.swift"),
                                str(HERE / "Stage3TokenizerProbe.swift"), "-o", str(executable)], capture_output=True, text=True, timeout=180)
        save(run / "build-logs" / f"tokenizer-{time.time_ns()}.json", {"returncode": built.returncode, "stdout": built.stdout, "stderr": built.stderr})
        require(built.returncode == 0, "Swift tokenizer compilation failed; see build-logs")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    from transformers import AutoTokenizer
    original = workspace / read(DATA / "model-manifest.json")["workspaceRelativeDirectory"]
    tokenizer = AutoTokenizer.from_pretrained(str(original), local_files_only=True, trust_remote_code=False, use_fast=True)
    requests = fixture_requests()
    # Extra token-only edge cases expose fast-tokenizer tie/Unicode behavior;
    # they are not model-quality examples or new heldout labels.
    extras = [("Σ ΟΣ ΑΣ", "İ I ı ß"), ("a\x00b\uFFFDc\uE000d", "x\t\ny\u200dz"),
              ("x[CLS]y[sep][MASK]", "[UNK][PAD][SEP]"), ("alpha " * 800, "beta " * 700),
              ("alpha " * 700, "beta " * 800), ("x" * 101, "x" * 100)]
    requests += [{"id": f"extra-{index}-{length}", "first": a, "second": b, "length": length}
                 for index, (a, b) in enumerate(extras) for length in (256, 512)]
    worker = subprocess.Popen([str(executable), str(original / "vocab.txt")], stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    try:
        for request in requests:
            boundary(run, f"tokenizer:{request['id']}")
            path = run / "tokenizer-cases" / f"{request['id']}.json"
            if path.exists():
                require(read(path)["passed"], "saved tokenizer mismatch")
                continue
            worker.stdin.write(json.dumps(request) + "\n"); worker.stdin.flush()
            with selectors.DefaultSelector() as selector:
                selector.register(worker.stdout, selectors.EVENT_READ)
                require(bool(selector.select(timeout=30)), "tokenizer response timed out")
                line = worker.stdout.readline()
            require(bool(line), "Swift tokenizer exited without a response")
            actual = json.loads(line)
            expected = dict(tokenizer(request["first"], request["second"], max_length=request["length"],
                                      padding="max_length", truncation="longest_first", return_tensors="np"))
            expected = {k: v.tolist() for k, v in expected.items()}
            require(actual["id"] == request["id"], "token response ID mismatch")
            passed = actual["inputs"] == expected
            frozen_path = STAGE2 / "reference/cases" / f"{request['id']}.json"
            if frozen_path.exists():
                require(expected == read(frozen_path)["inputs"], "Python tokenization changed from Stage 2")
            save(path, {"id": request["id"], "passed": passed, "inputs": actual["inputs"],
                        "expected": expected if not passed else None})
            require(passed, f"Swift token mismatch: {request['id']}")
    finally:
        worker.stdin.close()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill(); worker.wait()
        worker.stdout.close(); worker.stderr.close()
    save(receipt, {"passed": True, "cases": len(requests), "frozenReferenceCases": 416,
                   "extraTokenOnlyCases": len(requests) - 416, "sourceSHA256": source_hashes,
                   "vocabularySHA256": sha(original / "vocab.txt"), "tokenizerExecutableSHA256": sha(executable)})
    print(json.dumps({"phase": "tokenizer", "passedCases": len(requests)}), flush=True)


def coreml_checks(run, workspace):
    receipt = run / "parity-summary.json"
    if receipt.exists():
        require(read(receipt)["passed"], "saved Core ML parity failed")
        return
    snapshot(run, "parity", ["stage3_common.py", "stage3_parity.py"])
    import coremltools as ct
    conversion = read(run / "conversion.json")
    package = workspace / conversion["package"]
    verify_files(package, conversion["packageFiles"])
    expected_paths = sorted((STAGE2 / "reference/cases").glob("*.json"))
    require(len(expected_paths) == 416, "incomplete original references")
    summaries = {}
    for backend, compute in (("cpu_only", ct.ComputeUnit.CPU_ONLY), ("all", ct.ComputeUnit.ALL)):
        boundary(run, f"before-coreml-load:{backend}")
        model = ct.models.MLModel(str(package), compute_units=compute)
        description = model.get_spec().description
        require([i.name for i in description.input] == conversion["inputNames"], "input name/order mismatch")
        require([o.name for o in description.output] == conversion["outputNames"], "output name/order mismatch")
        for index, original_path in enumerate(expected_paths):
            boundary(run, f"parity:{backend}:{original_path.stem}")
            output = run / "parity" / backend / original_path.name
            if output.exists():
                continue
            original = read(original_path)
            tokens = read(run / "tokenizer-cases" / original_path.name)
            require(tokens["passed"] and tokens["inputs"] == original["inputs"], "unverified model tokens")
            started = time.monotonic()
            prediction = model.predict({k: np.asarray(v, dtype=np.int32) for k, v in tokens["inputs"].items()})
            seconds = time.monotonic() - started
            require(set(prediction) == {"logits", "probabilities"}, "unexpected model outputs")
            require(np.isfinite(prediction["logits"]).all(), f"nonfinite Core ML logits: {backend}:{original_path.stem}")
            delta = comparison(prediction["probabilities"], original["probabilities"])
            save(output, {"id": original["id"], "length": original["length"], "orientation": original["orientation"],
                 "backend": backend, "referenceSHA256": sha(original_path), **delta,
                 "probabilities": prediction["probabilities"].tolist(), "logits": prediction["logits"].tolist(),
                 "macPredictionSeconds": seconds, "untrainedHead": True})
            if (index + 1) % 40 == 0:
                print(json.dumps({"phase": "parity", "backend": backend, "completed": index + 1, "total": 416}), flush=True)
        rows = [read(run / "parity" / backend / p.name) for p in expected_paths]
        summaries[backend] = {"overall": summarize(rows), "byLength": {str(length): summarize([r for r in rows if r["length"] == length]) for length in (256, 512)}}
        del model
    passed = all(s["overall"]["passed"] and all(r["passed"] for r in s["byLength"].values()) for s in summaries.values())
    save(receipt, {"passed": passed, "backends": summaries, "referencePairs": 104, "referenceCasesPerBackend": 416,
         "convertedPackageBytes": conversion["packageBytes"], "phonePerformanceMeasured": False,
         "limitations": ["Reference head is untrained; this verifies numerical conversion, not grouping quality.",
                         "ALL allows Core ML to choose hardware; this does not prove Neural Engine placement."]})
    require(passed, "Core ML numerical parity gate failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--workspace", default=WORKSPACE)
    args = parser.parse_args()
    run, workspace = paths(args.run, args.workspace)
    setup_signals()
    try:
        initialize(run, workspace)
        tokenizer_checks(run, workspace)
        coreml_checks(run, workspace)
    except Paused as error:
        print(json.dumps({"status": "paused", "safeBoundary": str(error)}), flush=True)
    except Exception as error:
        failure(run, error)
        raise


if __name__ == "__main__":
    main()
