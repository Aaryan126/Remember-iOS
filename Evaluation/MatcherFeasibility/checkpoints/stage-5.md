# Stage 5 checkpoint — experiment complete; model does not qualify

11 September 2026. Run: `runs/stage-5-attempt-01`. **Stopped at this checkpoint. Stage 6 has not started and is not recommended for these candidates.** All training and evaluation workers have exited. The laptop can be closed; no phone is needed.

## Outcome

All nine planned MiniLM candidates were trained and evaluated: three random seeds × three epochs. **None reached 95% same-context precision while accepting at least 30 known development pairs.** The independent audit exhaustively recalculated the thresholds and confirmed that no qualifying operating point was missed.

The existing simple baseline remains the preferred experimental comparator. It was not replaced in Remember; this entire experiment is isolated from the production app. This is a completed feasibility experiment with a **quality no-go**, not an incomplete training job or proof that all small neural matchers are unsuitable.

| Development comparison | Correct accepted pairs | Incorrect accepted pairs | Precision | Recall | Macro-library recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Frozen simple baseline, approved development threshold | 73 | 3 | 96.05% | 29.80% | 29.94% |
| Highest-precision neural diagnostic, seed17 / epoch3 | 48 | 3 | 94.12% | 19.59% | 19.59% |

The neural row is a **post-run diagnostic**, not a selected model or approved threshold. It shows the best precision found across the nine candidates and all observed thresholds that accepted at least30 known pairs. It still misses the gate and finds fewer correct matches than the baseline for the same three mistakes. Both rows use the same six development libraries; neither is a new heldout-test result.

Because no development candidate qualified, **test inputs/labels were not released for Stage5 evaluation**, no test predictions were produced, and the test release remains available for a future development-frozen candidate. Frozen-byte integrity hashing is not model evaluation; Stage1 annotation necessarily examined test data before the experiment.

## What was actually trained and tested

- Backbone: pinned `microsoft/MiniLM-L12-H384-uncased`, with a new three-class head: same context, related context, unrelated. All model parameters were fine-tuned locally using PyTorch/MPS. This is a pair classifier, not generative local reasoning.
- Training: 18 fictional libraries /360 sources; 2,827 known unordered pairs (903 same,212 related,1,712 unrelated), presented in both orientations. The593 ambiguous pairs were excluded from loss. Each epoch used5,654 directional examples,354 optimizer steps, effective batch16, microbatch8. No memory-driven microbatch reduction was needed.
- Development: six separate libraries /120 sources;1,140 unordered pairs per candidate, comprising918 known and222 ambiguous pairs. Both directional probability vectors were saved and averaged. Nine evaluations produced10,260 pair predictions /20,520 directional predictions with no missing cases.
- Split boundaries, labels, hyperparameters and selection rules remained frozen. The tokenizer maximum was512; longest observed training/development pairs were242/177 tokens, so neither split required truncation.
- The baseline combines existing Mac embeddings with lexical/number/length features and a logistic classifier. Its1,140 development feature vectors and probability outputs were independently reproduced from frozen state without refitting.
- This tests final-library pair relationships, not chronological thread attachment, transitive merges, provenance correctness, or the end-to-end River experience. No new Core ML conversion or phone measurement was performed in Stage5.

## All candidate diagnostics

For each candidate, this table reports its highest development precision subject to at least30 accepted known pairs. It deliberately does **not** relax the official gate or select a replacement winner.

| Seed | Epoch | Best diagnostic precision | Accepted known pairs | Recall |
| --- | ---: | ---: | ---: | ---: |
| 17 | 1 | 90.99% | 111 | 41.22% |
| 17 | 2 | 65.87% | 252 | 67.76% |
| 17 | 3 | 94.12% | 51 | 19.59% |
| 29 | 1 | 74.63% | 67 | 20.41% |
| 29 | 2 | 78.57% | 56 | 17.96% |
| 29 | 3 | 69.39% | 49 | 13.88% |
| 41 | 1 | 80.00% | 80 | 26.12% |
| 41 | 2 | 67.48% | 163 | 44.90% |
| 41 | 3 | 69.23% | 65 | 18.37% |

Official selection is `null` for every candidate. Consequently the approved automation policy accepts no neural pairs and its precision is **undefined**, not zero and not100%. The diagnostic table prevents that abstention result from being misread as an absence of learned signal.

Training loss fell substantially for every seed (about0.78 in epoch1 to0.15–0.22 in epoch3), but this did not yield a robust development operating point. Results vary markedly by seed and library. This is consistent with inadequate generalization on this small, synthetic pilot; it does not establish a single root cause.

## Concrete errors and interpretation

