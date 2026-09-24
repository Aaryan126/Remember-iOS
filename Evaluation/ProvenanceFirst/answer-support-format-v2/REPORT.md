# Answer-format v2: qualified technical checkpoint

19 September 2026. **Eight of eight fresh neutral controls passed.** All four
repeat pairs produced identical structured output. This qualifies the local Mac
runtime and revised answer-format contract for a proposed dataset screen; it is
not evidence of benchmark accuracy, production readiness, or better grouping.

This checkpoint is complete and stopped for user review. Stage B, phone testing
and app integration have not started. Production D3 is unchanged.

## What changed

The isolated v2 scorer accepts either an original approved compact answer or an
exact independently approved support passage, still within 160 characters. It
does not accept arbitrary strings containing the expected word/number. The same
question, source, revision, answerKey, verdict and citation rules remain required.
Primary correctness and legacy-form compatibility are reported separately.

Two opposite-author reviewers examined all 72 supported annotations in their
full question/source context before any v2 output:

| Review | Entries | Approved passage forms | Rejected | Additional forms beyond legacy |
| --- | ---: | ---: | ---: | ---: |
| Development | 35 | 35 | 0 | 34 |
| Evaluation | 37 | 36 | 1 | 35 |
| Total | 72 | 71 | 1 | 69 |

The rejected evaluation passage says the new queue cutoff is 21:45, replacing
21:15. It is valid evidence of the old time, but an unfocused full answer to the
historical question because it foregrounds the new instruction. The original
`21:15` answer remains accepted; no label or evidence was changed. Reviews found
no blocking gold defect. These are agent reviews, not human ground truth.

Only the answer-granularity phrase in the prompt and corresponding Swift Guide
description changed. The new isolated native binary uses the same schema fields,
limits, default model, fresh sessions, greedy decoding, 768-token response cap,
60-second native deadline, 2-second grace and 75-second host watchdog. The original
binary and all v1 outputs remain unchanged. The addendum is an offline rubric;
neither it nor expected answers are supplied to the model.

## Actual fresh local results

| Tiny technical case | Expected behavior | Result | Repeat |
| --- | --- | --- | --- |
| Recorded locker code | Supported exact cited answer | 2/2 passed | Identical |
| Soil pH explicitly not measured | `explicit_missing`, empty answer, exact evidence | 2/2 passed | Identical |
| Two inconsistent festival opening times | `conflicting`, empty answer, both passages | 2/2 passed | Identical |
| Badge color absent from storage note | `not_established`, empty answer | 2/2 passed | Identical |

Both supported outputs were `Locker code: LARCH-58.` with the identical exact
citation. Their answer lengths were 22 characters. Both used the preapproved
passage form: **2/2 v2-correct; 0/2 legacy-compact compatible**. This is a presentation
distinction, not an observed factual failure. No post-output repair or tuning was
performed. The previous v1 ORBIT-27 failure remains failed under its frozen rule.

There were zero runtime/schema/citation errors and no retries in these eight
controls. Four tiny cases repeated twice are a readiness check, not eight distinct
semantic examples or a claim of 100% real-world accuracy.

Runtime: Mac Foundation Models default model, macOS `27.0 (Build 26A428)`, available,
reported context size 8192. Per-request native elapsed time ranged **0.963–3.643 s**,
median **1.710 s**. Probe-process peak RSS ranged **19.19–20.41 MiB**. These exclude
the system model service's memory, are not total model RAM, do not distinguish
true cold/warm model loading, and are not iPhone measurements.

## Verification and saved checkpoint

- `v2_qa.py tests`: **317 tests passed** across nine suites (276 prior regressions,
  41 new tests). Exact commands and output are in `tests.json`.
- `v2_runner.py build`, `freeze`, and `controls`: completed successfully.
- `v2_qa.py audit`: passed; reparsed all raw receipts, verified request/reservation
  and frozen input/code/binary bindings, checked all 256 corpus/packet gold records,
  preserved v1 artifacts, and confirmed all owned probe processes exited.
- Pause/prepare/resume proof passed: completed proposals retained identical bytes
  and modification times; no inference was used for that proof. Mocked tests cover
  in-flight timeout/cancellation, refusal, malformed receipts, spent unknown
  reservations, repeat disagreement, tampering and first-failure stopping.
- `git diff --check` and a whitespace scan of the new Python/Markdown files passed.
  No Git state was changed.

Saved artifacts include both independent reviews, immutable addenda, code freeze,
build receipt, all eight requests/raw outputs/reservations/scored units, controls,
tests, pause proof, audit, status and resume instructions. The unchanged original
stop and failed control remain bound by hashes.

At the audit, conservative growth was **19.40 GiB of 21 GiB** and free space was
**22.48 GiB**, above the 10 GiB reserve. The original baseline was not reset; whole-
Mac free-space changes count conservatively and are not all experiment allocation.
No downloads, cleanup, paid API calls or phone work occurred.

## Recommended next decision

Approve **Stage B: one fixed development/held-out answer-support screen**, Mac
only, estimated **2–4 active hours**, with pause/resume and a final review stop.
Run 64 development questions plus four fixed repeats. Only if every unchanged
quality gate passes, run 64 evaluation questions plus four repeats. A development
failure stops before evaluation predictions; no prompt/model/scoring search.

Compare the same cached retrieval with source browsing, the fixed score-only
diagnostic and the v2 local extract-or-abstain verifier. Measure correct answers,
false support, missing/conflict decisions, citations, retrieval misses and errors;
also report compact-versus-passage usage separately. Source lists stay available.
The existing retrieval supplies support for 30/32 development and 31/32 evaluation
answerable questions; those three misses remain misses.

Nine lifetime requests are spent: one preserved v1 attempt plus eight v2 controls.
The proposed 136 Stage B requests fit the approved **145 cumulative ceiling**, but
the ceiling itself does not authorize Stage B. It requires the user's next go-ahead.
The current runner has no benchmark-dispatch path. Even a passing Stage B would
justify a separate fresh-validation/device proposal, not automatic app integration.
