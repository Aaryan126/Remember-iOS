# Approved two-checkpoint plan — 17 September 2026

## Current boundary

Implement checkpoint 1, then stop for review. Checkpoint 2 must not begin just
because preparation succeeds. The app, personal vault, phone and Git state stay
untouched. No downloads, paid APIs, training or inference in checkpoint 1.

1. **Contract and ideal-label proof (6–10 active hours, Mac only):** author 24
   libraries × 12 chronological events with four retrieval tasks each; use independent
   prediction-blind agent reviews; freeze development/evaluation splits; validate
   experiment-only relationships and run ideal labels through the production ledger
   in an isolated simulator store. Save receipts, limitations and resume instructions.
2. **Frozen-model comparison (10–16 active hours, only after review):** A=current
   D3 reference; B=A plus up to three local evidence-search suggestions; C=frozen D3
   with project-grouped proposals and selective automatic placement. Development
   thresholds are current D3, 0.99, 0.995; choose highest coverage with >=95% observed
   precision over >=20 attachments, otherwise automatic placement is unsupported.
   Freeze before evaluation-label access. Chronology plus one dependency-valid
   ordering per library; no auto merge/separate or new scorer training.

## Checkpoint-2 advancement gates (not measured in checkpoint 1)

- All ledger, chronology, correction and citation-reference invariants pass.
- Suggestions: >=90% observed precision@3 and >=10 percentage-point recall@3 gain
  over A. Report returned-result counts; missing slots must not masquerade as correct.
- Automatic candidate: >=95% observed attachment precision, no more wrong attachments
  than A, >=80% of A's correct automatic attachments, and unsupported automatic
  decisions on <=10% of unresolved cases. Insufficient denominators are inconclusive.
- Report counts, per-library variation and correlated orders; no release qualification
  or confidence claim from agent-authored fiction. Suggestions can advance alone.

## Resource and pause rules

New artifacts including builds and simulator growth: <=4 GiB; keep >=10 GiB free.
No automatic deletion. Save hashes and durable receipts after each library. A pause
finishes the bounded unit, stops workers, verifies saved progress, then reports safe
to close. Resume verifies hashes and skips completed units. Test pause/resume before
long replay. Report revised estimates during work and at each review stop.

## Deferred

Opt-in River UI and phone validation need a separate approved integration plan.
Project-aware training, formal uncertainty calibration, feedback learning and RL
remain queued, not authorized work in these checkpoints. Existing D3 and Pro
results and the unresolved FP16 compatibility concern are not superseded.
