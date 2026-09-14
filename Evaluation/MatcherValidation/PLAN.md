# Hybrid validation: prospective experiment

## Decision and boundaries

Compare the D3 hybrid with the existing six-feature C10 classifier recipe. Do not expand the architecture search. Prior screening remains immutable: D3 is promising, not qualified. Its development precision was about95% with56–63% macro-library recall versus the baseline's96.05% /29.94%; development was reused for calibration. These are not independent reliability estimates.

This is a new experiment, not a continuation of `screen-attempt-01`. No old final-test data, private memories, phone access, downloads, production changes or Git operations are needed for preparation. The old final test remains sealed. Authoring access to fictional new gold is not model-evaluation access, and agent-authored/reviewed data is not human-blind validation.

## Checkpoints and estimates

| Checkpoint | Work | Hardware | Estimated active time | Stop condition |
| --- | --- | --- | --- | --- |
| P0: preparation | Prospective rules, executable gate tests, four-library development-only pilot, immutable checkpoint | Mac | About30–60 minutes | Stop for review; no training |
| P1: benchmark release | Author and review48 new libraries; validate splits, ambiguity, near duplicates and history expectations; freeze all data | Mac | 4–8 hours | Stop; repair label/input issues before fitting |
| P2: validation | Implement new-data runner; fit baseline and three hybrid seeds; calibrate; freeze models/thresholds; evaluate once; audit | Mac | 8–16 hours, provisional | Stop with go/no-go report |
| P3: downstream feasibility | Only if P2 qualifies: retrieval/history integration experiment, Core ML parity and phone measurements | Mac, then connected iPhone | Re-estimate after P2; roughly3–6 hours for device work alone | Separately approved; never automatic deployment |

P0 does **not** mean the full benchmark or training runner is ready. Beyond P0, roughly12–24 active hours remain for P1/P2, excluding pauses and corrections. Re-estimate from measured throughput before P2. Existing phone timings describe an earlier model, not a validated new winner.

## New data and review

- Target48 libraries ×20 items =960 sources and9,120 within-library unordered pairs. Split24 train /12 calibration /12 evaluation. No cross-library pairs silently added.
- Author24 independent story families with two distinct libraries each. Assign12 families to train, six to calibration, six to evaluation **before authoring**. Both libraries in a family and all variations stay in one split. Group shared narrative/template families together too; renaming entities is not independence.
- The four P0 pilot libraries are permanently development-only, outside these48. Never promote them into calibration/evaluation after inspecting them.
- All pairs are evaluated, not just hand-picked hard negatives. Enrich **training narratives** with related-but-separate work, shared names/templates, identifier collisions, renamed threads, corrections, bridges and sparse voice/OCR text. Report the challenge set separately from routine cases; do not claim its engineered prevalence matches real users.
- Gold uses source-to-thread memberships, explicit related-thread links and uncertainty. Shared membership means `same`; a related-thread link means `related`, not permission to merge. A bridge can belong to A and B without making every A/B pair `same`. Insufficient information is `uncertain`, never a convenient negative.
- Model inputs contain only source IDs, text and source modality. Memberships, explanations, difficulty tags, split/template names and history gold are host-side metadata, never text features. These are **text representations of media**, not a visual/audio extraction benchmark.
- Review pair text first for sufficiency, then library context for membership policy. Record disagreements, evidence and amendments before freezing. P0 review is by the executing agent and is not independent. Do not claim independent agent review unless separate reviewers actually perform it. Broader independent review should be arranged at P1 if available; otherwise label the resulting release provisional and restrict conclusions.
- Validate identifiers, relation endpoints, unique IDs, all-pair coverage, exact duplicates, cross-split token-shingle similarity, story/template split leakage, and ambiguity. Near-duplicate detection is a warning screen, not proof of independence. Review against old **train/development** examples too, never open the old test to do so.
- Predeclare incremental histories for each library: source insertion, revision/rename, one bridge, explicit undo where relevant. Preserve source identity; no automatic transitive union of pair matches. P2 verifies expectations and pair decisions; full production replay belongs to P3 and must pass before integration.

