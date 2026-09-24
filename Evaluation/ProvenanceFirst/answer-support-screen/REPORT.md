# Stage B: development no-go; held-out inference not run

19 September 2026. **The local answer verifier did not qualify.** The approved
screen ran all 64 development questions and four fixed repeats, then stopped at
the development gate. No held-out model requests, prompt changes, retries, model
search, phone tests or app integration followed. Production D3 is unchanged.

The result is more nuanced than “the model understands only 28% of facts”: many
answers failed exact answer-form rules. However, genuine question/entity/conflict
errors remain, and presentation-only changes cannot make this run qualify.

## What was tested

The frozen v2 Mac Foundation Models verifier received the same cached B0 top-three
source packets prepared in Stage A. No labels, accepted-answer forms, categories
or lexical scores entered its prompt. One fixed prompt, unchanged native binary,
fresh sessions, greedy decoding and the original host validators were used.

The development set contains eight independently agent-reviewed fictional libraries,
64 questions: 32 answerable (16 current and 16 historical) and 32 non-answering
(eight explicit-missing, eight conflicts, eight topical-only, eight wrong-scope).
Examples concern theatre cue books, seed accessions, bicycle repair plans, museum
loans, sign designs, supper requests, fictional radio logs and booking records.
They are short English extracted text, not real user libraries or media parsing.

Evaluation fixtures and labels were already frozen/reviewed in Stage A. Their
**model predictions remain unconsumed** because development failed. This is not
a held-out generalization result, an iPhone comparison, or an evaluation of D3
project grouping. Agent review is not human ground truth. The corpus's hostile
instruction was not retrieved; do not infer prompt-injection robustness.

## Results and unchanged gates

| Development measure | Observed | Required | Result |
| --- | ---: | ---: | --- |
| Retrieved support | 30/32 (93.8%) | At least 29/32 | Pass |
| Strict answer precision after host validation | 9/25 (36.0%) | At least 90% | Fail |
| End-to-end correct answers | 9/32 (28.1%) | At least 24/32 | Fail |
| Current / historical correct answers | 6/16; 3/16 | At least 12/16 each | Fail |
| Libraries with a correct answer | 5/8 | At least 6 | Fail |
| Accepted unsupported assertions on non-answering questions | 3/32 (9.4%) | At most 1/32 | Fail |
| Validation/execution errors | 4/64 (6.25%) | At most 3/64 | Fail |
| Explicit-missing precision / recall | 6/17 (35.3%); 6/8 (75%) | 90%; 75% | Fail precision |
| Conflict precision / recall | 3/5 (60%); 3/8 (37.5%) | 90%; 75% | Fail |
| Valid, identical repeat pairs | 3/4 | 4/4 | Fail |
| Emitted invalid citations / source-list suppression | 0; 0 | 0; 0 | Pass |

All 64 primary native executions returned `ok`; the four primary errors came from
host validation, not model availability or timeouts. Three supported outputs were
rejected, leaving 25 accepted assertions from 28 raw supported outputs. Strict raw
answer precision was 9/28 (32.1%); raw false support was 4/32, reduced to 3/32 after
one invalid quotation was blocked. A quote can be valid yet support the wrong topic.

All four repeat pairs had **identical raw structured outputs**. One pair repeated
the same 167-character answer, exceeding the 160-character limit, so only three pairs
met the combined validity-and-repeat gate. This is not observed nondeterminism.

Conditional on support being retrieved, 9/30 answerable questions passed the strict
answer/citation score. Of the nine credited answers, three used original accepted
forms and six used the approved v2 passage form. The 25 valid supported answer lengths
ranged 9–115 characters, median 42. Invalid answers remain in error counts.

## Baselines: do not confuse source selection with generated answers

| Layer | What its metric means | Development result |
| --- | --- | --- |
| R0: broad source browsing | Answer evidence present somewhere in top-three sources | 30/32 answerable targets; 64/64 source lists retained; no answer assertions |
| R1: fixed lexical diagnostic | Returned source is answer-bearing under corpus gold | 20/30 correct selections (66.7%); 20/32 coverage; 10/32 false-support selections |
| V2: local verifier | Accepted answer matches reviewed form and full citation rules | 9/25 strict answer precision; 9/32 coverage; 3/32 accepted false support |

R1 does not generate an answer, so its 66.7% is **not** directly comparable with
V2's 36% as answer accuracy. V2 made fewer unsupported assertions than R1, but it
does not meet the intended safety/usefulness gates. No layer here proves external
truth; even correct support is evidence about what a stored source says.

## What the failures mean

Post-hoc diagnostic grouping of all 32 answerable questions, without rescoring:

| Exclusive category | Questions |
| --- | ---: |
| Correct under frozen primary rules | 9 |
| Qualifying citations, but answer not one of the approved forms | 13 |
| Wrong non-answering state despite retrieved support | 5 |
| Host-validation failure with support retrieved | 3 |
| Retrieval missed the needed support | 2 |

