# Stage 2 checkpoint — controls complete, reviewer screen interrupted

16 September 2026. **Stopped for review after a device-transport failure.** The
frozen grouping-quality comparison is incomplete; there is no new accuracy score
or production recommendation yet. Production, personal memories and Git state
were not changed. No paid API, cloud fallback, training or model retry occurred.

## Completed work

The [prospective protocol](PROTOCOL.md), two prompts, C7-compatible output schema,
dataset mapping, schedule, production source copies, model exports and signed
isolated app are frozen in `manifest.json`. The corpus is the exposed C5/C6
fictional diagnostic: 112 unique visible inputs mapping to 160 scored packets,
across eight agent-reviewed families. It is not new held-out validation.

| Check | Result | Interpretation |
|---|---:|---|
| Fresh phone pair controls | 56/56 completed | Both Apple embedding representations and both pair-model exports ran |
| FP16 versus FP32 pair decisions | 56/56 agree | No precision-induced acceptance difference in this set; not evidence of better grouping |
| Scheduled primary reviewer responses | 8/224 completed | Four distinct inputs reviewed by both frozen prompts |
| Valid pilot schema and quotations | 6/8 | Structural validity, **not** 75% judgment accuracy |
| Invalid pilot quotations | 2/8 | One response from each reviewer; retained as errors, not repaired |
| Pilot generation latency | Median 3.22 s; maximum 5.07 s | Excludes process launch/host overhead; small pilot only |
| Repeatability requests | 0/8 | Not reached |
| Runner regression tests | 64 passed | Eight iOS 27 runner suites |
| Full evaluator smoke | Passed | Synthetic outputs only, zero model calls; checks all 15 report variants |
| Pause/resume | Passed | First real phone unit retained its SHA-256 and modification time |

Fresh controls use copied production feature/matcher code and unchanged weights
and threshold. FP32 is still the separately versioned evaluation candidate. These
are pair acceptance controls, **not** the full online organizer's retrieval,
two-member corroboration, manual-placement protection or chronological River replay.

## Why collection stopped

After the eight-response operational pilot, the next reserved launch, `c7-004`,
returned CoreDevice error 1010: “Unexpected EOF while reading socket ID.” It
produced no console output. Both result-file and trace-file recovery checks failed
because the requested probe files were unavailable. The app remains installed and
its container accessible; a filtered process inspection found no running probe.

The available evidence does **not** establish whether the request reached the
model, nor whether cable, device services or another runtime issue caused the
connection failure. It is a transport/unknown-outcome event, not a wrong model
answer. The reserved attempt and raw error remain intact. It was not retried and
no synthetic native response was created to fill the gap.

The protocol required a stop on lost console/native failure, so collection stopped
without changing either prompt, threshold, output rules or sample set. Eight
confirmed generations plus one uncertain reservation count conservatively as nine
Stage 2 attempts. Including the two prior generation attempts gives **11/256**.
There are 223 unattempted scheduled generations, plus the unresolved disposition of
`c7-004`. The original schedule remains 224 primary + eight repeat generations.

## Saved state and safe shutdown

All 64 completed phone units have checksummed raw evidence. `verify` passes.
`process-closure.json` confirms the host worker is stopped and no probe process is
running: **it is safe to close the laptop or disconnect the phone**.

The frozen runner's generic `status` deliberately still reports `safeToClose: false`
because a reservation has no native outcome. It cannot interpret the separately
verified closure; this conservative discrepancy is recorded rather than patched
inside the frozen runner. Do not blindly run `resume`: it will refuse the unresolved
reservation. `collect` must never be replaced with a model relaunch for that unit.

## Next step requiring review

Approve a bounded connection-recovery check and a prospective continuation record
that explicitly retains the unknown launch as a transport error/missing outcome,
without retrying it. Then finish the **same** frozen reviewers and inputs, keeping
all error denominators and request accounting intact. No new prompt/model search.
Estimated remaining collection and analysis: **35–60 minutes after recovery**, if
the connection remains stable. Recovery time is uncertain.

Until the comparison is complete, do not rank the reviewers from this pilot, claim
an iOS 27 grouping uplift, deploy either reviewer or bypass the original FP16
historical numerical-compatibility failure. Even a successful completed screen
would only justify fresh validation, not automatic production promotion.

## Validation actually run

- `python3 -B -m unittest discover -s scripts/ios27-quality -p 'test_*.py'`: 16 passed.
- The same command for `ios27-boundary`, `ios27-evaluation`,
  `ios27-generation-trace`, `ios27-parity-diagnostic`, `ios27-phone-diagnostic`,
  `ios27-precision`, and `ios27-sentence-diagnostic`: another 48 passed.
- `python3 -B scripts/ios27-quality/run.py build --platform phone`: passed;
  signed isolated `SimpleStudio.Remember.GroupingQuality` installed successfully.
- `run --platform phone --device <id> --max-units 1`, pause, and bounded resume:
  56 controls and eight primary requests saved; pause returned expected exit 75.
- Continuing `resume`: failed at `c7-004` with CoreDevice error 1010; preserved.
- `collect --platform phone --device <id> --unit c7-004`: no checkpoint available.
- `python3 -B scripts/ios27-quality/run.py verify`: passed after stopping.
- Synthetic full-evaluator smoke: passed; fixtures used a probe-owned temporary
  directory which was removed afterward. No actual results were overwritten.

Key receipts: `pilot.json`, `resume-proof.json`, `validation/tests.json`,
`validation/evaluator-smoke.json`, `inspection/`, `process-closure.json`, and
`checkpoint-summary.json`. Experiment storage is about 4.35 GiB, below the 8 GiB
cap; approximately 43.2 GiB remained free at checkpoint, above the 10 GiB reserve.
