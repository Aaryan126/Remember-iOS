# C4 — useful reconnection proposals, inadequate mixed-thread repair

**Completed; stopped for user review.** The frozen hybrid scorers can suggest useful
links between fragments, but cannot reliably diagnose and repair their own contaminated
threads using these rules. Keep this as research evidence, not an automatic repair feature.

## What we actually tested

Four corroborated histories (baseline and hybrid seeds 17/29/41), each containing 12
fictional stories in three orders. Every saved prefix was evaluated by all four scorers:
**144 stream units, 2,316 anchored states, 9,264 scorer-contexts**. These are correlated
repetitions of 12 exposed stories, not 9,264 independent examples.

The proposer used current source text, memberships, frozen pair scores/thresholds and
explicit correction protections. It inspected all active pairs (894 distinct observed
text-version pairs were needed). It did not receive reference labels or future events.
Four bounded proposal types were tested: split, reassign, add membership, and merge.
At most one proposal per type was offered, in that fixed order. A separate evaluator
then reviewed the frozen proposals against the reference labels.

A proposal is **beneficial** only if it repairs at least one pair error, introduces no
new pair error and changes no uncertain pair. Harm is not cancelled by other benefits.
The simulated perfect reviewer explicitly accepts the first beneficial proposal, at
most one per state. All other proposals are rejected. **This acceptance uses gold**;
it is not a learned reviewer, real-user acceptance or autonomous model performance.
Repaired states do not feed into the next prefix. See [protocol](../C4_PROTOCOL.md).

## 1. How good are the proposals on matched states?

Each scorer below sees the same 2,316 anchored states. Proposal counts include repeated
offers at successive prefixes. Different scorers can offer different candidate sets.
Uncertain proposals remain in the denominator; they are not counted as correct.

| Scorer | Offered | Beneficial | Harmful | Indeterminate | Beneficial / offered |
|---|---:|---:|---:|---:|---:|
| Simple baseline | 2,481 | 1,884 | 453 | 144 | 75.9% |
| Hybrid 17 | 2,421 | 2,037 | 245 | 139 | 84.1% |
| Hybrid 29 | 2,342 | 1,955 | 253 | 134 | 83.5% |
| Hybrid 41 | 2,373 | 2,051 | 211 | 111 | 86.4% |

There were respectively 651, 605, 586 and 586 unique action signatures within streams;
these are not independent observations either. Hybrid 41 is the most promising pooled
proposal scorer here, **not a qualified winner**. Keep all seeds. Performance depends
on history: baseline proposals score 91.3% on their own more-fragmented history versus
70.8–72.5% on hybrid histories. Do not compare own-history proposal rates as if the
inputs were matched, or claim hybrids win in every anchor.

Proposal quality differs substantially by operation (same matched states):

| Operation: beneficial / offered | Baseline | Hybrid 17 | Hybrid 29 | Hybrid 41 |
|---|---:|---:|---:|---:|
| Add membership | 81.6% | 86.8% | 85.5% | 87.8% |
| Merge fragments | 86.0% | 85.1% | 86.0% | 88.3% |
| Reassign a source | 13.0% | 59.0% | 63.0% | 65.7% |
| Split a thread | 14.0% | 55.9% | 51.0% | 61.9% |

These split/reassign samples are small and repeated. Their results are insufficient
even for a dependable review queue, much less automatic cleanup. A failing match score
is not reliable evidence that two sources belong to different projects.

## 2. What happens after a perfect reviewer accepts one repair?

Primary own-history final-prefix results: 36 final states per row, pooling three orders.
Recall denominator is 1,065 known same-project pairs. This is a **one-action upper-bound
diagnostic for the offered candidate set**, not a full repair ceiling or online result.

| History and repair scorer | Final precision: before → accepted | Final recall: before → accepted | Missed pairs: before → accepted | Wrong pairs: before → accepted |
|---|---:|---:|---:|---:|
| Baseline | 69.4% → 72.7% | 24.5% → 28.8% | 804 → 758 | 115 → 115 |
| Hybrid 17 | 78.0% → 79.9% | 34.6% → 38.9% | 697 → 651 | 104 → 104 |
| Hybrid 29 | 75.2% → 77.1% | 34.5% → 38.3% | 698 → 657 | 121 → 121 |
| Hybrid 41 | 77.0% → 79.1% | 33.2% → 37.6% | 711 → 665 | 106 → 106 |

Each own-history final state had at least one beneficial offered proposal. Nevertheless,
most missing relationships remained. Precision rose because more correct links were
added—not because incorrect links were removed. Mixed-thread counts were unchanged:
baseline 24, hybrids 19/19/20 across the 36 final states.

Across all 579 own-history prefixes, accepted proposals occurred in 332 baseline states
and 290/271/288 hybrid states. Among error-containing states, 74.4% and 67.8%/63.6%/67.9%
had a beneficial offer. Counts include repeated exposure, not distinct user actions.

