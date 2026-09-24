# iOS 27 core-intelligence evaluation

**Latest checkpoint:** [Stage 2 complete — no-go for local reviewers](quality-continuation/REPORT.md).
All remaining frozen requests and eight repeats completed without another transport
failure. There are 231 returned responses and one explicitly retained unknown-outcome
launch, with 234 total attempts including the prior generation checks. Neither prompt
nor any D3 combination passes the safety gate. On 80 context packets, D3 recognizes
25/32 true continuations; the boundary reviewer recognizes 12/32 and falsely separates
15/32. Its stronger separation recall comes with substantial damage and unsupported
assertions on uncertainty. All 75 runner tests and the 90-scope metric recount pass.
Production is unchanged; work is saved and stopped for review, safe to close.

**Previous checkpoint:** [Stage 2 controls complete; reviewer screen interrupted](quality/REPORT.md).
All 56 fresh phone pair controls completed with identical FP16/FP32 decisions.
Eight scheduled reviewer responses returned (six structurally valid, two invalid
quotations), before the next launch failed with a CoreDevice socket EOF. No native
result or trace could be recovered; no retry occurred. The full screen remains
incomplete and cannot establish a quality uplift. Frozen prompts and all saved
results are intact, 64 runner tests pass, and production is unchanged. The probe
is no longer running: verified safe to close via `quality/process-closure.json`.
Review the unresolved launch's disposition before continuing; the generic runner
conservatively still reports an unresolved reservation. See the
[prospective protocol](quality/PROTOCOL.md) and report for the exact stop condition.

**Previous checkpoint:** [Instrumented generation smoke passed](generation-trace/REPORT.md).
The identical fictional code-extraction request returned the correct answer in
3.52 seconds of generation after the probe verified active foreground state. A
separate no-model control proved the app-side watchdog saves a terminal outcome
even for an uncooperative task. Exactly one model request was made in this step;
48 Python tests passed. Foreground timing is a hypothesis for the old timeout,
not a proven cause. The evaluation-readiness blocker is cleared; Stage 2 has not
started and work is paused for review. The original FP16 historical parity gate
is still failed; the separately versioned FP32 candidate and production default
must not be conflated. No production model or thresholds changed.

**Previous checkpoint:** [Boundary and safeguard checks complete; generation blocked](CHECKPOINT-2026-09-16.md).
Twenty-four threshold-near pairs across 11 fictional libraries retain every decision
on Mac and phone with both precisions. FP32 passes 48/48 neural bounds; FP16 passes
45/48. All 23 selected current-organizer/store/readiness-cache tests pass on the
physical phone. However, one tiny local-generation request produced no result by
the 120-second host deadline despite reporting model availability. The isolated
probe was safely terminated; no retry or Stage 2 quality screen was started.
Stage 1 remains incomplete. Production model, threshold and personal library are
unchanged. Next is a bounded generation-readiness diagnostic, not another model search.

**Previous checkpoint:** [FP16/FP32 numerical comparison completed](precision/REPORT.md).
All 64 Mac/phone units completed. FP32 passes the original neural-to-PyTorch bound
for 32/32 directions and its own conversion-reference score check for 16/16 pairs;
both precisions preserve all 16 fixed and fresh-embedding decisions. FP32 doubles
model storage and takes 2.36× the measured phone warm inference time. The original
historical FP16 score gate remains failed; no tolerance or production model changed.
This is not a grouping-quality improvement. Work is saved and stopped for review;
Stage 1 is incomplete and Stage 2 has not started.

**Previous checkpoint:** [Bounded readiness retry implemented and verified](embedding-recovery-v2/REPORT.md).
An immediate retry proved unreliable in the production actor. The updated provider
waits asynchronously for 200 ms after an initial failure, retries once, and caches
success. All 16 fresh-process phone embedding checks and all 16 Mac checks completed
with matching spaces and unchanged decisions. Seven Swift tests and 33 runner tests
pass. Contextual vectors have small reported numeric differences; the earlier Core ML
parity issue remains open. Stage 1 is incomplete; Stage 2 has not started. The main
app was not reinstalled and its weights/thresholds remain unchanged.

