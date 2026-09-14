# Hybrid validation

Status: **P0/P1 and P2 attempt 02 complete; the hybrid did not pass the all-seeds qualification gate.** All twelve fits finished. Seed 29 passed, but seeds 17 and 41 fell below 95% precision. Nothing is qualified for production integration. See [final results](P2_REPORT.md), [current checkpoint](../CheckpointSnapshot/README.md), [resume instructions](RESUME.md), and the unchanged historical [P2 protocol](P2_PROTOCOL.md).

The first checkpoint contains the acceptance contract, a four-library fictional pilot, a source/gold projection validator, and tested calibration/evaluation policy. It deliberately leaves full dataset authoring, independent review, training, model selection manifests, bootstrap reporting and end-to-end replay for later checkpoints. A procedural file seal is not access control.

New implementation is isolated in `scripts/matcher-validation/`. Existing feasibility/screening code and results are unchanged.

## Completed benchmark checkpoint

P1 contains 48 fictional libraries, 960 sources and 9,120 within-library pairs, split into 24 training, 12 calibration and 12 evaluation libraries by preassigned story family. Three separate agents cross-reviewed all source memberships and 576 sampled pairs. Root adjudication preserves disagreements, contextual labels and eight pair-only uncertainty overrides. This is agent-reviewed text data, not a human-reviewed or full-media benchmark.

`runs/p1-01/complete.json` binds 81 source/evidence files and 16 release artifacts. Both verification and a repeated freeze command passed without changing that receipt. Reference history fixtures are included; production history replay is not done. The historical P0 receipt still describes only its original pilot.

```sh
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/p1_release.py verify
```

P2 compared the refitted simple control against all three D3 seeds using separate calibration and evaluation data. Full-state pause/resume was exercised before the long fits. Those fits and evaluation are finished; do not restart them. The user confirmed the preparation commit, and both [diagnostic checkpoint 1](../OrganizationDiagnostics/REPORT.md) and [checkpoint 2](../OrganizationDiagnostics/c2/REPORT.md) are complete. Stop for review before another experiment; neither diagnostic changes P2 qualification.

The subsequent [C3 matched corroboration/fixed-state audit](../OrganizationDiagnostics/c3/REPORT.md) is also complete. It finds a hybrid benefit under matched policy/state conditions, but remains exposed diagnostic evidence, not a replacement for P2 qualification. All workers stopped; another experiment needs user approval.

[C4 repair-proposal diagnostics](../OrganizationDiagnostics/c4/REPORT.md) are now complete
too: 9,264 fixed scorer-contexts, 120 passing tests and full deterministic replay. Useful
fragment reconnection does not solve mixed threads. Gold-assisted simulated acceptance
is reported separately from proposal correctness; nothing was integrated into the app.
Stop for review before the proposed conflict-review/fresh diagnostic preparation step.

That preparation is now completed as [C5](../OrganizationDiagnostics/c5/REPORT.md): eight
fictional families, 160 pair/context input packets, strict source/gold separation and
139 passing tests. No model evaluation or training ran. Independent semantic review is
still required at that historical checkpoint before scoring.

That review and scoring are now complete as [C6](../OrganizationDiagnostics/c6/REPORT.md):
two independent reviewers, one separately preserved label amendment, 1,440 predictions,
172 passing tests and exact reference/replay checks. On the pair-only stress tests the
legacy scorers wrongly assert same-project on 21–22 of 24 separate-project packets.
The narrow rule verifier abstains on every packet; its gates offer no improvement.
No production winner, training or app change follows. Stop for user review before any
new context-aware semantic-verifier experiment; see current diagnostic resume instructions.

That isolated experiment is now completed as [C7](../OrganizationDiagnostics/c7/REPORT.md),
with a [runtime median correction](../OrganizationDiagnostics/c7/ERRATA.md). The fixed-prompt
local verifier failed four of five exploratory gates. All 193 tests and replay/recovery
checks passed; the observed quality failure is not a hidden runtime failure. Some
combined policies reduce false attachments, but unresolved-reference and bridge errors
remain severe. No app change, training or subsequent experiment followed. Stop for review.

## Commands

Run from the repository root with the existing Python environment (no installation):

```sh
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" -m unittest discover -s scripts/matcher-validation -p 'test_*.py' -q
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/prepare.py prepare
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/prepare.py verify
```

`prepare` saves `runs/preparation-01/complete.json` last, after publishing pilot inputs, gold and audit counts. Repeating it resumes identical partial files or verifies a complete checkpoint. Changed files fail closed; use a new attempt for an approved amendment. Source hashes bind the plan, contract, pilot, implementation and tests. Verification establishes integrity relative to that receipt, not an independent accuracy audit.

## Pause and resume

For current status, see [RESUME](RESUME.md). The original P0 instructions below remain historical reference.

P0 commands finish in seconds and start no workers. Once this checkpoint is saved, it is safe to close the laptop; no phone connection is required. To resume P0, use `prepare` above; to check it without publishing anything, use `verify`.

Send “pause” during future work and wait for saved-state confirmation before closing the laptop. P2 implemented and exercised training recovery; the original P0 preparation command itself does not implement training recovery. Each new diagnostic checkpoint must stop for review and must not automatically start a later stage.

## Pilot limitations

Forty source texts form180 unordered pairs:52 same-thread,36 related-but-separate,56 unrelated and36 uncertain. The four libraries intentionally share a simple test topology (three threads, a bridge and an ambiguous item). This exercises policy branches; it is not evidence of diverse held-out generalization. See [review notes](pilot-review.md). Media examples are fictional transcriptions, not real image/audio/video processing.

The projected inputs contain no memberships, gold, reviewer rationale or challenge tags. The pilot cannot qualify in `validation_policy.py`, and corpus validation never marks a release qualification-ready on structure alone. P1 supplies the reviewed release and split routing; completed P2 results are reported separately, without changing the pilot or its frozen receipt.
