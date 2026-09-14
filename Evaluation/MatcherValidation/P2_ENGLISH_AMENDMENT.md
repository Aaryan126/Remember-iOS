# P2 attempt 02: explicit English

Authorized by the user's “Carry on with ur recoemmednation” after the automatic-language coverage failure. This amendment is prospective: no benchmark baseline/neural fits or held-out model evaluation completed in attempt 01.

## One change

The fictional benchmark is English-only. Its isolated Apple embedding provider will select `NLLanguage.english` for every source in training, calibration and evaluation, identically for baseline and hybrid. Automatic detection had routed two short training sources to unavailable Dutch/Indonesian sentence models. No source is removed, relabeled, zero-filled or silently skipped.

The adapter changes exactly one language-selection guard in the extracted provider, not the app. Chunking, token pooling, normalization, feature construction, seeds, splits, training, thresholds, qualification gates and pause/recovery behavior remain frozen. The existing offline probe checks installed assets before embedding; downloads remain disabled.

## Evidence and safeguards

- Preserve all attempt-01 files with hash inventories in the new manifest; bind the original frozen implementation and all new adapter sources.
- Write only to `runs/validation-02` and the feasibility workspace's `validation/validation-02` for new experiment evidence/models.
- Before fitting, require exact equality for previously available training embeddings, restored valid 512-dimensional unit vectors for unavailable ones, and complete training/calibration pair features. Calibration checks measure coverage only, not model selection. Evaluation remains inaccessible until all model/threshold choices are frozen.
- Re-run the cross-process MPS pause exercise and a two-step real-model checkpoint before continuing long fits. `pause` is a request; wait for saved-state exit before closing the laptop.
- Keep the combined new-validation storage below 4 GiB including pending writes, preserving at least 10 GiB free. Retain all final exports and the latest two verified recovery states in attempt 02; earlier attempts are never pruned.
- Stop after P2 for user review. No P3, phone work, production integration or old-test access is authorized here.

## Interpretation

Results apply to an English-configured pipeline, not automatic language routing or multilingual production traffic. The original failure remains a robustness finding. The English policy must be disclosed alongside candidate results; neither comparison may quietly use a different language policy.

## Commands

Use the existing feasibility Python environment with `scripts/matcher-validation/p2_english.py`: `prepare`, `exercise --pause-after-steps 2`, `exercise --resume`, `run --pause-after-steps 2`, then `run --resume`. For user-requested pauses use `pause`; inspect `status`/`verify` only when the worker has stopped. The original `p2.py` remains bound to attempt 01 and must not be used to resume attempt 02.
