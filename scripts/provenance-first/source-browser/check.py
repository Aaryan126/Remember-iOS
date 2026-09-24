#!/usr/bin/env python3
"""Bounded Mac-only source-browser tests. No downloads, app/vault or model access."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

CODE = Path(__file__).resolve().parent
ROOT = CODE.parents[2]
APP = ROOT / "Remember/Remember"
WORK = ROOT / "Evaluation/ProvenanceFirst/source-browser"
RUN = ROOT / "Evaluation/ProvenanceFirst/runs/source-browser"
sys.path.insert(0, str(CODE.parent / "answer-support-screen"))
import sb_control as prior


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(text, start, end):
    if text.count(start) != 1:
        raise ValueError("ambiguous production extraction boundary")
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


def support():
    # Compile actual model/Codable declarations and the unmodified text chunker.
    # Inert GRDB protocol shims and an in-memory read-only store avoid linking iOS
    # frameworks or a personal vault. This is NOT an app/GRDB integration test.
    memory = (APP / "MemoryItem.swift").read_text().split("nonisolated struct MemoryLibraryItem")[0]
    provenance = (APP / "Provenance.swift").read_text()
    models = provenance.split("nonisolated struct ProvenanceCluster")[0]
    errors = extract(provenance, "nonisolated enum ProvenanceError:", "\nextension MemoryStore")
    extractor = (APP / "MemoryContentExtractor.swift").read_text()
    chunk_types = extract(extractor, "nonisolated enum MemoryExtractionMethod:", "\nnonisolated struct ExtractedMemoryContent")
    chunker = extract(extractor, "nonisolated struct MemoryTextChunker {", "\nactor MemoryContentExtractor")
    return ("import Foundation\n"
            "nonisolated protocol DatabaseValueConvertible {}\n"
            "nonisolated protocol FetchableRecord {}\n"
            "nonisolated protocol PersistableRecord {}\n"
            "nonisolated struct ProvenanceSnapshot { var memories: [UUID: MemoryItem] = [:] }\n"
            + (memory + models + errors + chunk_types + chunker).replace("import GRDB\n", "")
            + "\nnonisolated enum FixtureStoreError: Error { case offline }\nactor MemoryStore {\n"
            "let events: [ProvenanceEvent]; let fails: Bool; private(set) var readCount = 0\n"
            "init(events: [ProvenanceEvent], fails: Bool = false) { self.events = events; self.fails = fails }\n"
            "func provenanceEvents() async throws -> [ProvenanceEvent] { readCount += 1; "
            "if fails { throw FixtureStoreError.offline }; return events }\n}\n")


def boundary():
    if (WORK / "PAUSE").exists():
        raise SystemExit("Paused at saved boundary; remove only source-browser/PAUSE to resume.")
    return prior.previous.resources()


def publish(path, value):
    if path.resolve() != path or not path.is_relative_to(RUN):
        raise ValueError("output escaped source-browser runs")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", choices=["build", "test", "regression", "seal", "verify"], required=True)
    args = parser.parse_args()
    resources_before = boundary()
    prior.verify_prior()
    prior.verify_frozen()
    for name, expected in prior.load(prior.WORK / "checkpoint-stop.json")["hashes"].items():
        if digest(prior.WORK / name) != expected:
            raise ValueError("prior stopped checkpoint changed: " + name)
    checkpoint = WORK / "checkpoint-stop.json"
    if args.unit == "verify":
        saved = json.loads(checkpoint.read_text())
        for name, expected in saved["hashes"].items():
            path = ROOT / name
            if path.resolve() != path or digest(path) != expected:
                raise ValueError("saved checkpoint changed: " + name)
        print(json.dumps({"status": "verified-review-stop", "files": len(saved["hashes"]),
                          "resources": resources_before}))
        return
    if checkpoint.exists():
        raise ValueError("checkpoint is stopped; use --unit verify, not an artifact overwrite")
    if RUN.resolve() != RUN:
        raise ValueError("redirected runs directory")
    RUN.mkdir(parents=True, exist_ok=True)
    generated = RUN / "ProductionSupport.swift"
    binary = RUN / "SourceEvidenceTests"
    inputs = [CODE / "check.py", CODE / "SourceEvidenceTests.swift",
              APP / "SourceEvidenceSearch.swift", APP / "SourceEvidenceStoreAdapter.swift",
              APP / "MemoryItem.swift", APP / "Provenance.swift", APP / "MemoryContentExtractor.swift"]
    bindings = {str(path.relative_to(ROOT)): digest(path) for path in inputs}
    if args.unit == "regression":
        command = ["python3", "-B", "-m", "unittest", "discover", "-s",
                   "scripts/provenance-first/answer-support-screen", "-p", "test_*.py"]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
        count = re.search(r"Ran (\d+) tests?", result.stderr)
        publish(RUN / "regression.json", {"command": command, "exitCode": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr,
                "testCount": int(count.group(1)) if count else 0})
        print(result.stderr)
        raise SystemExit(result.returncode)
    if args.unit == "build":
        # Generated test support/receipts, never edits to production source files.
        generated.write_text(support())
        command = ["xcrun", "swiftc", "-swift-version", "5", "-default-isolation", "MainActor",
                   "-strict-concurrency=complete", "-warnings-as-errors", "-parse-as-library",
                   "-module-cache-path", str(RUN / "ModuleCache.noindex"),
                   str(generated), str(APP / "SourceEvidenceSearch.swift"),
                   str(APP / "SourceEvidenceStoreAdapter.swift"), str(CODE / "SourceEvidenceTests.swift"),
                   "-o", str(binary)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        receipt = {"command": command, "bindings": bindings, "exitCode": result.returncode,
                   "stdout": result.stdout, "stderr": result.stderr,
                   "generatedSHA256": digest(generated), "resourcesBefore": resources_before,
                   "resourcesAfter": prior.previous.resources(),
                   "swiftVersion": subprocess.check_output(["xcrun", "swiftc", "--version"], text=True, timeout=30)}
        if result.returncode == 0:
            receipt["binarySHA256"] = digest(binary)
        publish(RUN / "build.json", receipt)
        print(json.dumps(receipt))
        raise SystemExit(result.returncode)
    build = json.loads((RUN / "build.json").read_text())
    if build["bindings"] != bindings or build.get("binarySHA256") != digest(binary) or build["generatedSHA256"] != digest(generated):
        raise ValueError("build inputs changed; rebuild this checkpoint before testing")
    if args.unit == "seal":
        tests = json.loads((RUN / "tests.json").read_text())
        regression = json.loads((RUN / "regression.json").read_text())
        result = json.loads(tests["stdout"])
        if (build["exitCode"] != 0 or tests["exitCode"] != 0 or result["failed"] != 0
                or result["passed"] != 52 or regression["exitCode"] != 0 or regression["testCount"] != 25
                or tests["buildSHA256"] != digest(RUN / "build.json")):
            raise ValueError("checkpoint verification incomplete")
        artifacts = inputs + [generated, binary, RUN / "build.json", RUN / "tests.json", RUN / "regression.json",
                              prior.WORK / "checkpoint-stop.json"]
        artifacts += [WORK / name for name in ("PLAN.md", "REPORT.md", "RESUME.md", "STATUS.md")]
        record = {"status": "foundation-complete-review-stop", "nativeTests": 52, "regressionTests": 25,
                  "modelRequests": 0, "appUIIntegrated": False, "fullAppBuildVerified": False,
                  "resources": prior.previous.resources(),
                  "hashes": {str(path.relative_to(ROOT)): digest(path) for path in artifacts}}
        with checkpoint.open("x") as stream:
            json.dump(record, stream, indent=2, sort_keys=True)
            stream.write("\n")
        print(json.dumps({key: value for key, value in record.items() if key != "hashes"}))
        return
    result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
    receipt = {"command": [str(binary)], "exitCode": result.returncode,
               "stdout": result.stdout, "stderr": result.stderr,
               "buildSHA256": digest(RUN / "build.json"),
               "resourcesBefore": resources_before, "resourcesAfter": prior.previous.resources()}
    publish(RUN / "tests.json", receipt)
    print(json.dumps(receipt))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
