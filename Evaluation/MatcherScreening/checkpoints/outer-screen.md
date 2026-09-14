# Outer-screen checkpoint — 2026-09-12

All twelve profiles across three outer folds are complete: **36/36 comparisons**. The frozen rule selected **C3 (full MiniLM fine-tuning) and D3 (MiniLM plus explicit-feature hybrid)** for repeated-seed confirmation. This completes the screen, not Stage 2, and does not authorize deployment.

## What the results mean

Full MiniLM is a promising ranking model: its average precision (AP) was 0.911, 0.917 and 0.897 in the three separate evaluation folds. But a threshold chosen to achieve at least 95% precision on calibration libraries did not reliably transfer to unseen evaluation libraries. C3 evaluation precision was 94.22% and 83.70% in the first two folds; no qualifying calibration threshold existed in the third, so it abstained there. D3 did not fix this weakness.

The table pools out-of-fold evaluation results. Calibration-qualified folds are not evaluation passes. Precision is the fraction of accepted known-label pairs that really share a thread. Macro recall averages the recovered fraction of same-thread pairs across libraries. AP measures ranking, not accuracy; pooled AP is not the mean of the three fold APs. Abstention has undefined precision, not 100% precision.

| Profile | Calibration-qualified folds | Evaluation precision | Macro recall | Pooled AP |
| --- | ---: | ---: | ---: | ---: |
| A1: six-feature logistic | 1/3 | 87.50% | 4.28% | 0.683 |
| A2: expanded-feature logistic | 0/3 | — | 0% | 0.726 |
| A3: boosted trees | 1/3 | 93.89% | 14.74% | 0.717 |
| B1: embedding-feature logistic | 1/3 | 94.00% | 5.57% | 0.745 |
| B2: embedding-feature MLP32 | 2/3 | 90.38% | 10.20% | 0.716 |
| B3: embedding-feature MLP64 | 1/3 | 88.76% | 8.08% | 0.730 |
| C1: MiniLM head only | 0/3 | — | 0% | 0.398 |
| C2: MiniLM last two layers | 1/3 | 81.44% | 9.14% | 0.690 |
| C3: full MiniLM | 2/3 | 87.40% | 52.65% | 0.889 |
| D1: C1 hybrid | 0/3 | — | 0% | 0.721 |
| D2: C2 hybrid | 1/3 | 90.91% | 10.69% | 0.629 |
| D3: C3 hybrid | 2/3 | 86.65% | 51.64% | 0.871 |
| Prior all-six C10 control | 1/3 | 87.50% | 8.28% | 0.729 |

C3 accepted 430 true matches and 62 false matches among known labels, plus 40 uncertain pairs. D3 accepted 422 true matches and 65 false matches, plus 60 uncertain pairs. Their much higher recall is useful research evidence, but these false-join rates are unsuitable for claiming reliable automatic grouping. The hybrid adds complexity without an outer-screen improvement over C3.

Selection follows the predeclared ranking (calibration-qualified folds, macro recall, precision, complexity), not a post-hoc choice of flattering metrics. Selection occurred before development confirmation. Summary SHA256: `5059f30bac8f7a9e5477956182471c40f39fb367527d1548d36f790a31ae4034`.

## Evaluation scope and limitations

The screen used the existing 18 fictional training libraries: 360 sources and 3,420 unique pairs (903 same, 212 related, 1,712 unrelated, 593 uncertain). Each outer fold fitted on nine libraries, calibrated on three and evaluated on six. Hybrid training scores came from library-disjoint inner folds. Each pair was evaluated out of fold once per profile. Uncertain labels were excluded from fitting and reported separately.

The labels are agent-reviewed synthetic examples, not blind human-reviewed real-user evidence. Pairwise same-thread matches are non-transitive: a source bridging two topics must not automatically merge the entire topics. This experiment measures pair matching, not end-to-end clustering or provenance correctness. The final test remains sealed. The six development libraries for the next confirmation have already been inspected, so that phase is exploratory, not fresh generalization proof.

## Checks actually completed

Using the existing feasibility venv, from the repository root:

- `python -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q`: 170 passed during the runtime-fix validation.
- `python -m unittest discover -s scripts -p 'test_organization*.py' -q`: 22 passed during the runtime-fix validation.
- `python scripts/matcher-feasibility/screening2_runtime.py verify --run Evaluation/MatcherScreening/runs/screen-attempt-01`: passed after the pause; original and continuation freezes verified, stage incomplete.
- Read-only Python diagnostics using `audit_screening2` helpers checked all 36 comparisons: independent gold coverage, 61,560 calibration/evaluation rows, threshold sweeps, saved decisions, reconstructed portable predictions, neural prediction bindings, fitting-only vocabulary/scalers and hybrid out-of-fold provenance.
- Follow-up diagnostics verified completed fit exports/spec hashes, fitting-pair coverage and step counts, all pooled counts/APs, and frozen candidate selection.
- Latest recovery was SHA-verified and loaded with model, optimizer, RNG and step 23 intact. No screening worker remains.

An initial extra diagnostic incorrectly required two directions for embedding MLPs as well as MiniLM. That diagnostic stopped after the comparison/portable-model checks. It was corrected to the original audit's family-specific one/two-direction rule and the remaining checks passed. No experiment source or result was changed. These are interim outer-screen checks; the full Stage 2 audit still requires completed confirmation results.

The performance-only change, its exact files and scan-parity measurements are recorded in [the runtime checkpoint](runtime-continuation.md). Original training/evaluation settings and evidence remain unchanged; no dependencies, phone work, production changes or Git mutations occurred. Only superseded Stage 2 recovery blobs were rotated under the existing latest-two policy; those old rolling states are removed, while current recovery, permanent fits, predictions and receipts remain.

## Pause, resource decision and next step

The first confirmation fit briefly started and paused safely at C3 seed17 step23, at 22:07 Singapore time. **Zero confirmation evaluations are complete.** Recovery SHA256: `1e15e246f38dbf4d42684d45b3c36becb620fbacf4ad2d717798cf06c42b3e3a`. See [RESUME.md](../RESUME.md) for its exact location and commands. It is safe to close the laptop.

Current screening assets measure about 2.43 GiB, with about 15.49 GiB free on the Mac. Projection from retained export sizes, two rolling recoveries and a 64 MiB metadata allowance estimates 3.90 GiB retained at completion, but 4.19 GiB including planned checkpoint-write headroom. These are estimates, not final measurements.

Permission is pending for **up to 4.5 GiB temporary checkpoint headroom**, preserving the 4 GiB retained-results target and at least 10 GiB free. Limits have not been raised. Do not resume on the assumption that permission was granted; any approved amendment must be separately recorded without rewriting frozen sources or evidence.

After that decision: confirm both selected families at seeds17/29/41, reusing shared MiniLM fits; audit every seed and report failures as well as successes; then stop for user review. Estimated remaining work is **2–3 active hours**, including the operational amendment if approved, excluding pauses. This estimate depends on save/scan times and Mac load. No phone is needed. Even successful development confirmation would not erase the outer-screen reliability limitations.
