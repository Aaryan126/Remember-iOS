"""Small isolated native policy/search probe; no app store or model initialization."""
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common as c

BUILD = c.WORK / "runs/comparison-01/native"
APP = c.ROOT / "Remember/Remember"


def extract(text, start, end):
    c.require(text.count(start) == 1, f"ambiguous extraction start: {start}")
    begin = text.index(start)
    finish = text.index(end, begin)
    return text[begin:finish]


def generated():
    chunker = extract((APP / "MemoryContentExtractor.swift").read_text(),
                      "nonisolated struct MemoryTextChunker {", "\nactor MemoryContentExtractor")
    search = (APP / "MemorySearch.swift").read_text()
    lexical = extract(search, "    private nonisolated static func lexicalCoverage", "    private nonisolated static func semanticScore")
    helpers = extract(search, "    private nonisolated static func normalized", "\n}\n\nnonisolated struct MemorySearchDocument")
    return ("import Foundation\n" +
            "enum MemoryExtractionMethod: String, Codable, Sendable { case fixture }\n" +
            "struct MemoryChunkDraft { let ordinal: Int; let locator: String; let text: String; let extractionMethod: MemoryExtractionMethod }\n" +
            chunker + "\nenum LocalEvidence {\n" + lexical.replace("private nonisolated", "nonisolated", 1) + helpers + "\n}\n")


def build():
    c.boundary()
    BUILD.mkdir(parents=True, exist_ok=True)
    generated_path = BUILD / "ProductionSearch.swift"
    content = generated()
    if generated_path.exists():
        c.require(generated_path.read_text() == content, "generated native helper changed")
    else:
        # Generated compile artifact, not an edit to production source.
        with generated_path.open("x") as stream:
            stream.write(content)
    source = Path(__file__).with_name("ComparisonProbe.swift")
    binary = BUILD / "ComparisonProbe"
    cache = c.PF / "runs/checkpoint1/ledger/build/ModuleCache.noindex"
    c.require(cache.is_dir(), "existing registered compiler cache missing")
    command = ["xcrun", "swiftc", "-O", "-parse-as-library", "-module-cache-path", str(cache),
               str(source), str(APP / "D3OrganizationPolicy.swift"), str(generated_path), "-o", str(binary)]
    receipt = {"sources": {str(p): c.digest(p) for p in (source, Path(__file__), generated_path,
               APP / "D3OrganizationPolicy.swift", APP / "MemoryContentExtractor.swift", APP / "MemorySearch.swift")},
               "command": command, "swiftVersion": subprocess.check_output(["xcrun", "swiftc", "--version"], text=True, timeout=30)}
    target = BUILD / "build.json"
    if target.exists():
        old = c.read(target)
        c.require(all(old[key] == value for key, value in receipt.items()) and c.digest(binary) == old["binarySHA256"], "native build binding changed")
        return old
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    c.publish(BUILD / "compile.json", {"exitCode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    c.require(result.returncode == 0, "native build failed; see compile.json")
    receipt["binarySHA256"] = c.digest(binary)
    receipt["locale"] = invoke({"kind": "metadata"})["locale"]
    c.publish(target, receipt)
    c.boundary()
    return receipt


def invoke(request):
    result = subprocess.run([str(BUILD / "ComparisonProbe")], input=json.dumps(request)+"\n",
                            text=True, capture_output=True, timeout=30, check=True)
    lines = result.stdout.splitlines()
    c.require(len(lines) == 1, "native probe response count")
    response = json.loads(lines[0])
    c.require("error" not in response, f"native request failed: {response.get('error')}")
    return response


class Native:
    def __init__(self):
        self.receipt = c.read(BUILD / "build.json")
        c.require(c.digest(BUILD / "ComparisonProbe") == self.receipt["binarySHA256"], "native binary changed")

    def __call__(self, request):
        result = invoke(request)
        c.require(result["locale"] == self.receipt["locale"], "native locale changed")
        return result
