# C6 — project-boundary stress test

## Verdict

**Complete; stop for review. No candidate is ready for integration.** The frozen
matchers frequently assert “same project” for explicitly separate undertakings with
similar subject matter. The independent controlled-English rule prototype abstains
on every natural-prose packet, so its conflict gates provide no improvement.

This is a diagnostic of existing models, not new training, actual River grouping,
repair execution, or a replacement for P2 qualification. Earlier C3/C4 benefits under
their tested policies remain valid; C6 exposes a different boundary weakness.

## What was evaluated

- C5's eight fictional English story families: 160 pair/context packets, representing
  80 queries with repeated pairs across episodes and views. Deduplicating identical
  visible contexts yields 112 review contexts and 56 distinct queried text pairs.
- Two independent agents each reviewed 56 pair-only contexts, sealed those judgments,
  then reviewed 56 additional contextual inputs. They agreed on all 112 judgments.
  Both identified one original-label issue; root adjudication changed one expanded
  packet from `same_project` to `abstain` in a separate C6 reference. C5 is unchanged.
- Four frozen scorers: the simple feature classifier and the existing neural-plus-
  feature hybrids, seeds 17, 29 and 41. Passing the unchanged attachment threshold
  means `same_project`; failing means `abstain`, **not** `separate_projects`.
- One independently implemented, corpus-blind rule verifier, plus four candidates
  using its explicit-separation verdict to veto the corresponding legacy prediction.
  Nine candidates × 160 packets = **1,440 predictions**.

The baseline is not raw cosine similarity alone. The hybrids combine existing
embedding/feature signals with the trained neural pair scorer. Review agents label
the benchmark; they are **not** a local model candidate evaluated here. The rule
verifier is not a general-purpose language model.

All legacy scorers see only the queried pair, even in the context view. The rule
verifier receives the complete visible packet. No model receives labels or review
rationales. Legacy evidence quotations are automatically attached input provenance,
not model-generated explanations.

## Primary results: pair-only view

80 packets: 23 same-project, 24 separate-project and 33 uncertain references.
Repeated pairs are correlated; these are not 80 independent trials.

| Candidate | Same-project precision | Same-project recall | Wrong “same” on separate projects | Unsupported “same” on uncertain inputs |
| --- | ---: | ---: | ---: | ---: |
| Simple baseline | 19/51 (37.3%) | 19/23 (82.6%) | 21/24 | 11/33 |
| Hybrid 17 | 21/55 (38.2%) | 21/23 (91.3%) | 21/24 | 13/33 |
| Hybrid 29 | 20/52 (38.5%) | 20/23 (87.0%) | 21/24 | 11/33 |
| Hybrid 41 | 21/56 (37.5%) | 21/23 (91.3%) | 22/24 | 13/33 |
| Scope rules | Undefined: no assertions | 0/23 (0%) | 0/24 | 0/33 |

Precision here is verified same-project assertions divided by **all** same-project
assertions, including unsupported assertions on uncertain inputs. Recall measures
how many verified same-project examples were recognized. High recall does not offset
the very high false-attachment rate on explicit separation cases.

The rules make **zero decisive predictions on all 160 packets**. They require explicit
project-name bindings and relationship statements in a restricted controlled-English
grammar that these natural-prose inputs do not satisfy. Their zero false assertions
are not evidence of a useful verifier: coverage is zero and precision is undefined.
All four rule-gated candidates exactly reproduce their ungated counterparts.

## Context view and diagnostic partition

Context view: 80 packets, with 32 same-project, 32 separate-project and 16 uncertain
references. The legacy scores do not change when context is added. Differences below
come from the contextual **reference judgments**, not successful context reasoning.

| Candidate | Same-project precision | Same-project recall | Wrong “same” on separate projects | Unsupported “same” on uncertain inputs |
| --- | ---: | ---: | ---: | ---: |
| Simple baseline | 24/51 (47.1%) | 24/32 (75.0%) | 22/32 | 5/16 |
| Hybrid 17 | 27/55 (49.1%) | 27/32 (84.4%) | 22/32 | 6/16 |
| Hybrid 29 | 25/52 (48.1%) | 25/32 (78.1%) | 22/32 | 5/16 |
| Hybrid 41 | 27/56 (48.2%) | 27/32 (84.4%) | 23/32 | 6/16 |

The four-family diagnostic partition alone contains 80 packets across both views,
with 28 same-project, 28 separate-project and 24 uncertain references:

| Candidate | Same-project precision | Same-project recall | Wrong “same” on separate projects |
| --- | ---: | ---: | ---: |
| Simple baseline | 19/42 (45.2%) | 19/28 (67.9%) | 20/28 |
| Hybrid 17 | 22/48 (45.8%) | 22/28 (78.6%) | 20/28 |
| Hybrid 29 | 21/44 (47.7%) | 21/28 (75.0%) | 20/28 |
| Hybrid 41 | 22/48 (45.8%) | 22/28 (78.6%) | 20/28 |

