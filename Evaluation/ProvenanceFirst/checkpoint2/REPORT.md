# Checkpoint 2 preflight hold — not a quality result

17 September 2026. Checkpoint 2 was authorized and started. **The A/B/C benchmark
comparison is not complete and has not begun inference.** Its compatibility gate
stopped execution before any development or evaluation predictions.

## What was completed

- Verified the unchanged checkpoint-1 freeze and all saved native ledger receipts.
- Added isolated, immutable, hash-bound control receipts and a pause/resume runner.
- Verified the local seed-29 model/tokenizer assets, production combiner, TF-IDF,
  threshold, and exact Apple embedding-space identifier. No models were downloaded.
- Reused the existing isolated SciPy 1.17.1 compatibility copy read-only. The first
  attempt failed to import SciPy 1.15.3 on macOS 27; that failure is preserved.
  The old Python environment was not modified or replaced.
- Exercised an actual one-unit stop, pause request and resume. The first receipt's
  SHA-256 and nanosecond mtime remained unchanged (`pause-proof.json`).
- Diagnosed the failed numerical gate using only the already-exposed historical
  controls: 17 source texts forming 16 P2 seed-29 pairs. No provenance benchmark
  examples were used to tune or evaluate a policy.

## Results

| Check | Observed result |
|---|---:|
| Frozen weights, tokenizer, transforms and production threshold | Matched |
| Apple embedding identifier and both dimensions | Matched; 512 + 512 |
| Control sources exceeding the predeclared 0.00001 vector tolerance | 2 / 17 |
| Largest embedding-component difference | 0.00008964 — gate failed |
| Lowest old/new embedding cosine | 0.9999998567 |
| Largest resulting feature difference | 0.00000969 |
| Saved-vector feature implementation parity | Within 1e-12 |
| Largest original neural directional-output difference | 0 — exact match |
| Largest combined D3-score difference | 0.00000590 — within 0.00001 |
| Changed production-threshold decisions | 0 / 16 |
| Positive automatic pair decisions among controls | 2 / 16 |
| Nearest control score to the production threshold | 0.01149 away |
| Checkpoint-1 Python regression tests | 55 passed |
| New checkpoint-2 control tests | 9 passed |

The vectors remain extremely close, and the checked final decisions did not change.
This is consistent with small runtime numerical drift, **not proof that the model
or organization quality got worse**. However, none of these 16 scores is especially
close to the threshold; this control set cannot establish broad decision stability.
Do not reinterpret 16/16 unchanged decisions as 100% organization accuracy.

The first resumed preflight stopped at a component difference of 0.00006432. A
separate diagnostic collected the remaining historical controls to explain the
failure; it cannot approve benchmark execution. `control-diagnostic.json` records
the full comparisons and explicitly leaves preflight failed. The original 0.00001
embedding tolerance was not relaxed, and no successful `preflight.json` was written.

## Recommended decision before continuing

Approve a **separate, predeclared runtime-compatibility qualification** using a
larger fixed historical control set, including pairs nearer the three prespecified
placement thresholds. It should judge feature/scorer stability and decision
agreement while explicitly reporting vector drift, rather than claiming identical
embeddings merely because their model identifier matches. This changes the
compatibility acceptance method, so it needs a deliberate decision; it must not
silently convert this failed run into a pass.

Estimated additional work: **1–2 active hours, Mac only**. Preserve this failed
attempt, register the new criteria before running that set, and do not change the
model, placement thresholds, benchmark labels or A/B/C quality gates. If that
qualification fails, report the incompatibility before choosing any replacement.
If it passes, resume the approved frozen-model comparison. Approximately **10–16
active hours** remain for implementing/running that comparison and its ledger
checks and report; this is not a short inference-only job.

The iPhone was not needed: this issue is in the Mac evaluation representation.
Device/Core ML FP16 qualification remains separate and unresolved. No app behavior,
personal memories, paid APIs, production schema or Git state was changed.

## Commands actually run

```sh
python3 -B -m unittest discover -s scripts/provenance-first -p 'test_*.py'
python3 -B -m unittest discover -s scripts/provenance-first/checkpoint2 -p 'test_*.py'
python3 -B scripts/provenance-first/checkpoint.py verify
python3 -B scripts/provenance-first/checkpoint.py verify-native
python3 -B scripts/provenance-first/checkpoint.py resources
git diff --check
```

These checks passed. With the existing matcher virtual environment's Python:

```sh
python -B scripts/provenance-first/checkpoint2/run.py preflight --max-units 1
python3 -B scripts/provenance-first/checkpoint2/run.py pause
python -B scripts/provenance-first/checkpoint2/run.py preflight --resume
python -B scripts/provenance-first/checkpoint2/diagnose_controls.py
```

The initial preflight import failed as described above. After the read-only SciPy
compatibility override, the bounded run stopped successfully after one unit;
resume failed the numerical gate as intended. The separate control diagnostic
completed without authorizing benchmark execution. Failures and receipts are
retained under ignored `runs/`, not deleted or rewritten.

Final measured conservative growth was approximately **3.28 GiB** against the
shared 4 GiB cap, with approximately **38.60 GiB free** against the 10 GiB reserve.
The worker has stopped; progress is saved and it is safe to close the laptop.
