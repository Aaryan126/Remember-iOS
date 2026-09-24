# Source-first browsing: two checkpoint plan

## Purpose

Help people find retained evidence and understand revisions. Do not generate an
answer, assert that an absent search hit proves absence, or change project grouping.
The failed Stage B answer verifier remains excluded from the app.

## Checkpoint 1 — read-only foundation (current authorization)

Estimated active work: 45–90 minutes; Mac only. Stop for review when complete.

1. Add an isolated source-search projection and a read-only ledger adapter. Do not
   wire UI, change ordinary search, migrate data, or initialize a model.
2. Search retained extracted text and distinct user captions only. Generated titles,
   summaries, tags and organization rationales are not evidence. Reuse the existing
   text chunker; keep lexical ranking simple and explicitly non-probabilistic.
3. Default to current, unarchived revisions. Explicit history scope includes retained
   superseded revisions and archived memories. Archive is not erasure: the existing
   app explicitly promises retained originals/history. Support an exclusion set but
   do not pretend the app already has a hard-erasure registry.
4. Bind every hit to source, revision, enrichment snapshot, ledger sequence and field.
   Respect historical cutoffs; never use later enrichment to answer an earlier view.
   Mark imported history gaps and partial extraction. Do not invent PDF pages, video
   timestamps, or original-file availability when the ledger does not retain them.
5. Validate ordering, identity and revision chains, fail closed on malformed inputs,
   support cancellation, and rank before pagination. Return explicit errors for
   safety limits rather than silently claiming a complete search.
6. Run deterministic native tests with fictional data; record source bindings,
   commands and actual results. Preserve frozen experiments, their source files and
   the untouched evaluation split. Save a report and resume instructions.

No paid calls, training, device/private-vault access, dependencies or Git mutations.
Keep the existing 21 GiB conservative-growth cap and 10 GiB free-space reserve;
do not reset the original resource baseline. Compile artifacts stay under the
already-accounted ProvenanceFirst runs tree. Pause between bounded compile/test units.

## Checkpoint 2 — UI and integration (review first)

Proposed 4–8 active hours, conditional on checkpoint-1 review and build/device access.

- Add a distinct local “Search saved evidence” entry; do not route it through the
  cloud assistant or silently replace ordinary search.
- Show Current / Include history, exact excerpts, revision/archive context, source
  availability limitations and honest no-match/error/loading states.
- Navigate to the retained version, not the latest replacement. Return directly to
  search/River with query and position preserved. Verify accessibility and light/dark
  appearance, cancellation and stale-result handling.
- Before editing previously frozen production inputs, preserve reproducible baseline
  bindings explicitly. Do not rewrite historical receipts to hide source changes.
- Run full app build, integration tests and fictional-data phone smoke tests. Personal
  vault testing requires a separate explicit choice. Re-measure retrieval quality on
  approved fixtures before making quality claims.

This plan does not qualify lexical search as a reliable answer system. Foundation
tests establish scope/provenance correctness, not real-world search accuracy.
