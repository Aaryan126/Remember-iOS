# Provenance-first project memory

Approved product direction, 17 September 2026:

> Save anything. Recover the right context. See how your projects developed—with evidence.

The differentiator is trustworthy context and traceable project history, not a
promise that every capture can be automatically filed with certainty. General
capture/search stays broad. Projects represent specific continuing undertakings.

## Shipped versus proposed

The current organizer remains D3 (`d3-p2-seed29-corroborated-v1`). Existing source
preservation, multi-thread assignments, manual corrections, provenance replay and
evidence search are reusable foundations. No existing placements are migrated.
The prior iOS 27 quality screen did not qualify either local reasoning reviewer.

Proposed additions are supported multi-project associations without project
merging, explicitly unresolved associations, and source-linked retrieval suggestions.
The eventual UI is optional review **inside the River**, with one/several/neither
project choices, never a question blocking capture. These additions are not shipped.

## Current work and gates

[The approved offline plan](../Evaluation/ProvenanceFirst/PLAN.md) has two mandatory
review stops:

1. Contract, independently agent-reviewed fictional benchmark, and ideal-label
   production-ledger replay. This proves representability, not model quality.
2. Only after review: frozen D3 versus retrieval-assisted and conservative
   relationship policies. Measure useful recovery, harmful decisions, uncertainty,
   chronology and costs before proposing integration.

Checkpoint 1 completed and was reviewed: 24 libraries passed native
replay, with 288 current and 288 historical prefix checks, 24 reopen checks, 31
ledger invariants, and 55 Python tests. At that checkpoint, the 96 query tasks were
reviewed but retrieval quality had not been measured. See the [checkpoint report](../Evaluation/ProvenanceFirst/REPORT.md).
No checkpoint-2 inference, new training, phone test,
personal-vault access or paid API request is part of checkpoint 1. Evaluation labels
are sealed from later policy selection, not from the author/review team. Agent
review does not establish real-user preferences or independently human-validated
accuracy. Fictional extracted media text does not test OCR/transcription quality.

Checkpoint 2 was subsequently approved and started. It first encountered a
[runtime-compatibility hold](../Evaluation/ProvenanceFirst/checkpoint2/REPORT.md):
two of 17 historical control embeddings exceeded the strict numerical tolerance
on the updated Mac, despite identical model identifiers. All 16 checked D3 pair
decisions remained unchanged and neural outputs matched exactly. These are
compatibility controls, not new quality results. No A/B/C benchmark predictions or
app changes had been made at that point; a broader, explicitly approved compatibility
check followed before resuming the comparison.

That separately approved [broader compatibility qualification](../Evaluation/ProvenanceFirst/checkpoint2/runtime-qualification/REPORT.md)
has now completed: 88 historical pairs across 12 libraries produced **zero changed
pair-threshold decisions** at all three planned cutoffs. Six final scores exceeded
the registered numerical tolerance, so qualification still failed. All six were
middle-score controls, far below automatic placement. This is not a measured
semantic-quality regression. The recommended next decision is to explicitly use a
current-runtime D3 reference for A/B/C, sharing frozen embeddings and scores across
variants while retaining historical results separately. The user has now approved
that [current-runtime amendment](../Evaluation/ProvenanceFirst/checkpoint2/comparison/PROTOCOL.md).
The Mac-only comparison is now complete and stopped for user review. Development
selection was frozen before evaluation predictions. It does not qualify shipped
Core ML outputs or change app behavior. See the [final comparison report](../Evaluation/ProvenanceFirst/checkpoint2/comparison/REPORT.md).

The original 4 GiB and approved 5 GiB resource guards both stopped work. The user
then approved an [8 GiB resource-only amendment](../Evaluation/ProvenanceFirst/checkpoint2/comparison/BUDGET-AMENDMENT-8GIB.md),
retaining the 10 GiB reserve and original accounting baseline. Saved units were
verified unchanged before each resume; all historical failures remain preserved.