**Earlier checkpoint:** [Physical iPhone checked; compatibility blocked](phone-diagnostic/REPORT.md).
All 16 phone reference decisions agree, but only 5/16 pass the original strict score
gate and one neural output exceeds the original conversion tolerance. Phone neural
outputs exactly match the new Mac outputs. Apple Foundation Models is available on
the phone (4,096-token context), but its English sentence embedding was unavailable
and the first production embedding check failed. Collection stopped there.
The original [Stage 1 failure](stage1/REPORT.md) and [Mac diagnostic](parity-diagnostic/REPORT.md)
are preserved. All 28 runner tests pass. Work is saved and paused for review; Stage 1
is incomplete and Stage 2 has not started. No tolerances or production behavior changed.

Approved scope: two stages, with a mandatory review stop after each. Stage 1 is
compatibility and baseline measurement; Stage 2 is a separately started, bounded
grouping screen. The later approved readiness fix is recorded above; no personal-library
access, threshold change or paid API use is included.

## Stage 1

The isolated runner lives in `scripts/ios27-evaluation/`. It freezes production
sources and existing parity fixtures, verifies the new toolchain, and runs each
native check as a separately checkpointed unit. Mac and phone results are distinct.
Historical reports are never overwritten. Temporary stores are probe-owned.

Resource limits: 8 GiB new experiment/cache storage, 10 GiB Mac free-space reserve.
No Git commands other than read-only inspection. No automatic PCC entitlement
application, cloud calls, model training or threshold adjustment.

Required evidence before Stage 2: phone model availability, embedding representation
and numeric checks, all 16 D3 parity decisions with existing tolerances, organizer
safeguards, and a demonstrated pause/resume preserving completed output hashes.
An unavailable device/model or failed parity is not a passed compatibility check.

## Stage 2 (completed; all reviewer/policy gates failed)

Compare the unchanged C7 source-only reviewer and one frozen boundary-focused
reviewer against baseline/D3 controls on 112 unique inputs (160 scored packets).
At most 256 local phone generation attempts including smoke/repeatability checks.
Precision-first gate: same precision ≥95%, same recall ≥75%, separation precision
≥90%, separation recall ≥80%, unsupported uncertain decisions ≤10%, errors ≤5%,
and more fixed than damaged D3 decisions. Exposed diagnostics do not qualify a
model for production. Fresh validation and suggestions-first integration need review.

PCC is optional only after verified no-API-cost eligibility and entitlement, with
fictional inputs and a separate result table. It cannot qualify an offline model.

### Stage 2 saved-state commands

```sh
python3 -B scripts/ios27-quality-continuation/run.py pause
python3 -B scripts/ios27-quality-continuation/run.py status
python3 -B scripts/ios27-quality-continuation/run.py resume --device <connected-device-id>
python3 -B scripts/ios27-quality-continuation/run.py verify
```

The completed screen is paused for review; no new experiment or integration is
started by this result. `verify` checks saved evidence; a completed `resume` has no
remaining inference units. Use the **continuation** runner. The original runner
still deliberately refuses its historical unresolved reservation; do not use it
to resume. The approved disposition is recorded separately, not inserted as a
fabricated native answer.
Completed units remain immutable. During collection a native failure
or three consecutive invalid outputs stops the screen for review; resuming does
not bypass that stop. Lost-console attempts require checkpoint collection rather
than another inference. Do not use the historical Stage 1 runner to resume Stage 2.

## Commands

Run from the repository root with Python 3.11 or newer (no new dependencies):

```sh
python3 -B scripts/ios27-evaluation/run.py prepare
python3 -B scripts/ios27-evaluation/run.py build --platform mac
python3 -B scripts/ios27-evaluation/run.py run --platform mac --max-units 1
python3 -B scripts/ios27-evaluation/run.py pause
python3 -B scripts/ios27-evaluation/run.py status
python3 -B scripts/ios27-evaluation/run.py resume --platform mac
python3 -B scripts/ios27-evaluation/run.py evaluate
python3 -B scripts/ios27-evaluation/run.py verify
```

Phone execution uses `--platform phone --device <connected-device-id>`. The runner
never installs or terminates the main Remember app. Check `status` and wait for
`safeToClose: true` before disconnecting. Interrupted attempts are retained; they
are not automatically retried. Never change the frozen configuration to bypass an
error. Read the checkpoint report for completion and blockers.

`prepare` and `build` are only for an unfrozen attempt; they intentionally refuse an
existing manifest. Do not rerun these setup commands on this saved checkpoint.
`resume` will preserve and stop at the current failed parity result. Recovery from a
lost phone console uses `collect --platform phone --device <id> --unit <unit>` without
another inference. The `install` action targets only the signed compatibility probe.
