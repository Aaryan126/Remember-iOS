# Independent code audit and resolutions

Reviewer: the beta agent, after its independent pair/context judgments were sealed.
The reviewer inspected only this new diagnostic implementation and ran its tests;
root implemented changes. It did not modify the authored evidence or production app.

## Findings addressed before release

| Finding | Resolution |
|---|---|
| A story build could trust a receipt's existence without checking the complete evidence chain | Release now requires existing author/reviewer seals, verifies source/packet/specification/validator hashes, and validates review/adjudication coverage before producing outputs. Tests reject changed author labels and a changed review even when an adjudication supplies its new hash. |
| Per-story outputs could be published before all shuffle/final-state checks succeeded | All 12 stories' payloads, unique orders, equal final states, and existing destination contents are checked before story publication. A duplicate-shuffle regression verifies that no release directory is created on failure. |
| A context packet could rely only on its own reviewer-supplied hash | New `integrity.py` independently reconstructs the exact source-only pair and context payloads. The original frozen packet builder was not edited. Tests reject additional gold fields and changed context. |
| Unknown amendments or unresolved review blockers could be skipped | Finalization requires every contextual disagreement, every story membership disagreement and every reviewer finding to be resolved explicitly. Invalid/duplicate targets fail, and a blocker cannot be waived as an accepted limitation. |
| Prediction uniqueness, eligibility and split assumptions were implicit | The additional verifier checks canonical distinct source-pair IDs, within-library identity, evaluation split, finite probabilities/thresholds, boolean eligibility and identical baseline/hybrid identity records. It also recomputes deterministic selection. |
| Missing seals could be recreated during a release check | Finalizer release paths now require existing pair/context and story review receipts before calling idempotent seal verifiers. Regression coverage verifies that a missing story-review seal is not recreated. |

The re-audit found no remaining required code blocker for the explicitly retrospective
manual-review workflow. It still required the separate textual-dependency review before
release. Root subsequently expanded dedicated failure-path regression coverage.

## Deliberate limits

- Prose can imply prerequisites not present in `dependsOn`. A topological validator
  cannot discover them. The reviewer reproduced such a counterexample with an in-memory
  fixture. Independent story review checks those references, and separate adjudication
  records the added edges; this is not proof that natural-language causality is solved.
- Story reviewers see full stories and declared project scopes. Their audit is
  retrospective, not a blinded test restricted to observed prefixes. Actual scorer
  inputs and generated reference states are separately projected by event order.
- Explicit authoring `prepare`/`seal` commands can create missing receipts; do not use
  them as a repair for a completed checkpoint. `finalize.py verify` is the read-only
  verification entry point after completion.
- A local receipt is not cryptographic access control. Files and reviewers share the
  workspace. Evidence restrictions were procedural and communicated explicitly.
- The batch preflight covers story output payloads, not every downstream report and
  completion destination. A later failure can leave valid story outputs without a
  final receipt. Identical retries are supported; different outputs fail rather than
  overwrite. Completion is published last and partial progress is never labelled done.