Development selection found that none of the three C thresholds met its
95% precision requirement (the strictest achieved 75%), so the prescribed
suggestions-only fallback was frozen before held-out inference. Held-out results:

| Measure | A: current-runtime D3 | B: retrieval-assisted | C: suggestions-only |
| --- | ---: | ---: | ---: |
| Correct / automatic project edges | 30/84 (35.71%) | 30/84 (35.71%) | 0/0; undefined precision |
| Answerable macro recall@3 | 47.22% | 56.94% | 56.94% |
| Outside-suggestion precision | Not applicable | 5.26% | 7.25% |
| Historical recall | 0% | 0% | 0% |

Neither new variant qualified. The 9.72-point recall gain was below the registered
10-point gate, and suggestion precision was far below 90%. C avoided automatic
mistakes by not making automatic assignments, not by proving a better matcher.
All 12 historical questions required evidence excluded by current-source search:
nine archived sources and three superseded revisions.

Integrity did pass: 96 production-ledger replays, 1,152 current and 1,152 historical
prefix checks, 96 reopen checks, 31 invariants and 143 Python tests. Model and native
pause/resume checks passed; metrics recomputed identically from saved predictions.
No new variant was integrated and the isolated simulator was shut down.

This small, agent-reviewed fictional stress test is not app-wide accuracy or an
iOS regression measurement. In particular, project-membership edges are a different
task from the earlier pair-classification benchmark. D3 remains experimental.

## Later pipeline

The user has approved the [history-recovery plan](../Evaluation/ProvenanceFirst/history-recovery/PLAN.md).
Its first checkpoint has completed an isolated, version-aware evidence index
and a fresh independently agent-reviewed fictional benchmark. Ordinary search scope
remains current evidence; **Include history** is an explicit user choice. This is
not integrated into the app, and it does not change the D3 placement policy.

The [history coverage report](../Evaluation/ProvenanceFirst/history-recovery/REPORT.md)
records 24 passing native libraries, 288 prefixes in each scope, 24 reopen checks,
31 existing plus 33 history invariants, and 165 Python tests. All 72 expected
question-evidence targets were reachable, including every historical task.
This is candidate availability, **not** measured ranking, precision, abstention or
real-user accuracy. Checkpoint 1 stopped for review; the user subsequently approved
[checkpoint 2](../Evaluation/ProvenanceFirst/history-recovery/checkpoint2/PROTOCOL.md),
which has now completed the bounded Mac relevance/abstention comparison. On its
48 held-out questions, current lexical A recovered 23/36 answerable targets;
history-aware lexical B0 recovered 35/36, including 12/12 historical targets.
Both returned results for all 12 unanswerable questions. The frozen strict B/C
filters returned only five/three results, all correct, but recovered just 5/36 and
3/36 answers. That sparse 100% precision is **not a qualifying improvement**.
No development candidate passed the gates, and no evaluation reselection occurred.
196 Python tests, a 296-citation audit and identical metric replay passed. See the
[final report](../Evaluation/ProvenanceFirst/history-recovery/checkpoint2/REPORT.md).

This is global evidence search, not outside-River suggestions, automatic membership
or app-wide accuracy. The useful result is retained-history coverage, not a validated
answer-support policy. A related source can explicitly say the requested fact was
never recorded; similarity alone cannot distinguish that from an answer. The next
recommended decision is to define separate related-context, supported-fact and
unknown-evidence states before a narrow follow-up experiment. No app integration
or further experiment has started; checkpoint 2 is stopped for user review.

Following the user's continuation request, an [answer-support contract and bounded
plan](../Evaluation/ProvenanceFirst/answer-support/PLAN.md) are now prepared. The
proposal keeps retrieved sources visible and tests one optional extract-or-abstain
verifier, not another grouping/threshold sweep. Stage A prepares independently
reviewed fresh fixtures and checks runtime readiness; Stage B is a separately
approved development/held-out screen with a 144-request total cap. The original
planning checkpoint did not authorize execution; the subsequent approval and
current status below supersede its readiness and resource hold.

