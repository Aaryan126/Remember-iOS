# C5 complete — conflict-review test material prepared

**Preparation is complete; stop for user review. No new model accuracy has been
measured.** C5 defines the task, prepares fresh diagnostic packets and provides a
tested metric adapter. Independent semantic review is still pending, so the receipt
explicitly says `readyForModelScoring: false`. No training or app integration occurred.

## What was built

The [protocol](../C5_PROTOCOL.md) separates three judgments:

- `same_project`: at least one shared continuing undertaking;
- `separate_projects`: affirmative evidence of distinct undertakings;
- `abstain`: insufficient or contradictory evidence.

A low match score does not become a conflict label. A shared bridge does not make two
projects equivalent. Source text is not a trusted instruction to mutate the user's
organization. A conflict finding may flag review; it is not itself a safe split plan.

The design uses capability-focused behavioral tests, motivated by
[CheckList](https://aclanthology.org/2020.acl-main.442/), and paired scope contrasts,
motivated by [contrast sets](https://aclanthology.org/2020.findings-emnlp.117/).
These are methodological references, not evidence about Remember's performance.

## Prepared dataset

Eight fictional families cover radio production, conservation grants, equipment design,
annual events, software migration, building restoration, horticulture experiments and
translation contracts. Each family has seven authored texts, six diagnostic episodes
and ten pair queries. Each query is presented in pair-only and observed-context views.

| Prepared artifact | Count |
|---|---:|
| Families | 8 |
| Source texts | 56 |
| Episodes | 48 |
| Pair queries | 80 |
| Input packets across two views | 160 |
| Model predictions or training runs | **0** |

All variants of a family remain in one partition: four discovery families and four
diagnostic families. No training split exists. The author has seen all labels; this
is not an untouched or independently blinded qualification benchmark.

| Authored expected judgment | Pair-only packets | Context packets |
|---|---:|---:|
| Shared project | 24 | 32 |
| Separate projects | 24 | 32 |
| Abstain | 32 | 16 |

These are **label counts, not successful model predictions**. The repeated topology,
views and contrast episodes are correlated; there are only eight underlying families.
The deliberately enriched mix does not represent real-world conflict prevalence.

### Small example

Pine Signal commissions an oral-history episode about harbour night workers and a
separately approved harbour weather programme. Both use some of the same recorded sound.

- Oral-history work versus weather work: separate projects.
- The oral history is renamed *When the Quay Sleeps*: same project, not a new commission.
- A studio booking schedules both: the booking belongs with both, but does not merge them.
- “The producer approved that harbour segment”: unresolved, because either programme
  could be meant.
- A later visible clarification identifies the oral-history episode: context can resolve
  the memo. The identical pair-only packet, which cannot see that clarification, must
  still abstain.

Other cases include late event refunds, warranty work, repeated experiments, reused
identifiers and a misleading imperative quoted inside imported text.

## Validation and review limits

All 139 diagnostic tests passed, including 19 new C5 tests. They cover:

- strict source-only packet projection, rejecting label/rationale fields;
- fixed family partitions, exact duplicate rejection and grounded evidence spans;
- bridge non-transitivity and negated separate-project interpretations;
- unchanged pair-only inputs before/after a context-only clarification;
- missing/duplicate predictions failing instead of becoming silent abstentions;
- uncertainty excluded from evidence of a separate project;
- an always-abstain fixture having zero recall and undefined precision;
- joint success for complete scope contrasts, bridge triples and reference sequences;
- immutable work units, resource guards and pause/resume.

All 160 packets and their reference records were deterministically reconstructed.
A real one-family stop/resume preserved the first unit's bytes and timestamp. The
prior C4 completion chain verifies unchanged. Tests using hand-supplied predictions
exercise arithmetic and schemas only; their correctness is not model performance.

The 56 source texts had **zero exact matches** against C2's 157-text catalogue. Maximum
word-trigram Jaccard overlap was 4.26% against that catalogue and 5.45% across the new
partitions. These lexical checks do not establish semantic independence from all prior
experiments, novelty of the underlying template, or absence of annotation shortcuts.

The primary assistant authored and self-reviewed the examples; see
[author review](AUTHOR_REVIEW.md). There was **no independent agent consensus or human
review**. The scope language is often explicit; harder implicit boundaries, distractors,
contradictory/retracted context, multilingual material, real OCR/ASR and user-specific
preferences remain untested. This small release cannot substantiate a production
precision threshold, and training on its obvious wording could teach shortcuts.

## Next step and mandatory stop

The next checkpoint should first obtain independent, prediction-blind semantic review
of these exact source-only packets, preserve disagreements and append any adjudication.
Then freeze a limited scoring protocol and adapters before comparing the existing
baseline and all three hybrid seeds with an evidence-aware conflict-review prototype.
Legacy attachment models must not be described as context-aware verifiers, and their
below-threshold scores must not silently become cannot-link predictions.

Report conflict precision **and coverage**, false conflict flags on genuine continuations
and bridges, unsupported assertions on ambiguity, and joint contrast consistency.
Keep actual model predictions separate from simulated user acceptance. Do not introduce
another neural training run until this shows whether useful conflict evidence exists.

Estimated next review-and-bounded-scoring checkpoint: **4–8 active hours, Mac only**,
with pause/resume and a review stop. This is a planning estimate, not a measured runtime;
the final candidate/adapters must be frozen before execution. It excludes training,
production integration and phone validation. It is not started or approved.

## Saved files and verification

- `authored-families.json`, `AUTHOR_REVIEW.md`: frozen initial text and author rationale.
- `runs/c5-01/release/inputs.json`: source-only packets for a future model adapter.
- `runs/c5-01/release/gold.json`, `splits.json`: evaluator-only references and partitions.
- `runs/c5-01/manifest.json`, `prepared.json`: source and release bindings.
- `runs/c5-01/validation/`: test command/output and lexical-overlap evidence.
- `scripts/organization-diagnostics/c5_*.py`, `test_c5.py`: compiler, metric adapter,
  checkpoint runner and tests. No production sources were modified.

Use the existing Python environment from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/organization-diagnostics/c5_run.py verify
```

No model downloads, inference, training, phone/simulator use, personal-vault access or
Git-state mutations occurred. Resource guards retained the 4 GiB cumulative diagnostic
cap, existing 1 GiB simulator reserve and 10 GiB free-space floor. No files were deleted.
At handoff all C5 workers are stopped; it is safe to close the laptop. Read
[resume instructions](../RESUME.md) before continuing; do not restart completed work.
