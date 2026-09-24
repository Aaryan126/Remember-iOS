# Broader runtime qualification complete — numerical gate failed

17 September 2026. The approved compatibility experiment completed. **The A/B/C
provenance benchmark remains blocked under the registered acceptance rule.**
No policy was tuned, model replaced, benchmark prediction made, or app changed.

## Result in plain language

The updated Mac produced the same threshold decisions on all tested pairs, including
the controls closest to the three proposed thresholds. However, six final scores
differed from their historical values by more than the strict numerical tolerance.
All six were around 0.5, far below the automatic-placement thresholds near 0.98–1.0.

This is evidence of **small numerical differences with unchanged decisions on
these controls**, not evidence that D3's semantic quality improved or deteriorated.
It is also not proof that every possible input would give the same decision. The
registered rule required every numerical criterion to pass, so the result is a
failure even though the observed decision agreement is reassuring.

## What was tested

The fixed selection contains **88 historical P2 seed-29 pairs from all 12 evaluation
libraries**, with **108 distinct source texts**:

- The original 16 numerical controls.
- Each library's lowest, nearest-to-0.5, and highest historical score.
- Six scores below and six at/above each of the three prespecified thresholds.

Selection used historical scores, not new outputs or semantic labels. The protocol,
code, selected IDs, source/reference files, model assets and runtime were hash-bound
before the first new embedding. Manifest SHA-256:
`065a08129159e84f181316f764c3fb370cb4c4ae8cbc68d49591a3f23391708e`.

Every selected embedding was recomputed; the earlier 17-source fresh-vector cache
was not substituted. The same frozen seed-29 original model ran locally on MPS,
in both text directions. These are exposed, correlated, boundary-enriched controls,
not 88 independent quality tests or a new benchmark accuracy estimate.

## Numerical results

| Check | Observed | Registered requirement | Result |
|---|---:|---:|---|
| Model/tokenizer/transforms/space identity | Matched | Exact bindings | Pass |
| Saved-vector feature parity | 0 difference | <= 1e-12 | Pass |
| Largest fresh-feature difference | 0.00005411 | <= 0.0001 | Pass |
| Lowest old/new vector cosine | 0.9999989972 | >= 0.99999 | Pass |
| Largest relative vector-norm difference | 0.00000005194 | <= 0.001 | Pass |
| Largest neural directional-output difference | 0.0000004172 | <= 0.00001 | Pass |
| Largest final D3-score difference | **0.00007928** | <= 0.00001 | **Fail: 6/88 pairs** |
| Changed decisions across three thresholds | **0/264 checks** | Zero | Pass |

The maximum raw vector-component difference was 0.00030881; 16/108 source vectors
exceeded the earlier 0.00001 component bound. This was a reported diagnostic in
the new approved protocol, not its acceptance rule. The original vector-identity
preflight remains failed and unchanged.

| Threshold | Historically at/above | Below | Changed | Closest historical distance below / above |
|---|---:|---:|---:|---:|
| 0.9804276486 (production) | 44 | 44 | 0 | 0.00026807 / 0.00004726 |
| 0.99 | 32 | 56 | 0 | 0.00024284 / 0.00012875 |
| 0.995 | 19 | 69 | 0 | 0.00004890 / 0.00001907 |

The 264 checks reuse the same 88 pairs at three cutoffs; they are not 264
independent samples. These are pair-score eligibility decisions, not full
corroborated thread-placement or user-experience outcomes.

All six numerical failures came from the prespecified per-library middle-score
controls; none came from the near-threshold selection. Five of these six had
exactly unchanged neural outputs, so their final-score drift arose from the fresh
embedding-derived features rather than changed neural predictions. The sixth also
had a small neural difference. Raw per-pair values, all failures, vector statistics,
selection reasons and library counts are saved in `result.json` and `selection.json`.

## Next decision: explicitly establish a current-runtime reference

Recommended next step is **not another round of numerical-tolerance adjustment**.
Instead, approve a current-Mac-runtime D3 reference for the planned offline A/B/C
comparison, keeping historical P2 numbers separately labeled as historical.

This would preserve the same weights, tokenizer, feature transforms and placement
thresholds; it changes what we claim about reproducibility across runtimes. A, B
and C would share the same frozen current-runtime source embeddings and pair scores.
Any measured difference between variants would then come from their policies, not
from giving them different representations. Cache generation remains label-free;
online policy callbacks must still receive only the observed prefix.

This requires an explicit amendment to the compatibility prerequisite, because
the old and new runtime outputs have **not** met the registered numerical-equivalence
rule. It must not relabel either failed compatibility result as a pass. No such
amendment or benchmark execution was performed in this qualification.

If approved, the next work is to freeze the runtime-specific comparison contract,
implement and verify the A/B/C replay adapters, run development selection, freeze
the chosen configuration, then evaluate once and report the original quality gates.
Estimated remaining work: **10–16 active hours, Mac only**, subject to the existing
resource limits. No additional model training or compatibility-model search is
proposed. This remains an offline experiment; iPhone/Core ML FP16 qualification
and app integration require their own checks later.

## Saved progress, validation and limits

- All 108 embedding receipts and 88 neural receipts are complete and hash-verified.
- Actual one-unit pause/resume preserved the first receipt's hash and nanosecond
  mtime; see `pause-proof.json`.
- 55 checkpoint-1 regression tests and 31 checkpoint-2 tests passed: **86 total**.
  The checkpoint-2 suite also passed in the actual matcher virtual environment.
- `git diff --check` passed. No Git state was changed.
- Shared conservative growth stayed below 4 GiB, with over 38 GiB free. This run's
  generated artifacts use about 2.8 MiB; existing model assets were not copied.
- No phone, personal memories, network/model downloads, paid APIs, training,
  production migrations or app changes were used.

Commands actually run from the repository root:

```sh
python3 -B -m unittest discover -s scripts/provenance-first -p 'test_*.py'
python3 -B -m unittest discover -s scripts/provenance-first/checkpoint2 -p 'test_*.py'
python3 -B scripts/provenance-first/checkpoint2/qualify_runtime.py verify
python3 -B scripts/provenance-first/checkpoint.py resources
git diff --check
```

With the existing matcher virtual environment's Python:

```sh
python -B scripts/provenance-first/checkpoint2/qualify_runtime.py prepare
python -B scripts/provenance-first/checkpoint2/qualify_runtime.py run --max-units 1
python3 -B scripts/provenance-first/checkpoint2/run.py pause
python -B scripts/provenance-first/checkpoint2/qualify_runtime.py run --resume
python -B -m unittest discover -s scripts/provenance-first/checkpoint2 -p 'test_*.py'
python -B scripts/provenance-first/checkpoint2/qualify_runtime.py run
```

The completed `run` exits with status **2** to report the failed numerical criteria;
that is an expected recorded result, not an ignored infrastructure exception.
The last command verifies cached work and regenerates analysis without new model
inference; immutable publication requires the same result bytes. Full paths and
pause/resume instructions are in [RESUME.md](RESUME.md).