The rules also abstain throughout this partition; gated results are unchanged.
No seed is a defensible winner from these small, correlated differences.

All candidates have zero explicit-separation recall. For legacy models that is by
construction: they were attachment scorers, not trained three-way conflict verifiers.
The important observed failure is their confident **same-project assertions** on
explicit separation. Joint scope/bridge tests requiring an explicit-separation output
score 0/8 in each view; that structural limitation must not be mistaken for an
independent learned-conflict evaluation.

## Concrete failure: similar subject matter is not project identity

In fictional family f05, the first note defines Marble Desk's LedgerOne-to-LedgerTwo
appointment-database migration. Another explicitly defines a **distinct security
incident**, with its own owner and closure criteria, outside that migration. All four
scorers nevertheless predict same-project (`qb957718c29ac1fdb632a58af`, context view).

A genuine continuation describes a rollback and second cutover as recovery work in
the **original migration engagement**, not the access-revocation incident. All four
abstain (`q37c475a4972a0e261da5898b`, context view).

| Scorer | Separate incident score | True continuation score | Frozen threshold |
| --- | ---: | ---: | ---: |
| Baseline | 0.999811 | 0.985355 | 0.998462 |
| Hybrid 17 | 0.995348 | 0.973295635 | 0.973296195 |
| Hybrid 29 | 0.996254 | 0.979401 | 0.980428 |
| Hybrid 41 | 0.995036 | 0.970804 | 0.974235 |

These are model scores, not calibrated real-world probabilities. The wrong pair ranks
above the true continuation in every scorer. Raising a single threshold cannot reject
that wrong pair while retaining this positive example. No thresholds were tuned here.

The one annotation amendment concerns Pine Signal: pair-only evidence names a second
episode title without establishing its link to the original oral-history commission.
Both reviewers abstained (`q52625745202b9a832c89e949`); additional context resolves it
in the contextual variant. All four legacy scorers assert same-project for the amended
pair, reducing each scorer's pooled verified-same count by one versus original labels.
Both original and adjudicated metrics are retained in [summary.json](summary.json).

## Verification and saved checkpoint

- 172 tests passed, including 23 isolated rule fixtures and 10 C6 pipeline tests.
- Two native embedding reference checks had maximum delta zero.
- All three neural seeds reproduced 16 existing reference pairs each: feature,
  directional neural and combined-score deltas were zero; threshold decisions matched.
  This is numerical regression evidence, not device conversion or fresh accuracy proof.
- A real stop after one new embedding, followed by resume, preserved that embedding's
  SHA-256 **and modification timestamp**.
- Full deterministic replay reconstructed all 56 pair features, 1,440 predictions and
  18 candidate/reference metric variants exactly, without repeating neural inference.
- Frozen review records, inputs, sources, model bindings, cached units, errors and
  runtime records are under `runs/c6-01/`; publication is bound by `complete.json`.

Executed with the existing feasibility virtualenv and `PYTHONDONTWRITEBYTECODE=1`:

```sh
python -m unittest discover -s scripts/organization-diagnostics -p 'test_*.py'
python scripts/organization-diagnostics/c6_finalize.py proof-after
python scripts/organization-diagnostics/c6_finalize.py tests
python scripts/organization-diagnostics/c6_finalize.py audit
```

Completion publication must be followed by `c6_finalize.py verify`. For the exact
interpreter and current verification command, see [RESUME.md](../RESUME.md).
No training, downloads, phone/simulator tests, personal-memory access, production
changes or Git-state mutations occurred. Storage remained within the cumulative
4 GiB limit including the 1 GiB simulator reserve, with more than 10 GiB free.

## Limitations and recommended next decision

These are small, agent-reviewed synthetic English stress tests, with shared story
templates, repeated pairs and only four diagnostic families. Agent agreement is not
human validation; shared model-family errors and procedural rather than enforced
packet isolation remain limitations. These results neither estimate normal-user
accuracy nor validate OCR, audio/video understanding, multilingual use or phone speed.

**Do not ship, expand training, or tune the rules on these exposed families yet.**
The useful next question is whether a context-aware semantic verifier can distinguish
project identity from topical similarity. A bounded next experiment could test the
existing local language reasoner in a narrower role: return same/separate/uncertain
with visible-source evidence, never choose or mutate Rivers itself. Its previous poor
placement results make success uncertain; this is a hypothesis to test, not a solution
already shown to work.

First check local runtime availability and freeze the output contract and evaluation
plan. Keep the current scorers and abstention control, separate runtime failures from
uncertainty, and use fresh independently reviewed examples before claiming improvement.
No cloud fallback, new model, automatic merge or training is implicitly authorized.
This subsequent checkpoint requires user approval; C6 ends here.
