# C3 — matched corroboration control and fixed-prefix audit

Authorized by “Go on with ur recommedndation” after C2. Estimated 2–4 active hours,
Mac only. Stop after this checkpoint. No training, inference, downloads, simulator,
phone, production integration, new labels, or threshold tuning. C1/C2/P2 stay immutable.
These 12 exposed, agent-reviewed fictional stories remain diagnostics, not qualification.

## Prospective comparisons

The eight controlled variants are simple-baseline strongest/corroborated and hybrid
strongest/corroborated for all three seeds (17, 29, 41). Reuse C2's exact 935 cached pair
scores, 36 streams, explicit correction anchors and thresholds. Baseline eligibility
still requires its original three-class argmax. Retrieval, stable ties, ambiguity,
small-thread quorum and no-auto-merge behavior stay exactly as C2.

A new isolated generic policy implementation must reproduce all 252 existing controlled
C2 traces exactly (decisions and states) before new results are accepted. Add only the
missing baseline corroboration policy. No edits/monkeypatching to frozen C2 modules.
Save 36 new online traces / 579 prefixes; retain every old result as a comparison.

## Fixed states, not competing evolving histories

Use every controlled lineage: seven existing C2 policies plus the new baseline
corroboration policy. Each contributes 36 streams × 12 pre-capture states. At each
state, evaluate all eight variants on identical observed source versions, memberships,
archives and candidates. A counterfactual decision never changes the next anchor state.
Thus 3,456 anchored capture contexts produce 27,648 one-step decisions. Do not treat
these correlated contexts as independent examples; report each anchor lineage, story,
order, scorer and rule, not just a pooled headline or best seed. No gold-derived/oracle
anchor state and no production-reference lineage with different retrieval are included.

Reconstruct text only from captures/revisions observed by that prefix. Validate text
hashes/revision/archive fields against its saved trace. Decision inputs exclude semantic
memberships and gold. Freeze all online and fixed-state decisions before the separate
metric process reads prefix gold. The old stories/results are already exposed; this
information separation is an implementation safeguard, not a new blind evaluation claim.

## Measurements

Online: reuse C2's prefix, final pooled/macro pair, false/missed capture, correction,
proposal, fragmentation and order metrics. Add the new control without replacing C2.

Fixed-state: known-label new-capture wrong/missed pair counts and event rates with
denominators, proposals, uncertain joins, and pair classification over every retrieved
source (once per scorer/context, independent of rule). Compare all four scorers within
each identical anchor under each identical rule. The proposal/abstention distinction
and non-transitive bridge semantics remain unchanged.

Classify wrong decisions into mutually exclusive support categories: at least one known
disjoint supporting pair; otherwise uncertain support; otherwise all supports known
same-project (inherited contamination/non-transitivity, not a direct pair error).
Split missed events by new/proposal/attach action. Separately flag gold bridges and
whether a retrieved candidate thread could join every known same-project predecessor
without any known disjoint predecessor. This last flag is a post-hoc known-label
structural diagnostic, not an oracle policy; unknown members do not establish safety.
Do not add these overlapping flags together or claim every abstention is a scoring bug.

## Integrity and pause

Bind protocol, new code/tests, C2 completion, cached scores, inputs, thresholds and all
source traces before comparison. Validate frozen bindings on resume. Publish immutable,
checksummed units per stream/anchor; reject missing/changed receipts and publish completion
last. One worker holds its own C3 lock and also the shared C2 lock, without changing C2
globals or clearing any C2 pause markers. A pause stops at the next stream/anchor boundary,
saves an acknowledgement and exits. `--max-units` exercises real stop/restart recovery.

Keep the combined diagnostic cap 4 GiB (retain C2's 1 GiB allowance for prior simulator
growth) and at least 10 GiB free. No cleanup/deletion of earlier evidence. No additional
ledger replay is claimed: C3 tests semantic policies using the previously verified command
contract. Curate summary, errors, validation and resume instructions, then stop for review.
