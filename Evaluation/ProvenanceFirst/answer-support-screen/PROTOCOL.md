# Approved Stage B — fixed answer-support screen

19 September 2026. User: “Great, carry on” following the completed v2 technical
checkpoint and explicit Stage B recommendation. Mac only, 2–4 active hours; pause
and resume supported. No phone, paid API, download, training, app integration or
Git-state changes. Stop after the bounded screen or on an operational hold.

Use the unchanged v2 binary, prompt, schema, model, decoding, answer-form addenda,
original corpus, cached retrieval and semantic/numeric gates. Prior qualifications
and failures stay immutable. This sibling runner is transport/reporting only.

## Frozen order and limits

Development: libraries dev01–dev08, q1–q8, then four repeats. Repeats are selected
before inference: library01 current_a; library02 archived; library03 explicit_missing;
library04 conflict. Evaluation uses the corresponding eval libraries/categories.
This spans answerable current/history and two non-answering states without selecting
repeats from observed results. Each split has 64 primary requests and four repeats.

Evaluation dispatch requires a saved, recomputable all-pass development decision.
One failed development gate ends the screen, leaving held-out predictions unconsumed.
No prompt/model/threshold/scorer search, automatic retry, or dropping errors. Ordinary
semantic errors do not trigger early stopping within development: finish its 68
requests to preserve the planned denominators. Unknown executions, resource/integrity
failures or changed runtime stop dispatch for investigation; known native errors
remain errors in the 64-question denominator, never successful abstentions.

At most 136 new requests; cumulative cap145 includes the already spent9 (v1=1,
v2 controls=8). Each attempt is durably reserved before dispatch. Unknown reservations
are never replayed. Completed units are immutable and reused on resume. Same 60s
native deadline, 2s cancellation grace and 75s host watchdog. Keep the approved
21GiB conservative growth allowance, original baseline and10GiB free reserve.

## Comparisons and scoring

- R0: unchanged cached B0 top-three source browsing. Report support availability;
  it makes no answer assertion, so answer precision is not applicable.
- R1: unchanged cached minimum0.50/margin0.10/top-one diagnostic. Report whether
  the selected source establishes an answer under corpus gold. This is source
  selection, not implemented extraction; exact-answer accuracy is not applicable.
- V2: same cached packet, one local extract-or-abstain response, frozen host
  validation and exact reviewed-answer/citation scoring. Retain all source lists
  on errors/abstentions. No answer/rubric/score/category enters the prompt.

Use the unchanged as_policy.gates: retrieval29/32, supported precision90%, correct
answers24/32 including12current+12history across6libraries, falseSupport<=1/32,
errors<=3/64, missing/conflict precision90% and recall75% with6gold packets perstate,
zero emitted invalid citations/scope violations/list suppression, all four repeats.
Repeat comparison uses identical full structured output, matching v2 qualification.
Host-rejected citations are execution/validation errors, not emitted citations.

Report raw verdict counts/false support/strict semantic correctness separately from
host-accepted assertions. Malformed/unknown-citation outputs cannot earn raw semantic
credit; no repair. Report corpus and packet correctness, legacy compatibility,
approved-passage usage, all valid supported answer lengths, error reasons, source
availability, task/library slices, native latency and probe-only RSS. Shorter real
citations that miss the reviewed quote remain primary failures, separately flagged;
do not call all exact-rubric failures established reasoning errors.

For uncertainty, predeclare 2000 library-cluster bootstrap draws, seed20260919,
eight libraries sampled with replacement per draw; percentile2.5/97.5 intervals
for precision, recall and false-support rate. Exclude undefined ratios only from
that interval's bootstrap denominator and report valid-draw counts. These small,
correlated, agent-reviewed fictional sets cannot establish production reliability.

Freeze new code, schedules, protocol, qualified binary and all relevant prior input
bindings before inference. Dataset scoring is offline only. No new quality gate,
answer form or threshold may be selected after outputs. Stage B success would
justify a separate validation/device proposal, never automatic integration.
