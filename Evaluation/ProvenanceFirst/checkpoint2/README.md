# Checkpoint 2 — frozen-model comparison

Authorized by the user's “Carry on with next checkpoint” on 17 September 2026.
Checkpoint 1 remains immutable; its historical `checkpoint2Allowed: false` records
the earlier review stop, not the current authorization.

This folder records the Mac-only comparison of A (D3), B (D3 plus evidence
suggestions), and C (conservative project proposals). No app integration, training,
downloads, paid APIs, or personal-vault access. The connected phone is available
only if a specific compatibility check proves necessary.

## Preflight, before benchmark predictions

Verify checkpoint 1, the frozen seed-29 weights, tokenizer, TF-IDF and combiner.
Use the first 16 historical P2 control pairs in their saved order, the same control
set used by the prior C2 numerical check. These are exposed numerical controls,
not fresh quality data. Recompute embeddings for their source texts and compare
against saved vectors (maximum absolute component error <= 0.00001); require the
exact production embedding-space identifier. Compare original-model directional
and combined scores with saved outputs (maximum absolute error <= 0.00001) and
require unchanged decisions at the production threshold. Frozen feature parity
using saved embeddings must remain within 1e-12.

Use the original local PyTorch/MPS seed-29 model for this offline policy screen.
It is not a new qualification of the shipped Core ML FP16 runtime. The known FP16
parity concern remains open. Stop if controls fail; do not loosen tolerances,
substitute embeddings, download assets, or change thresholds to continue.

The initial import attempt hit the previously documented macOS 27 SciPy 1.15.3
PROPACK loader failure, before inference. Reuse the existing isolated SciPy 1.17.1
override from `Evaluation/iOS27/precision/build/python-overrides` read-only. Hash
its files and record its runtime version. No installation, download, mutation of
the old environment, or copying of dependencies is needed. Preserve the failed
attempt under `runs/failures/`; numerical controls still have to pass.

## Resource and resume boundary

The original shared 4 GiB new-write cap and 10 GiB free-space reserve still apply,
including checkpoint-1 simulator growth. Models are reused in place, not copied.
New scripts live in a subdirectory so the checkpoint-1 code freeze is unchanged.
Each completed control unit is immutable and hash-bound to inputs, code, runtime,
and assets. SIGINT/SIGTERM or the pause command stops at a bounded unit boundary.
Resuming verifies receipts before skipping work; it does not overwrite results.

```sh
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" -B scripts/provenance-first/checkpoint2/run.py preflight
python3 -B scripts/provenance-first/checkpoint2/run.py pause
```

Full benchmark policy details and selection must be recorded and frozen before
development predictions; evaluation inference is prohibited before a development
selection receipt. Stop for user review after the checkpoint report.
