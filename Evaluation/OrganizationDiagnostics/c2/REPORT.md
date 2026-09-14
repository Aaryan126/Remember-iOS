# Checkpoint 2 — organization policy and provenance results

2026-09-14. **Diagnostic checkpoint complete; stop for user review.**

The most promising finding is **corroborated attachment**, not a proven neural-model
win. It consistently reduces wrong attachments, but increases missed groupings and
fragmentation. None of the tested paths is ready for a production recommendation.

## What we tested

- 12 agent-authored/reviewed/adjudicated fictional English stories, 12 captures each.
- 193 events, including revisions, explicit corrections, archives and restores.
- Chronology plus two dependency-valid shuffles per story: 36 sequences, 579 prefixes.
- Eight policy instances: one native production embedding-only **placement adaptation**,
  the frozen simple baseline, and strongest/corroborated hybrids for seeds 17, 29, 41.
- Total: **288 policy streams and 4,632 scored prefixes**. All predictions were frozen
  before the separate semantic metric process read prefix gold.

Models, vocabulary, features and thresholds stayed unchanged from P2 English attempt 02.
No training, downloads, phone measurements, personal memories or production integration.
The 157 exact text versions all received English embeddings; 935 pairs per seed were
scored symmetrically. All 16 original numerical reference cases reproduced exactly for
each seed (48 checks; maximum directional difference 0). Baseline/feature/combiner checks
also passed. This verifies reuse of the original models, not a new Core ML conversion.

## Main results

All three orders pooled. Wrong-event denominator = 360 eligible known captures;
missed-event denominator = 279 captures with a known same-project predecessor.
Final precision/recall below are **pooled pair metrics**, not equal-story macro averages.
Each policy has 432 capture actions across the repeated orders.

| Policy | Wrong attachment events | Missed attachment events | Final pair precision | Final pair recall | Proposals |
|---|---:|---:|---:|---:|---:|
| Production placement reference | 98/360 (27.2%) | 186/279 (66.7%) | 72.6% | 41.8% | 0 |
| Simple baseline, strongest | 106/360 (29.4%) | 165/279 (59.1%) | 60.4% | 38.4% | 112 |
| Hybrid strongest, seed 17 | 94/360 (26.1%) | 173/279 (62.0%) | 60.2% | 37.7% | 129 |
| Hybrid strongest, seed 29 | 91/360 (25.3%) | 177/279 (63.4%) | 60.5% | 37.7% | 117 |
| Hybrid strongest, seed 41 | 101/360 (28.1%) | 169/279 (60.6%) | 60.2% | 41.6% | 113 |
| Hybrid corroborated, seed 17 | 52/360 (14.4%) | 206/279 (73.8%) | 78.0% | 34.6% | 104 |
| Hybrid corroborated, seed 29 | 54/360 (15.0%) | 202/279 (72.4%) | 75.2% | 34.5% | 96 |
| Hybrid corroborated, seed 41 | 46/360 (12.8%) | 215/279 (77.1%) | 77.0% | 33.2% | 103 |

A wrong event joins at least one known disjoint predecessor. A missed event leaves at
least one known same-project predecessor unjoined. **Both can occur in one event.**
Misses include proposals/abstentions and partial membership of bridges, not just scorer
rejections. Final pair metrics include the effects of scripted corrections and restores.
Uncertain gold is excluded from known-label denominators and reported separately.

## What the results mean

1. **The policy matters substantially.** For the same hybrid scores, corroboration
   cuts wrong events from 94→52, 91→54 and 101→46. However, misses rise for every seed.
   This is a safety/completeness tradeoff, not an across-the-board improvement.
2. **Retrieval is not the main observed bottleneck.** Controlled policies retrieve
   861/906 relevant prior pairs (95.03%). Only 45 are missing from retrieval, compared
   with 549–585 missed same-project pair links under strongest hybrids and 618–636
   under corroboration. Scoring and placement behavior account for much of the gap.
3. **A good pair match does not imply a safe whole-thread attachment.** Already mixed
   threads propagate mistakes, including cases where the model rejects the disjoint
   pair but accepts other legitimate members. Explicitly independent projects can also
   receive high scores at the first singleton attachment.
4. **Conservative proposals leave work unresolved.** A real bridge can belong to two
   separate projects, while the automatic policy permits at most one attachment. Multiple
   qualifying threads become proposals, not merges. The fixture does not simulate user
   resolution of every proposal; repeated abstentions can preserve fragmentation.
