# Stage 2 complete — matcher screening and confirmation

Completed on **2026-09-13 at 06:12 Singapore time**. The worker exited successfully. **Both stages of this two-stage investigation are now complete and stopped for user review.** This is experiment completion, not approval to deploy a matcher.

## Bottom line

The hybrid is the strongest lead from development confirmation, but **neither family passes the complete predeclared qualification rule**. Standalone MiniLM failed all three confirmation seeds. The hybrid recovered substantially more true matches than the simple baseline at approximately 95% precision; one seed passed every gate, while two narrowly failed the allowed precision-drop gate. The outer-screen failures and the reused development data remain important limitations.

Do not replace Remember's existing matcher or deploy these weights based on this run. Keep the simple classifier as the comparison baseline and retain the hybrid as a research candidate for a separately approved validation experiment.

## What was evaluated

The existing release, `Evaluation/MatcherFeasibility/releases/v1`, supplied fictional, agent-reviewed libraries. The screen used 18 training libraries: 360 sources and 3,420 pairs (903 same, 212 related, 1,712 unrelated, 593 uncertain). Each of three outer folds fitted on nine libraries, calibrated on three and evaluated on six. All twelve profiles were run: **36 comparisons**. The [outer-screen report](outer-screen.md) contains the full table and interpretation.

The fixed selection rule chose C3 and D3 before development confirmation:

- **C3:** a fully fine-tuned, binary MiniLM pair classifier. It reads both texts together and averages the two input directions. It is not a generative local-reasoning prompt.
- **D3:** a lightweight logistic combiner of C3's score, six existing pair features (including embedding-derived similarities) and four identifier-clue features. Its training scores are produced by models that did not train on the scored libraries.
- **Comparison baseline:** the earlier frozen all-six-feature C10 classifier, using the existing cached Apple embeddings and other pair features. This is not merely a raw embedding cosine threshold.

Confirmation fitted each selected candidate on all 18 training libraries, using seeds17/29/41. D3 required three inner fits per seed (fit12/score6); its final all18 base model was reused from C3. All nine inner fits and all three shared base fits are retained. Confirmation scored the six already-inspected development libraries: 120 sources, 1,140 pairs, including918 known-label and222 uncertain pairs.

**The final test split was not opened.** Development was used both to calibrate and report confirmation results, so these figures are exploratory, not fresh held-out reliability estimates. Three seeds reuse the same pairs and must not be counted as three independent datasets.

## Confirmation results

Precision answers “of the known-label pairs we accepted, how many really share a thread?” Macro recall averages the recovered fraction of true matches across libraries. Average precision (AP) measures ranking, not accuracy. A dash means abstention with no accepted known pairs, not perfect precision.

| Candidate | Seed | Precision | Macro recall | Ranking AP | True / false accepted matches | All gates passed? |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Frozen simple baseline | — | 96.05% | 29.94% | 0.765 | 73 / 3 | Reference |
| C3 MiniLM | 17 | — | 0% | 0.795 | 0 / 0 | No |
| C3 MiniLM | 29 | — | 0% | 0.768 | 0 / 0 | No |
| C3 MiniLM | 41 | — | 0% | 0.765 | 0 / 0 | No |
| D3 hybrid | 17 | 95.03% | 62.56% | 0.920 | 153 / 8 | No: precision drop |
| D3 hybrid | 29 | 95.10% | 55.65% | 0.901 | 136 / 7 | **Yes** |
| D3 hybrid | 41 | 95.03% | 62.57% | 0.917 | 153 / 8 | No: precision drop |

Every candidate scored all918 known pairs; C3's abstention was not a missing-output failure. It found no qualifying threshold with >=95% precision and >=30 accepted known pairs. Each D3 seed additionally accepted three uncertain pairs; these are reported separately, not silently counted as correct matches.

All seven or eight known false joins in each D3 seed were **related-but-not-same-thread** pairs, rather than unrelated pairs. Distinguishing related topics from actual shared-thread membership remains a concrete weakness.

### Why the hybrid still does not qualify

The frozen gates required >=95% precision, >=30 accepted known pairs, >=5 percentage points of macro-recall improvement over baseline, <=1 percentage point of precision loss, and no missing known scores. Every stochastic seed had to pass.

Baseline precision is96.0526316%, so the precision-drop gate requires at least95.0526316%. Seeds17 and41 achieved95.0310559%: **0.0215757 percentage points below that gate**, despite meeting the separate95% floor. Their precision drop was1.0215757 points, just beyond the permitted1 point. Seed29 achieved95.1048951% and passed. We did not relax a gate after seeing the results or select only the favourable seed. This narrow miss should be distinguished from the stronger evidence limitation below.

In the outer screen, D3's pooled evaluation precision was only86.65%, with calibration qualifying in two of three folds. C3's was87.40%. Confirmation does not erase those unseen-library threshold-transfer failures. More attractive development numbers do not establish robust automatic grouping.