## Exactly what is compared

1. **Refitted simple control:** six original features, three-class logistic regression, C10, balanced weights, lbfgs, max_iter2000, seed17. Retain its `same`-winning requirement and fit TF-IDF/scaler only on training data. Historical frozen weights can be a separately labeled descriptive reference, not the primary fair control.
2. **D3:** pinned English MiniLM L12H384 binary matcher plus a C1 logistic combiner of its logit and the ten existing features. Use prior C3/D3 training settings unchanged: three epochs, seeds17/29/41, both directions averaged, effective batch16, head LR0.001, backbone LR0.000005, AdamW, weight decay0.01, 10% warmup, max512 tokens. No hyperparameter search.
3. Train combiner on three-fold **out-of-fold** neural scores, grouping by story family within the24 training libraries (16 fit /8 scored per fold). Fit a final base model on all24. No in-sample neural scores for combiner training; no calibration/evaluation sources in vocabulary/scaler/model fits. Twelve neural fits total across three seeds; no full final-test access in training commands.

## Calibration and one-time evaluation

Use `contract.json` and `validation_policy.py` for the prospective numerical gates. The baseline selects its calibration threshold at>=95% empirical precision and>=30 accepted known pairs, maximizing macro-library recall, then precision, then threshold. A missing baseline operating point means inconclusive comparison, not an automatic hybrid win.

Each hybrid selects on calibration only, requiring **all**: precision>=max(95%, baseline calibration precision minus1 percentage point), recall>=baseline calibration macro recall plus5 percentage points, >=30 accepted known pairs, and complete known-pair scores. No qualifying threshold means abstention. Include tied scores together. Never count uncertain examples toward precision, recall or the minimum count; report accepted uncertainty separately.

Freeze all three models, transformations, thresholds, baseline, input/label hashes and review records before evaluation. Evaluate all seeds, never pick the lucky seed. On evaluation, apply those thresholds unchanged and compare against the baseline's **evaluation** results using the same complete rule. Do not reuse historical96.05% as a new-split target. Failure/inconclusive results do not authorize threshold retuning on evaluation.

Report precision, macro-library recall, average precision, false-related/false-unrelated joins, uncertain acceptance, per-library results and matched differences. Use paired bootstrap over the six held-out **story families**,2,000 samples, seed1729, reporting undefined samples. Pairs and repeated seeds are not independent observations. Intervals are descriptive; six families provide limited evidence.

All three seeds must pass empirical gates to advance to P3. This is a research gate, not proof of95% population precision or readiness to ship. No numerical rule silently changes after seeing outcomes. If the baseline has no evaluation operating-point support, or scores are missing, report inconclusive/failure rather than fabricate a win.

## Persistence and storage

P0 writes only a small immutable receipt, projected pilot inputs and labels. Its `prepare` command is idempotent: verifies a completed receipt instead of overwriting; `verify` detects source/artifact changes. A crash can resume publication of byte-identical files. No training is hidden in either command.

Before later work, calculate **combined retained assets plus temporary writes**. New work defaults to<=4GiB and>=10GiB free space; previous experiment assets remain untouched. The previous4.5GiB exception is not automatically reused. A larger data/model footprint must pause for a revised storage plan, not delete old evidence.

P1 saves each authored/reviewed batch before proceeding. P2 must implement and exercise cooperative pause **before** long training: finish current effective batch, save model/optimizer/RNG/epoch/data offset, atomically publish checkpoint, exit all workers. Save at most every50 steps and at boundaries. Retain final fit exports and at least the latest two verified recovery states within the new run; deletion needs exact validated targets and receipts. Unexpected closure can repeat unsaved work; do not promise bitwise MPS continuation. Stop after each checkpoint and await instruction.
