# Screening Stage 1 — completed; stopped for review

Run: `audit-attempt-01`. No Stage 2, final heldout evaluation, phone testing, or production integration was started. All workers exited. It is safe to close the laptop.

## Bottom line

The learning/input pipeline passed its checks, but neither the earlier neural model nor the simple baseline has demonstrated reliable transfer to new libraries. The evidence supports continuing the bounded four-family screen, not deploying a winner or simply increasing model size.

No Stage 1 rerun is required by the checks performed. One ambiguity-label policy concern should be acknowledged before continuing. It does not invalidate this run's known-pair comparisons, and no labels were changed.

## What was done

1. Verified the completed feasibility evidence, pinned local environment and existing model assets.
2. Reviewed 60 development pairs: ten per library, pair-first, then with the complete library and annotations.
3. Compared four feature sets across three fixed library-separated folds: nine fitting libraries, three calibration libraries and six evaluation libraries per fold. TF-IDF and scaling were fitted without seeing calibration/evaluation sources.
4. Checked original token caches, label/direction indexing, dynamic padding and reproduction of prior development predictions.
5. Trained a tiny 12-pair/24-direction sanity set, including a real saved pause and resume.
6. Evaluated the prior diagnostic MiniLM candidate on all 3,420 training pairs and compared it with its already-saved development results.
7. Independently recomputed counts and thresholds, verified integrity, and froze the proposed twelve Stage 2 configurations.

The final test split remains sealed. All data used was the existing fictional training/development dataset, not a personal memory vault.

## 1. Pipeline and tiny-learning checks

- All 5,654 known-label training directions matched the expected pair/label indexing.
- Re-tokenized 96 directions across training and development: exact cache matches.
- No training/development directions were truncated in the original cache.
- Dynamic versus full-length padding checks: largest probability difference `0.000003785`, below the frozen `0.002` tolerance.
- Reproduced twelve prior development pair outputs: maximum difference **0**.
- Tiny learning test passed at **160 optimizer steps**: all 24 directions correct and cross-entropy below 0.1 at both steps 150 and 160. This is memorization evidence, not generalization.
- Paused after step 2, exited, then restored model, optimizer and random state. Recovery receipts preserve this exercise even after the old step-2 blob was superseded.

These checks found no input-order, label-index or tested padding/reproduction fault. They do not prove the absence of every possible implementation issue.

## 2. Training versus development

The neural diagnostic is the previous **seed 17, epoch 3** candidate, not the tiny sanity model. It was chosen post hoc in the earlier study; it remains nonqualifying.

| Model | Training three-class accuracy | Development three-class accuracy | Training same-match AP | Development same-match AP |
| --- | ---: | ---: | ---: | ---: |
| Original six-feature classifier | 74.1% | 38.2% | 0.882 | 0.765 |
| Original MiniLM diagnostic | **99.2%** | **46.2%** | **0.997** | **0.775** |

Accuracy here means the highest-scored class among **same / related / unrelated**, with uncertain pairs excluded. It is not auto-join precision. AP means average precision over the same-match ranking; it is not the precision of an approved operating threshold.

The neural model fits the training pairs almost perfectly but transfers much less well. This strongly supports a generalization/overfitting concern. Its development ranking is slightly better than the baseline's, yet its high-confidence joining result is worse:

| Previously fixed development operating point | Correct joins | Wrong joins | Precision | Same-pair recall |
| --- | ---: | ---: | ---: | ---: |
| Baseline, threshold 0.994161 | 73 | 3 | 96.05% | 29.80% |
| Neural diagnostic, threshold 0.983143 | 48 | 3 | 94.12% | 19.59% |

The slight AP difference is not evidence of a statistically established winner. It explains why better average ranking does not necessarily yield safer automatic joins. These are already-inspected development results, not a fresh test.

The baseline also shows score-distribution instability: its same fixed threshold accepts only twelve training pairs but 76 development pairs. Training and development are not interchangeable populations; the earlier 96% result cannot establish broad reliability.

## 3. Feature comparisons on unseen training-library folds

Each profile used C10 balanced multinomial logistic regression. A fold could automate only if its separate calibration set reached at least 95% precision and 30 accepted known pairs. Every profile qualified on only **one of three** calibration folds. The other two correctly abstained.

This is an empirical screening gate, not a statistical guarantee of 95% precision on future memories. The small number of independent libraries limits confidence even when many correlated pairs are scored.

| Features | Pooled evaluation precision | Macro-library recall | Accepted known pairs | Same-match AP |
| --- | ---: | ---: | ---: | ---: |
| Two embedding similarities | 64.86% | 5.22% | 74 | 0.548 |
| Word/character/number/length clues | 89.19% | 7.81% | 74 | 0.730 |
| All six features | 87.50% | 8.28% | 80 | 0.729 |
| All except number overlap | 86.57% | 6.93% | 67 | 0.672 |

