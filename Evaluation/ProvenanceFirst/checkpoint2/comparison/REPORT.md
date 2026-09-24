# Checkpoint 2 — provenance-first comparison

**Completed; stop for user review. Neither B nor C qualifies for advancement.**
The production ledger preserved histories correctly, but automatic project identity
and evidence relevance did not meet the registered quality gates. No app integration,
vault migration, new training, phone test, paid API call or Git write was performed.

## What was tested

The frozen, independently agent-reviewed fictional benchmark contains 24 libraries:
12 development and 12 held-out evaluation. Each has 12 events and four questions.
Events cover captures, revisions, explicit user corrections, archive and restore.
Libraries include separate projects sharing equipment or vocabulary, generic
reference material, genuinely shared sources, and unresolved statements.

Each library was replayed in chronological order and one dependency-valid alternate
order. The two orders are **correlated**, not independent libraries. Queries were
evaluated only at their original chronological prefixes: 48 per split, including
36 answerable and 12 unanswerable evaluation questions. No future text, gold
memberships, expected evidence, project titles or dependency metadata entered policy
or retrieval inputs. Explicit fixture corrections represent simulated user choices.

The reference is `d3-seed29-mac27-pf2-reference-v1`: the existing frozen seed-29
neural matcher, Apple embeddings and fixed feature combiner on the current Mac
runtime. It is **not embedding-only**, a newly trained model, or an LLM API.
All variants share immutable per-split scores. Earlier numerical-equivalence
failures remain failed; this study does not qualify shipped Core ML FP16 behavior
or establish an iOS 27 regression.

| Variant | Placement | Evidence recovery |
| --- | --- | --- |
| A | Current D3 policy, checked against actual native D3 for every capture | Up to three current-source hits in the routed River |
| B | Exactly A | Adds up to three unconfirmed outside-River suggestions |
| C | Conservative project proposals; automatic mode selected on development only | Same recovery rule as B |

C's automatic mode additionally requires exclusive project support and no competing
qualifying project. None of its three development thresholds qualified, so the
prespecified **suggestions-only fallback (`Coff`)** was frozen before evaluation.
It creates no automatic attachments; explicit user corrections still apply.

Questions do not provide a selected River. The declared, gold-free routing adapter
uses the highest-ranked current-source lexical hit to choose one. Search reuses
production chunking and lexical scoring; this is not a test of semantic query
embeddings or the complete app UI. B/C's common top-three metric scores the ranked
union of confirmed hits and suggestions, while outside suggestions are also scored
separately. See the [frozen protocol](PROTOCOL.md) and [metric definitions](../../METRICS.md).

## Held-out results

| Metric | A: D3 reference | B: retrieval-assisted | C: selected fallback |
| --- | ---: | ---: | ---: |
| Automatic project edges | 84 | 84 | 0 |
| Correct / wrong automatic edges | 30 / 54 | 30 / 54 | 0 / 0 |
| Automatic-edge precision | **35.71%** | **35.71%** | Undefined—no decisions |
| Unresolved captures assigned automatically | 6/24 (25%) | 6/24 (25%) | 0/24 |
| Answerable library-macro recall@3 | **47.22%** | **56.94%** | **56.94%** |
| Recall gain over A | — | +9.72 percentage points | +9.72 percentage points |
| Correct / returned top-three evidence identities | 18/92 | 22/144 | 22/144 |
| Pooled evidence precision@3 | 19.57% | 15.28% | 15.28% |
| Pooled evidence recall@3 | 18/39 (46.15%) | 22/39 (56.41%) | 22/39 (56.41%) |
| Correct / returned outside suggestions | — | 6/114 | 10/138 |
| Outside-suggestion precision | — | **5.26%** | **7.25%** |
| Unanswerable questions receiving results | 12/12 | 12/12 | 12/12 |

Precision counts eligible source/revision identities, not generated-answer truth.
There is no generated answer in this experiment. B/C found four additional eligible
identities in the common top three but added many irrelevant results. C's identical
combined retrieval score is expected: it uses the same global lexical ranking as B,
with different placement boundaries. It is not independent corroboration of B.

