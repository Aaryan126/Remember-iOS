# C4 — bounded state-recovery proposals

Prospective protocol, approved direction 2026-09-14. Freeze this file, implementation
and tests before generating proposals. No threshold selection, fitting, downloads,
phone use, production changes, personal data access or Git mutations.

## Question and scope

Can frozen pair scorers propose useful repairs to the states saved by C3? Separate
proposal correctness from outcomes conditional on explicit simulated acceptance.
This is a **fixed-prefix, one-repair diagnostic**, not an online repaired trajectory,
an app integration, or evidence that a person will accept the proposals.

Use all 12 exposed fictional stories, three orders and 579 prefixes. Four corroborated
anchor histories (baseline, hybrid seeds 17/29/41) supply identical states to all four
scorers: 144 stream units, 2,316 anchor prefixes, 9,264 scorer-contexts. Own-anchor
results are primary; cross-anchor results check whether comparisons depend on history.
Orders, anchors and repeated prefixes are correlated, not independent test examples.

All C1–C3 artifacts, inputs, cache, thresholds and baseline eligibility stay unchanged.
Reconstruct observed text versions and memberships from the frozen anchor, checking
every snapshot. Pair lookups use only current, observed, active sources. Exhaustive
within-state inspection (at most 12 sources / 66 pairs) deliberately removes retrieval
as a bottleneck; do not compare its compute cost to the online top-k policy or claim
scalability. Missing scores abstain; a below-threshold score is not proven contradiction.

## Frozen gold-free proposal rules

Evaluate baseline and all three hybrids independently at their frozen thresholds.
The proposer receives observed state, corrected source IDs and cached scores—no gold,
project labels, rationales, future events or acceptance decisions.

1. **Split:** within a thread, make a graph of threshold-passing pairs. If all pair
   scores are available and it has multiple connected components, propose separating
   those components. Keep the first component's thread ID, create stable IDs for the
   others, and retain unrelated memberships. This deliberately conservative rule may
   fail when one false-positive edge connects unrelated topics.
2. **Reassign:** move one source to a different thread only if every old peer has an
   available, failing score, at least one old peer exists, and the entire destination
   plus source passes every pair test. Replace only that source's memberships.
3. **Add membership:** link a source to another thread if the entire destination plus
   source passes every pair test. Preserve its existing memberships (maximum three
   after addition). This permits bridges without merging their independent topics.
4. **Merge:** consolidate two threads only if every pair in their combined active
   membership passes. Preserve other memberships. This is a semantic assignment
   simulation, not production cluster-retirement/lineage execution.

Never change archived or explicitly corrected sources' membership IDs; also preserve
every existing joined/unjoined relation involving such protected sources, even when
changing someone else. Corrections protect their target from that event onward.
This is stricter than a realistic UI permitting a later deliberate override; no such
override is inferred. Membership edits must change an active pair relation; no-op
renaming or redundant membership changes do not count as repairs.

Within each kind sort by stable source/thread IDs, then offer the first admissible
proposal. Maximum four per context, in the order above. Deduplicate identical resulting
memberships across kinds, keeping the earlier kind. Record pre-budget eligible counts
and full offered assignments/evidence. No confidence ranking or gold-based ranking.
Each proposal is bound to its full pre-state; reject stale acceptance atomically.

## Scoring and explicit simulated acceptance

Freeze all proposal units before opening C4 evaluation gold. Score each offered proposal
independently against the same pre-state, across **all changed active source pairs**:

- beneficial: at least one pair error repaired, zero new pair errors, zero changed
  uncertain pairs;
- harmful: any new known pair error (even if more other errors are repaired);
- indeterminate: no known harm but any changed pair has an uncertain endpoint;
- neutral: no changed known or uncertain pairs (should be excluded by proposer).

Empty reference membership is uncertainty, not a negative. Bridges use overlapping
membership sets; two topics are not equivalent merely because a bridge touches both.
Report introduced and repaired pair errors, proposal counts by kind, helpful-context
coverage, and repeated versus unique proposal signatures per stream/scorer. Precision
means beneficial / all offered proposals (uncertainty is not silently discarded).

For the **oracle-reviewed acceptance arm**, a perfect simulated reviewer explicitly
accepts the first beneficial offered proposal in frozen order, or rejects all. At most
one repair per context. Save the acceptance record and before/after states and metrics.
Gold is used ONLY by this evaluator. Outcomes are an upper-bound diagnostic for this
candidate set and one-action budget, not model autonomy or global best achievable repair.
No automatic-repair arm. No acceptance feedback reaches later anchor states.

Report unchanged versus accepted final-prefix pair precision/recall and FP/FN counts,
plus mixed-thread diagnostics, per seed/anchor/story/order. Prefix aggregates measure
repeated exposure; final-prefix metrics pool three orders and must be labeled separately.
Report missed opportunities (error states with no beneficial offered proposal), review
burden and residual errors. Never promote a lucky seed or use this exposed set as an
untouched qualification benchmark. A later online/ledger test requires a new checkpoint.

## Controls, execution and stop

Synthetic unit fixtures exercise bridges, contamination, fragmentation, score failures,
protected corrections, archives, revisions, stale acceptance, uncertainty and budgets.
Every unchanged anchor final state must reproduce C3 pair metrics. Acceptance must
never increase FP or FN; unchanged metadata and protected relations are invariant.
These tests validate the diagnostic model, not a new production-ledger workflow.

Use the pinned feasibility Python environment. New files only: `c4_*.py`, tests,
`runs/c4-01`, curated `c4/`. Atomic checksum-bound immutable stream units; single shared
worker lock; signals or `pause` stop at a short unit boundary. Resume verifies hashes
and skips existing units. Exercise a real bounded stop/resume preserving the first
unit's hash and timestamp. Publish prediction, metric and completion receipts last.
Keep cumulative diagnostic writes under 4 GiB including the existing 1 GiB simulator
reserve, and at least 10 GiB free. No automatic artifact deletion.

Estimated 4–8 active hours for implementation, testing, execution and analysis; cached
execution is expected to take minutes. Save progress and revise estimates as measured.
Stop after C4 for user review, even if results are promising. No training, new dataset,
phone testing or integration starts automatically.