## Recommended next decision — not executed

Treat **the hybrid, not standalone MiniLM**, as the candidate worth further investigation. Before integration, separately approve a validation design with new library-level data, explicit related-versus-same hard cases, distinct calibration/evaluation libraries, and an end-to-end thread-history test. Keep the already-used development set diagnostic and the existing final test sealed until a new evaluation contract explicitly authorizes its use.

Pair matching is only one part of the product. Shared-thread membership is non-transitive: an item spanning two topics must not cause both topics to merge. This run does not establish correct branching, merging, provenance or recovery in the full memory-map system. Real-user reliability, blind human validation and device performance of these newly trained candidates remain unestablished. No additional experiment, dataset expansion, Core ML conversion, phone testing or integration starts automatically.

## Verification and reproducibility

Commands actually run with the existing feasibility venv, from the repository root:

```sh
python -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q
python -m unittest discover -s scripts -p 'test_organization*.py' -q
python scripts/matcher-feasibility/screening2_headroom_v2.py run --run Evaluation/MatcherScreening/runs/screen-attempt-01 --resume --pause-after-steps 2
python scripts/matcher-feasibility/screening2_headroom_v2.py run --run Evaluation/MatcherScreening/runs/screen-attempt-01 --resume
```

- Final regression rerun: **183 matcher tests passed** in5.553 seconds; **22 organization tests passed** in0.052 seconds.
- Live pause exercise: restored step23, advanced to25, saved and exited. The saved model, optimizer, RNG and step were loaded and verified before normal resumption.
- Full audit: **68,400 prediction rows**, **36 screen comparisons**, **six confirmation runs**. Independent gold/counts and brute-force threshold checks passed, as did fit-only transforms, library-disjoint hybrid provenance, fitting coverage/steps, all seed reporting, frozen selection, lossless model hashes and recovery-retention receipts.
- The normal driver's post-completion verification passed for the original experiment, fast-scan continuation and approved headroom retry. Process inspection found no remaining training worker.

Run `screening2_headroom_v2.py verify --run Evaluation/MatcherScreening/runs/screen-attempt-01` for future integrity checks. A completed `run --resume` only verifies and exits; it does not train or start another stage. Do not edit frozen sources, manifests, snapshots or result records.

### Saved evidence

Run: `runs/screen-attempt-01`.

- `screen-summary.json` / `selection.json`: outer results and frozen family choice.
- `confirmation/*.json` / `confirmation-summary.json`: every seed's predictions, thresholds, metrics and gates.
- `fits/`, `predictions/`, `recovery/`, `retention/`: fitting lineage, scores, recovery receipts and authorized rotation records.
- `audit.json` / `complete.json`: passed full audit and immutable completion hashes.
- Large weights and the latest two recovery states remain in the existing Application Support feasibility workspace under `screening/screen-attempt-01`.

Completion SHA256: `dbf644d321dd50f7a455161dcf9d9a04a25a234122092d08b5f1270b03e0cefd`.
Audit SHA256: `8cf00e1b91f4af5a6fa1ea84b3f4d1f3bb554dd6d6770b21ff684197cf3d5b89`.
Confirmation summary SHA256: `d62dbf24079e086a094bc69a4e9efe351af4af4371015435d87be6a7bd584b4f`.

## Operational changes and storage

The [fast-scan continuation](runtime-continuation.md) reduced storage-check overhead without changing statistical settings. The user then approved [temporary4.5 GiB checkpoint headroom](../CHECKPOINT_HEADROOM.md), keeping the final4 GiB target and10 GiB free reserve. [Preparation retry02](../CHECKPOINT_HEADROOM_RETRY.md) preserves a failed preparation01 whose test snapshot was captured just before a fixture correction; its run failed verification before training. All failed-attempt evidence remains retained.

Final retained screening assets measured **4,166,587,183 bytes (3.88 GiB)** before this small report update, below4 GiB. The strict4 GiB check was restored before the final audit and passed. Free space was above10 GiB at that boundary and measured approximately13.29 GiB after completion. These are observed checks, not a continuously sampled peak-storage measurement. The temporary cap is no longer in use by a running worker.

Only superseded Stage2 rolling recovery blobs were removed under the existing latest-two policy; those older recovery states are not retained. Permanent model exports, predictions, receipts, Stage1 evidence and prior feasibility experiments remain. No Git state was changed, no packages were installed, and no app or phone changes were made.

Files introduced for the operational amendment: `screening2_headroom.py`, `test_screening2_headroom.py`, `screening2_headroom_v2.py`, `test_screening2_headroom_v2.py`, and the two headroom documents. Status/hand-off updates are in `RESUME.md`, `README.md` and this report. Original model/data/evaluation sources remain frozen.

**Stopped for user review. Remaining work within this two-stage experiment: none.**
