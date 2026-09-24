# Bounded answer-support screen — plan for approval

19 September 2026. User asked to carry on with the checkpoint-2 recommendation.
This turn prepares the contract and plan only. **No new inference, dataset
authoring team, training, app change or phone deployment has started.**

Final planning check: execution is also **on resource hold**. The existing
`history/control.py resources` command exited 1 because conservative growth now
exceeds the approved 18 GiB cap. No limit or accounting baseline was changed.

## Decision and position in the larger plan

Keep the version-aware index; keep broad source browsing; test one small answer
verification task before considering app integration. Do not repeat a similarity
threshold sweep. Do not train another matcher or begin RL.

| Larger checkpoint | Position |
| --- | --- |
| Retained history, versions and citation integrity | Complete; 72/72 old benchmark targets reachable |
| History-aware relevance/abstention | Complete; B0 recovered 35/36 held-out answers, but strict B/C recovered only 5/36 and 3/36; neither qualified |
| Answer-support contract and narrow experiment | Contract/plan prepared here; execution awaits approval |
| App/phone integration | Not started; conditional on fresh quality evidence and separate approval |

The architecture to test is: explicit search scope → unchanged history-aware
retrieval → visible source list; the same top-three evidence packet → optional
verifier → cited extract, explicit missing fact, conflict, or no established answer.
The verifier's failure never empties the source list. It does not affect D3.

See [precise contract and examples](CONTRACT.md) and the
[unchanged preceding report](../history-recovery/checkpoint2/REPORT.md).

## Why this experiment, not another model search

