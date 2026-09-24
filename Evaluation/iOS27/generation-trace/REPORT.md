# Instrumented local-generation check — smoke passed

16 September 2026. **The same fictional extraction request now completes on the
physical iPhone.** Stopped at this checkpoint; the grouping-quality screen has not
started. Production sources, models, thresholds and personal data are unchanged.

## Results

| Measurement | Observed |
|---|---:|
| No-model timeout control | Passed; saved terminal result and exited in 4.22 s |
| Actual generation requests in this checkpoint | 1 |
| Model availability / reported context | Available / 4,096 tokens |
| Time until active foreground was verified | 0.328 s from probe start |
| Session initialization | 0.00124 s |
| Response call | 3.523 s |
| Complete probe task | 3.923 s |
| Extracted code | `ORBIT-27`, exact expected value |
| Model-request deadline fired | No |

These are one-device, one-prompt observations, not latency percentiles, quality
metrics or a sustained reliability claim. No prewarming, paid/cloud call, model
training, prompt change or generation-parameter change was used. The prompt,
instructions, one-field generated schema, greedy sampling and 100-token response
cap match the earlier failed smoke request.

## What changed and what it tells us

The new probe records atomic on-device progress before/after model lookup,
availability checks, session construction and the response call. It waits for
`UIApplication`'s active state and available protected data before requesting
generation. Its initial SwiftUI task entered while the app was inactive, then the
active check succeeded about 0.33 seconds later. It temporarily disables automatic
idle sleep only within this isolated test app; the setting ends with its process.

Foreground timing is a **plausible explanation**, not an established root cause of
the earlier timeout. The old probe has no equivalent progress trace; model/service
readiness or caches may also have changed between attempts. We did not run an A/B
reproduction of the old launch behavior, restart the phone, change Apple Intelligence
settings, or claim the OS bug was fixed. The narrower conclusion is that the phone
can currently complete this guided generation call with the new evaluation wrapper.

## Bounded failure handling was tested separately

A lock-backed recorder writes progress independently of the main actor. At the
app-side deadline it requests task cancellation; after a two-second grace interval
it can publish a terminal failure and exit the isolated process without indefinitely
waiting for an uncooperative task. The host's longer timeout remains a backup.

Before calling the model, a no-model control deliberately parked a continuation
that ignores cancellation. Its two-second deadline fired, and the recorder saved
the expected terminal result and exited after the grace interval. This control is
explicitly distinguished from successful generation; its intentional timeout cannot
satisfy the generation gate. The real request had a 60-second app deadline.

This is an evaluation-process safeguard, **not a production app behavior change**.
It does not establish that Apple's backend honors cancellation, or guarantee an
app-side deadline while iOS has suspended the whole process. The host deadline and
verified isolated-process closure remain necessary fallbacks.

## Plan position

- The generation-readiness blocker is cleared for the **bounded evaluation path**.
- Earlier FP32 numerical/boundary checks and 23 selected organizer/store tests remain
  passed. Their immutable reports and results were not rewritten.
- The original FP16 historical score gate remains failed; this successful smoke
  does not qualify that artifact numerically. FP32 remains a separately versioned
  evaluation candidate, not the app's new production default.
- The next step is the already planned **Stage 2 quality screen**, not another model
  search: compare the current D3 control and explicitly identified FP32 reference
  with the old C7 reviewer and one frozen boundary-focused local reviewer.
- Use the foreground guard, per-request progress/checkpoints and bounded deadlines
  in that evaluation harness. Count timeouts/errors rather than silently retrying
  them. Include the two actual Stage 1 generation attempts so far (the prior timeout
  and this success) when accounting for the existing overall attempt budget; the
  watchdog control consumed no generation attempt.

The planned screen is 112 unique inputs / 160 scored packets, with the existing
precision-first gates and maximum 256 local generation attempts including smoke/
repeatability checks. Freeze the exact allocation across reviewers before inference;
do not interpret 160 packets as permission for 160 calls per reviewer plus unlimited
retries. It still requires later fresh held-out validation before any promotion.
Estimate remains 4–8 hours for preparation, phone execution and analysis, with
per-unit pause/resume checkpoints. Keep the phone connected/unlocked for inference;
Mac-only preparation and reporting do not need it.

## Verification and handoff

- Signed isolated phone probe build succeeded. The bundle is
  `SimpleStudio.Remember.GenerationTrace`, not the personal Remember app.
- Both native units passed their respective gates; the actual generation produced
  a successful atomic result, not a host-synthesized timeout closure.
- **48 Python tests passed** across the new six result-gate tests and the prior
  boundary/precision/evaluation/phone/parity/sentence runner suites.
- Artifact verification and `git diff --check` passed. The original readiness
  timeout/closure and prior checkpoint evidence were separately hash-verified.
- A paused run returned exit 75. Completed replay dispatched zero new native units;
  both saved output hashes and modification times remained unchanged.
- The runner is paused, both processes exited, and `safeToClose` is true. No Git
  state was changed. No main-app installation or private-library access occurred.

Files added: `scripts/ios27-generation-trace/` and this matching evaluation folder.
Updated overview documentation links here. Key evidence: `manifest.json`,
`protocol.json`, `units/phone/`, `progress-01.json`, `summary.json`,
`pause-resume-proof.json` and `checkpoint.json`.

```sh
python3 -B scripts/ios27-generation-trace/run.py status
python3 -B scripts/ios27-generation-trace/run.py verify
```

Do not rebuild over the frozen attempt. Resuming this completed diagnostic does not
start Stage 2 or issue another model request. Stop here for the planned review.
