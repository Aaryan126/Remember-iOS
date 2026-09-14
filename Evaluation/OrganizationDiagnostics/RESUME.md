# Checkpoint 7 — complete; stopped for user review

The user approved the C6 recommendation. Read [C7_PROTOCOL.md](C7_PROTOCOL.md).
The isolated Mac probe builds and reports the local model available. No phone, cloud,
training, downloads, production writes or Git-state changes are allowed. Existing C6
data is exposed diagnostic reuse, not independent validation. Stop after C7 for review;
fresh reviewed validation is a separate checkpoint, not automatically authorized.

Read [c7/REPORT.md](c7/REPORT.md) and the [median-time correction](c7/ERRATA.md).
All 112 native responses and 2,240 derived outcomes are saved. The local verifier
failed four of five prospective contextual gates: separation precision 64.3%, recall
28.1%, unsupported decisions on uncertain cases 93.8%, errors 7.5%. Same-project recall
90.6% passed. Combined policies offer some diagnostic gains but no production candidate.

All 193 tests, exact response/prediction/metric replay, C6 parent verification and real
saved-unit pause/resume proof passed. No worker remains; safe to close the laptop.
Remaining time: none. No next experiment is approved or started. Completion SHA-256:
`ba2bb8124f80566ffcce228812430fda9c69b250348a570b8a409e2715dcec02`.
The completion-bound report is preserved; ERRATA.md corrects only its rounded median.

Verify using the existing environment:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/organization-diagnostics/c7_run.py verify
```

Historical execution (already complete): `c7_run.py tests`, `freeze`, `predict --max-units 1`, `proof-before`,
`pause`, verify paused worker exit, `predict --resume`, `proof-after`, `evaluate`,
`audit`, write report, `complete`, `verify`. Do not restart these phases or edit C7 source, tests,
prompt, protocol or receipts. Preserve all earlier checkpoints.

Historical recovery: send pause or run `c7_run.py pause`. Each request is bounded to 60 seconds;
wait for saved-boundary acknowledgement and worker exit before closing the laptop.
Resume with `predict --resume`; saved units, including errors, are verified and skipped.
Three consecutive errors pause the run for investigation; do not silently retry them.
The first unit's hash and timestamp must survive resume. Keep the cumulative 4 GiB cap
(including the 1 GiB simulator reserve) and at least 10 GiB free. Leave unrelated
output/ untouched. No phone work or further training follows from a status/resume request.

## Historical checkpoint 6 handoff — completed

The user approved independent review and bounded scoring after C5. Read C6_PROTOCOL.md.
Two agents reviewed 112 unique contexts each, pair phase sealed before context. Both
agreed on one correction to C5: q52625745202b9a832c89e949 is uncertain without the title
mapping. Root adjudication and one expanded-packet amendment are preserved in C6; C5
gold is unchanged. The nine candidates are four frozen legacy scorers, an independently
implemented narrow controlled-English rule verifier and four conflict-gated variants.
Do not portray review agents as local model candidates. No training or app/phone work.

Read [c6/REPORT.md](c6/REPORT.md). All 1,440 predictions and original/adjudicated metrics
are saved. Existing matchers assert same-project on 21–22 of 24 explicit-separation
packets in the pair-only view. The narrow rule control abstains on all 160 packets;
all four gated variants reproduce the legacy outputs. No candidate is qualified.

All 172 tests passed. Native embedding checks and all three seeds' 16-reference-pair
checks reproduced their original outputs exactly. Deterministic replay reconstructed
all predictions and metric variants. A real one-embedding stop/resume preserved its
hash and modification timestamp. The report and evidence are bound by c6/complete.json.
Completion SHA-256: `a587031ff045f488521e3229ee75dba71108f8f0f40a02bb1a50ad6504181490`.

No scoring worker remains. Safe to close the laptop; no phone is needed. Nothing remains
in C6 and there is no subsequent experiment to resume. The proposed context-aware local
semantic-verifier experiment requires separate approval and an availability check; no
training, cloud fallback, new model download or production mutation is authorized.

Verify the completed checkpoint using the existing environment:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/organization-diagnostics/c6_finalize.py verify
```

