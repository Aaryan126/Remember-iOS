"""Read-only reuse of existing Mac probes, with no training or asset requests."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import time

import rk_control as c
from rk_policy import cosine

LEXICAL = c.PF / "checkpoint2/runs/comparison-01/native"
EMBED = Path.home() / "Library/Application Support/RememberMatcherFeasibility/v1/validation/validation-02/probe/EmbeddingProbe"
SPACE = "apple-dual:en:5C45D94E-BAB4-4927-94B6-8B5745C46289:1:512:1:512:token64-sentence256-v3"
CONTROLS = (
    "The violet bicycle is parked beside the library.",
    "The ferry timetable lists a departure at nine tomorrow.",
    "Please retrieve the earlier written instructions for the rehearsal.",
    "The archived laboratory checklist records a calibration step.",
    "No supplier invoice or payment amount was saved.",
    "The community garden storage room holds a green watering can.",
)


def identity():
    lexical = c.load(LEXICAL / "build.json")
    c.require(c.digest(LEXICAL / "ComparisonProbe") == lexical["binarySHA256"], "lexical probe changed")
    for name, expected in lexical["sources"].items():
        c.require(c.digest(Path(name)) == expected, f"lexical source binding changed: {name}")
    old = c.load(c.ROOT / "Evaluation/MatcherValidation/runs/validation-02/probe.json")
    c.require(c.digest(EMBED) == old["SHA256"] and old["downloadsAllowed"] is False,
              "English embedding probe changed or downloads allowed")
    return dict(lexicalBinarySHA256=lexical["binarySHA256"], lexicalBuildSHA256=c.digest(LEXICAL / "build.json"),
                locale=lexical["locale"], embeddingBinarySHA256=old["SHA256"],
                embeddingProbeRecordSHA256=c.digest(c.ROOT / "Evaluation/MatcherValidation/runs/validation-02/probe.json"),
                space=SPACE, channel="sentence", encoding="same explicit-English provider for query and passage",
                os=subprocess.check_output(["sw_vers"], text=True, timeout=15))


def request(binary, value):
    c.boundary()
    began = time.monotonic()
    process = subprocess.Popen([str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        data = json.dumps(value) + "\n"
        while True:
            try:
                output, error = process.communicate(input=data, timeout=1)
                break
            except subprocess.TimeoutExpired:
                data = None
                c.resources()
                if time.monotonic() - began > 60: raise TimeoutError("local probe timed out after 60 seconds")
        c.require(process.returncode == 0, f"local probe failed with exit {process.returncode}: {error[:300]}")
        lines = output.splitlines()
        c.require(len(lines) == 1, "probe response count mismatch")
        return json.loads(lines[0]), time.monotonic() - began
    finally:
        if process.poll() is None:
            process.terminate()
            try: process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=5)


def lexical(query, candidates, locale):
    if not candidates: return {}
    payload = dict(kind="search", query=query, documents=[dict(id=row["id"], text=row["quote"],
                    revision=row["revision"], locator=row["locator"], created=row["created"]) for row in candidates])
    result, seconds = request(LEXICAL / "ComparisonProbe", payload)
    c.require(result["locale"] == locale, "lexical locale changed")
    c.require(len({r["sourceId"] for r in result["hits"]}) == len(result["hits"]), "duplicate native lexical response")
    by_id = {row["id"]: row for row in candidates}
    for hit in result["hits"]:
        c.require(hit["sourceId"] in by_id and hit["quote"] == by_id[hit["sourceId"]]["quote"]
                  and hit["revision"] == by_id[hit["sourceId"]]["revision"], "native lexical citation mismatch")
        c.require(math.isfinite(hit["score"]) and 0 < hit["score"] <= 1, "native lexical score invalid")
    return {row["sourceId"]: row["score"] for row in result["hits"]}


def valid_embedding(value, text):
    key = hashlib.sha256(text.encode()).hexdigest()
    c.require(value.get("id") == key and value.get("status") == "ok", "embedding unavailable or ID mismatch")
    c.require(value.get("space") == value.get("expectedSpace") == SPACE, "embedding space mismatch")
    for channel in ("contextual", "sentence"):
        vector = value.get(channel, [])
        c.require(len(vector) == 512 and all(type(v) in (float,int) and math.isfinite(v) for v in vector),
                  "invalid embedding channel")
        c.require(abs(math.sqrt(sum(v*v for v in vector))-1) <= .001, "embedding norm mismatch")
    return value


def embed(text):
    key = hashlib.sha256(text.encode()).hexdigest()
    value, seconds = request(EMBED, dict(id=key, text=text))
    valid_embedding(value, text)
    return dict(**value, textSHA256=key, seconds=seconds)


def qualify():
    rows = []
    for text in CONTROLS:
        c.boundary()
        first, second = embed(text), embed(text)
        delta = max(abs(a-b) for channel in ("contextual", "sentence") for a,b in zip(first[channel],second[channel]))
        c.require(delta <= 1e-5, "repeated embedding outputs differ")
        c.require(cosine(first["sentence"],second["sentence"]) >= .99999, "query/passage identical-text compatibility failed")
        rows.append(dict(text=text, first=first, repeat=second, maxDelta=delta))
    return dict(status="qualified", supported=True, controls=rows, historicalParityClaim=False, phoneQualified=False)
