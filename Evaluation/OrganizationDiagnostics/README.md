# River organization diagnostic

Latest: [C7's local semantic-verifier diagnostic](c7/REPORT.md) is complete and stopped
for review. It failed four of five exploratory gates; some reduced false-attachment
counts do not justify integration. All 193 tests, replay and pause/resume checks passed.
These are exposed-data diagnostics, not new qualification. See the
[runtime median correction](c7/ERRATA.md) and [RESUME.md](RESUME.md).

Six earlier checkpoints are also complete; [C6 project-boundary stress test](c6/REPORT.md)
adds independent agent review and 1,440 frozen predictions on C5's 160 packets.
The existing scorers frequently assert same-project on explicit separations; the narrow
rule verifier has zero coverage and its gates do not improve results. All 172 tests,
reference parity, replay and pause/resume checks passed. Stop for review before another
experiment, training or integration. [C5 preparation](c5/REPORT.md) remains unchanged.
Read [C4 repair-proposal results](c4/REPORT.md),
[C3 matched-control results](c3/REPORT.md), [checkpoint 2 results](c2/REPORT.md), or
[RESUME.md](RESUME.md) for verification and the mandatory review stop. C4 found useful
reconnection proposals but inadequate mixed-thread cleanup; perfect-reviewer acceptance
is explicitly separated from model quality. No production-qualified winner or next
experiment is implied. Prior protocols and evidence remain unchanged. The material below
documents C1.

This experiment diagnoses the boundary and context needed for continuing-project Rivers.
It does not train a model, change the app, rerun qualification or use the personal vault.
Read [CONTRACT.md](CONTRACT.md) for the new prospective meaning of a River and
[RESUME.md](RESUME.md) for checkpoint status. Historical P2 results remain unchanged.

## Evidence and workflow

1. `selection.json` records deterministic, distinct sampling of 20 FP, 20 FN, 20 TP and
   20 TN pairs from the union of three frozen P2 hybrid seeds. Error strata take
   precedence over correct-decision strata. This deliberately enriched sample is not
   an estimate of deployment accuracy; a pair can have different outcomes by seed.
2. `packets/pairs.json` contains only aliased source IDs, text and modality. Two separate
   agents reviewed all 80 pairs without predictions, old labels or strata. Their
   judgments were sealed before full-library context was published.
3. `packets/context.json` adds only the source text from the relevant libraries. Both
   agents saved a separate contextual review with citations. This is retrospective
   context, not necessarily information available at capture time. Root adjudication
   is not prediction-blind; original independent judgments are preserved.
4. A separate agent authored 12 fictional stories with 12 captures each. Another agent
   reviews initial assignments and textual dependencies, without authored membership
   labels. The story review sees full narrative, declared scopes and explicit future
   commands: it is a retrospective manual causal audit, **not prefix-blind validation**.
5. Root adjudication preserves author/reviewer differences and applies any membership
   or dependency changes to copies. Original stories and reviews are never overwritten.
   Three valid orders per story produce separate capture/edit inputs and reference
   state after every event. Actual production-ledger replay is checkpoint 2, not here.

## Boundaries and interpretation

- Capture/edit model inputs omit memberships, author rationales, challenge tags and
  expected state. Explicit user corrections are separate action records containing
  the user's requested project IDs; these must never be used as pair-model features.
- Empty membership is uncertain/unassigned, not 'unrelated'. Archive changes visibility
  without deleting membership, content or revision history. A text edit does not
  silently change membership; an explicit correction can do so.
- Topological checks enforce declared dependencies. They cannot infer all dependencies
  from prose; that is why independent causal review and resolved findings are required.
- Agent reviews can share systematic errors. These fictional English text fixtures do
  not validate actual OCR, ASR, image/video understanding, multilingual behavior, real
  user preference, large-scale operation or device performance.
- Full completion requires `complete.json` and successful verification. Presentation
  status files are not completion receipts. Hash seals are integrity checks, not access
  control; reviewers had shared filesystem access but explicit evidence restrictions.

## Commands

Run from repository root with Python 3.10 or newer; no installation is needed:

```sh
python3 -m unittest discover -s scripts/organization-diagnostics -p 'test_*.py' -v
python3 scripts/organization-diagnostics/checkpoint.py verify-selection
python3 scripts/organization-diagnostics/stories.py validate
python3 scripts/organization-diagnostics/finalize.py verify
```

The last command requires the completed checkpoint and original local P2 evidence.
A fresh checkout alone lacks ignored raw artifacts: see the preparation checkpoint's
[restore requirements](../CheckpointSnapshot/README.md). Never replace a receipt to
hide an integrity failure or rerun training to 'restore' an original result.

`prepare`, `seal`, `build` and `complete` are explicit publication commands used during
authoring, not normal resume commands for a completed checkpoint. They refuse differing
outputs. Story payloads are fully validated before publication; an interruption can
leave identical resumable files but no final completion receipt. The finalizer requires
existing review seals rather than silently recreating a missing review checkpoint.

There is no background inference/training worker in checkpoint 1. During authoring,
'pause' means finish/save the current short agent/file unit, stop contributors and
record progress before confirming safe to close. After completion, no process needs
to remain running. Checkpoint 2 still requires separate user approval.
