# Runtime qualification: pause, resume and verification

Run commands from the repository root. This run is separate from the failed
checkpoint-2 preflight and must never overwrite its bindings or receipts.

The fixed protocol is [PROTOCOL.md](PROTOCOL.md). `selection.json` records the
88 selected historical pairs across 12 libraries and the selection reasons.
The generated manifest, embeddings and neural outputs live under the ignored
`../runs/runtime-qualification-01/` directory. No benchmark inputs, training,
downloads or phone are needed. Existing model assets are referenced in place.

## Pause

```sh
python3 -B scripts/provenance-first/checkpoint2/run.py pause
```

This writes the shared checkpoint-2 pause request. Wait for the running worker
to report its saved boundary and exit before closing the laptop. A source probe
has a 65-second timeout; neural work is bounded to at most eight pairs per batch.
The shared worker lock prevents overlapping writers. Do not start a second runner
to bypass it, and do not delete pause markers or incomplete receipts manually.

## Resume

```sh
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" -B \
  scripts/provenance-first/checkpoint2/qualify_runtime.py run --resume
```

Resume verifies the prior freeze, active runtime, qualification manifest and every
completed unit's hash, filename, source/weight identity and numerical shape before
moving the pause request into retained history. Completed units are not rewritten.
The original files `common.py`, `preflight.py`, `run.py`, and the new registered
qualification code/tests/protocol are hash-bound: do not edit them mid-run.

## Verification and final result

```sh
python3 -B scripts/provenance-first/checkpoint2/qualify_runtime.py verify
python3 -B -m unittest discover -s scripts/provenance-first/checkpoint2 -p 'test_*.py'
python3 -B scripts/provenance-first/checkpoint.py resources
```

`verify` checks saved-unit integrity and reports counts; it does **not** by itself
declare numerical compatibility or certify that the worker has stopped. To
recompute the completed analysis without new model inference, rerun the `run`
command after all 108 embedding and 88 neural receipts are present. Its immutable
publication check requires byte-identical `result.json`. Exit status 2 means the
compatibility criteria failed, not an infrastructure exception. Exit status 0 with
a paused message means only that work stopped safely, not that all controls passed.

The original shared 4 GiB conservative growth cap and 10 GiB free-space reserve
remain active. A limit stops work; it does not authorize deletion or budget changes.
No Git operations are part of this workflow.