The 13 form mismatches include answers such as `handling code FOLD-9`, where the
rubric allowed `FOLD-9` or an exact reviewed sentence. Others add adjacent source
sentences. They have qualifying citations but are not automatically approved as
good answers; this diagnostic does not change the score or create new gold labels.
It would be misleading to label all 13 as established factual hallucinations.

Even the optimistic hypothetical of crediting all 13 would yield 22/25 precision
(88%) and 22/32 coverage (68.8%), still below 90% and 75%. It would not fix the three
accepted unsupported assertions, state failures or invalid outputs. This is an
illustrative upper bound for **answer-form-only** changes, not a measured new score.

Concrete interpretation failures include:

- **Wrong entity:** asked which courier was confirmed for Tide Bowl loan L-14,
  it answered using Dune Jug loan L-41's courier. The quote was real but irrelevant.
- **Unresolved conflict:** two Rill-62 closing tallies said 43 and 47 packets; it
  asserted 47. Two Oriole deposit records said 30 and 40 tokens; it asserted 40.
- **Question sensitivity:** asked whether a sound level had been recorded, the
  source directly answered no, but the model chose `explicit_missing` rather than
  a supported negative answer. Similar errors occurred on permission/measurement
  questions. These are contract/state failures, not all invented facts.
- **Wrong detail:** asked where Rill-62 should be stored, it claimed missing
  information even though cabinet K was present, apparently mixing that fact with
  an unmeasured germination percentage in the same source.

The four host errors were: overlong answer, non-verbatim/capitalized answer outside
the quoted evidence, missing required evidence, and a reordered non-verbatim quote.
Two missing-information responses also cited unrelated extra sources. Conflict
outputs sometimes cited the wrong passage or omitted part of the reviewed quote.
None received post-hoc credit. See `error-analysis.json` and the immutable decision
rows for exact inputs, outputs and failure classifications.

## Uncertainty, runtime and storage

The predeclared 2,000-draw library-cluster bootstrap (eight libraries, seed 20260919)
gave descriptive 95% intervals: strict precision 16.7–50.0%, recall 9.4–46.9%, and
accepted false-support rate 3.0–18.8%. All 2,000 draws had defined ratios. These small,
correlated fictional samples are not a production reliability estimate; intervals
do not remove review or dataset-construction bias.

On the Mac's unchanged macOS 27.0 build 26A428 runtime, primary native elapsed time
was 1.508–7.771 seconds, median 3.796 seconds. Probe-only peak RSS was about 19.33–21.08 MiB.
This excludes the system model service and does not measure total model RAM,
true cold-start latency, app size or iPhone performance.

68 new requests were spent, **77 cumulative** including the preserved nine earlier
attempts. Held-out requests: **zero**. The unused request allowance is not permission
to bypass the failed development gate or try another model/prompt. At final audit,
conservative growth was 19.44 GiB of 21 GiB, free space 22.43 GiB, reserve 10 GiB. The original
baseline was retained. New screen artifact folders total about 1.5 MiB; whole-Mac
accounting changes are not all caused by this experiment.

## Checks and recommendation

- `sb_qa.py`: 342 tests passed (317 prior plus 25 new); full commands in `tests.json`.
- `sb_runner.py prepare`, `freeze`, `run --split development`, `audit`: completed.
- Full raw replay reproduced the saved failed decision; prior v1/v2 bindings,
  eligible source packets, request counts and source lists passed audit.
- Actual evaluation authorization was checked read-only and rejected before
  dispatch; `evaluation-lock-proof.json` confirms zero held-out reservations.
- Pause/resume preserved schedule bytes and modification times. Mocked tests
  exercised in-flight interruption, host timeout, refusal and unknown reservations.
- The 25 screen tests passed again after execution; whitespace/Git diff checks passed.
- Worker and owned probes exited. No production files or Git state changed.

**Do not integrate this answer verifier. Do not reopen evaluation or loosen the
rubric to make this run pass.** Keep D3 and previous production behavior unchanged.

The next best product checkpoint is a separately approved **source-first history
browsing prototype**: explicit current/history scope, ranked original sources,
clear revision/archive context and a direct route into the River, without an AI
claim that an answer or project relationship is established. Preserve ordinary
search and verify the real app's indexing/migration/privacy behavior before any
integration. The retained-history foundation provides value independently of this
failed answer layer; this recommendation is not permission to ship it automatically.

If answer automation is revisited later, separate question/entity/conflict behavior
from answer-form coverage using fresh examples and a predeclared citation policy.
Do not silently relabel the consumed development set or treat this run as a held-out
win. Pro/cloud work stays separate. This checkpoint is stopped for user review.