All 48 B/C query lists contained three identities. A returned zero/one/two/three
identities on **0/21/10/17** questions. Thus these low precision values are not hidden
by abstention; the tested recovery adapter effectively failed to abstain.

### Recall by question type

| Answerable mode | Questions | A | B / C |
| --- | ---: | ---: | ---: |
| Current context | 12 | 83.33% | 87.50% |
| Historical context | 12 | **0%** | **0%** |
| Overlapping projects | 12 | 58.33% | 83.33% |

All 12 historical questions requested unavailable evidence for this **current-source**
retriever: nine archived sources and three superseded revisions. This is a concrete
retrieval-coverage gap, not proof that the ledger lost history. Historical replay
passed. Fixing coverage would make those tasks reachable; it does not guarantee
correct ranking or a particular future score.

### Placement, overlap and fragmentation

The reference's 54 incorrect edges comprise 39 wrong-project assertions and 15
attachments to anchors without a unique capture-time gold project. Ambiguous/shared
anchors are treated as unsupported, as specified before evaluation. These are
project-membership judgments, not a repetition of the earlier pair-classification
benchmark; the percentages must not be compared as if the tasks were identical.

Of 194 capture opportunities across both orders, exact semantic membership sets
were recovered on 85 for A/B and 108 for C. Fresh singletons do not automatically
receive semantic credit, except canonical project roots; correctly unresolved
captures do. C's higher count does not imply useful automatic filing.

- A/B had 19 canonical-root pairs sharing a thread; C had zero. These are
  cross-project co-locations, **not explicit ledger merge operations**.
- Additional occupied threads across gold projects totaled 72 for A/B versus 112
  for C. Avoiding automatic decisions reduced misfiling but increased fragmentation.
- At the final prefixes, only 2/26 active shared-source instances appeared in both
  canonical Rivers for every variant. Both successes followed explicit corrections.
- C's unconfirmed project proposals recovered both projects on 16/24 shared capture
  opportunities, but proposal edge precision was only 89/247 (36.03%). High shared
  coverage alone is not enough to present those proposals as reliable.

### Per-library variation

Orders are pooled for edges; query recall uses chronological prefixes only.

| Evaluation library | A correct / automatic edges | A recall | B / C recall |
| --- | ---: | ---: | ---: |
| eval01 | 3/5 | 66.67% | 66.67% |
| eval02 | 3/7 | 66.67% | 66.67% |
| eval03 | 2/8 | 66.67% | 66.67% |
| eval04 | 2/4 | 33.33% | 66.67% |
| eval05 | 3/11 | 66.67% | 66.67% |
| eval06 | 4/10 | 33.33% | 33.33% |
| eval07 | 4/7 | 66.67% | 66.67% |
| eval08 | 0/5 | 66.67% | 66.67% |
| eval09 | 4/7 | 33.33% | 33.33% |
| eval10 | 1/7 | 16.67% | 50.00% |
| eval11 | 3/7 | 16.67% | 66.67% |
| eval12 | 1/6 | 33.33% | 33.33% |

## Development selection and gates

| Development policy | Correct / automatic edges | Precision |
| --- | ---: | ---: |
| A / C at production threshold | 45/73 | 61.64% |
| C at 0.99 | 46/66 | 69.70% |
| C at 0.995 | 39/52 | 75.00% |

All automatic C candidates failed the >=95% development precision requirement,
despite sufficient denominators. The fallback was frozen before evaluation; no
threshold, feature, label or model was retuned afterwards.

**Suggestions gate: failed.** Both require >=90% outside precision and >=10-point
macro recall gain. Observed outside precision was 5.26% / 7.25%, with a 9.72-point
gain. That gain is below the registered threshold; it must not be rounded into a
pass. **Automatic C gate: not qualified.** With no automatic edges, precision is
undefined and correct-A-edge retention is 0/30, not a safety/usefulness success.
Native integrity passed but cannot override either quality gate.

## What the failures look like

In `eval01`, a bat survey and an owl census share recorder R7. The owl source says
it produces a separate appendix and explicitly excludes bat totals. A nevertheless
attached it to the bat project in chronological order. Shared equipment and topic
similarity are not sufficient evidence of a continuing project identity.

