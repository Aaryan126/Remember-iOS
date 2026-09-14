"""Explicit split access and token caches; test files remain behind selection."""
from collections import Counter
from itertools import combinations
import json
import random

from experiment import validate_inputs, validate_labels, pair_rows
from stage5_common import *


def inputs_for(split, run):
    require(split in ["train", "development", "test"], "unknown split")
    if split == "test": authorize_test(run)
    value = read(RELEASE / f"inputs-{split}.json")
    validate_inputs(value, complete=False)
    require(all(lib["split"] == split for lib in value["libraries"]), "mixed input split")
    return value


def pair_inputs(document):
    pairs = []
    for library in document["libraries"]:
        by_id = {item["id"]: item["text"] for item in library["items"]}
        for first, second in combinations(sorted(by_id), 2):
            pairs.append({"id": first + "--" + second, "library": library["id"],
                          "first": first, "second": second, "texts": [by_id[first], by_id[second]]})
    return pairs


def gold_for(split, run):
    document = inputs_for(split, run)
    labels = read(RELEASE / f"labels-{split}.json")
    validate_labels(document, labels)
    lookup = {lib["id"]: lib for lib in labels["libraries"]}
    return [{**pair, "id": pair["first"] + "--" + pair["second"], "library": library["id"]}
            for library in document["libraries"] for pair in pair_rows(library, lookup[library["id"]])]


def order_for(seed, epoch, count):
    order = list(range(count)); random.Random(seed * 100 + epoch).shuffle(order)
    return order


def class_weights(labels):
    count = Counter(labels)
    require(set(count) == {0, 1, 2}, "training must cover all classes")
    return [len(labels) / (3 * count[index]) for index in range(3)]


def prepare_tokens(run, external, split):
    if split == "test": authorize_test(run)
    receipt = run / "tokens" / f"{split}.json"
    if receipt.exists():
        result = read(receipt)
        require(sha(external / result["file"]) == result["SHA256"], "cached tokens changed")
        return result
    boundary(run, f"tokenize:{split}")
    import torch
    from transformers import AutoTokenizer
    from safetensors.torch import save_file
    model_dir = WORKSPACE / read(DATA / "model-manifest.json")["workspaceRelativeDirectory"]
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False, use_fast=True)
    pairs = pair_inputs(inputs_for(split, run))
    rows = []
    values = {k: [] for k in ["input_ids", "attention_mask", "token_type_ids"]}
    for pair in pairs:
        boundary(run, f"tokenize:{split}:{pair['id']}")
        token_lengths = []
        for reverse in [False, True]:
            first, second = pair["texts"][::-1] if reverse else pair["texts"]
            tokens = tokenizer(first, second, padding="max_length", max_length=512, truncation="longest_first")
            token_lengths.append(len(tokenizer(first, second, truncation=False)["input_ids"]))
            for key in values: values[key].append(tokens[key])
        rows.append({k: v for k, v in pair.items() if k != "texts"} | {"untruncatedTokens": token_lengths})
    file = external / "tokens" / f"{split}-{time.time_ns()}.safetensors"
    publish_tensor_file(file, lambda pending: save_file({k: torch.tensor(v, dtype=torch.int64) for k, v in values.items()}, str(pending)))
    result = {"split": split, "rows": rows, "file": str(file.relative_to(external)), "SHA256": sha(file),
              "sourceSHA256": sha(RELEASE / f"inputs-{split}.json"), "directionOrder": ["forward", "reverse"],
              "truncatedDirections": sum(n > 512 for row in rows for n in row["untruncatedTokens"]),
              "directionCount": len(rows)*2, "maxUntruncatedTokens": max(n for row in rows for n in row["untruncatedTokens"])}
    save(receipt, result)
    return result


def training_examples(run, receipt):
    labels = {row["id"]: row for row in gold_for("train", run)}
    examples = []
    for index, row in enumerate(receipt["rows"]):
        relation = labels[row["id"]]["relation"]
        if relation == "uncertain": continue
        for direction in [0, 1]: examples.append((index*2+direction, CLASSES.index(relation)))
    require(len(examples) == 5654, "frozen training pair coverage changed")
    return examples


def batch_inputs(tokens, indices, device, length=None):
    import torch
    index = torch.tensor(indices, dtype=torch.long)
    if length is None:
        longest = int(tokens["attention_mask"][index].sum(-1).max())
        length = min(512, ((longest + 31) // 32) * 32)
    return {key: value[index, :length].to(device) for key, value in tokens.items()}