Historical execution (already complete): `c6_run.py score --max-units 1`,
`c6_finalize.py proof-before`, `c6_run.py pause`, `c6_run.py score --resume`,
`c6_finalize.py proof-after`, `c6_run.py evaluate`, then `c6_finalize.py tests`,
`audit`, report publication, `complete`, `verify`. Do not restart these phases.

Historical recovery: run `c6_run.py pause` during inference; wait for the active worker's saved
boundary and process exit before closing the laptop. Embedding/text units and neural
batches (<=8 pairs) are immutable. Resume uses `score --resume`; existing units are
verified/skipped and model state is reloaded only as needed. Do not edit frozen C6
protocol/code/tests, review files, reference labels, transforms or thresholds. Preserve
the shared 4 GiB diagnostic cap including the 1 GiB simulator reserve and 10 GiB free.
No Git-state mutations; leave unrelated output/ and prior evidence untouched.

Remaining C6 time: none. Stop for user review regardless of results; no training or
subsequent experiment is approved. Earlier checkpoint handoffs below are historical,
not instructions to repeat completed work. Restore requires the original ignored raw
artifacts and environment, including saved timestamps, not regenerated receipts.

## Historical checkpoint 5 handoff

The user approved the C4 recommendation. C5 prepared a conflict-review contract and
fresh diagnostic material; read [c5/REPORT.md](c5/REPORT.md) and [C5_PROTOCOL.md](C5_PROTOCOL.md).
Eight families, 56 authored texts, 48 episodes, 80 queries and 160 pair/context packets
are frozen. No model inference, training, app/phone work or Git-state changes occurred.

All 139 tests passed, all packets/reference records reconstruct exactly, and a real
one-family stop/resume preserved the first unit's SHA-256 and timestamp. Completion SHA:
`a605f858144dc3e416a28dacd1dc20d2dd3441ad135b056e1fa48c2f5b911216`.

**Independent semantic review is pending.** This is author-reviewed synthetic material,
not independently adjudicated qualification data. The receipt intentionally records
`readyForModelScoring: false`, `modelPredictions: 0`, and `productionQualified: false`.
Do not report unit-fixture predictions or expected-label counts as model results.

All C5 workers are stopped; safe to close the laptop. Nothing remains in this preparation
checkpoint. The proposed independent agent review and bounded model-scoring checkpoint
(4–8 active hours, Mac only) is not approved or started. Wait for explicit user direction.
No automatic neural training or app integration. Preserve all previous evidence and
leave unrelated `output/` alone; never mutate Git state.

Verification from the repository root (does not start model work):

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/organization-diagnostics/c5_run.py verify
```

Historical execution: `c5_run.py freeze`, `prepare --max-units 1`, `proof-before`,
`pause`, `prepare --resume`, `proof-after`, `tests`, `complete`, `verify`. Do not edit
frozen `c5_*.py`, `test_c5.py`, protocol, authoring or author review. Amendments must
preserve initial labels and artifacts. Model inputs are only `runs/c5-01/release/inputs.json`;
gold, splits and author rationales are evaluator-only. A future scorer needs a new
frozen protocol/adapters, not a hidden expansion of the preparation runner.

Recovery for interrupted preparation uses `pause` and `prepare --resume` with the same
executable. Wait for worker exit/saved-boundary acknowledgement before closing the Mac.
There is currently no worker to resume. Restore requires original artifacts, environment
and timestamps, not regenerated receipts. Keep the cumulative 4 GiB cap including the
1 GiB simulator reserve and at least 10 GiB free; C5 adds less than 1 MiB.

## Historical checkpoint 4 handoff

The user approved the C3 recommendation. C4 is a fixed-prefix state-repair proposal
diagnostic, not training, an online repaired trajectory, phone testing or app integration.
Read [C4_PROTOCOL.md](C4_PROTOCOL.md). Four corroborated histories and four scorers;
gold-free proposals are frozen before separately labeled perfect-reviewer acceptance.
Preserve C1–C3 and P2. Never change Git state. Leave unrelated `output/` alone.

Read [c4/REPORT.md](c4/REPORT.md). All 144 proposal units and 144 metric units are saved:
9,264 scorer-contexts; 120 tests passed; full deterministic replay and unchanged-anchor
parity passed. The real stop/resume preserved the first unit's SHA-256 and timestamp.
Completion verification passed; SHA-256:
`0546cbfe3acd5a2670f68b881bc0b69eea95447198e278c2d3b2e2bfc7f85568`.

All workers stopped. No phone/simulator or app was used. It is safe to close the laptop.
No C4 work remains. The recommended conflict-review design/fresh diagnostic preparation
checkpoint (4–8 active hours, Mac only) is **not approved or started**. Do not start it
from a status/resume request. Keep all seeds; no production-qualified winner exists.

Use `PYTHONDONTWRITEBYTECODE=1` and the existing Python executable below for all commands:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/organization-diagnostics/c4_finalize.py verify
```

