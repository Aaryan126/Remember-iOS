"""Split-gated source representations. No label-derived text features."""
import itertools
import json
import selectors
import subprocess

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

import p2_common as c
from stage2 import pair_features, validate_embedding, content_sha
from screening2_data import identifier_features
from stage5_common import publish_tensor_file


def probe():
    source = (c.ROOT / "Remember/Remember/ProjectIntelligence.swift").read_text()
    provider = source.split("nonisolated struct ProjectEmbedding:", 1)[1].split("nonisolated enum ProjectMath", 1)[0]
    normalization = source.split("    static func normalized(_ vector:", 1)[1].split("    static func cosine(", 1)[0]
    body = "import Foundation\nimport NaturalLanguage\nnonisolated struct ProjectEmbedding:" + provider
    body += "nonisolated enum ProjectMath {\n    static func normalized(_ vector:" + normalization + "}\n"
    from environment import publish_bytes
    generated = c.EXTERNAL / "probe/ProductionEmbedding.swift"
    if generated.exists():
        c.require(generated.read_text() == body, "generated embedding provider changed")
    else:
        publish_bytes(generated, body.encode())
    executable = generated.parent / "EmbeddingProbe"
    receipt = c.RUN / "probe.json"
    if receipt.exists():
        c.require(c.digest(executable) == c.read(receipt)["SHA256"], "embedding executable changed")
    else:
        c.require(not executable.exists(), "orphan executable; inspect before retry")
        result = subprocess.run(["xcrun", "swiftc", "-parse-as-library", "-O", "-target", "arm64-apple-macos26.0",
                                 str(generated), str(c.ROOT / "scripts/matcher-validation/P2EmbeddingProbe.swift"),
                                 "-o", str(executable)], capture_output=True, text=True, timeout=180)
        c.require(result.returncode == 0, "embedding probe build failed: " + result.stderr)
        c.publish(receipt, {"SHA256": c.digest(executable), "generatedSHA256": c.digest(generated), "downloadsAllowed": False})
    return executable


