# C7 — local semantic-verifier diagnostic

Approved after C6. This is a bounded, Mac-only follow-up using Apple's existing
on-device Foundation Models runtime. No training, downloads, cloud fallback, app or
ledger changes, device tests, or Git operations. Stop after the report for user review.

## Scope and limits

First check `SystemLanguageModel.default.availability`. On this Mac the initial check
reported available. Verify the C6 completion receipt before preparing the new run.
Freeze code, prompt, tests, input bytes, C6 reference and cached legacy predictions
before any task inference. No prompt/threshold/model selection after seeing results.

Use the existing 160 agent-reviewed C6 packets, deduplicating only exact ordered pair
and source content (112 distinct contexts). The prompt author has seen C6 findings:
**this is exposed-data diagnostic reuse**, not a fresh benchmark or qualification.
A positive result would justify a separate fresh, independently reviewed test; do not
claim generalization, train, or create that next checkpoint automatically.

## Candidate and output contract

Each distinct context gets a new session with `SystemLanguageModel.default`, default
guardrails, greedy sampling and a maximum of 600 response tokens. No tools, history,
retrieval or application state. Only source IDs, text and queried pair are transmitted
locally; no query/view IDs, gold, scores, family or episode labels, or reviewer notes.
Use the full packet without truncation. Enforce a 16,000-character prompt-input limit.

Structured output contains evidence (up to four exact visible-source quotations), a
same_project/separate_projects/abstain verdict, and one short explanation. Decisive
outputs must cite both queried sources. Validate exact substrings and IDs; quotations
prove provenance, not semantic entailment. Preserve native responses, including invalid
evidence. Malformed outputs, refusal, unavailability, timeout and process errors are
**errors**, never correct abstentions. No automatic retries or quote repair.

Compare 14 fixed candidates: four cached legacy controls, local verifier, always-abstain,
four conflict-veto combinations, and four confirmation combinations. Veto: explicit
local separate overrides legacy; otherwise retain legacy. Confirmation: explicit local
separate overrides; same requires both local and legacy same; otherwise abstain.
If local inference fails, dependent combinations also record an error, not silent
fallback. No grouping or split operation is executed by any candidate.

## Execution, pause and integrity

Build one isolated Swift command-line executable with caches/output under runs/c7-01.
Allow up to 256 MiB planned build overhead within the cumulative 4 GiB diagnostic cap
(including the existing 1 GiB simulator reserve); maintain 10 GiB free disk space.
Bound each model process to 60 seconds; terminate/reap it on timeout. One process and
one request at a time. Save each raw response and validated outcome as an immutable
checksum unit before the next request. Stop after three consecutive terminal errors.
Any resumption after an error stop preserves those errors; no hidden reruns.

Use the shared worker lock and independent C7 pause marker. A pause request/signal
takes effect after the current request is saved, at most approximately 60 seconds.
Wait for the worker's exit acknowledgement before closing the laptop. Exercise one-unit
stop/resume, checking the first unit's hash and timestamp remain unchanged. Resume skips
verified units. Asset revisions are not exposed by the API; record macOS/toolchain,
availability, source and binary hashes, not an invented model-weight version. Greedy
sampling is not a guarantee of future bitwise inference reproducibility.

## Evaluation and stopping

Freeze all outcomes before loading reference labels in the evaluator. Report both
original and C6-adjudicated references; pair/context/family/partition/behavior breakdowns,
false same on separate, false separate on same, uncertainty assertions, same/conflict
precision and recall, error count/rate, valid coverage, and full-denominator correctness.
Errors contribute no true positives and remain in recall/correctness denominators;
precision is undefined with no assertions. Report raw latency separately from accuracy.
Contrast checks require every constituent output correct; errors fail them. Reconstruct
derived outputs/metrics from cached units without repeating model inference.

Prospective *exploration* gate for the local verifier on the contextual view: conflict
precision >=90%, conflict recall >=80%, same-project recall >=75%, unsupported decisive
assertions on uncertain inputs <=10%, and error rate <=5%. All conditions must hold;
undefined rates fail. These small exposed-data thresholds do not qualify production.
Keep all legacy seeds in comparisons; do not select a winning seed retrospectively.

If the gate fails, report which mechanism failed and stop; don't tune on these cases.
If it passes, recommend (but do not start) fresh independent validation. Unit tests,
saved stop/resume proof, complete inventory checks, deterministic replay and parent
verification are required before completion. Initial estimate 1–3 active hours,
updated after measuring inference. No phone required for this checkpoint.

## API references checked

Apple documents the on-device model and availability check in
[SystemLanguageModel](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel).
The installed macOS SDK also confirms guided generation and greedy sampling; it is the
build compatibility authority for this experiment, not newer beta-only APIs.