Historical execution phases (already completed; do not restart):
`c4_run.py prepare`, `predict --max-units 1` (real saved stop),
`c4_finalize.py proof-before`, `c4_run.py predict --resume`,
`c4_finalize.py proof-after`, `c4_run.py evaluate`, then `c4_finalize.py tests`,
`audit`, write the report, `complete`, `verify`. Prepare seals source/tests/protocol;
do not edit them after that point. New attempts require preserved amendments.

Historical recovery: send `pause` or run `c4_run.py pause` while a worker is active; wait for its exit and
saved-boundary acknowledgement before closing the laptop. Resume the interrupted
phase with `--resume`; completed stream files are validated and skipped, never reset.
All cached units are short. A status read does not start work or acknowledge a pause.

Keep the cumulative 4 GiB diagnostic cap (including existing 1 GiB simulator reserve)
and 10 GiB free-space floor. C4 added approximately 85 MiB; completion had roughly
19.2 GiB free. Original raw artifacts, environment and timestamps are required for
restore; missing evidence is not permission to recreate receipts. No further experiment
is automatically authorized. Presentation status files are not completion receipts.

## Historical checkpoint 3 handoff

The user approved the C2 recommendation with “Go on with ur recommedndation”.
C3 is isolated under `runs/c3-01`, with `C3_PROTOCOL.md` and new `c3_*.py` sources.
C1/C2/P2 remain immutable. No training, inference, phone, simulator or app changes.

C3 completed baseline corroboration and all-scorer fixed-prefix comparisons across
eight controlled lineages. Read [c3/REPORT.md](c3/REPORT.md). All 252 old controlled runs
reproduce exactly; 36 new streams / 579 prefixes and 27,648 fixed-state decisions are
saved. All 100 Python tests passed. Real stop/resume preserved the first unit's hash
and timestamp. The completion receipt SHA-256 is:
`2721f912ce16646f448782578788c6e72afce2cdf10a892924be139fcba78ca5`.

All workers have stopped. No phone or simulator was used for C3. It is safe to close
the laptop. The proposed next state-recovery/proposal diagnostic (4–8 active hours,
Mac only) is **not approved or started**. Wait for explicit user direction.

