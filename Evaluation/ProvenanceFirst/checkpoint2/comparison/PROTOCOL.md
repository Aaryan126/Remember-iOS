# Current-runtime A/B/C comparison — approved amendment

The user approved this amendment with “Sure go for it” after the broader runtime
qualification report on 17 September 2026. The old vector-identity and numerical
equivalence runs remain **failed**; no tolerance is changed and no historical
result is relabeled. This is a new, explicitly runtime-specific offline reference:
`d3-seed29-mac27-pf2-reference-v1`, not a qualification of shipped Core ML FP16.

## Shared scorer and sealed selection

Reuse the existing seed-29 weights, tokenizer, fixed TF-IDF/features/combiner and
current Mac PyTorch/MPS runtime. Record all asset/code/runtime hashes. Produce one
immutable source-version embedding cache and symmetric neural-pair cache per split,
shared by all variants. No fitting, model downloads, paid APIs or phone. Source-only
cache generation can enumerate versions but policy callbacks may consume only the
observed prefix, never future sources/versions or annotations.

Use the frozen 12 development libraries before opening evaluation inference or
metrics. Select C's automatic threshold from production D3, 0.99 and 0.995, with
>=95% observed edge precision over >=20 automatic edges. Choose greatest correct+
incorrect automatic-edge coverage; break equal coverage by stricter threshold.
Count chronological and fixed alternative orders together but disclose correlation.
If none qualifies, C is suggestions-only (no automatic attachments). Proposal
eligibility remains fixed at the production D3 threshold. Freeze the choice, code,
development predictions and selection metrics before evaluation. No test retuning.

## Placement and authority

- A: actual frozen D3 retrieval (top five contextual + top five lexical, RRF 60,
  stable UUID ties), first three retrieved members/project, min(2, active member
  count) corroboration, exactly one qualifying project required to attach.
- B: **identical placements to A**; changes evidence recovery only.
- C: same retrieval/scores; proposals retain each corroborated project separately,
  including multi-project suggestions. Automatic placement additionally requires
  a unique qualifying project at the selected threshold and enough supporting
  sources whose memberships are exclusively that project. A shared source cannot
  alone propagate membership into another project. No automatic merge/separate.
- No qualifying evidence means unresolved, not a declaration of different projects.
  Singletons are storage defaults, not semantic assertions. Suggestions never
  become confirmed automatically. Explicit fixture correction events are the only
  simulated user choices; revisions/archive/restore cannot silently move sources.
- Use the frozen prefix allowlist, which removes gold, rationales, dependency metadata
  and project titles. Corrections may specify observed source-root thread IDs.
  Native UUIDs use the existing ledger harness's deterministic source-ID mapping.

## Evidence recovery without an oracle River

Fixture questions do not supply a user-selected River. Simulate routing uniformly:
rank current, unarchived source chunks against the visible fictional question using
the production `MemorySearchService` **local lexical evidence** formula, with no
optional cloud embedding provider. Select a River containing the highest-ranked
source; if it belongs to several, choose stable thread UUID order. No gold project
metadata enters routing. This is a declared routing adapter, not a shipped UI claim.

Compile the unchanged production D3 policy and text chunker plus the exact extracted
lexical/normalization helpers into a small isolated Mac probe. Reuse the production
800-character chunks/120-character overlap, score, newer-source tie break and ordinal
tie break. Fictional fixture locators remain attached. Deduplicate by source/revision.

- A returns up to three ranked identities confirmed in the selected River.
- B retains those River results and adds up to three ranked outside identities as
  **unconfirmed suggestions**. For the common P@3/R@3 comparison, rank the union and
  score only its first three unique identities; separately score the outside list.
- C uses B's same recovery rules with C's placements. Global top-three recovery may
  therefore equal B; its separate question is placement/proposal safety.
- This reuses current-source search, which does not index archived/superseded ledger
  revisions. Historical tasks are still measured, and missing old-version recovery
  is reported as a limitation, not silently supplied by an oracle history lookup.
  Query mode is evaluator metadata only, not an input filter chosen from gold.
- Query metrics use the original chronological question prefixes only. Both orders
  are used for placement, corrections, proposal and native ledger checks. Reusing
  chronological answer sets at different alternate prefixes could label unavailable
  evidence as a failure or leak future answers, so no alternate-query denominator
  is invented. Report 48 questions/split, not twice that many independent questions.

## Scoring additions to the frozen measurement definitions

Gold is loaded only by the separate evaluator, after label-free predictions exist.
Automatic edges are capture-time source→semantic-project assertions. For evaluating
a predicted thread, map its anchor to the anchor capture's unique gold project if
one exists. This gives credit for a correct same-project fragment without hiding
fragmentation. Unknown or multi-project anchors have no unique semantic identity:
an automatic attachment to them is an unsupported edge, not an inferred separation.
Gold mappings never enter policy/routing inputs and never retroactively use later
corrections to justify an earlier edge.

Also report exact semantic membership-set recovery; fragmentation as additional
occupied threads per gold project at the final prefix; distinct canonical project
roots sharing a thread; multi-project sources present in both canonical Rivers;
and capture-time project-proposal edge precision/recall for C. Separate automatic
and explicit-user-corrected outcomes. An uncertain capture receiving any automatic
edge is an unsupported decision. Retention uses identical source/event/order/project
edge identities between candidate and A. State/order correlations are explicit.

Use the original METRICS.md query identity, P@3/R@3, coverage, no-answer and macro
definitions. Suggestions advancement uses the outside-suggestion list's >=90%
observed precision and the union's >=10-point answerable macro recall gain over A.
Report pooled, library-macro and mode-macro results, zero/one/two/three-result counts,
and all unanswerable returns. The latter are suggestions, not generated answers.

Automatic advancement retains the original >=95% precision, >=20 edges, no more
wrong edges than A, >=80% retained correct A edges, and <=10% unresolved automatic
decisions gates. Zero denominators are undefined/inconclusive, not success. All
ledger/citation/chronology/correction invariants must pass. No release claims.

## Integrity, native replay, budgets and stop

Save per-library/order prediction receipts and model-cache units durably. Test
one-unit pause/resume, verify before skipping, and bind every run to its manifest.
Compare the Python placement adapter against the actual native D3 policy for every
A capture. Validate source-version/locator citations against each observed state.
Replay predicted A and C actions through the already-built isolated production
ledger on the registered simulator, both orders, with independently built expected
state. B's state is byte-equal to A and may share native receipts if equality is
explicitly checked. Never use the personal app/store. Existing checkpoint-1 native
invariants remain binding; native output lives in a new checkpoint-2 run directory.

The shared <=4 GiB new-write cap and >=10 GiB free reserve still apply; no automatic
deletion. Stop on resource/identity/invariant failure, retain partial work, and
report the blocker. Stop for user review after the checkpoint-2 results. App UI,
production integration, device qualification, training and wider searches remain
outside this checkpoint. Estimate: 10–16 active hours, Mac only.