The final planning resource check exceeded the existing 18 GiB guard. The user
subsequently approved [Stage A and a scoped 19 GiB allowance](../Evaluation/ProvenanceFirst/answer-support/APPROVAL.md),
keeping the original accounting baseline and 10 GiB reserve. After the next hold,
the user approved 21 GiB and Stage A resumed. Its [report](../Evaluation/ProvenanceFirst/answer-support/REPORT.md)
records 16/16 native replays, 128 reviewed packets, 384 audited citations and 276
passing tests. Fixed retrieval supplies support for 30/32 development and 31/32
evaluation answerable questions; these are not model-accuracy results.

The first local-model control returned the correct cited sentence
`Receipt code: ORBIT-27.` rather than the frozen minimal span `ORBIT-27`.
Runtime/schema/citation validation passed, but the exact-format gate failed.
Inference stopped: one control request, zero benchmark requests, no retries or
prompt tuning. Under v1, Stage B remained unqualified and unapproved. The next decision was answer
granularity, not another model search; the original failed gate remains unchanged.
Workers and simulator are stopped. See [current status](../Evaluation/ProvenanceFirst/answer-support/STATUS.md) and
[resume instructions](../Evaluation/ProvenanceFirst/answer-support/RESUME.md).

The subsequent [answer-format review](../Evaluation/ProvenanceFirst/answer-support-format-v2/REVIEW.md)
proposes accepting an existing answer span or its exact independently reviewed
support passage, still within 160 characters. It separates factual/citation quality
from brevity, without arbitrary substring credit. All 72 supported annotations have
reviewed passages within the current limit; 70 do not already accept that passage
as an answer string. These are annotation-level findings, not model-quality gains.
That review was documentation-only. The user subsequently approved the isolated
[v2 implementation/control checkpoint](../Evaluation/ProvenanceFirst/answer-support-format-v2/APPROVAL.md)
and cumulative cap of 145, including the preserved v1 attempt. Independent reviewers
approved 71/72 proposed passage forms; one historical answer form was excluded as
unfocused, leaving 69 additions beyond legacy forms. Original labels, retrieval,
failed v1 result and stop checkpoint remain unchanged.

V2 now has **8/8 passing fresh neutral controls**, with identical structured output
in all four repeat pairs, and **317 passing regression tests**. Both supported
control outputs used the preapproved full sentence, not the legacy compact string.
This is technical qualification, not benchmark or real-user accuracy. Nine lifetime
requests are spent; **zero benchmark requests** have run. The
[v2 report](../Evaluation/ProvenanceFirst/answer-support-format-v2/REPORT.md) records
the frozen addenda, raw outputs, audit, resource accounting and limitations. Work
stopped for user review before Stage B; the user subsequently approved its fixed
Mac development/held-out screen, preserving all numeric gates and the
development-first stop rule. No phone testing or app integration was authorized.

That [Stage B screen](../Evaluation/ProvenanceFirst/answer-support-screen/REPORT.md)
has now stopped at **development no-go** after 64 primary requests and 4 repeats.
Strict answer precision was 9/25 (36%), answer coverage 9/32, accepted false support
3/32 and validation errors 4/64. Thirteen answer-form failures had qualifying
citations, so these strict scores must not be described as pure factual accuracy;
even crediting all 13 hypothetically would still miss precision and coverage gates.
Wrong-entity answers and one-sided conflict assertions remain substantive failures.
All four raw repeats matched, but one pair repeated the same overlong invalid
answer, leaving 3/4 valid-and-identical pairs. The 342-test suite and raw replay/audit
passed; **zero held-out model requests** were made. All 77 lifetime requests remain
counted, and original v1/v2 results are preserved. Production D3 is unchanged.

The verifier should not be integrated or tuned against this consumed development
set to claim a win. Next product recommendation is a separately approved
source-first history-browsing prototype with explicit current/history scope and
original-source/version context, not AI answer assertions or automatic relationship
claims. App integration still needs its own plan and approval. See
[current status](../Evaluation/ProvenanceFirst/answer-support-screen/STATUS.md).

