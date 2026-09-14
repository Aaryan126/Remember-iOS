# P2 execution protocol

Authorized by the user's “cary on” after the P1 checkpoint. The frozen prospective plan and contract are unchanged. P0/P1 sources and all earlier experiment assets remain immutable. New implementation is confined to `p2*.py`, `test_p2.py` and `P2EmbeddingProbe.swift`; the run is `runs/validation-01`, with large artifacts in the existing local feasibility workspace under `validation/validation-01`.

## Fixed comparison

Refit the six-feature C10 balanced three-class logistic control on new training data only. Preserve same-class argmax eligibility. Fit D3 for seeds 17/29/41, each with three family-held-out neural fits and one final full-training fit. Use the previously pinned local MiniLM L12H384 backbone, binary unweighted cross-entropy, three epochs, effective batch16/microbatch8, head LR0.001, full-backbone LR0.000005, AdamW weight decay0.01, 10% warmup and length512. Train both pair directions; average probabilities before applying the clipped logit for the C1 logistic combiner.

TF-IDF and all scalers fit on training only. The combiner uses ten original features and out-of-fold neural logits; no in-sample replacement. Only training and calibration source/gold loaders are available before the selection receipt. Every seed and the baseline, their portable transforms and exact thresholds, all final/inner weights and the P1 hash are bound before model-evaluation access. Missing qualifying calibration thresholds mean abstention, not a default threshold. All three seeds are reported with the unchanged gates, including failed/inconclusive comparisons. No search or tuning on evaluation.

Apple representations use the unchanged production embedding arithmetic, extracted into a standalone Mac probe. The probe checks installed assets before calling it, preventing asset download requests. Missing or incompatible known training embeddings stop fitting rather than silently impute or exclude data. Missing evaluation scores are reported and fail complete-coverage gates. These are Mac representations; phone parity is deferred.

## Persistence and resources

First pass CPU regression tests and a separate-process MPS pause/resume exercise on a small dropout fixture using the actual training/checkpoint engine. The fixture is not benchmark training. Before long fits, verify local assets and estimate twelve final FP32 exports plus two retained AdamW recovery states, one temporary recovery write and384MiB representation/metadata headroom.

Save full model, optimizer, Python/NumPy/Torch/MPS RNG states, epoch, next data offset and step at most every50 steps, at epoch boundaries and cooperative pause. On pause, finish the current effective batch, save/reload/verify its state, and exit. The driver must confirm worker exit before saying the laptop can close. Unexpected closure can repeat unsaved work. Do not promise bitwise MPS equivalence.

Retain all twelve final fit exports and the latest two verified recovery states globally in this run. Before removing older states, verify the two replacements and the exact superseded file hash; preserve an immutable removal receipt. This is the rolling retention explicitly included in the approved plan, not permission to delete earlier experiments. Combined new validation data/scripts/external assets, including pending writes, must stay within4GiB, with10GiB free. The old4.5GiB exception does not apply. A worker lock prevents simultaneous writers.

## Reporting and stopping

Use the frozen numerical policy for calibration/evaluation. Report per-seed precision, macro-library recall, average precision, false-related/false-unrelated joins, accepted uncertainty, missing coverage and library-level metrics. Jointly resample the six evaluation families2,000 times with seed1729; distinguish undefined precision samples. Intervals are descriptive, not a population guarantee. Retain complete pair predictions for later audit.

For an additional descriptive challenge/routine breakdown, mark a pair challenging if either source has at most eight whitespace-separated words, the existing identifier-conflict feature is set, or its gold relation is related-but-different. Routine is the complement, not a claim that those examples are easy or representative. These fixed slices never select thresholds or affect fits; their synthetic prevalence is not production prevalence.

P1 reference histories stay frozen; do not claim production replay or integration. Stop after P2 with a go/no-go report. No phone, app integration, old final-test access, downloads or Git mutations are authorized by this stage.
