# iOS 27 core-intelligence evaluation

**Current checkpoint:** [Numeric diagnostic complete; compatibility unresolved](parity-diagnostic/REPORT.md).
All 16 Mac reference decisions agree, but only 5/16 pass the original strict score
gate and one neural output exceeds the original conversion tolerance. The original
[Stage 1 failure](stage1/REPORT.md) is preserved. Both builds and 20 runner tests
(12 Stage 1 + 8 diagnostic) pass. The phone is disconnected; the last Mac language
model check was not ready. Work is saved for review; Stage 1 is incomplete and Stage
2 has not started. No tolerances or production behavior were changed.

Approved scope: two stages, with a mandatory review stop after each. Stage 1 is
compatibility and baseline measurement; Stage 2 is a separately started, bounded
grouping screen. No app behavior changes, personal-library access or paid APIs.

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

## Stage 2 (not started)

Compare the unchanged C7 source-only reviewer and one frozen boundary-focused
reviewer against baseline/D3 controls on 112 unique inputs (160 scored packets).
At most 256 local phone generation attempts including smoke/repeatability checks.
Precision-first gate: same precision ≥95%, same recall ≥75%, separation precision
≥90%, separation recall ≥80%, unsupported uncertain decisions ≤10%, errors ≤5%,
and more fixed than damaged D3 decisions. Exposed diagnostics do not qualify a
model for production. Fresh validation and suggestions-first integration need review.

PCC is optional only after verified no-API-cost eligibility and entitlement, with
fictional inputs and a separate result table. It cannot qualify an offline model.

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
