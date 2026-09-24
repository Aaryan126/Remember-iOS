# Answer-format review: concise, source-backed extracts

19 September 2026. Review checkpoint only. **No new model calls, scoring-code
changes, gold-label changes or app integration.** The previous failed qualification
remains failed. This document proposes a separately versioned next experiment.

## Recommendation

Accept either an existing approved answer span or its exact, independently
reviewed supporting passage, provided the answer stays within **160 characters**.
Prefer concise wording, but measure brevity separately from factual/citation
correctness. Do not accept arbitrary surrounding sentences just because they
contain the expected word or number.

For example, a source saying `Gate code: FERN-42.` can support either `FERN-42`
or `Gate code: FERN-42.` when both are preapproved for that question. This proposal
does not turn the observed ORBIT-27 control into a passed test or prove future
model performance. We changed our recommendation after seeing that one failure;
the next experiment must disclose that fact rather than claim an untouched design.

The product remains: save anything, recover the right context, and show project
development with evidence. This changes answer presentation, not project grouping,
retrieval, the four evidence states, or the requirement for source-backed answers.

## What the repository review found

`as_policy.validate_output` already accepts a verbatim answer up to 160 characters
inside a supplied citation. The stopped response passed that validation. The
stricter check lives in the exact expected-answer control and offline scorer's
`answerSpans` lookup. There is no reason to increase context length, the answer
limit, or app/model size to address this particular mismatch.

Across the 64 corpus-supported questions, there are 72 supporting annotations
(some questions have multiple valid sources):

| Annotation-level inspection | Development | Evaluation |
| --- | ---: | ---: |
| Supported questions | 32 | 32 |
| Supporting annotations | 35 | 37 |
| Reviewed support passages within 160 characters | 35 | 37 |
| Those passages already in accepted answer strings | 1 | 1 |
| Candidate additional passage-form entries | 34 | 36 |

Thus 70 annotation entries could admit their reviewed passage form without any
length-limit increase. These are **candidates for a format addendum**, not 70 new
questions, newly proven answers, unique strings, or measured model improvements.
The proposed additional answer form still needs review for focus and preserved
qualifiers; being a supporting citation does not automatically make every word
in it an appropriate short answer.

The old retrieval remains 30/32 and 31/32 supported questions. Its three misses
remain misses. No missing evidence is supplied or repaired by this format change.

## Proposed v2 contract

| Aspect | Rule |
| --- | --- |
| Answer form | One contiguous verbatim extract: an approved compact answer or approved supporting passage; no concatenation, paraphrase or generated explanation |
| Length | Keep 160 characters, whitespace and exact-source checks; no silent trimming/repair |
| Meaning | Exact requested entity, time and fact; preserve negation, units, uncertainty and revision qualifiers |
| Evidence | Same eligible source/revision and exact reviewed support passage; other citations must support the same fact, not merely match wording |
| Four states | Keep `supported`, `explicit_missing`, `conflicting`, `not_established`; non-supported answers remain empty |
| Failures | Runtime/schema/citation errors remain errors, never successful abstentions |
| Retrieval | Same top-three B0 packet, order, scopes, source visibility and source-list fallback |
| Product safety | No tools, cloud fallback, memory mutation, automatic merging or claim of external truth |

Keep the current evidence-passage scoring rule: every emitted citation must contain
its reviewed support passage. This review does **not** loosen the separate issue
of plausible shorter citations documented in v1 SCORING.md. A copied passage is
not sufficient without correct entity/time, evidence identity and verdict.

### Evaluation addendum, not a rewritten dataset

Create a new answer-form addendum keyed by split, library, question, source,
revision and answerKey. It references the original corpus hash. Preserve existing
accepted strings exactly; nominate only each existing gold `quote` as one possible
additional string. No new wording, source selection, value, state label or retrieval
change. Independent reviewers check all 72 support annotations in their question
and eligible-source context, before any v2 output. Record exclusions and reasons.
If the review finds an actual factual/label defect, stop and report it; don't hide
the correction in a formatting addendum.

For v2 primary credit, require the same correct verdict, cited identities and
reviewed evidence as v1, plus exact membership in that citation's approved answer
forms. At least one cited passage must anchor the accepted answer. Other valid
citations can express the same answerKey differently. No substring-only credit,
case folding, punctuation stripping, regex extraction or LLM judge.

The addendum is an **offline evaluation rubric**, never a runtime answer lookup,
prompt hint, production whitelist or source of gold-label leakage. In the app,
exact-quote validation alone still cannot prove semantic correctness.

### Keep correctness and brevity separate

Report reviewed-answer precision/recall, false support, missing/conflict quality,
execution errors and citation integrity as primary measures. Retain all original
questions and errors in their denominators. Also report:

- Character-length distribution of valid supported answers, with an explicit
  count/denominator; invalid answers remain visible in error totals.
