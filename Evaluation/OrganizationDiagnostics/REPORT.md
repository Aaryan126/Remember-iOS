# Checkpoint 1: River boundary and context diagnosis

Completed 2026-09-14. **Stop before checkpoint 2 for user review.** No model was
trained, no phone test was run, and no production behavior changed. This is a completed
diagnostic checkpoint, not a passing model qualification.

## Main finding

There are two problems, not just one: the earlier benchmark used narrower task
boundaries than the user's intended continuing-project River, and some model decisions
remain wrong even with that broader definition. Context helps, but does not remove all
ambiguity or make the remaining errors disappear. Proceed with a small frozen policy
comparison before considering more training.

## What the independent reviews found

Two separate agents reviewed 80 distinct P2 pairs twice. Their first pass contained
only the pair's source text; both reviews were sealed before full-library source context
was published. Predictions, historical labels and outcome strata were withheld from
both reviewers. The sample deliberately includes 20 pairs in each historical outcome
category across the union of seeds 17/29/41; an error need occur in only one seed.
Selection precedence is FP, FN, TP, TN, with deterministic hash ordering and no duplicates.

| Historical sampled category | Same continuing project now | Related, separate | Unrelated | Still uncertain |
|---|---:|---:|---:|---:|
| 20 false-positive pairs | 7 | 10 | 1 | 2 |
| 20 false-negative pairs | 20 | 0 | 0 | 0 |
| 20 true-positive controls | 20 | 0 | 0 | 0 |
| 20 true-negative controls | 2 | 10 | 8 | 0 |

Of the seven historical false positives now judged same-project, six were independently
agreed and one required root adjudication. The two reviewers agreed on 70/80 pair-only
relations and 75/80 contextual relations. Root resolved the five contextual disagreements
with cited reasoning and preserved both agents' original judgments. Root was not
prediction-blind. One reviewer changed 14 judgments with context, the other 11; at least
one reviewer marked extra context necessary for 20 pairs. These are descriptive counts,
not population accuracy, and reviewer judgments are not a measured context-aware model.

Examples:

- Correcting Chen's membership term, updating that same renewal row, regenerating its
  receipt and checking the gate's matching expiry can be phases of one correction.
  The separately described gate-timing repair remains distinct. This boundary required
  adjudication and remains a preference-sensitive interpretation of the approved rule.
- Dane's whole archived interview and the exhibit's specifically selected excerpt are
  not interchangeable. The text never establishes that the corrected passage belongs
  to that excerpt. Both sampled passage/exhibit pairs remain uncertain.
- Every sampled historical missed match still belongs together under the new rule.
  A boundary change alone therefore does not address those missed decisions.

**Do not re-score this selected sample as if it were a fresh test or rewrite P2 as a
pass.** The original complete receipt was reverified unchanged:
`1fc484bd5f2c6f787713ffa010a874aecf9eec1bed4640cae3951119edf2b830`.
The original all-seeds gate still fails. Retrieval, automatic attachment policy and
actual ledger replay were not evaluated in this checkpoint.

## Chronological fixtures now ready

- 12 fictional stories, 144 captures, 193 total events including explicit revisions,
  corrections, archive and restore; three orders per story, **36 sequences and 579
  saved reference prefixes**.
- Domains include loans, experiments, annual events, commissions, software work,
  installations, theatre, oral history, boat work, print orders, observatory studies
  and a multi-year programme. Scope varies; bridges do not create transitive merges.
- A separate agent audited all 144 initial assignments without authored membership
  labels and agreed with them. Its 23 findings included one definite dependency
  blocker, optional ordering questions, preserved correct chains and limitations.
- Root added three dependency edges: the bakery glaze comparison follows its antecedent;
  the allotment clarification follows the referenced library specification; the fair
  closeout follows the referenced cooling signage. Authored files were preserved and
  amendments applied to separate release copies. No membership amendments were needed.
- All orders satisfy amended prerequisites and reach equal reference final states.
  Tests check that future captures do not appear early, revisions update the expected
  text, unresolved fragments remain unresolved, partial supported links are retained,
  and archive/restore do not invent identity evidence.

This review was a **retrospective manual causal audit**: the reviewer could see all
future narrative, project definitions and explicit commands. It is not an independently
blinded prefix evaluation. The released source inputs and reference state are separated;
future model runs must consume only their available prefix. Explicit user corrections
are action records, never pair-model features.

## Verification and saved state

Commands actually run successfully:

```sh
python3 -m unittest discover -s scripts/organization-diagnostics -p 'test_*.py' -v
python3 scripts/organization-diagnostics/checkpoint.py verify-selection
python3 scripts/organization-diagnostics/review_stories.py seal
python3 scripts/organization-diagnostics/finalize.py build
python3 scripts/evaluation_snapshot.py verify
git diff --check
```

All **28 tests passed**, covering source-only reconstruction, deterministic sampling,
causal histories, the saved 579 prefixes, immutable publication, tampered/missing seals,
unresolved review blockers and validation before publication. The original
`scripts/matcher-validation/p2_english.py verify` also passed using the existing
feasibility Python environment. See [the code audit](CODE_REVIEW.md) for findings and
fixes. Finalization publishes `complete.json` last; verify it with
`python3 scripts/organization-diagnostics/finalize.py verify`.

The new diagnostic directories used approximately 2.2 MiB allocated before final
documentation, well below 4 GiB. At the final test measurement approximately 19.5 GiB
was free, above the 10 GiB reserve. No model downloads, app/vault writes, Git mutations
or deletions of existing artifacts occurred. Unrelated `output/` files were left alone.

## Recommendation and limits

Proceed to **checkpoint 2 only after user approval**: compare the production embedding
reference, simple-baseline attachment, hybrid attachment and corroborated hybrid
attachment on identical controlled streams; then replay actions in an isolated store.
Keep all seeds and existing thresholds visible, and measure wrong attachments, missed
attachments, fragmentation, ambiguity/proposals and order sensitivity. Estimate:
**8–16 active hours, Mac only**, with safe pause/resume and a final review stop.

No fresh training is justified by this checkpoint alone. The old thresholds were
calibrated for the earlier contract, so subsequent comparisons under the broader rule
remain diagnostic. Any eventual winner still needs an untouched qualification set and
trained-model phone measurements before integration.

The fixtures are small, explicitly scoped and template-influenced, with unusually clear
project names and deliberate ambiguity cases. They use fictional English descriptions,
not real media processing. Some real-world intermediate actions/hardware identities
are not captured. Agent agreement can reflect shared model-family biases. None of this
establishes real-user preference, multilingual robustness, scale or production accuracy.

For exact data, see `analysis.json`, the separate adjudication files, sealed reviews,
and `release/inputs/` versus `release/gold/`. Original runs remain local and ignored;
the preparation checkpoint documents the separate backup/restore requirements.
