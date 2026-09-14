"""Inference-only reuse of P2 transforms and weights. No labels, fitting or downloads."""
from contextlib import contextmanager
import gc
import gzip
import json
import math
import os
import select
import selectors
import subprocess
import sys
import time

import c2_common as c

# Import only pure feature/export functions. Never invoke a legacy pipeline.
sys.path.insert(0, str(c.LEGACY))
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from stage2 import pair_features, exported_probabilities, validate_embedding
from screening2_data import identifier_features
from screening2_models import portable_scores


class Features:
    def __init__(self, texts, embeddings):
        frozen = c.read(c.P2 / "tfidf.json")
        self.vectorizer = TfidfVectorizer(
            vocabulary=frozen["vocabulary"], ngram_range=tuple(frozen["ngramRange"]),
            lowercase=frozen["lowercase"], token_pattern=frozen["tokenPattern"],
            norm=frozen["norm"], dtype=np.float64)
        self.vectorizer.idf_ = np.asarray(frozen["idf"], dtype=np.float64)
        self.texts, self.embeddings = texts, embeddings
        self.ids = sorted(texts)
        self.index = {key: n for n, key in enumerate(self.ids)}
        self.vectors = self.vectorizer.transform([texts[key] for key in self.ids])
        self.baseline = c.read(c.P2 / "baseline.json")["model"]
        c.require(self.baseline["classOrder"] == ["same", "related", "unrelated"], "Baseline class order changed")
        self.hybrids = {seed: c.read(c.P2 / f"hybrid-{seed}.json")["model"] for seed in ("17", "29", "41")}

    def values(self, first, second):
        a, b = self.texts[first], self.texts[second]
        lexical = float((self.vectors[self.index[first]] @ self.vectors[self.index[second]].T).toarray()[0, 0])
        values = pair_features({"text": a}, {"text": b}, self.embeddings[first], self.embeddings[second], lexical)
        return values + identifier_features(a, b)

    def scores(self, values, neural=None):
        usable = all(value is not None and math.isfinite(value) for value in values)
        probability = exported_probabilities(self.baseline, [values[:6]])[0] if usable else None
        result = {"baseline": {"score": float(probability[0]) if usable else None,
                               "eligible": bool(np.argmax(probability) == 0) if usable else False},
                  "hybrid": {}}
        for seed, value in (neural or {}).items():
            p = np.clip(value, 1e-6, 1 - 1e-6)
            result["hybrid"][seed] = (float(portable_scores(self.hybrids[seed],
                [values + [float(np.log(p / (1 - p)))]] )[0]) if usable else None)
        return result


@contextmanager
def embedding_probe():
    executable = c.EXTERNAL / "probe/EmbeddingProbe"
    receipt = c.read(c.P2 / "probe.json")
    c.require(not receipt["downloadsAllowed"] and c.digest(executable) == receipt["SHA256"], "English probe changed")
    folder = c.RUN / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / f"embedding-{time.time_ns()}.log").open("wb") as error_log:
        process = subprocess.Popen([str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=error_log, bufsize=0)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        os.set_blocking(process.stdin.fileno(), False)
        buffered = bytearray()
        def query(key, text):
            request = (json.dumps({"id": key, "text": text}) + "\n").encode()
            c.require(len(request) < 16000, "Embedding request exceeds bounded pipe payload")
            deadline = time.monotonic() + 60
            pending = memoryview(request)
            while pending:
                remaining = deadline - time.monotonic()
                c.require(remaining > 0 and select.select([], [process.stdin], [], remaining)[1], "Embedding request timed out")
                try:
                    sent = os.write(process.stdin.fileno(), pending)
                except BlockingIOError:
                    continue
                c.require(sent > 0, "Embedding request write failed")
                pending = pending[sent:]
            while b"\n" not in buffered:
                remaining = deadline - time.monotonic()
                c.require(remaining > 0 and selector.select(remaining), "Embedding probe timed out")
                chunk = os.read(process.stdout.fileno(), 65536)
                c.require(bool(chunk), "Embedding probe exited early")
                buffered.extend(chunk)
                c.require(len(buffered) <= 1024 * 1024, "Oversized embedding response")
            line, _, tail = buffered.partition(b"\n")
            buffered[:] = tail
            record = {**json.loads(line), "textSHA256": c.text_sha(text)}
            validate_embedding({"id": key, "text": text}, record)
            if record["status"] == "ok":
                c.require(record["space"].startswith("apple-dual:en:"), "Wrong embedding language")
                c.require(all(len(record[k]) == 512 for k in ("contextual", "sentence")), "Embedding dimension changed")
            return record
        try:
            yield query
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
                    process.wait(timeout=5)
            selector.close()
            process.stdout.close()


class Neural:
    def __init__(self, seed):
        import torch
        from transformers import AutoTokenizer, BertConfig, BertForSequenceClassification
        torch.set_num_threads(4)
        c.require(torch.backends.mps.is_available(), "MPS unavailable; do not silently change backend")
        self.seed = str(seed)
        self.record = c.read(c.P2 / f"hybrid-{seed}.json")["final"]
        weights = c.EXTERNAL / self.record["file"]
        c.require(c.digest(weights) == self.record["SHA256"], "Frozen weights changed")
        assets = c.read(c.ROOT / "Evaluation/MatcherFeasibility/model-manifest.json")
        directory = c.WORKSPACE / assets["workspaceRelativeDirectory"]
        self.tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True,
                                                       trust_remote_code=False, use_fast=True)
        config = BertConfig.from_pretrained(str(directory), local_files_only=True, num_labels=2,
                                            id2label={0: "not_same", 1: "same"}, label2id={"not_same": 0, "same": 1})
        config._attn_implementation = "eager"
        self.model = BertForSequenceClassification(config)
        with gzip.open(weights, "rb") as stream:
            saved = torch.load(stream, map_location="cpu", weights_only=True)
        c.require(saved["fingerprint"] == self.record["fingerprint"], "Weight fingerprint changed")
        self.model.load_state_dict(saved["model"], strict=True)
        del saved
        self.model.to("mps").eval()

    def predict(self, pairs):
        import torch
        c.require(0 < len(pairs) <= 8, "Inference unit must contain one to eight pairs")
        left, right = [], []
        for first, second in pairs:
            left.extend((first, second))
            right.extend((second, first))
        encoded = self.tokenizer(left, right, padding="max_length", max_length=512,
                                 truncation="longest_first", return_tensors="pt")
        longest = int(encoded["attention_mask"].sum(-1).max())
        length = min(512, ((longest + 31) // 32) * 32)
        with torch.inference_mode():
            inputs = {key: value[:, :length].to("mps") for key, value in encoded.items()}
            values = self.model(**inputs).logits.softmax(-1)[:, 1].cpu().tolist()
        c.require(all(math.isfinite(v) and 0 <= v <= 1 for v in values), "Invalid neural probability")
        return [{"directions": values[n:n+2], "score": sum(values[n:n+2]) / 2,
                 "weightsSHA256": self.record["SHA256"]} for n in range(0, len(values), 2)]

    def close(self):
        import torch
        self.model = None
        self.tokenizer = None
        gc.collect()
        torch.mps.empty_cache()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