- How many correct answers use only legacy accepted forms versus the new passage
  form. If a string qualifies for both, count it once under legacy-compatible.
- Agreement with v1 accepted strings as a secondary compatibility metric—not
  a universal linguistic measure of minimality. Some old strings are already
  sentence-like. Do not call a passage-form answer a reasoning error solely for
  missing that secondary exact-form metric.

All numeric quality gates stay unchanged: retrieval ≥29/32; answer precision ≥90%;
≥24/32 correct (≥12 current, ≥12 historical, ≥6 libraries); false support ≤1/32;
missing/conflict precision ≥90% and recall ≥75%, each with ≥6 eligible packets;
errors ≤3/64; no integrity failures; all four per-split repeats match. Only the
predeclared set of acceptable answer forms changes in the new primary metric.
Retain the original v1 score and stopped report; no retroactive pass.

## Required deterministic examples before another model call

| Case | Expected outcome |
| --- | --- |
| Exact approved compact answer | Correct |
| Exact approved focused source sentence | Correct; report passage-form usage separately |
| Passage includes an accepted token but is not an approved answer form | No automatic credit |
| `permitted` cut from `not permitted` | Incorrect |
| Correct number from another person's source | Incorrect |
| Old value used for a current-scope question | Incorrect |
| Suggested value substituted for an approved value | Incorrect |
| Correct answer with an unrelated extra citation | Incorrect |
| Equivalent additional citation uses different wording | Can be correct; no identical-wording requirement for every citation |
| Two unresolved answers; model chooses one | Wrong supported assertion, even with a real quote |
| No recorded measurement; model supplies a value | Wrong supported assertion |
| Invented quotation, unknown candidate, 161-character answer | Validation error; no automatic repair |
| Oversized packet, timeout, refusal, malformed output | Error; source-list fallback retained |

Use new fictional values for these tests. These are planned cases, not newly
executed tests or measured v2 results.

## Bounded next checkpoint — proposal requiring approval

**Mac only, estimated 1–2 active hours; phone not needed.**

1. Create sibling v2 implementation/output folders. Bind the old stop, corpus,
   cached retrieval and binary hashes read-only; do not change or rerun v1.
2. Prepare/review the answer-form addendum and deterministic tests above. Reuse
   existing annotations and independent author/reviewer roles, not model grading.
3. Freeze one prompt with only the answer-granularity instruction changed from
   minimal span to concise verbatim extract. No example-driven prompt search.
   Keep the schema, model, greedy decoding and timeout/watchdog settings. Reuse
   the immutable native verifier binary if its interface/runtime bindings match.
4. Freeze four **fresh neutral cases**, one per evidence state, repeated twice.
   Declare all accepted compact/passage forms and evidence before dispatch.
   Require factual/citation/schema correctness and identical structured output
   within each repeat pair. Brevity is reported separately, not ignored safety.
5. Run at most eight new requests. Stop at the first failure; no retries, alternate
   prompts/models or hidden repairs. Save raw outputs, reservations and result.
6. Stop for user review. No Stage B or app integration follows automatically.

Saving/pause behavior stays the same: persist each completed unit, stop dispatch
when asked to pause, bound/cancel active work, confirm host exit, then report safe
to close. Resume verifies hashes and skips saved units; unknown attempts are not
blindly repeated. Preserve the original disk baseline, approved 21 GiB allowance
and 10 GiB reserve. No deletion or further resource increase is proposed.

### Request-budget detail that must not be hidden

One v1 request has already been spent. Eight fresh controls plus the unchanged
future benchmark 64+4+64+4 requests would make **145 total**, not the original 144.
Any approval for this proposal must explicitly allow eight new v2 controls
(nine control attempts including the preserved v1 failure) and, if the later
full screen is desired, a cumulative ceiling of 145. Do not reset the old counter,
drop a repeat, or claim the original 144 cap covers the same sequence.

This document authorizes none of those calls. The immediate approval would cover
only the new preparation/control checkpoint; Stage B remains a separate decision.
If qualified and later approved, Stage B retains its 2–4 active hour estimate.

## Review checkpoint and checks actually run

- Read the frozen contract, scorer, control implementation, failure receipt and
  independent packet-review caveats. No new agents or model requests launched.
- `as_approved.py runner verify` passed; native/corpus/code bindings preserved.
- `as_approved.py resources` passed under 21 GiB; original baseline unchanged.
- Read-only JSON inspection produced the annotation counts above and verified
  every file bound by `stage-a-stop.json`, including old report/status/resume.
- The existing answer-support unit suite and `git diff --check` are checked at
  handoff; their results are recorded in CHECKPOINT.md.

No v2 scorer, addendum, prompt, control set or model outcome has been implemented
or approved by this review alone. The next user decision is the bounded proposal
above—not another unbounded round of recommendations.