On matched final states, baseline, hybrid 17 and hybrid 41 acceptance produced identical
pair counts. Hybrid 29 left nine additional missing pairs across the four histories.
The modest final improvement therefore is **not evidence that a larger neural repair
model is necessary**; policy and candidate-budget limitations also matter.

## 3. The central failure: the scorer rarely questions its own mistakes

**Zero admissible split or reassignment candidates occurred on any scorer's own
history**, even before selecting the first candidate per type. All own-history repair
offers were links or merges. Cross-scorer histories did produce splits/reassignments.

Interpretation: a history built from passing pair scores tends to stay connected under
that same scorer. One confident wrong edge can connect independent topics; connected
components then fail to expose the contamination. This is a limitation of this frozen
repair rule and evidence, not proof that all split algorithms or models must fail.
The conservative protection rules may also suppress repairs; they deliberately preserve
even currently incorrect relationships involving explicitly corrected sources.

Three concrete examples from baseline-anchor states, reviewed by hybrid 17:

- **Useful split — story 04, chronological e02.** An Orchard Hall wedding cake and a
  separately commissioned Stone Pier cafe order shared a pale-green glaze. The baseline
  joined them; hybrid 17 proposed separating them and repaired that incorrect link.
- **Harmful move — story 01, shuffle-1 e14.** Moving a North Gallery exhibition update
  beside two other North Gallery sources repaired two missing links, but removed a
  valid link to the shared courier itinerary. The proposal was rejected: bridges must
  retain legitimate memberships rather than force an exclusive move.
- **Harmful merge — story 05, chronological e07.** A voice memo about duplicate offline
  field records was proposed for merging into a thread containing both the offline
  release and a separate billing incident. It repaired two links but introduced the
  wrong memo–billing link, despite every model pair test in the proposed union passing.

Exact assignments, before/after state hashes, reviews, changed pairs and explicit
accept/reject records remain in `runs/c4-01/proposals/` and `metrics/`. These examples
are fictional test material. No personal memories were inspected.

## Recommendation and review stop

1. **Retain hybrid + corroboration as a research candidate.** Keep multi-membership
   links for bridges and proposal-only reconnection. Do not ship automatic merge/split.
2. **Prioritize independent conflict evidence, not a larger generic matcher.** The next
   bounded design should distinguish “same continuing project” from “similar content,
   explicitly separate job/incident,” using source context and user constraints. Scorer
   disagreement can flag review candidates, but the split numbers show it cannot decide
   acceptance reliably by itself. Do not interpret low similarity as a cannot-link label.
3. Before another training run, prepare a small, separate project-conflict/bridge test
   set and freeze a conflict-review contract. Evaluate an evidence-aware verifier against
   the existing scores and simple classifier; require high precision **and nontrivial
   coverage** for detecting mixed threads. Retain all seeds and an untouched later
   qualification set. Do not tune this checkpoint's thresholds after seeing results.
4. Only if that succeeds, evaluate ranked/sequential proposals and production-ledger
   acceptance, rejection, stale-state handling and undo. C4 did not test those workflows.

A bounded next **conflict-review design + fresh diagnostic preparation** checkpoint is
estimated at 4–8 active hours, Mac only, pause/resume and review stop. That does not include
new neural training, final qualification, app integration or phone testing. It is **not
started or approved**. The broader project remains unqualified; P2's failed all-seed
gate and C1–C3 evidence are unchanged.

## Verification, resource use and limitations

- 120 Python tests passed, including 20 new tests. An initial overrestrictive archive
  fixture was corrected before freezing; valid links that leave archived relationships
  unchanged are allowed. No production behavior was changed for the fixture.
- All 144 unchanged final states reproduce C3 pair and structure metrics exactly.
- Reconstructed all 144 proposal units and 144 evaluation units, then reproduced the
  full summary. This is deterministic replay, not an independent semantic annotation.
- Real bounded stop and resume preserved the first stream's SHA-256 and timestamp.
- C3 and its parent chain verify unchanged. Completion binds protocol, code, tests,
  predictions, metrics, summary, review report and saved validation evidence.
- No training, model inference, installs, simulator/phone run, app/ledger mutation or
  Git-state changes. Existing 4 GiB cap / 10 GiB free-space reserve were respected.
- Twelve exposed agent-reviewed English stories; media is supplied text, not actual
  OCR/ASR/video testing. No real-user acceptance, new-model device measurements,
  large-vault scalability, longitudinal repair or production lineage claim is made.

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/organization-diagnostics/c4_finalize.py verify
```

Full recorded commands/output are in `runs/c4-01/validation/tests.json` and
`validation/replay-audit.json`. See [resume instructions](../RESUME.md). At handoff no
workers remain active; it is safe to close the laptop. Stop here for user review.
