# C3 — does the hybrid help when the policy is matched?

**Yes, on these diagnostics.** With the same corroboration rule, every hybrid seed
beats the simple baseline on both wrong and missed attachment events across all eight
fixed-state lineages. The hybrid benefit is not just an artifact of assigning it a
better policy. However, absolute grouping quality remains too weak to recommend shipping.

Checkpoint complete on 2026-09-14; stop for user review. No further experiment started.

## What changed—and what did not

Added the missing simple-baseline corroboration control. Everything else stayed frozen:
12 fictional agent-reviewed stories, 36 chronological/shuffled streams, cached pair
scores, thresholds, eligibility, retrieval, correction actions and no-auto-merge rule.
No training, inference, downloads, phone/simulator run, production change or Git mutation.

The new generic policy implementation reproduced **all 252 existing controlled C2
traces exactly**, including decisions and every state. The new control added 36 online
streams / 579 prefixes. A bounded stop/resume preserved the first unit's bytes and mtime.

For the fixed-state audit, each of eight controlled lineages supplied all 432 pre-capture
states. Each of the eight policy variants evaluated the identical prior threads at each
state; counterfactual choices did not affect the next state. This produced **3,456
contexts and 27,648 decisions**, frozen before semantic scoring. All 3,456 own-lineage
decisions reproduced their original online decisions. These repetitions are correlated,
not thousands of independent examples.

## 1. Online results: each policy builds its own history

Wrong events are out of 360 eligible captures; missed events are out of 279 captures
with a known same-project predecessor. Final precision/recall pool pair counts over
all three orders, after scripted corrections and restores. A capture can be both wrong
and missed. Proposals/abstentions count as misses when valid links remain unresolved.

| Policy | Wrong events | Missed events | Final pair precision | Final pair recall |
|---|---:|---:|---:|---:|
| Baseline strongest (C2) | 106 | 165 | 60.4% | 38.4% |
| **Baseline corroborated (new)** | **55** | **224** | **69.4%** | **24.5%** |
| Hybrid strongest 17 (C2) | 94 | 173 | 60.2% | 37.7% |
| Hybrid strongest 29 (C2) | 91 | 177 | 60.5% | 37.7% |
| Hybrid strongest 41 (C2) | 101 | 169 | 60.2% | 41.6% |
| Hybrid corroborated 17 (C2) | 52 | 206 | 78.0% | 34.6% |
| Hybrid corroborated 29 (C2) | 54 | 202 | 75.2% | 34.5% |
| Hybrid corroborated 41 (C2) | 46 | 215 | 77.0% | 33.2% |

Corroboration helps the baseline avoid mistakes too, but it loses more valid grouping
than the hybrids. Relative to baseline corroboration, all hybrid seeds produce fewer
wrong and missed events and higher final pair precision/recall. All reused C2 metric
summaries match exactly; old results and qualifications were not replaced.

## 2. Fixed states: an apples-to-apples one-step comparison

Now earlier membership history is held identical within every comparison. Pooled wrong
events below are out of 2,880 eligible anchored contexts; missed events are out of 2,232.
These are **one-step counterfactual results**, not new end-to-end trajectories.

| Evaluated policy | Wrong events | Missed events |
|---|---:|---:|
| Baseline strongest | 714 (24.8%) | 1,502 (67.3%) |
| Baseline corroborated | 549 (19.1%) | 1,623 (72.7%) |
| Hybrid strongest 17 | 689 (23.9%) | 1,482 (66.4%) |
| Hybrid strongest 29 | 665 (23.1%) | 1,494 (66.9%) |
| Hybrid strongest 41 | 702 (24.4%) | 1,452 (65.1%) |
| Hybrid corroborated 17 | 499 (17.3%) | 1,588 (71.1%) |
| Hybrid corroborated 29 | 494 (17.2%) | 1,569 (70.3%) |
| Hybrid corroborated 41 | 489 (17.0%) | 1,566 (70.2%) |

The corroborated hybrid improvements persist in **every** anchor lineage, not just a
pooled average or favorable seed. Each cell below is change from the baseline using the
same corroboration rule on that same lineage: wrong events / missed events. Negative
numbers mean improvement. Each lineage has denominators 360 / 279.

| Anchor history | Hybrid 17 | Hybrid 29 | Hybrid 41 |
|---|---:|---:|---:|
| Baseline strongest | −5 / −8 | −6 / −11 | −5 / −12 |
| Baseline corroborated | −7 / −3 | −8 / −6 | −9 / −6 |
| Hybrid strongest 17 | −7 / −3 | −7 / −6 | −7 / −7 |
| Hybrid strongest 29 | −7 / −4 | −7 / −6 | −8 / −6 |
| Hybrid strongest 41 | −6 / −3 | −7 / −5 | −6 / −6 |
| Hybrid corroborated 17 | −6 / −5 | −7 / −7 | −9 / −7 |
| Hybrid corroborated 29 | −6 / −5 | −6 / −7 | −8 / −7 |
| Hybrid corroborated 41 | −6 / −4 | −7 / −6 | −8 / −6 |

