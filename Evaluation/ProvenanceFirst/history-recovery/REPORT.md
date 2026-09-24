# History recovery checkpoint 1 — complete; stop for review

The isolated history-aware evidence foundation passed its coverage and integrity
checks. **This is not a ranking result, a better grouping model, or an app release.**
Checkpoint 2 is not authorized by completing this checkpoint. See the machine
[completion receipt](checkpoint1-complete.json) and [coverage results](coverage.json).

## What was implemented

An experiment-only Swift projection reads the unchanged production provenance
ledger and rechunks retained source text with the production text chunker. Evidence
identities distinguish the source, source revision, evidence snapshot, field and
chunk. It handles late enrichment without exposing a future revision at an earlier
ledger prefix. Generated summaries are not treated as source quotations.

The default scope is `current`: current versions of nonarchived sources. Explicit
`includeHistory` adds retained archived and superseded evidence. The projection
supports source restrictions, result limits and a fail-closed external tombstone
filter. It enumerates eligible evidence deterministically; it does not score query
relevance. No production search API, app UI, database schema or personal vault changed.

## Benchmark and results

Fresh fictional data: 12 development and 12 evaluation libraries, each with 12
events and four questions (current, historical, overlap, unanswerable). Of the 24
historical tasks, 12 require archived sources and 12 superseded active-note versions.
Queries have explicit scope; the index does not infer it from evaluator labels.

| Check | Result |
| --- | ---: |
| Reviewed libraries / chronological events | 24 / 288 |
| Query tasks: answerable / unanswerable | 72 / 24 |
| Expected question-evidence targets available | **72/72** |
| Historical questions with all expected evidence available | **24/24** |
| Native prefix checks in current / history scope | 288 / 288 |
| Library database reopen/rebuild checks | 24 |
| Existing ledger / new history invariants | 31 / 33 passed |
| Python tests | 165 passed (143 existing + 22 new) |
| Fixture / native pause-resume proof | Passed / passed |
| Previously saved source/experiment files verified unchanged | 2,779 |

These are **candidate availability** checks, not precision, recall@3, abstention,
answer accuracy or real-user performance. Each expected target is counted per
question, not as an independent distinct source. An unanswerable question still has
an eligible candidate collection; this checkpoint does not claim it can decide which
results to suppress. Ideal assignments enter the existing ledger verification
harness, never the history index. Automatic organization was not evaluated again.

Development and evaluation were authored separately and reviewed by the other
author without model predictions. Initial reviews identified missing causal edges,
false-premise unanswerable questions, contradictory rationales and a duplicated
scenario mechanism. Authors corrected them; separate re-reviews passed before the
data/code/build bindings were frozen. Original reviews and correction notes are
retained. Evaluation was used only for coverage/integrity, not threshold or model
selection. This is agent-reviewed fiction, not independent human ground truth.

## Limitations requiring honest product behavior

- Pre-import revisions that were never saved remain unavailable.
- Historical text is retained, but historical page/audio/video locations are not
  reliably recorded. The prototype cites ledger text/versions and explicitly marks
  media locators unavailable; it cannot recreate them by rechunking.
- No originals exist in these fictional fixtures. Media playback, OCR, ASR and
  original-file recovery were not tested.
- Production `delete(id:)` currently archives rather than erases. History can
  therefore include such archived content. The external tombstone filter is tested,
  but a production erasure registry is not implemented. Deletion terminology and
  visibility need explicit resolution before live history-search integration.
- No query ranking, embeddings, new model, paid API, phone or personal data was used.
  Existing Core ML qualification concerns are not superseded.

## Validation and reproducibility

Commands actually run include `benchmark.py validate`, `native_driver.py prepare`
and `build`, `benchmark.py freeze` and bounded/resumed `prepare`, one native library
with both invariant suites, then resumed native replay through all 24 libraries.
`verify_coverage.py --complete --save`, both `pause_proof.py verify` commands,
`benchmark.py verify`, and `control.py verify` passed. The explicit build command
and hashes are in [native-build.json](native-build.json); exact Python suite commands
and outputs are in [python-tests.json](python-tests.json). `git diff --check` passed.

The fixture pause proof preserved three completed files; the native proof preserved
82 previously completed unit/receipt/projection/ledger files with identical hashes
and modification times. All 24 native libraries are processed in bounded units.
Two overlapping CLI attempts (native launch during fixture preparation, verification
during native replay) were rejected by the single-worker lock with
`BlockingIOError`; both were rerun sequentially and passed. No saved work was lost
or overwritten. Native build/runtime and quality gates were not weakened.

The user-approved 18 GiB cap retained the original shared baseline and 10 GiB free
reserve. In the completion receipt, conservative growth was approximately 16.5 GiB,
with approximately 25.4 GiB free. This checkpoint's code/artifacts/build occupied
about 282 MiB, excluding registered simulator growth. Whole-Mac free-space decline
is not all attributable to this work. No cleanup or baseline reset occurred.

Workers stopped; the isolated simulator was shut down. Safe to close the laptop.
The app, personal vault and Git state were not changed.

## Next decision

Proceed to checkpoint 2 only after user review: compare the fixed current-source
reference, history-aware lexical search and history-aware lexical-plus-existing
embedding search, tuning only on development data. Before tuning, freeze the finite
settings, abstention/coverage criteria and selection rule. Retain the original
outside-suggestion precision/recall advancement requirements. Do not treat this
coverage pass as automatic permission to integrate or promote a new model.

Estimate for that separately approved stage: 8–14 active hours, Mac only, with
the same pause/resume and review-stop workflow. Device/UI integration remains a
later conditional checkpoint. See [RESUME.md](RESUME.md) and [PLAN.md](PLAN.md).
