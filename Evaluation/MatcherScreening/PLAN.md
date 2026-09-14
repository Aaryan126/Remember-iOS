# Two-stage matcher screening

Authorized: implement Stage1 only, then stop for explicit checkpoint review. This is a new experiment, not a modification of completed feasibility Stages1–5. Stage2 is a four-family screen, not heldout testing or phone integration.

## Stage1 — audit and cheap comparisons (2–4 active hours, Mac only)

Verify prior immutable evidence and environment. Review60 development pairs, ten per library, in a pair-first/context-second protocol. The executing agent has prior exposure to reports; this is not an independent blind or human label validation. Record evidence sufficiency, label concerns and error causes; do not rewrite gold. Check model input/label/direction handling, training-versus-development scores and a tiny known-label learning subset.

Run four multinomial logistic ablations, C10/balanced/lbfgs/max_iter2000/seed17: embedding similarities; lexical/character/numeric/length features; all six; all except numbers. Three fixed outer folds each score six training libraries, fit on nine others and calibrate on three others. Fit TF-IDF on fitting-library sources only and scaler/classifier on known fitting pairs only. Threshold selection uses calibration only: maximize macro recall at >=95% precision and >=30 accepted known pairs, ties precision then threshold. No qualifying calibration point means abstention, not fabricated perfect precision. Score all known and ambiguous heldout-fold pairs; report ranking curves separately.

Save folds, full predictions, fitted transforms, review receipts, sanity checkpoints, diagnostic summary, tests, hashes and the exact proposed Stage2 settings. Complete an independent metric/integrity audit. Stop all workers. If input/label/harness concerns require amendments, report them and request a revised scope rather than mutating frozen data.

## Stage2 — bounded screen (4–8 additional active hours, Mac only)

Not authorized by Stage1 execution. The Stage1 run freezes12 proposed configurations: improved simple classifiers, small heads on fixed Apple embeddings, restrained MiniLM variants and cross-fitted hybrids. The manifest specifies parameters, fold grouping, binary task, ambiguity policy, ranking and maximum two-family confirmation. Stage2 implementation receives a new source freeze after explicit continuation. No arbitrary grid expansion or opening of the final test split. Confirmation on the already-inspected development libraries is exploratory, not a fresh reliability claim.

## Persistence and safety

Use only fictional train/development inputs and existing local assets. No phone, paid compute, private vault, production changes or Git mutations. All prior feasibility artifacts remain untouched.

New runs target at most4GiB total additional storage with10GiB free reserved. User selected rolling recovery: keep the newest two recovery states of the active trial, permanent final trial models/predictions/logs and all receipts; never clean prior feasibility assets. Before deleting superseded new recovery blobs, validate exact paths and hashes and preserve a receipt.

Pause stops scheduling, finishes the current effective neural batch (or short classifier fit), atomically saves state and exits. Save model/optimizer/random/data position every50 steps and at boundaries. Confirm safe laptop closure only after all workers exit. Resume verifies bindings and skips finished records. Unexpected closure can repeat unsaved work; exact bitwise MPS continuation is not promised. Stop after each stage and await user continuation.

Initial two-stage allowance6–12 active hours excludes pauses and separately approved corrections. Re-estimate after measured work. Stage1 completion does not authorize Stage2; Stage2 completion does not authorize final test, conversion or integration.
