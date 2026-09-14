# P1 checkpoint: reviewed benchmark ready

Completed 13 September 2026. **Stopped before training for user review.** This is a dataset-readiness result, not a new model-quality result or permission to ship the hybrid.

## What is saved

| Split | Story families | Libraries | Fictional sources | All within-library pairs |
| --- | ---: | ---: | ---: | ---: |
| Training | 12 | 24 | 480 | 4,560 |
| Calibration | 6 | 12 | 240 | 2,280 |
| Evaluation | 6 | 12 | 240 | 2,280 |
| Total | 24 | 48 | 960 | 9,120 |

Families and splits were assigned before authoring. The P0 pilot is excluded. Model inputs are projected separately from memberships, rationales and history expectations. Three family-grouped training folds each reserve eight libraries for out-of-fold scoring and fit on the other sixteen.

| Final pair label | Count | Meaning |
| --- | ---: | --- |
| Same thread | 1,753 | At least one shared concrete objective |
| Related, different thread | 2,508 | Linked work, but not permission to merge |
| Unrelated | 3,277 | Distinct objectives without a supported contextual link |
| Uncertain | 1,582 | Unresolved source identity or explicit pair-only insufficiency |

Source memberships include 821 single-thread sources, 54 multi-thread bridges and 85 unresolved sources. An explicit bridge does not merge all its neighboring threads. Modalities are 288 notes, 199 files, 195 voice transcripts, 184 image transcriptions and 94 video descriptions/transcriptions—all fictional text, not real media processing.

For example, correcting a book's catalogue record and dispatching that book can be **related** while remaining separate objectives. A note that both reserves stock and prepares its packing list can explicitly belong to both. A fragment like “90 by Thursday; ask L.” may be resolved by the full cello-loan history while remaining uncertain when paired with a note that lacks those identifying details.

## Review and corrections

Three authors independently created their assigned stories, then reviewed a different author's batch in two stages. Pair-first packets omitted proposed labels and full-library context. Context review followed only after the pair review was sealed, and supplied thread definitions/history expectations but not authored memberships or rationales.

- **576 pairs** received direct pair-first judgments: 12 per library, selected by lexical overlap plus deterministic sampling. This is about 6.3% of all pairs, not exhaustive pair review.
- **All 960 sources** received a second context-level membership assignment.
- **131 disagreements** received explicit root adjudication: seven memberships, 23 link sets and 101 pair judgments. Root also corrected one unsupported link on which both agents had agreed.
- **35 affected sampled pairs** received a final reassessment after contextual corrections. Eight explicit pair-only uncertainty overrides preserve missing-context cases without deleting contextual history membership.
- The final projection changes 630 authored pair labels, mainly related/unrelated subtypes propagated from link corrections. No model scores informed those decisions.

Original author files, pair/context reviews, receipts and disagreement evidence are preserved. See [adjudication](adjudication.json), [source review and limitations](source-review.md), and [machine-readable audit](releases/v1/audit.json).

## Checks completed

All **269 tests passed** in the final run, using the existing feasibility Python environment:

```sh
python -m unittest discover -s scripts/matcher-validation -p 'test_*.py' -q
# 64 passed
python -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q
# 183 passed
python -m unittest discover -s scripts -p 'test_organization*.py' -q
# 22 passed
python scripts/matcher-validation/prepare.py verify
python scripts/matcher-validation/p1_release.py freeze
python scripts/matcher-validation/p1_release.py verify
python scripts/matcher-validation/p1_release.py freeze
# P0 verified; P1 published and verified; repeat freeze verified the same receipt.
```

Here `python` denotes `/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python`; exact copyable invocations are in [RESUME](RESUME.md).

Final validation checked strict per-library quotas and identifiers, split/family isolation, all-pair coverage, membership/link endpoints, historical overlap and history invariants. A separate thread-member-set implementation independently reconstructed all 9,120 pair labels and matched the release. Forty-eight **reference** history fixtures replay successfully; Remember's production history implementation has not been tested in this stage.

The final harness includes regression checks for missing manifest inventories, changed labels needing fresh pair dispositions, invalid post-adjudication libraries, uncertainty overrides and additional root corrections. The earlier independent harness audit's three findings were fixed; its re-audit passed. Subsequent root additions also passed the final test suite.

No exact or ≥0.85 three-token-shingle duplicate was found against the 520 already-inspected old training/development/pilot sources. Largest old/new overlap was 0.056; largest cross-split overlap was 0.154. Root inspected the 24 highest cross-split overlaps. **The old final test was not opened.** Low lexical overlap is not proof of semantic independence.

The P1 receipt binds 81 source/evidence files and 16 release artifacts. SHA-256:

`a00ed7144b3fa443d6234ee39f4d0186c3d1cd1179f612108a5a7d4721f2ebcc`

Integrity verification detects changes relative to this local receipt; it is not tamper-proof access control or an independent accuracy certificate. Presentation files such as this report are outside the frozen source manifest.

## Limitations and decision

**Proceed to P2 after user approval.** No structural or integrity blocker remains. This release is suitable for the predeclared controlled experiment, with important limits:

- Reviewers are separate agents with shared model-family capabilities, not humans with independent error distributions.
- Concrete-objective granularity is an agent-defined policy; users may prefer broader Rivers. Relatedness boundaries remain judgment calls.
- Most sources are short English text; only nine notes are 100–160 words. There is no multilingual, long-document, real OCR/ASR or production distribution coverage.
- Pair-only sufficiency was directly reviewed for a sample, not every generated pair. Some context-defined targets may remain ambiguous to a pair-only matcher.
- Synthetic hard negatives are deliberately common. Six evaluation families give limited independent evidence, and pair counts must not be treated as independent sample counts.
- No new model was fitted or scored. Nothing here establishes an improvement over the baseline or end-to-end memory-map reliability.

## Resources, pause and next stage

The validation data and scripts occupy approximately **4.4 MiB** at handoff; the volume had approximately **33.5 GiB free** at the final measurement. No models were downloaded, prior artifacts deleted, app files changed or Git state modified. All three contributors are finished, and no training worker is running. It is safe to close the laptop.

Next is **P2: baseline versus three-seed D3 validation**, estimated **8–16 active hours, Mac only**, subject to measured throughput. First implement and exercise full-state training pause/resume and verify peak-storage headroom. Then fit on training only, select thresholds on calibration, freeze all choices and evaluate once. Report every seed; do not tune on evaluation or choose only a lucky seed. Stop again with a go/no-go report.

The hybrid must satisfy the unchanged precision/recall gates for all three seeds before any separately approved downstream or phone experiment. This checkpoint does not start that work automatically.