Our saved errors show sources that closely match a question but explicitly state
the requested value was never recorded. Topic similarity is therefore not an
answerability test. This distinction is also the motivation for SQuAD's deliberately
plausible unanswerable questions. We borrow that evaluation principle, not its
dataset or reported performance. [Rajpurkar et al., 2018](https://aclanthology.org/P18-2124/)

Measure answer correctness and citation support separately. ALCE treats correctness
and citation quality as different evaluation dimensions; a citation-shaped output
is not sufficient evidence of a correct answer. Our first experiment is narrower:
verbatim extraction rather than generated multi-source prose.
[Gao et al., 2023](https://aclanthology.org/2023.emnlp-main.398/)

**One proposed candidate:** the existing Apple on-device Foundation Models runtime,
using one fresh session per question, greedy decoding, one fixed guided-generation
schema and one frozen extract-or-abstain prompt. This avoids a new weight download
and directly tests the semantic distinction the scores cannot establish. Apple
documents structured generation and notes that greedy results can change with
model updates; record the runtime identity and recheck reproducibility.
[Apple framework deep dive](https://developer.apple.com/videos/play/wwdc2025/301/)

This is a low-cost hypothesis, not confidence in that model. Prior local **project
relationship** reviewers failed badly. Their exact quotes did not prevent incorrect
semantic judgments. A much narrower extraction task may behave differently, but
that must be measured. If it fails, stop; do not automatically try more prompts,
models, training, cloud providers or a phone rerun to seek a better score.

## Scope and hard limits

- English, fictional short extracted text, explicit current/history scope; no
  original media, personal library, generated summaries, arithmetic, multi-hop
  synthesis, automatic organization or user-facing “verified truth” claim.
- Reuse checkpoint-1 native indexing and checkpoint-2 B0 lexical scoring, positive
  scores, maximum three distinct source/revision results, unchanged tie rules.
  Cache **fresh fixture** retrieval once. Old caches serve regression only; old
  held-out examples are consumed and must not become a new held-out set.
- One model, one prompt, one decoding setup. No prompt selection/grid on development.
  A failed development gate ends the screen before opening evaluation predictions.
- Model and scorer receive no gold labels. No tools, API key, proxy, cloud fallback,
  model download, adapter, new weights or dependency is allowed in this screen.
- Existing production sources and all frozen experiments remain unchanged. Put
  future implementation in sibling `scripts/provenance-first/answer-support/` and
  results under this folder / an isolated accounted run directory, never inside
  a previous frozen code manifest.

## Stage A — build and freeze the test; stop for review

**Estimate: 4–8 active hours. Mac first; phone not needed for fixtures/harness.**

1. Verify earlier checkpoint hashes and resource accounting. Recheck current Mac
   model availability using a bounded metadata-only probe. The last saved Mac
   result was `modelNotReady`; phone availability is not evidence of Mac readiness.
   If unavailable, finish non-inference preparation and stop. Do not download,
   change device settings or silently move the test to the phone.
2. Implement the isolated schema, exact-span/provenance validator, metric code and
   durable runner. Test these with deterministic mocked outputs: wrong IDs,
   wrong revision, negation, wrong entity, stale evidence, conflicts, refusal,
   malformed output, prompt injection, truncation, timeout and interrupted units.
3. Prepare 16 new fictional libraries: eight development, eight evaluation, eight
   queries each (128 total). Per library: four supported questions (two current,
   one archived-history, one superseded-history) and four non-answering cases
   (explicit missing fact, topical-only context, unresolved conflict, wrong
   entity/time or other scope distractor). History is included only when requested.
   Use at most 16 ledger events and at most eight sources per library.
4. Proposed agent review requires approval with this stage: separate author and
   reviewer roles, no self-review, distinct scenario families across splits, and
   documented adjudication before inference. Each receives CONTRACT.md, fixture
   format, examples, exclusions, split restrictions and chronology rules. Reviewers
   see no model outputs. No agents have been launched for this plan.
5. Include affirmative/negative question contrasts, plausible answer-shaped
   distractors, paraphrases, disagreements, explicit revisions and quoted hostile
   instructions. Spread missing/conflict wording across natural phrasing so a
   keyword such as “not” does not reveal the label. Keep related variants together
   in one library/split. Record agent-review limitations, not “human ground truth”.
6. Before model inference, freeze corpus gold and all eligible evidence judgments.
   Run/cache fixed B0 retrieval and derive separately reviewed packet labels, still
   blind to model output. Validate schemas, splits, spans, scopes, versions and
   reproducible index replay. Gold annotations never enter source-only packets.
7. If Mac readiness permits, run at most **eight** frozen neutral technical controls:
   four tiny extraction/schema tasks, each twice. Require valid outputs, exact
   spans and identical structured decisions on repeats. No benchmark prompt tuning.
   Use a host watchdog plus native cancellation/terminal receipt, not availability
   alone as proof generation works. One failed control stops inference.

**Saved checkpoint:** contract, source-only packets, corpus/packet labels, independent
reviews/disagreements, split definitions, native projections, retrieval cache,
prompt/schema/source/runtime hashes, tests, controls and pause/resume proof. Stop
and show the user readiness, coverage, storage and revised Stage B estimate. An
unsupported Mac is a hardware/runtime hold, not a negative model-quality result.

## Stage B — one controlled screen; stop for review

**Estimate: 2–4 active hours once runtime-ready. Mac if Stage A qualifies it.**
Phone use requires a separate explicit decision if the Mac cannot run the model;
do not mix device runtimes within a comparison or treat Mac timings as phone timings.

Compare on identical retrieval packets:

- **R0, source browsing only:** unchanged B0 sources, no asserted answer. Measure
  retrieval coverage; answer precision is not applicable, not perfect.
- **R1, fixed score-only diagnostic:** prior lexical minimum 0.50, margin 0.10,
  limit one. Treat a returned source as an asserted answer-bearing source for this
  diagnostic, not as implemented answer extraction. No recalibration. Compare
  answer-support selection precision/recall; exact-answer accuracy is not applicable.
- **V1, extract-or-abstain:** the single local verifier plus host validation.
  Measure both raw model semantic decisions and post-validation user-visible output.
  Invalid outputs remain errors; the visible source list is the same as R0.

Run 64 development packets, then four fixed repeat packets. If all pilot gates
below pass, freeze the development decision and code, then open the 64 evaluation
packets and four repeats. Otherwise stop without consuming evaluation predictions.
No “best failing candidate”, no retry selection, no evaluation-driven prompt edits.

Maximum **144 generation reservations total**: eight Stage A controls, 64+4
development and 64+4 evaluation. Failures and interrupted/unknown outcomes count
toward the cap. A 60-second native deadline with short cancellation grace, and a
separate bounded host watchdog, limit each unit. Freeze exact timeout/grace values
before controls. Missing/oversized context is an error, never silently shortened.

Report results by library and task type with exact numerators, retrieval coverage,
answer precision/recall, wrong-answer and false-support rates, missing/conflict
state precision/recall, execution errors, list availability, latency and memory.
Show conditional verifier performance when support was retrieved **and** end-to-end
performance over every answerable question. Do not drop retrieval misses or errors.
Report uncertainty intervals with library-level resampling; eight libraries remain
a small correlated pilot, not a production safety guarantee.

## Predeclared pilot gates

These are **new answer-layer feasibility gates**, not replacements for failed old
recovery/project/outside-River gates. They license a proposal for further validation,
not production integration. Freeze before data inference; require all on both splits:

| Gate (64 questions per split) | Requirement |
| --- | --- |
| Retrieval sufficiency | B0 supplies acceptable support for at least 29/32 answerable questions; otherwise stop to report retrieval limitation |
| Semantic answer precision | At least 90% of displayed `supported` answers are correct, with correct supporting evidence |
| Useful end-to-end coverage | At least 24/32 correct answers, including at least 12/16 current and 12/16 historical; present across at least six libraries |
| Unsupported assertion | At most 1/32 non-answering questions receives a `supported` verdict; raw pre-validation failures also reported |
| Explicit missing / conflict | Each state precision at least 90% and recall at least 6/8 where that state is present in the retrieved packet; require at least six evaluable gold packets of each kind, otherwise insufficient support/no-go |
| Operational errors | At most 3/64, kept in every end-to-end denominator |
| Integrity | Zero emitted invalid/altered citations, ineligible revisions, future evidence or source-list suppression; all binding/replay tests pass |
| Repeats | All four scheduled per-split repeat decisions and answer spans match their originals |

Packet-level missing/conflict denominators can differ from corpus-level counts
because retrieval may not supply all relevant evidence. Use exact measured packet
counts in the state recall gate: at least 75%, not a fictional fixed denominator;
6/8 above describes the complete-retrieval case. End-to-end counts always include
all original queries. No-support states caused by retrieval misses are reported.

If a gate fails, stop with a cause breakdown (retrieval, interpretation, abstention,
integrity or runtime). Do not loosen it. If all pass, propose a separately approved
fresh validation/device step; do not ship automatically. A later local-only UI must
still offer ordinary search when the model is unavailable.

## Pause, resources and resumption

Implement the familiar `pause`, `status`, `resume`, `verify` commands in the new
runner, with one lock and one serial model request. These commands do not exist yet;
do not copy an old experiment's resume command to start this task.

Reserve each request durably before dispatch. On pause, launch no next request;
finish/cancel the active bounded unit, save its terminal outcome and confirm the
owned process has exited before declaring safe to close. An unresolved reservation
is never blindly retried. Resume checks all hashes/runtime identity and skips
completed units without rewriting them. Save preparation progress per library too.

The original 18 GiB growth cap and 10 GiB free-space reserve remain unchanged.
At planning inspection, free space was about 23.9 GiB, but the conservative growth
measurement was about 17.99 GiB: only about 14 MiB remained under that cap. This
accounting includes whole-Mac free-space decline; free disk is not the same as
approved experiment headroom. No cleanup, baseline reset or increase is authorized.

The final check crossed that guard: a subsequent read-only snapshot measured
23.871 GiB free and 18.004 GiB whole-Mac free-space decline from the original
44,962,967,552-byte baseline. These are changing observations, not proof that the
experiment itself allocated 18 GiB; the two new planning documents total about
22 KiB. Preserve the failure and recheck before execution. If the user wants to
proceed despite this accounting hold, propose a separately approved **19 GiB**
growth cap for the new screen, keeping the original baseline and 10 GiB reserve.
That is a proposal only. Any approved amendment must use a new scoped controller
and receipt; never edit the earlier frozen 18 GiB controller or its results.

Stage A must stop before builds/inference if headroom is insufficient. Estimate
0.1–0.5 GiB additional bounded harness/cache artifacts, excluding any unapproved
model asset download. Before execution, either fresh accounting must demonstrate
sufficient headroom or the user must explicitly approve a resource-only amendment.
Do not prescribe broad deletion; identify exact safe-to-remove caches separately
if the user asks for cleanup. This planning turn adds only small Markdown files.

## Expected handoff and approval

Proposed execution total: **6–12 active hours**, excluding runtime readiness,
resource holds, user review and any later device integration. Eight neutral controls
are not a phone performance benchmark; app size/latency remain unmeasured here.

Approve Stage A's bounded scope and independent agent author/review work before
execution. Resolve the resource preflight before any sizable work. Stage A then
stops for review; Stage B needs a separate go-ahead. This plan authorizes no paid
API, no downloads, no Git writes and no app changes.