Use the existing environment for all execution:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/organization-diagnostics/c3_finalize.py verify
```

There is no unfinished worker to resume. The historical recovery commands are
`c3_run.py pause`, `predict --resume` and `evaluate --resume`; do not rerun completed
work or start the next experiment merely to resume a conversation. Do not edit frozen
sources, restart earlier training or change Git state. A restore requires the original
raw artifacts, saved timestamps and pinned local environment; missing evidence is not
permission to recreate receipts.

Combined cap remains 4 GiB, retaining the 1 GiB prior simulator reserve; keep at least
10 GiB free. C3 added roughly 76 MiB of artifacts. Earlier artifacts were not deleted.

## Historical checkpoint 2 handoff

The user approved checkpoint 2 with “proceed” on 2026-09-14. Checkpoint 1 remains
immutable and verified. Current C2 run: `runs/c2-01`; protocol: `C2_PROTOCOL.md`.
No training, downloads, phone use, personal vault access or production integration.

Frozen manifest SHA-256:
`40cd63bebaeeb0ee33677b62dde38a08ac41ebe4491c8208e55277b8303b50ef`.
Do not edit the C2 sources bound by that manifest. A change requires an explicit,
preserved amendment/new attempt, never replacing the old receipt.

Saved preflight: native reference tests pass; isolated simulator app builds; 31 ledger
invariants and 12 smoke/history prefixes pass, including database reopen and pause/resume.
All 16 original P2 reference cases reproduce exactly for each of the three neural seeds
(maximum directional probability difference 0). Feature/baseline/hybrid parity passed.
Scoring, semantic analysis and production-ledger replay are complete: 157 text versions,
935 pairs per seed, 288 policy streams / 4,632 prefixes. All 4,632 historical-prefix and
288 restart checks passed, plus 31 explicit ledger invariants and 94 Python tests.
Read [c2/REPORT.md](c2/REPORT.md) and [c2/ERROR_REVIEW.md](c2/ERROR_REVIEW.md).

C2 completion SHA-256:
`01e2cde53a3ed12f1f25be8ccefc9e31259e391050a339ad8ff3edc376fc026e`.
All workers exited; the test simulator was shut down. It is safe to close the laptop.
No new experiment is approved or running. The suggested next checkpoint is the missing
baseline corroboration control and fixed-prefix audit, estimated 2–4 active hours,
Mac only. Wait for explicit user approval; do not start it from a status/resume request.

Use the existing environment (do not install or upgrade dependencies):

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/organization-diagnostics/c2_finalize.py verify
```

Do not rerun completed model/replay work merely to resume the conversation. The runner
supports `c2_run.py pause` and `score --resume` for interrupted incomplete units, and
`c2_report.py --resume` for interrupted metric publication; those are historical recovery
commands now. Saved ledger commands and isolated simulator identities are in
`runs/c2-01/ledger/replay-commands.json` and `ready.json`. Never use the personal app/vault.

Resource limits: 4 GiB combined diagnostic writes, with 1 GiB reserved for incremental
simulator files outside the repository; at least 10 GiB free. No automatic deletion.
Stop after C2 with results and recommendation. This is diagnostic evidence, not model
qualification or permission to ship it.

## Historical checkpoint 1 handoff

The user confirmed the preparation commit; read-only inspection showed commit bb66de1
and a clean working tree before diagnostic edits on 2026-09-14. No Git state was changed.

Scope: continuing-project contract, prediction-blind pair/context review, and 12 fictional
chronological stories. No training, phone use, production mutation or checkpoint 2.

Current saved boundary: all pair/context and story reviews are sealed and adjudicated.
The 12 stories (144 captures, 193 events) are released in 36 dependency-valid sequences
with 579 reference prefixes. Three dependency amendments preserve original authoring
and review files. All 28 tests pass. Read REPORT.md and verify complete.json before
resuming; no training/inference worker or contributor task remains active at handoff.

Independent code audit caught seal-chain, source-packet reconstruction and partial
publication risks; fixes and regression tests pass. Do not
edit frozen checkpoint.py, CONTRACT.md, STORY_AUTHORING.md, stories.py, review_stories.py,
packets, authored stories or sealed reviews. Corrections to authored memberships or
dependencies must be separate story-adjudication entries, not edits to originals.

Next, only after user approval: checkpoint 2's frozen attachment-policy comparison and
isolated production-ledger replay. Estimate 8–16 active hours, Mac only. Build new files
for that checkpoint; do not edit the files bound by this completion receipt. No model
training, downloads, phone work or integration starts automatically.

From repository root:

```sh
python3 scripts/organization-diagnostics/finalize.py verify
python3 -m unittest discover -s scripts/organization-diagnostics -p 'test_*.py' -v
```

Verification needs the ignored original P2 artifacts on this Mac. Missing artifacts
are a restore requirement, not permission to recreate a receipt. Completed checkpoint 1
does not need a resume worker: inspect/verify and wait for the next-stage approval.

On a user pause: stop delegation, let the current short file/validation unit finish,
save each contributor's progress, stop active workers, and update this file before
confirming safe to close. Resume must inspect existing files/receipts and verify hashes;
never overwrite a saved independent review or restart completed work blindly.

Initial estimate: 4–8 active hours. New work cap 4 GiB including temporary files;
free-space reserve 10 GiB. Existing experiments are immutable. Stop for user review
after checkpoint 1; do not automatically run policy comparisons.
