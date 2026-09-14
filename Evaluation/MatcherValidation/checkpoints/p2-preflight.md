# P2 saved stop: language routing needs an approved amendment

13 September 2026. P2 is **not complete**. No baseline or benchmark MiniLM fit was trained. The tiny pause/resume fixture ran successfully. All workers have exited; it is safe to close the laptop.

## Completed

- Built an isolated runner for the fixed baseline and three-seed D3 comparison, including family-held-out neural scoring, calibration-only selection, an evaluation-access gate, portable model checks and family bootstrap reporting.
- Preserved the frozen P0/P1 datasets, earlier experiment code/assets and production app.
- Passed 80 validation tests (including 16 new P2 tests), 183 existing feasibility tests and 22 organization tests: **285 total**.
- CPU dropout-fixture training resumed to exactly the same parameters and optimizer tensors as uninterrupted training.
- The MPS fixture paused after two effective batches, exited, restored in a separate process and finished all eight steps. No bitwise MPS claim is made. Two superseded tiny fixture recovery files were removed under the approved retention policy; the two newest verified states and removal receipts remain.
- Compiled the isolated Apple embedding probe. It checks installed assets and does not request downloads.
- Saved all 4,560 training pairs in the directional token cache, all 480 training-source embedding responses and the training feature matrix.

P2 runner/asset/settings manifest SHA-256:

`837d557d2b0b744060f1af3a8c672ecb59ea65a1523e0d42b8ee4ec4b529bfd5`

P1 remains verified at:

`a00ed7144b3fa443d6234ee39f4d0186c3d1cd1179f612108a5a7d4721f2ebcc`

## Why execution stopped

The actual command was:

```sh
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/p2.py run --pause-after-steps 2
```

It exited with code 1 at the baseline feature-coverage check:

`known training pairs missing compatible embeddings; no silent imputation/filtering`

This happened **before** fitting the baseline, not after a bad model score, and before the planned two-batch real-MiniLM recovery exercise. The separate small MPS recovery exercise had already passed.

Of 480 sources, 478 produced the expected English dual embeddings. Two known-membership fragments failed:

| Source | Exact fictional text | Automatic language | Sentence model for that language |
| --- | --- | --- | --- |
| hv02b-i08 | 62? lid won't shut | Dutch (`nl`) | Unavailable |
| hv05b-i18 | Nickel sample / Saturday / ask Olek? | Indonesian (`id`) | Unavailable |

Read-only Swift diagnostics passed the exact source strings through Apple's language recognizer and inspected installed embedding availability. Contextual assets for the detected languages were available, but the sentence model required by the production dual-embedding pipeline was not. The installed English sentence and contextual models were both available. A separate diagnostic using English explicitly produced finite, nonzero 512-dimensional representations for both notes, without downloads.

The two sources affect **36 known and two uncertain training pairs**. They must not be silently excluded, relabeled, assigned fake vectors, or used to weaken the prospective coverage gate. No calibration/evaluation model scores, baseline result or selection receipt exists. New evaluation data and the old final test were not opened by the runner.

## Recommended next action

Request approval for a **new recorded English-only experiment adapter** that selects English explicitly for all sources in this English benchmark, applied identically to the baseline and D3. Keep the embedding arithmetic, dataset, labels, splits, training settings and numerical gates unchanged. Preserve this automatic-language attempt and its failure evidence; do not overwrite its frozen scripts, manifest or cached representations. Do not change production language handling as part of this experiment.

This changes the representation-routing policy, so it should be recorded and approved before proceeding—not hidden inside a resume. It also limits the resulting experiment to English-hinted inputs, rather than validating production automatic language identification on fragments.

Estimate for the adapter, regression/parity checks and a fresh coverage pass: **30–60 minutes**. Remaining full P2 estimate is still **8–16 active hours**, provisional because actual MiniLM training throughput has not yet been measured. Re-estimate after the first real fit's recovery exercise. Mac only; no phone needed.

## Saved resources and verification

At the stop, combined new validation data/scripts/external artifacts occupied 128,946,773 bytes (about123MiB), with 34,102,353,920 bytes (about31.8GiB) free. The original conservative peak estimate was about2.99GiB additional; recompute combined retained-plus-temporary storage for any new attempt, including this preserved attempt. Keep the4GiB cap and10GiB reserve.

`p2.py verify` passed the frozen source/environment/model/P1 checks and correctly reported incomplete with zero benchmark fits. The pause fixture states remain readable. `runs/validation-01/failures/` records the failed coverage check. See [RESUME](../RESUME.md) before continuing.
