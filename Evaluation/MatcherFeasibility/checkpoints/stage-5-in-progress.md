# Stage 5 live checkpoint

**Historical progress note. Stage5 is now complete and stopped; see [the final checkpoint](stage-5.md).** All nine candidates were evaluated, none qualified, and the test release remained sealed. The audit passed. All76 recovery snapshots and nine epoch models are retained; no cleanup occurred. The original estimates and intermediate observations below are preserved as history, not current status.

11 September 2026. User authorized Mac-only specialist training/evaluation with pause/resume. **Stage 6 is not authorized.** Active run: `runs/stage-5-attempt-01`.

## Preparation

- Stage 1–4 checkpoint chain and original model assets verified; isolated 37-package environment check passed.
- Mac has 24 GiB physical memory, about 36 GiB free disk at preflight; MPS is available.
- New Stage 5 implementation is isolated from Remember and prior frozen stages.
- The 14 new regression tests pass, including CPU optimizer/dropout-RNG continuation, safe tensor/state roundtrip, tamper rejection, weighted gradient accumulation, split sealing and gate boundary arithmetic.
- Source/configuration freeze: `runs/stage-5-attempt-01/manifest.json` and `source-snapshots/`.

## Planned computation

18 training libraries / 360 fictional sources. Supervised loss uses 2,827 known unordered pairs, both orientations with half weight: 5,654 directional examples per epoch. Ambiguous pairs are excluded from supervised loss but retained in evaluation coverage. Three seeds (17, 29, 41), at most three epochs each, AdamW 2e-5 / weight decay0.01, effective batch16 and initial microbatch8. Weighted loss normalizes across the entire effective batch. The frozen 512-token maximum uses longest-first truncation; dynamic padding rounds the effective batch length to32 to avoid wasting Mac work on padding.

Each epoch's development predictions and threshold selection are retained. A winner is chosen only from the nine epoch candidates using the frozen development rules. Only after `selection.json` binds the winning weights/threshold and unchanged baseline may test inputs and labels be read. No qualifying development model means no heldout release and no Stage 6 recommendation.

## Recovery

The first live run intentionally paused after two optimizer steps (32 directional examples). It saved a full checkpoint and reported `paused` / `safeToCloseLaptop: true`. Resume then restored global step2 and nextOffset32 with model, optimizer, CPU/MPS/Python/NumPy random states; training subsequently advanced past step50. This is a verified live cooperative pause/resume, not a forced-sleep or crash test. Checkpoints are compressed, written atomically and hashed; candidate models are exported separately as safe tensors.

The initial no-optimizer checkpoint was 83.7 MB; the first full recovery checkpoint was 274.4 MB and took about10.2seconds to save. This is smaller than the initial storage allowance. Training/development token caches are complete: 6,840 / 2,280 directional inputs; maximum pre-truncation lengths242 /177; neither split needed truncation at512. Supervised training still uses only the5,654 known directional examples.

An optional retention question was sent to the user: two latest recovery checkpoints per seed plus permanent epoch models/metrics/history, versus preserving every full recovery state. **Until an explicit answer, preserve all.** No recovery cleanup is authorized by this note. The runner supports a separately recorded user-authorized policy without modifying the frozen plan. Full retention could consume roughly 25–30 GB; low disk causes a saved pause, not automatic deletion.

Say **“pause”** and wait for confirmation. Resume commands are in [RESUME.md](../RESUME.md). Unexpected closure may repeat work since the last valid saved checkpoint. No phone or paid compute is needed.

Original Stage 5 allowance: **6–12 active hours**. After the successful live resume, measured warm optimizer steps averaged about0.4seconds. **Revised remaining allowance: approximately1–2 active hours** for training, saved checkpoints, evaluations and auditing, excluding pauses or corrections. Stage 6, only if quality warrants it, remains **2–4 hours with the phone**. Stop at the Stage 5 report for user review.

## Progress update: final seed in progress

Seeds17 and29 have completed all three epochs and all six development evaluations. An independent reconstruction of development gold joins, metrics and exhaustive threshold selection agrees with all six reports: none qualifies at the frozen 95% precision / minimum30 accepted known-pair rule. Seed41 is running. This is an intermediate result, not the final verdict; heldout evaluation remains sealed until a qualifying development candidate is frozen.

The full matcher-feasibility test suite now passes **105 tests**, including four post-run diagnostic tests. The diagnostic precision ceiling is explicitly explanatory, not a replacement operating point. It excludes ambiguous pairs from the minimum-coverage count, requires the same-context class to win, and never splits tied probabilities to inflate precision.

Latest user-facing estimate during the first epoch of seed41: **15–30 minutes remaining** for Stage5, including its audit and report. This replaces the earlier runtime allowance for the current run only; pauses and any newly discovered correction add time. No recovery retention policy has been authorized and no checkpoint has been deleted.
