# Stage A: prepared evidence screen, stopped at first technical control

19 September 2026. **No benchmark verifier evaluation or app integration.**

## Outcome

The fresh test set, native evidence replay and fixed retrieval pass preparation
checks. The first local-model control did not meet the frozen minimal-answer
format, so inference stopped as planned. Stage B is not qualified. This failure
does not show that the model gave a wrong fact.

## Preparation and retrieval

| Measure | Development | Evaluation |
| --- | ---: | ---: |
| Independently reviewed fictional libraries | 8 | 8 |
| Questions | 64 | 64 |
| Answerable questions supplied with support by fixed B0 | 30/32 (93.75%) | 31/32 (96.875%) |
| Explicit-missing packets retaining evidence | 8/8 | 8/8 |
| Conflict packets retaining both answers | 8/8 | 8/8 |
| Not-established packets, including retrieval misses | 18 | 17 |
| Historical questions also answerable from a current source | 1/16 | 1/16 |

Both splits meet the predeclared retrieval minimum of 29/32. These numbers measure
**retrieval coverage**, not model accuracy, answer precision or organization quality.
The preceding checkpoint used different data and is not a direct score comparison.
Sources remain a separate browsing layer; not all three returned sources are
asserted to answer a question.

The three retrieval misses remain in their original denominators:

- `dev06/q4`: collection-point evidence absent from the packet.
- `dev06/q2`: original meal absent; revised meal retrieved.
- `eval03/q3`: shoe evidence absent; unrelated costume/room records retrieved.

Source-only packets contain no gold labels or category/scoring metadata. Independent
opposite-split reviewers checked all 128 actual packets. All 138 event prefixes,
128 query scopes, 16 reopen checks and 384 returned citation occurrences passed
audit. Fixed B0 replay and packet-label hash/mtime replay match.

## First neutral control: exact result

Question: `What exact receipt code was recorded?`

Supplied fictional source: `Receipt code: ORBIT-27.`

| Field | Frozen expectation | Actual |
| --- | --- | --- |
| Verdict | `supported` | `supported` |
| Answer | `ORBIT-27` | `Receipt code: ORBIT-27.` |
| Citation | Exact supplied candidate and sentence | Exact supplied candidate and sentence |

The native process completed successfully; schema, length limits and verbatim
citation validation passed. The answer sentence is factual and source-backed,
but it is not the exact minimal span declared by this control. The saved score
remains **failed**. It was not regraded, repaired, retried or prompt-tuned.

One request was reserved and completed. The remaining seven controls, repeat
checks and all benchmark verifier predictions were **not run**. Missing-fact,
conflict and unsupported-answer behavior are not yet tested on the real model.
Qualification remains failed—not a model-quality score of zero, a hallucination,
or an unavailable runtime.

Observed native time was 3.18 seconds for this single tiny request. Process peak
resident memory was 19,677,184 bytes (~18.8 MiB), **excluding the system model
service**. Neither number is a cold/warm benchmark, total model-memory measurement
or phone estimate. Mac runtime: macOS 27.0 build 26A428, available, context 8,192.

## Verification and preserved history

- 276 automated tests passed across eight suites: 80 answer-support tests and
  196 earlier regression tests. Exact commands/results are in `tests.json`.
- Native launcher and Foundation Models verifier compiled. The latter emitted a
  non-fatal deprecation warning for the `sampling:` initializer; it was preserved
  instead of changing frozen code after compilation.
- Final evidence audit, `runner verify` and `git diff --check` passed.
- Independent read-only audit confirmed raw control, input, reservation, build,
  corpus, code, amendment and stop-classification bindings.
- The approved allowance increased from 19 to 21 GiB. Original baseline and
  10 GiB reserve stayed unchanged. Final observation was about 19.52 GiB
  conservative growth and 22.35 GiB free. Whole-Mac changes affect this guard;
  these figures do not describe app size or new experiment storage alone.
- Original resource failure and early launcher rejection remain preserved. The
  latter required a separately scoped launcher, not old-output modifications.
  The resume-status correction preserves exact old status bytes while permitting
  only the live progress counter to advance; immutable results retain hash checks.
- Pause/resume preservation passed. All workers/probes have exited; simulator
  shut down. No phone, paid API, model download, training, production change,
  Git-state change or previous-result rewrite occurred.

## Limitations and next decision

This is a small English fictional pilot, agent-reviewed rather than human-reviewed.
Libraries are correlated and share a controlled task structure. The hostile text
authored in evaluation was not retrieved, so those packets do not test injection
exposure. SCORING.md documents conservative reviewed-passage credit and separately
flagged unreviewed shorter quotations. None of this qualifies project grouping,
outside-River suggestions or production reliability.

Recommendation: agree answer granularity before another inference run. For evidence
recovery, a concise verbatim sentence may be more appropriate than insisting on a
bare value. Keep minimal-span compliance separate from factual/citation correctness.
If approved, record a new contract/scoring version and accepted variants **before**
further inference. Preserve this failed result and existing gold. A changed contract
may require separately reviewed annotations; do not silently relax the old gate or
switch models/prompts because of this result.

No further experiment is authorized by this report. A bounded contract review is
estimated at 30–60 minutes. Revised controls and Stage B need a fresh go-ahead.
The original Stage B estimate is 2–4 active hours after a qualified setup, not work
that is currently running.