The user subsequently approved continuing with the source-first direction. Its
[two-checkpoint plan](../Evaluation/ProvenanceFirst/source-browser/PLAN.md) now has
an additive **read-only foundation** implemented, with **52 passing native tests**
and **25 passing existing regression tests**. Source-only search has explicit
current/history scope, revision/snapshot-bound excerpts, archive and imported-gap
context, and a narrowly checked compatibility path for earlier note-restoration
events. It does not generate answers or change organization. See the
[foundation report](../Evaluation/ProvenanceFirst/source-browser/REPORT.md).

The subsequently approved UI/integration checkpoint is implemented and verified:
**21 real-store/state, appearance and thread-presentation tests**, **3 simulator UI
cases**, and the same **3 UI cases on a physical iPhone 17 / iOS 27** passed. Full
production-entrypoint app sources also built successfully in an isolated bundle.
Fourteen final simulator/phone screenshots were inspected. Threads now exposes
Search saved evidence, with Current/Include history scope and exact saved-version
details. The real Remember installation was not replaced; physical testing used a
separately signed, fictional-data Evidence Check app without shared app-group access.

Engineering tests do not establish better retrieval accuracy. Prior failed
ranking/verifier results, evaluation boundaries and D3 organization remain unchanged.
Multimedia original playback, current-River destination, VoiceOver, extreme-text
usability polish and large-library performance need further bounded checks before
a broader rollout. The first phone attempt timed out during automation setup;
an unchanged retry passed. Failed and resource-interrupted runs remain preserved.

Checkpoint-specific resource approval progressed from 21 to 24 to **26 GiB**, with
the original accounting baseline and 10 GiB reserve retained. No cleanup was needed
for the successful final continuation. Stop for user review; do not automatically
start another experiment. See the [integration report](../Evaluation/ProvenanceFirst/source-browser-ui/REPORT.md),
[integration status](../Evaluation/ProvenanceFirst/source-browser-ui/STATUS.md) and
[resume instructions](../Evaluation/ProvenanceFirst/source-browser-ui/RESUME.md).
Historical source bindings are preserved using an explicitly hash-checked archive
of the original Threads screen, not by rewriting past evaluation receipts.

The [retention audit](../Evaluation/ProvenanceFirst/history-recovery/AUDIT.md) distinguishes
retained source text from generated summaries, superseded versions from current
versions, and ledger-text locations from unavailable historical media timestamps or
page locators. Imported memories cannot reveal revisions that were never recorded.
Production `delete(id:)` currently archives, rather than erases; the prototype's
external tombstone filter is a fail-closed contract, not a shipped erasure registry.

The history foundation and ranking checkpoints have both reached their review
stops. Conditional device/app integration remains unstarted and is not justified
by these failed relevance gates. Explicit historical queries
need retained revisions/archived evidence with exact citations; ordinary current
search must not silently substitute stale content. The consumed evaluation set is
no longer untouched data for future tuning claims. Do not integrate B/C as-is.

The history checkpoint has a separately approved **18 GiB** conservative growth
cap with the original baseline and 10 GiB free reserve retained. Historical budget
failures and completed experiment results remain unchanged. See its
[ranking status](../Evaluation/ProvenanceFirst/history-recovery/checkpoint2/STATUS.md) and
[saved-checkpoint instructions](../Evaluation/ProvenanceFirst/history-recovery/checkpoint2/RESUME.md).

Confirmation-first placement safeguards deserve a separate product decision in
light of these errors. App changes and device validation need separate approval.
Project-aware training, formal uncertainty calibration, feedback learning and RL
remain deferred; Pro/cloud research remains separate. The free-tier production
model and historical qualification limitations are unchanged.

See [contract](../Evaluation/ProvenanceFirst/CONTRACT.md),
[resume instructions](../Evaluation/ProvenanceFirst/RESUME.md), and
[iOS 27 quality report](../Evaluation/iOS27/quality-continuation/REPORT.md).
