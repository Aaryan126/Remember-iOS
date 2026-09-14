# Remember matcher screening

This experiment investigates why the earlier MiniLM diagnostic underperformed the six-feature classifier. It does not change Remember, open the final test split, or deploy a model.

**Both stages are complete and stopped for user review.** See [Stage 2 results and recommendation](checkpoints/stage-2.md). Neither family passed every confirmation seed; the hybrid remains a promising research lead, not an approved replacement.

- [Plan](PLAN.md): two stages, with explicit user review between them.
- [Current checkpoint and resume instructions](RESUME.md).
- [Completed Stage 1 results and recommendation](checkpoints/stage-1.md).
- [Authorized Stage 2 execution plan](STAGE2_PLAN.md): completed four-family screen and repeated-seed confirmation.
- [Performance-only continuation](checkpoints/runtime-continuation.md): separately frozen faster storage traversal; original model/data/evaluation settings retained.
- [Completed outer screen](checkpoints/outer-screen.md): historical checkpoint after36 comparisons and C3/D3 selection; final confirmation is now complete.
- [Approved checkpoint headroom](CHECKPOINT_HEADROOM.md): temporary4.5 GiB allowance; the final4 GiB cap and10 GiB reserve passed. Preparation01 failed before training; the preserved [clean retry](CHECKPOINT_HEADROOM_RETRY.md) completed with `screening2_headroom_v2.py`.
- `runs/audit-attempt-01/`: frozen Stage 1 settings, evidence, predictions and integrity records.
- `reviews/`: executing-agent pair-first and contextual assessments. These are not independent blind annotations.

## Reproduce or inspect

Use the existing `RememberMatcherFeasibility/v1/venv` Python, not system Python. No additional installation is required. Run commands from the repository root:

```sh
python -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q
python -m unittest discover -s scripts -p 'test_organization*.py' -q
python scripts/matcher-feasibility/screening.py verify --run Evaluation/MatcherScreening/runs/audit-attempt-01
```

The Stage 1 driver refuses Stage 2 execution. The separately authorized Stage 2 driver is `screening2.py`, with run `runs/screen-attempt-01`. A completed run is immutable: resuming only verifies it, and never launches another stage. Source or data changes require a separately preserved new attempt.

For an unfinished run, `pause` requests a cooperative stop; wait for the worker to exit before closing the laptop. `run --resume` verifies frozen bindings and reuses completed records. Recovery preserves model, optimizer, random state and the next step. Unexpected interruption can repeat unsaved work, and MPS continuation is not guaranteed bit-for-bit. See RESUME.md for commands.

## Evidence layout

| File or directory | Meaning |
| --- | --- |
| `manifest.json`, `source-snapshots/` | Frozen implementation/data hashes and Stage 1 authorization boundary |
| `folds.json` | Three training-library outer folds, each with separate fitting, calibration and evaluation libraries |
| `stage2-trials.json` | Twelve proposed configurations across four families; not authorized to execute |
| `ablations/` | Four feature comparisons per fold, fitted transforms, probabilities and calibrated decisions |
| `ablation-summary.json` | Pooled out-of-fold results; not the original development score |
| `review/`, `review-summary.json` | Sixty pair-first/context-second reviews, release chronology and limitations |
| `sanity/` | Tiny learning test and live pause/resume receipts; not generalization evidence |
| `diagnostics/` | Original trained candidate on training pairs, development reproduction and token/padding checks |
| `validation.json`, `audit.json` | Regression/environment checks and independent counting/integrity audit |
| `retention/` | Authorized deletion receipts for superseded new recovery blobs only |
| `report.json`, `complete.json` | Checkpoint verdict and hashes of retained evidence |

Large new weights/recovery states reside in the existing feasibility workspace under `screening/audit-attempt-01/`. Only the newest two new recovery blobs are kept; final models and all receipts remain. Earlier feasibility runs are never cleaned up by this experiment. New screening storage is capped at 4 GiB with a 10 GiB free-space reserve.

## Interpretation boundaries

“Same” means two sources share at least one thread, not that their full sets of threads are identical. A source can bridge two threads; accepting both pairwise links must not cause a transitive merge of those threads.

Thresholds are selected on calibration libraries only. Failure to meet 95% precision with at least 30 accepted known pairs means abstention, not perfect precision. Ranking average precision is a separate diagnostic and cannot substitute for a safe operating point.

The dataset is agent-reviewed synthetic data. Development examples have already been inspected, and the 60-case review intentionally emphasizes errors. Neither this review nor the small library folds establish real-user reliability.

## Stage 2 records

`screen-attempt-01` uses a separate manifest and source freeze. Its copied proposal retains the historical `authorizedToExecute:false`; the new manifest records the user's explicit Stage 2 authorization without rewriting the old checkpoint.

- `features/`: fitting-library-only vocabularies and explicit pair features.
- `fits/`: saved fitting identities, lossless model exports or portable classifier parameters, epochs and resumptions.
- `predictions/`: per-pair neural scores, both text directions, and weight hashes.
- `screen/`: twelve configurations across three outer folds, with separate calibration/evaluation predictions.
- `screen-summary.json`, `selection.json`: pooled results and frozen choice of at most two families, saved before development confirmation.
- `confirmation/`: every required seed on the already-inspected development libraries; no lucky-seed selection.
- `audit.json`, `complete.json`: final independent checks and immutable completion, followed by a mandatory stop.

Stage 2 completed with the separately recorded fast-scan and headroom-retry continuations. Use `screening2_headroom_v2.py verify --run Evaluation/MatcherScreening/runs/screen-attempt-01` to verify all freezes and retained evidence. The original scripts and evidence remain unchanged. Use the existing venv Python, as described in RESUME.md. No further execution follows automatically.
