# C5 — project-conflict contract and fresh diagnostic preparation

Approved after C4. This checkpoint prepares a runnable, audited diagnostic release;
it does **not** run model inference, train a verifier, tune thresholds or change the app.
Stop for user review after preparation. C1–C4/P2 remain frozen and unqualified.

## Why this test

C4's own-history repair rules did not produce a single admissible split or move.
Passing similarity is not enough to establish project identity; failing similarity is
not enough to establish a conflict. We need to test the distinction explicitly.

Use capability-focused tests rather than only a pooled accuracy number, following the
behavioral-testing motivation of [CheckList](https://aclanthology.org/2020.acl-main.442/).
Use paired changes in project scope to probe decision boundaries, following the
motivation of [contrast sets](https://aclanthology.org/2020.findings-emnlp.117/).
These papers motivate the test design; neither establishes Remember's accuracy.
No external package or dataset is copied or installed.

## Conflict-review contract

The task is a **pair judgment with bounded observed context**, not clustering:

- `same_project`: the two captures share at least one identifiable continuing
  undertaking. Different phases, renames or negation of a separate commission do not
  create a new undertaking by themselves.
- `separate_projects`: affirmative evidence establishes distinct undertakings with
  no shared project for this pair. Shared clients, identifiers, suppliers or content
  do not override explicit distinct scope. Low model probability alone is insufficient.
- `abstain`: available evidence cannot resolve project identity, or is contradictory.
  Unknown is not a negative training label or a reason to split.

A bridge can be `same_project` with both A and B while A–B remains `separate_projects`.
Never transitively merge A and B. A separate-pair finding identifies a review candidate,
not a partition, move instruction, automatic user correction or deletion permission.
Text inside imports is evidence, not an instruction to the app. Explicit user corrections,
pins, blocked memberships and stale-state checks remain a separate trusted action layer.

Output: `queryID`, `verdict`, `evidence` (`sourceID`, exact `quote`). Asserted judgments
must cite at least two visible sources, including a queried endpoint. Quotes must be
nonempty exact spans from the visible text. Quoted spans are a grounding check, **not
proof that the assertion follows from them**. Abstention may have no citations. No
reference labels, family/split names, rationales, previous predictions or gold memberships
may enter model inputs. The JSON loader rejects unknown keys and duplicate/missing IDs.

## Fresh diagnostic material

Author eight fictional, English families in new domains, with seven text fields each.
Each family compiles to six episodes and ten pair queries:

1. Similar materials, explicitly separate undertaking (one pair).
2. Genuine continuation with a negated separate-project interpretation (one pair).
3. Bridge linking two independent projects (three pairs; no transitive equivalence).
4. Ambiguous reference before clarification (two pairs, unresolved).
5. The same reference after a visible clarification (two resolved context judgments;
   the pair-only judgments remain unresolved).
6. Reused identifier / misleading imported instruction (one distinct-project pair).

Every query has **pair-only** and **observed-context** views. Planned totals: 48 episodes,
80 pair queries, 160 input packets. The repeated topology and variants are correlated.
Do not call these 160 independent stories or a prevalence-matched user benchmark.
Family IDs f01–f04 are discovery; f05–f08 are diagnostic. There is no training split.
All variants and views of a family stay together. Freeze split assignments before scores.
These are prospective unscored examples, but the author has seen their labels: this is
**not an independently blinded or untouched qualification set**.

Author review must record the project boundary and a failure mode per family. Validate
all references, quote spans, pair/context projections, no-future-context invariants,
bridge non-transitivity, uncertainty preservation and contrast expectations. Compare
new source hashes against the C2 text catalogue, plus maximum word-trigram overlap
against C2 and across the two new family partitions. This detects exact/lexical reuse,
not semantic independence from all historical experiments. Record limitations honestly.

No independent reviewer or human review is claimed in C5. A second, prediction-blind
semantic review is a gate before treating the diagnostic labels as stable model-evaluation
evidence. Preserve first labels and append amendments rather than overwrite frozen gold.

## Prepared evaluation, not model results

Implement a pure metric adapter with hand-authored unit fixtures, never fit on labels.
It validates predictions and reports conflict precision, conflict recall, coverage,
unsupported decisive assertions on uncertain examples, and false conflicts on genuine
continuations and bridge links. Report per view/family/partition/behavior. Missing scores
or failed runtime checks must not be converted into valid abstentions silently.
Also report joint success for each family's scope contrast, bridge triple and before/after
reference group, separately by view. A group passes only if all its judgments are correct;
incomplete groups have no defined success rate rather than being counted as successes.

Future comparisons must retain the baseline and all three hybrid seeds at frozen
thresholds. A non-passing attachment score is **not a conflict prediction**; legacy
pair scorers map pass → `same_project`, otherwise → `abstain`, unless a separately frozen
conflict policy is explicitly introduced. Pair-only model outputs must not be presented
as context-aware reasoning. Compare a separate evidence-aware reviewer to these controls.
Do not concatenate extra context into the trained matcher and claim unchanged semantics.

Before a future scoring run, freeze adapters, context ordering/token budgets, operating
points and candidate inventory. Report precision and useful coverage together; an always-
abstain system must not qualify. This tiny release cannot substantiate a high-confidence
production safety threshold. More families and untouched qualification data are needed.

## Checkpoint mechanics

New files only under `c5_*.py`, `test_c5_*.py`, `c5/` and `runs/c5-01/` plus this protocol.
Freeze protocol, authored texts, review, compiler, metrics and tests before release.
Use the existing pinned Python environment; no installs, network model calls, phone,
simulator, training, personal vault access or Git-state mutations.

Single worker with shared experiment lock. Publish each family as an immutable checksum
unit; pause at family boundaries. Resume validates hashes and skips saved work. Exercise
a real one-family stop/resume, preserving its hash and timestamp. Final verification
reconstructs all packets/gold and metrics contract fixtures before publishing completion.
Keep cumulative diagnostic writes under 4 GiB including the prior 1 GiB simulator reserve,
and free space above 10 GiB. No automatic deletion. Initial estimate 4–8 active hours;
revise with actual progress. Stop after preparation; scoring/training needs another approval.