At the best diagnostic point, the model confidently joined a repair note for accession **MC-71** to a correction explicitly for **MC-72**, and also joined a different **MC-88** object to that MC-72 correction. Another false positive joined **LO-ES** and **LO-FR** release notes: related undertakings in the annotated context, not one shared thread. Meanwhile, two notes explicitly referring to the same **AW-S** studio project fell just below the very high acceptance threshold.

These examples suggest that distinguishing a continuing project/object identity from shared subject matter deserves particular attention. They are not grounds to change labels or hard-code every differing identifier as unrelated: bridges, renamed projects and genuine aliases must still work. Correct and incorrect pairs can have almost identical high scores; a score around0.983 must not be presented as a calibrated98.3% guarantee.

Full fictional examples, per-library counts and confusion matrices are in [stage-5-diagnostics.json](stage-5-diagnostics.json). The diagnostic maximizes over development observations, so it is optimistic by construction and is not an unbiased quality estimate. Only six agent-reviewed synthetic development libraries were used. No heldout comparative bootstrap or quality-pass claim is available because test evaluation was correctly skipped.

## Saved state and pause verification

The live pause/resume exercise stopped at step2 / nextOffset32, saved model, optimizer and CPU/MPS/Python/NumPy random states, then resumed from that position and continued. Recovery snapshots were also saved every50 steps and at epoch boundaries. CPU next-step optimizer/dropout replay was regression-tested; exact bitwise MPS replay and abrupt laptop sleep were not established.

All **76 full recovery snapshots**, all nine epoch models, token caches, per-pair outputs and logs are retained. **Nothing was deleted.** Large Stage5 assets occupy21,874,982,681 logical bytes (~21.87GB /20.37GiB): recovery20.56GB, candidate models1.20GB, tokens112.07MB. These are Mac experiment assets, not app size. Roughly12.7GiB disk space was free after the run; availability can change with other Mac activity. Optional cleanup requires separate explicit approval.

Large assets: `~/Library/Application Support/RememberMatcherFeasibility/v1/stage5/stage-5-attempt-01/`.

Evidence: `runs/stage-5-attempt-01/{manifest.json,source-snapshots/,tokens/,recovery/,resumptions/,epochs/,evaluations/,selection.json,quality-report.json,complete.json,logs/}`. [stage-5.json](stage-5.json) binds this checkpoint's audit/diagnostic sources and reports. Completion SHA256: `316a288748307c4e1c8d4c4138e185c334ee42ed7573147be389cb577f954731`.

## Validation actually run

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q
python3 -m unittest discover -s scripts -p 'test_organization*.py' -q
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/audit_stage5.py --run Evaluation/MatcherFeasibility/runs/stage-5-attempt-01 --output Evaluation/MatcherFeasibility/checkpoints/stage-5-audit.json
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage5_diagnostics.py --run Evaluation/MatcherFeasibility/runs/stage-5-attempt-01 --output Evaluation/MatcherFeasibility/checkpoints/stage-5-diagnostics.json
```

Results: **105 feasibility tests passed;22 existing organization/audio tests passed**. The independent audit passed and verified10,374 run files,96 external files, all nine development threshold searches, prediction/gold joins, baseline binding, training coverage, preserved recovery files and the live pause receipt. The frozen Stage1–4 chain and historical/production source bindings remain intact. Audit outputs above already exist: use a new output path for any repeat audit, never overwrite them.

Read-only completion verification:

```sh
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage5.py verify --run Evaluation/MatcherFeasibility/runs/stage-5-attempt-01
```

## Recommendation and next checkpoint

**Do not proceed directly to Stage6 with these weights. Keep the baseline and preserve this negative result.** Stage5 remaining work is zero. Stage6 is conditional, not automatically the next useful action.

Recommended next action, only with user approval: a **2–4-hour Mac-only corrective analysis** of identity/granularity errors, score separation and training-versus-development behavior. Produce a new, bounded experiment proposal before changing frozen data or training settings. A follow-up pilot could compare a smaller/frozen-backbone classifier and a hybrid that adds the matcher score to embedding/lexical features, while retaining explicit abstention. Targeted hard negatives and more varied training examples may help; improvement is not guaranteed. Do not simply lower the precision gate or promote the best diagnostic candidate.

Implementing and validating the resulting follow-up pilot would provisionally need a further **4–8 active hours**, depending on approved data work. These are new corrective-work estimates, not work started by this checkpoint. If a future candidate clears development and untouched-test gates, Stage6 remains approximately **2–4 hours with the connected, unlocked iPhone** for conversion parity, threshold-decision agreement and device measurements. There is no reliable fixed overall completion time until a candidate clears the quality gate.