In `eval02`, an old teaching-folder glaze card mentions a finish a cafe order might
use, but explicitly makes no customer-approval claim. A filed it into the project;
the benchmark labels it background material rather than confirmed membership.

For history, `eval10` asks for an original, superseded proof instruction. The
retriever only exposes the current revision, so even better ranking over its
current candidates cannot recover the requested original.

These examples come from the [frozen evaluation data](../../authored/evaluation.json).
They illustrate measured errors; they are not new rules added after the test.

## Integrity, reproducibility and costs

- **143 Python tests passed:** 55 checkpoint-1, 31 compatibility/control, 45
  comparison, 6 first resource-amendment and 6 second amendment tests.
- The Python A adapter agreed with native D3 for all 402 capture opportunities
  across both splits/orders. Native search citations were checked against the
  observed source version, quote and locator.
- **96 actual production-ledger replays passed:** A and selected C, 24 libraries,
  two orders. There were **1,152 current-prefix checks, 1,152 historical-prefix
  checks, 96 reopen checks and 31 invariants**. B shares 48 A receipts because its
  placements are identical. No implicit merge/split, correction loss or replay
  mismatch was accepted.
- One-unit model and native pause/resume proofs passed. The first native receipt,
  invariant receipt and both backing ledgers retained their hashes and timestamps.
- Both splits' metrics were recomputed from saved predictions and were byte-identical.
  Completed cache hashes, manifests, selection and native receipts were reverified.
- 226 unique source-version embeddings and 931 symmetric neural-pair results were
  cached. Median recorded native embedding subprocess duration was 160 ms on
  development and 166 ms on evaluation. Median amortized neural forward-pass cost
  was about 8 ms/pair. These are **Mac component timings**, excluding model loading,
  feature/policy/search work, safety checks and interruptions—not phone latency.
- There were no downloads, training, paid calls or app/model package changes.
  The comparison run plus its native replay artifacts occupied about 139 MiB at
  verification; this is not the total storage footprint of all earlier checkpoints.

The original 4 GiB and subsequently approved 5 GiB guards stopped work; both stops
were preserved. The user then approved [8 GiB](BUDGET-AMENDMENT-8GIB.md), retaining
the 10 GiB reserve and original conservative accounting. Approximately 5.90 GiB was
the highest passing sampled growth in the recorded 8 GiB runs; roughly 36 GiB
remained free at verification. Overall disk changes include activity beyond the
tracked experiment folders, including system swap. No cleanup or baseline reset
was performed. The isolated simulator was shut down after verification.

Key evidence: [selection](selection.json), [machine-readable result](result.json),
[development metrics](../runs/comparison-01/development/metrics.json),
[evaluation metrics](../runs/comparison-01/evaluation/metrics.json),
[native verification](native-verification.json), [final checkpoint](checkpoint.json).
Use [resume/reproduction instructions](RESUME.md) and the 8 GiB wrapper to rerun
`model score --split development`, `model score --split evaluation`, or
`ledger verify`; those verify saved evidence without rerunning model inference.

## Recommendation and boundary

**Do not promote B or C into the app on this evidence.** The experiment is complete,
but no replacement winner qualified. Existing D3 remains unchanged and experimental;
these findings should inform a separate review of automatic-assignment safeguards.

The highest-priority next plan should be narrowly retrieval-first:

1. Make retained source revisions and archived evidence retrievable for explicit
   history requests, with exact version/locator citations. Keep current-context
   results distinct from historical evidence and honor deletion/privacy semantics.
2. Improve evidence relevance and allow an empty result when support is weak.
   Optimize precision and useful recovery together; do not equate filling three
   slots with helping the user. Keep uncertain project relationships unconfirmed.
3. Evaluate on a fresh held-out set before any suggestions-first River integration.
   This evaluation has now been inspected and must not become a tuning set while
   still being advertised as untouched. Discuss confirmation-first placement
   safeguards separately; do not silently migrate existing Rivers.

Additional neural training, RL, app integration and physical-phone qualification
remain outside this checkpoint. Agent-authored/reviewed English fiction is a
stress test, not human-validated real-world accuracy. Extracted media text does not
test OCR, speech transcription or video understanding. No confidence or release
claim follows from this small, correlated benchmark.