def embeddings(split):
    libraries, _ = c.split_data(split)
    items = [i for lib in libraries for i in lib["items"]]
    missing = [i for i in items if not (c.RUN / "embeddings" / f"{i['id']}.json").exists()]
    if missing:
        c.boundary("embedding-probe", 8 * c.MIB)
        executable = probe()
        with (c.RUN / f"probe-{split}-stderr.log").open("a") as error:
            process = subprocess.Popen([str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error, text=True, bufsize=1)
            try:
                for index, item in enumerate(missing):
                    c.boundary("embedding:" + item["id"])
                    process.stdin.write(json.dumps({"id": item["id"], "text": item["text"]}) + "\n")
                    process.stdin.flush()
                    with selectors.DefaultSelector() as selector:
                        selector.register(process.stdout, selectors.EVENT_READ)
                        c.require(bool(selector.select(timeout=60)), "embedding response timed out")
                    line = process.stdout.readline()
                    c.require(bool(line), "embedding probe exited")
                    record = json.loads(line) | {"textSHA256": content_sha(item["text"])}
                    validate_embedding(item, record)
                    c.publish(c.RUN / "embeddings" / f"{item['id']}.json", record)
                    if (index + 1) % 20 == 0:
                        c.log("embeddings", split=split, completed=len(items)-len(missing)+index+1, total=len(items))
            finally:
                process.stdin.close()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                process.stdout.close()
    result = {i["id"]: c.read(c.RUN / "embeddings" / f"{i['id']}.json") for i in items}
    for i in items:
        validate_embedding(i, result[i["id"]])
    return result


def pairs(libraries):
    return [{"id": a["id"] + "--" + b["id"], "library": l["id"], "first": a["id"], "second": b["id"],
             "texts": [a["text"], b["text"]]} for l in libraries for a, b in itertools.combinations(sorted(l["items"], key=lambda i:i["id"]), 2)]


def tokens(split):
    import torch
    from transformers import AutoTokenizer
    from safetensors.torch import save_file, load_file
    libraries, _ = c.split_data(split)
    path = c.RUN / "tokens" / f"{split}.json"
    if not path.exists():
        c.boundary("tokens:" + split, 160 * c.MIB)
        asset = c.read(c.ROOT / "Evaluation/MatcherFeasibility/model-manifest.json")
        tokenizer = AutoTokenizer.from_pretrained(str(c.WORKSPACE / asset["workspaceRelativeDirectory"]), local_files_only=True, trust_remote_code=False, use_fast=True)
        values = {k: [] for k in ("input_ids", "attention_mask", "token_type_ids")}
        rows = []
        for pair in pairs(libraries):
            c.boundary("tokenize:" + pair["id"])
            lengths = []
            for first, second in (pair["texts"], pair["texts"][::-1]):
                encoded = tokenizer(first, second, padding="max_length", max_length=512, truncation="longest_first")
                lengths.append(len(tokenizer(first, second, truncation=False)["input_ids"]))
                for key in values:
                    values[key].append(encoded[key])
            rows.append({k:v for k,v in pair.items() if k != "texts"} | {"untruncatedTokens": lengths})
        target = c.EXTERNAL / "tokens" / f"{split}.safetensors"
        tensor_values = {k:torch.tensor(v, dtype=torch.int64) for k,v in values.items()}
        if target.exists():
            old = load_file(str(target))
            c.require(set(old) == set(tensor_values) and all(torch.equal(old[k],v) for k,v in tensor_values.items()), "orphan tokens differ")
        else:
            publish_tensor_file(target, lambda pending: save_file(tensor_values, str(pending)))
        c.publish(path, {"file": str(target.relative_to(c.EXTERNAL)), "SHA256": c.digest(target), "rows": rows,
                         "inputsSHA256": c.digest(c.RELEASE / f"inputs-{split}.json"),
                         "truncatedDirections": sum(n>512 for r in rows for n in r["untruncatedTokens"])})
    receipt = c.read(path)
    target = c.EXTERNAL / receipt["file"]
    c.require(receipt["inputsSHA256"] == c.digest(c.RELEASE / f"inputs-{split}.json") and c.digest(target) == receipt["SHA256"], "token binding changed")
    return load_file(str(target)), {r["id"]: i for i,r in enumerate(receipt["rows"])}


def vocabulary():
    libraries, _ = c.split_data("train")
    items = [i for l in libraries for i in l["items"]]
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), dtype=np.float64)
    vectorizer.fit([i["text"] for i in items])
    record = {"fitSourceIDs": [i["id"] for i in items], "vocabulary": {k:int(v) for k,v in vectorizer.vocabulary_.items()},
              "idf": vectorizer.idf_.tolist(), "ngramRange": [1, 2], "lowercase": True,
              "tokenPattern": vectorizer.token_pattern, "norm": "l2"}
    c.publish(c.RUN / "tfidf.json", record)
    return vectorizer


def features(split):
    libraries, gold = c.split_data(split)
    vectorizer = vocabulary()
    representations = embeddings(split)
    output = []
    for lib in libraries:
        items = {i["id"]:i for i in lib["items"]}
        index = {key:n for n,key in enumerate(items)}
        mat = vectorizer.transform([i["text"] for i in items.values()])
        lexical = (mat @ mat.T).toarray()
        for row in [r for r in gold if r["library"] == lib["id"]]:
            a,b = row["first"],row["second"]
            values = pair_features(items[a],items[b],representations[a],representations[b],lexical[index[a],index[b]])
            values += identifier_features(items[a]["text"],items[b]["text"])
            output.append(row | {"features":values})
    c.publish(c.RUN / "features" / f"{split}.json", {"tfidfSHA256":c.digest(c.RUN / "tfidf.json"), "rows":output})
    return output