These are pooled out-of-fold decisions across all eighteen training libraries, with each library evaluated once. Recall includes the two abstaining folds. Precision is undefined within those abstaining folds, not 100%. Accepted uncertain pairs were respectively 2, 4, 11 and 8; they are reported separately and excluded from known-pair precision.

For example, all-six achieved 60 correct / 3 wrong joins on fold 2's calibration libraries (95.24%), but 70 correct / 10 wrong on its evaluation libraries (87.50%). Calibration success did not transfer reliably.

Interpretation:

- Word/character/number clues carry substantial useful signal on this dataset.
- Removing numeric overlap reduced ranking quality in all three folds. Numbers are useful clues, not safe identity rules: corrections can legitimately change them.
- Lexical-only and all-six ranking results are close; this does **not** establish that embeddings should be removed. Their retrieval role and richer vector features are different questions.
- No profile maintained the required precision across new libraries.
- These smaller, stricter folds are not directly comparable with the original model trained on all eighteen libraries and calibrated on six development libraries. Do not describe this as the same baseline simply “dropping from 96% to 87.5%.”

## 4. Contextual review

All 60 pairs received both reviews. Pair-first: 44 marked sufficient, 16 needing context. Contextual outcome: 59 labels supported and one possible policy issue. Primary causes recorded: 32 decision errors, six missing-context cases, eleven appropriate ambiguities, ten controls without an issue and one unresolved policy concern. These categories are diagnostic judgments, not exhaustive causal attribution.

This was a single executing-agent review with prior report exposure. The sample deliberately emphasized mistakes and ambiguity. It is **not** an independent blind review, a human-validated label-accuracy score, or a prevalence estimate.

Examples:

- `mf24-i04 / i05`: two solar installations share 14 Alder Walk, but the main house and detached studio have different job IDs and roofs. The baseline wrongly joins them.
- `mf21-i13 / i20`: distinct museum accessions share conservation vocabulary. The neural diagnostic wrongly joins them.
- `mf23-i10 / i13`: a third source explicitly establishes that “Meadow Lane Birch” is the “blue hive / ML-B.” The isolated pair does not contain that full identity mapping.
- `mf24-i07 / i17`: i07 is ambiguous between two Alder Walk jobs, but explicitly not the Linden Lane job in i17. The current item-level ambiguity policy marks this pair uncertain anyway. This is a possible pair-label granularity issue, not a silently corrected label.

Important product distinction: **shared thread membership is not transitive equivalence**. A source can belong to two threads. Pairwise matches to that bridge must not merge both threads into one. This screen does not yet validate the complete provenance/merge/undo workflow end to end.

## 5. Validation and saved checkpoint

Commands actually run with the existing feasibility venv:

```sh
python -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q
python -m unittest discover -s scripts -p 'test_organization*.py' -q
python scripts/matcher-feasibility/environment.py --workspace <existing-workspace>/v1 --output Evaluation/MatcherFeasibility --verify-only
python scripts/matcher-feasibility/screening.py verify --run Evaluation/MatcherScreening/runs/audit-attempt-01
```

Results: **124 matcher tests + 22 organization tests passed**; 37 packages and six pinned model assets verified. The completed-run audit passed, independently recounting **45,600 prediction rows** and checking calibration thresholds, fold coverage, fitted transforms, portable predictions, review chronology and recovery integrity. Repeated rows across models/partitions are included in that audit count; it is not 45,600 distinct examples.

Completed-run `run --resume` was also exercised: it verified completion without restarting training. `pause` returned `already_complete_and_stopped`. All four local Markdown links checked successfully.

New retained storage at handoff: approximately **0.66 GiB**; about **12.95 GiB free**, above the 10 GiB reserve. No dependencies were installed. The final tiny sanity model is diagnostic only.

Four superseded **new** recovery blobs were removed under the approved rolling policy (about 857 MiB logical bytes). Those earlier states are not retained; the latest two recovery states, final model and all receipts remain. All previous feasibility Stage 1–5 artifacts remain untouched and verified.

Completion SHA256: `90961460de28a80e53801b99724d24414e50bf9aec7702144c54a4ecc391e344`.

## Next checkpoint — requires your approval

Recommendation: proceed with the bounded Stage 2 screen, keeping the frozen labels unchanged and reporting ambiguous pairs separately. Test twelve configurations across:

1. Improved simple classifiers, including identifier clues.
2. Small classifiers on richer existing embedding features.
3. Binary MiniLM variants with frozen or restrained backbone training.
4. Hybrids using properly cross-fitted neural scores plus explicit clues.

The exact proposal is saved in `runs/audit-attempt-01/stage2-trials.json`. At most two families receive the planned confirmation runs. This is a search for a research lead, not permission to deploy or open the final test.

**Estimated next stage: 4–8 active hours, Mac only**, including implementation and verification. Pause/resume and a mandatory stop at its checkpoint remain required. No phone is needed for Stage 2.

If you instead want to resolve the ambiguity-label policy first, allow roughly **1–2 additional hours** for a targeted train/development review and a proposed amendment. That would require explicit approval and a separately versioned dataset/run; no automatic relabeling or overwriting this checkpoint.
