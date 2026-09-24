# iOS 27 checkpoint: boundary compatibility and safeguards complete

**Stopped for review. Stage 1 is still incomplete because local generation did not
finish its smoke check. Stage 2 has not started. Production remains unchanged.**

## What this step achieved

| Check | Result | Meaning |
|---|---|---|
| Threshold-near pairs across 11 fictional libraries | 24/24 decisions unchanged with both precisions, fixed and fresh embeddings, on Mac and phone | No decision regression observed in this selected stress set |
| FP32 neural compatibility on those pairs | 48/48 directional outputs within original 0.002 tolerance; maximum error 4.17e-7 | FP32 is the numerically faithful evaluation candidate |
| FP16 neural compatibility on those pairs | 45/48 within tolerance; maximum error 0.01178 | Existing artifact remains an explicit comparison control, not numerically requalified |
| Current organizer/store/readiness-cache tests | 23/23 passed on physical iPhone; none skipped | Tested safety branches still work with current sources and actual SQLite stores |
| Local language-model availability | Available; context 4,096 | API reports ready |
| One tiny local-generation smoke request | No completed result by 120-second host deadline | Cannot start the reasoning-quality screen yet |

Detailed evidence: [boundary comparison](boundary/REPORT.md), [organizer safeguards](safeguards/REPORT.md),
[generation timeout and closure](readiness/REPORT.md), and the earlier
[precision/storage/latency comparison](precision/REPORT.md).

The evaluation-only identity is `d3-seed29-fp32-ios27-evaluation-v1`, using the same
seed-29 weights and threshold as D3 but a separate FP32 export. The original FP16
historical score gate remains failed. No reference, tolerance or threshold was
silently changed, and no production model was replaced. Native matching fidelity,
organizer safety and language-model usefulness are three separate questions.

This step made 96 native boundary units (288 directional/repeat predictions), plus
48 original PyTorch and 96 Python Core ML reference predictions. One local
generation attempt was made; zero paid/cloud requests and zero new training runs.
These previously exposed boundary cases are not a new held-out benchmark.

## Plan position and next step

1. **Stage 1 compatibility/safety:** numeric candidate and selected organizer/store
   tests are now complete. **Remaining blocker: successful local generation smoke.**
2. **Next action:** a bounded, instrumented generation-readiness diagnostic, preserving
   the timeout and limiting retries. Mac + connected unlocked phone; approximately
   1–2 hours, excluding device/model waiting or a platform repair. Stop on another
   unexplained stall rather than starting a model/prompt search.
3. **Stage 2, only after readiness and review:** the planned 112 unique inputs / 160
   scored packets, comparing current D3 controls and the frozen FP32 reference with
   the old C7 reviewer and one boundary-focused local reviewer. Keep strict
   precision-first gates and report fixes versus damaged D3 decisions. Previous
   estimate remains 4–8 hours including preparation, execution and analysis; phone
   availability and generation speed may change it.
4. **After a positive screen:** separate fresh validation and suggestions-first
   integration review, not automatic deployment or rewriting existing placements.

There is no measured grouping-quality improvement from this checkpoint. The user
experience benefit demonstrated here is narrower: tested placement protections hold
and this selected set retains the same grouping decisions on the new platform.

## Validation and pause state

- Both boundary probe builds completed; all 96 native units completed without errors.
- Isolated current-source app/test build completed after correcting only the generated
  test target's signing configuration. Xcode reports 23 executed tests passed.
- Python test discovery passed: boundary 3, precision 6, evaluation runner 12,
  phone diagnostic 8, parity diagnostic 8, sentence diagnostic 5 — **42 total**.
- `run.py verify` passed for boundary, safeguards, readiness and original precision
  evidence; `git diff --check` passed. No Git state-changing command was run.
- The completed boundary replay dispatched zero additional units on Mac or phone.
  Pause returned exit 75; saved first-unit hashes/timestamps remained unchanged.
- The timed-out generation probe was explicitly terminated and its absence checked.
  It has a host closure receipt, not a fabricated successful native result.
- Work is saved and stopped; **safe to close the laptop or disconnect the phone**.

Sources/harnesses added: `scripts/ios27-boundary/`, `scripts/ios27-safeguards/` and
`scripts/ios27-readiness/`. Reports/checkpoints are under their matching evaluation
directories. Updated overview docs link to this checkpoint. No production source,
weights, thresholds, lockfile or personal data changed in this step.
