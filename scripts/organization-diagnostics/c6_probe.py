"""Existing English native embedding probe, with C6-only logs and bounded I/O."""
from contextlib import contextmanager
import json
import os
import select
import subprocess
import time

import c2_common as c


@contextmanager
def embedding_probe(run):
    from c2_models import validate_embedding
    executable = c.EXTERNAL / "probe/EmbeddingProbe"
    receipt = c.read(c.P2 / "probe.json")
    c.require(not receipt["downloadsAllowed"] and c.digest(executable) == receipt["SHA256"], "Native probe changed")
    folder = run / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / f"embedding-{time.time_ns()}.log").open("wb") as log:
        process = subprocess.Popen([str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, bufsize=0)
        os.set_blocking(process.stdin.fileno(), False)
        buffer = bytearray()
        def query(key, text):
            pending = memoryview((json.dumps({"id": key, "text": text}) + "\n").encode())
            c.require(len(pending) < 16000, "Oversized native request")
            deadline = time.monotonic() + 45
            while pending:
                remaining = deadline - time.monotonic()
                c.require(remaining > 0 and select.select([], [process.stdin], [], remaining)[1], "Native write timeout")
                try:
                    sent = os.write(process.stdin.fileno(), pending)
                except BlockingIOError:
                    continue
                c.require(sent > 0, "Native pipe closed")
                pending = pending[sent:]
            while b"\n" not in buffer:
                remaining = deadline - time.monotonic()
                c.require(remaining > 0 and select.select([process.stdout], [], [], remaining)[0], "Native read timeout")
                part = os.read(process.stdout.fileno(), 65536)
                c.require(bool(part), "Native probe exited")
                buffer.extend(part)
                c.require(len(buffer) <= 1024**2, "Native response too large")
            line, _, tail = buffer.partition(b"\n")
            buffer[:] = tail
            record = {**json.loads(line), "textSHA256": c.text_sha(text)}
            validate_embedding({"id": key, "text": text}, record)
            c.require(record["status"] == "ok" and record["space"].startswith("apple-dual:en:")
                      and all(len(record[k]) == 512 for k in ("contextual", "sentence")), "Missing/wrong English embeddings")
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
            process.stdout.close()