5. **Corrections help but do not repair whole destinations.** Strongest-hybrid target
   pair errors change 127→102 / 126→112 / 121→103. Corroborated errors change 125→83 /
   122→88 / 132→93. Copying an anchor's current thread correctly preserves any existing
   contamination rather than silently using gold to clean it up.
6. **Order still matters.** Final active-pair disagreement across order pairs is
   4.6–5.3% for strongest hybrids and 8.6–12.6% for corroborated hybrids. This compares
   membership overlap, not arbitrary thread IDs. Extra caution does not guarantee order
   stability. See the machine-readable summary for all exact values.

[ERROR_REVIEW.md](ERROR_REVIEW.md) gives concrete source/event examples and the
independent post-freeze review. It distinguishes direct scoring failures from thread
propagation and intentional abstention.

## Provenance and persistence: passed

The isolated simulator app compiled 21 unchanged production sources, including the
actual MemoryStore and ProvenanceSnapshot. It replayed policy commands, not semantic gold.

- 288/288 runs; 4,632/4,632 current prefixes and historical-prefix checks.
- 288/288 close/reopen reconstruction checks.
- 8,088 ledger events; no automatic merge/split in policy traces.
- 31 separate explicit invariants covering commanded merge/split/undo, stale rejection,
  corrections, archive/restore, append-only protection and related checks.
- Stop after one actual run, then resume: first receipt remained byte-identical.
- 89 Python tests in the diagnostic suite plus 5 ledger-preparer tests passed.

Ledger replay took 29.1 seconds including its bounded restart. This is a small isolated
simulator workload, not a production-scale or phone-performance benchmark. Peak measured
new storage was about **1.12 GiB** (diagnostics plus simulator growth); minimum measured
free space was **19.28 GiB**, within the 4 GiB cap and 10 GiB reserve. The test simulator
was shut down afterward; no inference, training or replay worker remains.

Operational issues were preserved, not hidden: initial build dependency/isolation fixes
and a Desktop input-access problem were resolved before freezing the harness. Fictional
input was staged into the isolated app's private directory. The first scoring `tee`
failed because its log directory did not yet exist; scoring itself completed, captured
output was saved, and an immutable-cache rerun exited successfully. A wrong-interpreter
ledger invocation was rejected before launch; rerunning with the frozen environment
passed. No thresholds, model weights, production code or Git state changed.

## Recommendation and next checkpoint

**Do not ship or start another neural training run from these results.** The current
comparison lacks a **simple-baseline corroboration** control, so it cannot establish
that a neural matcher is necessary for the observed policy gain.

Recommended next bounded checkpoint (estimated **2–4 active hours, Mac only**):

1. Add that missing baseline corroboration control, reusing cached scores and unchanged
   thresholds/retrieval. Retain all earlier results.
2. Compare scorers on identical saved prefix/thread states to separate direct scorer
   behavior from errors caused by earlier state divergence.
3. Report direct false matches, inherited contamination, unresolved proposals and bridge
   limitations separately; stop for review before choosing context/policy work or training.

If the cheap baseline plus the same policy is competitive, prefer its smaller operational
cost. If a residual scorer gap remains under matched conditions, use those failure types
to design a new training/evaluation task. Conflict-aware thread evidence and explicit
proposal/correction recovery are more targeted avenues than simply enlarging the model.
No next-stage work has started.

## Limitations and saved evidence

These are **12 distinct stories**, not 36 independent datasets or 4,632 independent
examples. They are fictional and agent-reviewed, not human-labeled deployment evidence.
Media modalities contain supplied text; OCR, ASR, video/image understanding, multilingual
behavior, real user preference, large maps and device performance were not tested.
The reference adapts only native new-capture embedding placement: no reasoner or periodic
merge/split maintenance. Its retrieval differs from the controlled comparisons.

The stories are now exposed diagnostics. Any tuning against them is development work;
eventual shipping requires new, untouched qualification evidence. Prior P2 failures and
checkpoint 1 evidence remain unchanged.

Curated files: `summary.json`, `ledger-summary.json`, `model-parity.json`, `tests.json`,
`ERROR_REVIEW.md`, and final `complete.json`. Full per-prefix metrics, raw predictions,
command logs, SQLite stores, ledger receipts and model bindings remain under ignored
`../runs/c2-01/`. Restoring the local raw artifacts and pinned model environment is
necessary for verification; a fresh checkout alone is insufficient.

Verify from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/organization-diagnostics/c2_finalize.py verify
```