This resolves the C2 policy confound on the tested examples. It does not establish
statistical independence, performance on new users, or a production-qualified winner.

## 3. Direct scores versus thread-state problems

Direct pair classification is identical across anchor histories because retrieval uses
observed text/activity, not memberships. Count it once across 432 capture contexts—not
eight times. There are 1,626 known retrieved pairs (861 positive, 765 negative) plus
243 uncertain pairs excluded from known-label metrics. Recall here is conditional on
retrieval, not recall over all possible prior pairs.

| Scorer | True positive | False positive | False negative | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Baseline | 577 | 137 | 284 | 80.8% | 67.0% |
| Hybrid 17 | 632 | 132 | 229 | 82.7% | 73.4% |
| Hybrid 29 | 585 | 120 | 276 | 83.0% | 67.9% |
| Hybrid 41 | 618 | 120 | 243 | 83.7% | 71.8% |

All three hybrids improve both direct precision and recall relative to the baseline,
but explicit separate-project pairs still score too highly in some cases.

For corroborated hybrids, the wrong fixed-state events decompose as:

| Cause of wrong attachment | Seed 17 | Seed 29 | Seed 41 |
|---|---:|---:|---:|
| At least one known disjoint supporting pair | 328 | 326 | 308 |
| Supports all valid; thread contamination/non-transitivity | 171 | 168 | 181 |
| Uncertain support, neither category above | 0 | 0 | 0 |

Scorer errors still matter. But a substantial fraction of mistakes arise even when the
supporting pairs are individually valid: joining the whole thread also joins unrelated
members. A bridge does not make its two independent projects transitively identical.

For **90.9–92.7% of missed corroborated-hybrid contexts**, no retrieved candidate thread
can join all the capture's known same-project predecessors without also joining a known
disjoint predecessor. This is a post-hoc, new-capture pair diagnostic; unknown members
do not establish safety, and it does not certify the whole thread's internal purity.
It includes fragmented histories, contamination, bridge constraints and candidate limits.
It is **not** evidence that all those misses would be fixed by automatic merging.

About 48–52% of missed events are proposals, with the rest split between new singletons
and incomplete attachments. The test does not assume a user resolves every proposal.
Simply changing which single thread wins—or making the pair matcher larger—cannot
fully repair these saved states under the current one-thread attachment rule.

## Recommendation

**Keep the hybrid-plus-corroboration approach as a research candidate. Do not replace
it with the simple baseline merely to save model size, and do not ship either yet.**
The model adds measurable value here, but final pair recall remains only about 33–35%.
Do not select a lucky seed or change thresholds using these exposed results.

The next best step is a bounded **state-recovery and proposal diagnostic**, not more
neural training: test how to identify mixed threads, propose splitting them, and propose
reconnecting legitimate fragments while respecting explicit user corrections. Measure
proposal correctness separately from the grouping after explicitly accepted repairs;
do not silently auto-merge or use gold as though the model discovered the repair.
Retain the three hybrid seeds as controls and quantify residual direct scoring errors.

A carefully scoped Mac-only prototype/evaluation of that next checkpoint is estimated
at **4–8 active hours**, with pause/resume and a review stop. Full app integration is
outside that estimate. It has **not started**; user approval and a prospective protocol
are required. Eventual shipping still requires an untouched qualification dataset and
appropriate device testing.

## Validation, scope and saved checkpoint

- 100 diagnostic Python tests passed, including 11 new C3 tests.
- Exact parity for 252 existing controlled streams and their semantic summaries.
- 3,456 own-lineage decision checks; all eight evaluators share retrieval/evidence at
  each fixed context. Original C2 model/ledger completion verifies unchanged.
- Real pause after one saved stream; resume preserved its SHA-256 and timestamp.
- No new ledger replay is claimed. C3 uses the previously verified command semantics.
- These remain 12 exposed, fictional, agent-reviewed English stories. Media input is
  supplied text, not tested OCR/ASR or image/video understanding. No new phone timing,
  model size, memory, multilingual or real-user validation was performed.

`summary.json` contains every anchor, story and order, pooled counts and online results;
`tests.json`, `resume-proof.json` and `complete.json` retain verification evidence.
Raw decisions, errors, all 579 new online-prefix metrics, complete summary and freezes
remain under ignored `../runs/c3-01/`. Earlier evidence was not overwritten or deleted.

Verify from the repository root using the existing environment:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/organization-diagnostics/c3_finalize.py verify
```
