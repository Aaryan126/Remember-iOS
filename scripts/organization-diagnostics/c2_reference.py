"""Offline native-Mac placement adapter, not a complete ProjectGraphService replay.

The production value type, math and NLTagger topic evidence are copied byte-for-byte
from current source into a generated compile unit. Only the new-capture automatic
embedding branch is adapted: no reasoning, manual-assignment preservation, periodic
maintenance, persistence or empty old singleton candidate. Active member evidence
uses source-ID order; lexical thread IDs replace production UUID tie order.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import selectors
import subprocess
import tempfile
import time
from collections.abc import Callable, Mapping
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INTELLIGENCE = ROOT / "Remember/Remember/ProjectIntelligence.swift"
GRAPH = ROOT / "Remember/Remember/ProjectGraphService.swift"
ADAPTER = Path(__file__).parent / "reference/C2ReferenceProbe.swift"
DEFAULT_RUN = ROOT / "Evaluation/OrganizationDiagnostics/runs/c2-01"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _publish_bytes(path: Path, data: bytes) -> None:
    """Publish immutable evidence, accepting only byte-identical retries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Reference artifact differs: {path}")
        return
    descriptor, temporary = tempfile.mkstemp(prefix=".reference-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError(f"Concurrent reference artifact differs: {path}") from None
    finally:
        os.unlink(temporary)


def _production_blocks(source: str) -> dict[str, str]:
    boundaries = {
        "ProjectEmbedding": ("nonisolated struct ProjectEmbedding: Sendable {", "\nnonisolated protocol ProjectEmbeddingProviding"),
        "ProjectMath": ("nonisolated enum ProjectMath {", "\n/// Independent source evidence"),
        "ProjectTopicEvidence": ("nonisolated struct ProjectTopicEvidence {", "\n@Generable\nnonisolated struct ProjectReasoningResult"),
    }
    result = {}
    for name, (start, end) in boundaries.items():
        if source.count(start) != 1 or source.count(end) != 1:
            raise ValueError(f"Production extraction boundary changed: {name}")
        result[name] = source[source.index(start):source.index(end, source.index(start))]
    return result


def build(runpath: Path = DEFAULT_RUN) -> Path:
    """Build once under runpath/reference; verify every existing receipt exactly."""
    directory = Path(runpath).resolve() / "reference"
    directory.mkdir(parents=True, exist_ok=True)
    source_path = directory / "C2ReferenceCompileUnit.swift"
    executable = directory / "C2ReferenceProbe"
    receipt_path = directory / "build-receipt.json"
    blocks = _production_blocks(INTELLIGENCE.read_text())
    generated = (ADAPTER.read_text() + "\n" + "\n".join(blocks.values())).encode()
    command = ["xcrun", "swiftc", "-O", "-parse-as-library", "-target",
               "arm64-apple-macos26.0", "-module-cache-path", str(directory / "module-cache"),
               str(source_path), "-o", str(executable)]
    version = subprocess.run(["xcrun", "swiftc", "--version"], check=True,
                             capture_output=True, text=True, timeout=60).stdout.strip()
    binding = {
        "schema": 1,
        "reference": "production embedding-only placement, no reasoning or batch maintenance",
        "sources": {str(path.relative_to(ROOT)): _digest(path.read_bytes())
                    for path in (INTELLIGENCE, GRAPH, ADAPTER, Path(__file__).resolve())},
        "extractedBlocks": {name: _digest(block.encode()) for name, block in blocks.items()},
        "generatedSourceSHA256": _digest(generated),
        "command": command,
        "swiftVersion": version,
        "adaptations": ["new capture embedding-only branch", "native Mac NLTagger",
                        "source-ID member order", "lexical thread-ID ties instead of UUID ties",
                        "no reasoning, manual-preservation branch, batch maintenance or persistence"],
    }
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if any(receipt.get(key) != value for key, value in binding.items()):
            raise ValueError("Reference build receipt no longer matches current sources/toolchain")
        if not source_path.is_file() or source_path.read_bytes() != generated:
            raise ValueError("Generated reference source differs from sealed build")
        if not executable.is_file() or _digest(executable.read_bytes()) != receipt.get("binarySHA256"):
            raise ValueError("Reference binary differs from sealed build")
        return executable
    if executable.exists():
        raise ValueError("Unsealed reference binary exists; use a fresh run directory")
    _publish_bytes(source_path, generated)
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)
    binding["binarySHA256"] = _digest(executable.read_bytes())
    _publish_bytes(receipt_path, (json.dumps(binding, indent=2, sort_keys=True) + "\n").encode())
    return executable


class ReferenceClient:
    """Serialized JSONL callback for current source and active cluster source maps.

    embedding_for_text(text) supplies {contextual, sentence, space} or None. The
    callback is skipped when a source already includes an explicit embedding key.
    No embedding model is loaded or requested by this adapter.
    """

    def __init__(self, executable: Path, embedding_for_text: Callable[[str], Any],
                 timeout: float = 60):
        self.embedding_for_text = embedding_for_text
        self.timeout = timeout
        self.process = subprocess.Popen([str(executable)], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        bufsize=0)
        self._buffer = b""
        os.set_blocking(self.process.stdin.fileno(), False)
        self._selector = selectors.DefaultSelector()
        self._selector.register(self.process.stdout, selectors.EVENT_READ)

    def _source(self, source: Mapping[str, Any]) -> dict[str, Any]:
        identifier, text = source["id"], source["text"]
        if not isinstance(identifier, str) or not isinstance(text, str):
            raise ValueError("Reference source ID and text must be strings")
        embedding = source["embedding"] if "embedding" in source else self.embedding_for_text(text)
        return {"id": identifier, "text": text, "embedding": embedding}

    def __call__(self, source: Mapping[str, Any],
                 active_clusters: Mapping[str, list[Mapping[str, Any]]]) -> dict[str, Any]:
        if self.process.poll() is not None:
            raise RuntimeError("Reference process is not running")
        request = {"source": self._source(source), "clusters": {
            thread: [self._source(member) for member in sorted(members, key=lambda item: item["id"])]
            for thread, members in sorted(active_clusters.items())}}
        payload = (json.dumps(request, allow_nan=False, separators=(",", ":")) + "\n").encode()
        deadline = time.monotonic() + self.timeout
        try:
            offset = 0
            while offset < len(payload):
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([], [self.process.stdin], [], remaining)[1]:
                    raise TimeoutError("Native reference request write exceeded timeout")
                try:
                    offset += os.write(self.process.stdin.fileno(), payload[offset:])
                except BlockingIOError:
                    continue
            while b"\n" not in self._buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not self._selector.select(remaining):
                    raise TimeoutError("Native reference request exceeded timeout")
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError("Native reference process ended without a response")
                self._buffer += chunk
            line, self._buffer = self._buffer.split(b"\n", 1)
            response = json.loads(line)
            if "error" in response:
                raise ValueError(f"Native reference rejected request: {response['error']}")
            selected = response.get("selected")
            if not isinstance(selected, list) or len(selected) > 1 or any(
                    thread not in active_clusters for thread in selected):
                raise ValueError("Native reference returned invalid assignments")
            return response
        except (OSError, ValueError, TimeoutError, RuntimeError):
            self.close()
            raise

    def close(self) -> None:
        self._selector.close()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout):
            if stream is not None:
                stream.close()

    def __enter__(self) -> ReferenceClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()
    print(build(args.run))
