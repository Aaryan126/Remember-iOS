# Runtime compatibility qualification 01

Authorized separately by the user on 17 September 2026 after the checkpoint-2
preflight hold. Register and hash this protocol, executable code, selected control
IDs, runtime and input assets **before any new qualification inference**.

This is a Mac-only compatibility experiment. It is not quality evaluation, training,
threshold optimization, Core ML FP16 qualification or an app change. No provenance
benchmark content or labels enter this qualification. Keep the prior failed run,
report and strict vector-identity criterion unchanged.

## Fixed historical controls

Use the frozen P2 seed-29 evaluation predictions and their original inputs. Select
by historical scores only, never by newly recomputed scores or semantic labels:

1. Retain the original 16 numerical-control pair IDs.
2. Within **every** historical evaluation library, take the lowest score, the score
   closest to 0.5, and the highest score; break ties by ascending pair ID.
3. At each threshold `0.9804276486193665`, `0.99`, and `0.995`, take the six closest
   scores strictly below and six closest scores at/above the threshold. Break ties
   by ascending pair ID. Require six available on each side or stop as incomplete.
4. Deduplicate by pair ID; evaluate in ascending ID order. Preserve all selection
   reasons and report actual library/source/pair counts and threshold distances.

This is intentionally a boundary-enriched control set, not an unbiased quality
sample. It includes previously exposed controls; it is not a fresh held-out test.
Do not replace controls after seeing their new outputs.

## Computation

- Reuse the exact original weights/tokenizer, TF-IDF and seed-29 combiner, existing
  read-only SciPy compatibility override and original-model PyTorch/MPS inference.
- Recompute **all** selected source embeddings with the hash-verified English probe,
  including the original 17 sources. No old fresh-vector cache is substituted.
- Validate ID, exact source-text hash, model-space identifier, 512 dimensions per
  channel, finite/nonzero vectors, and original input/weight associations.
- Recompute neural scores in the existing bounded batches of at most eight pairs,
  both directions. Evaluate the frozen feature transform with saved and fresh
  embeddings. Measure final-score differences from the historical P2 predictions.
- Save each embedding and each pair's neural result durably. Cancellation stops at
  a unit boundary; resume verifies manifests, hashes, filenames and identities before
  skipping completed work. Test a real one-unit pause/resume before the full run.

## Acceptance, fixed before inference

All criteria must pass; failures are reported, never rounded into a pass:

| Criterion | Required |
|---|---:|
| Asset, text, model-space and runtime bindings | Exact match to registered inputs |
| Saved-vector feature parity | Maximum absolute difference <= 1e-12 |
| Fresh-versus-saved feature values | Maximum absolute difference <= 0.0001 |
| Old/new vector cosine, each channel and source | >= 0.99999 |
| Relative vector-norm difference, each channel and source | <= 0.001 |
| Neural directional probability difference | <= 0.00001 |
| Final combined D3-score difference | <= 0.00001 |
| Changed decisions at **each of all three** thresholds | Zero |
| Missing, invalid, skipped or substituted controls | Zero |

Unlike the previous check, maximum vector-component error is a reported diagnostic,
not an identity gate. The new cosine/norm/feature bounds reject materially different
representations; the original neural and final-score tolerances remain unchanged.
These are engineering equivalence bounds, not statistical calibration guarantees.
They were chosen after observing the earlier control drift; disclose that exposure.

Passing only qualifies this recorded Mac runtime for the planned **offline** A/B/C
comparison. It does not declare the old vector-identity preflight passed. Failing
leaves that comparison blocked; stop and report, with no further acceptance changes
or automatic search for another runtime/model. Numerical failure does not itself
demonstrate poorer semantic quality. No policy tuning or evaluation-label access.

## Resources, duration and handoff

Reuse existing assets in place. Continue the original shared <=4 GiB conservative
growth limit and >=10 GiB free-space reserve; no automatic deletion or downloads.
Expected work: 1–2 active hours. Publish raw controls, per-library and threshold
summaries, runtime, resource observations, verification and pause proof. All logs,
generated inputs and inference units stay under the existing ignored `runs/` tree.
The acceptance report states separately whether checkpoint 2 remains blocked.
