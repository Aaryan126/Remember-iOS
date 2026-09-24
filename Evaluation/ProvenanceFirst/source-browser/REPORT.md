# Checkpoint 1 — source-first browsing foundation

## Result

The additive, read-only foundation is implemented and its **52 native tests pass**.
The prior Stage B **25-test regression suite also passes**. This is a technical
foundation checkpoint, not a retrieval-quality win or a shipped search screen.

No UI calls the new service. Ordinary search, D3 organization, cloud assistant,
database schema and existing ledger writers are unchanged. No model requests,
phone installation, private-vault access or Git mutations were performed.

## Changes

- `Remember/Remember/SourceEvidenceSearch.swift`: pure ledger projection and lexical
  passage ranking. Current/unarchived is the default; Include history explicitly
  includes retained superseded revisions and archived memories.
- `Remember/Remember/SourceEvidenceStoreAdapter.swift`: actor service using one
  read-only `provenanceEvents()` fetch, with cancellation and error propagation.
  Invalid requests are rejected before fetching the ledger.
- `scripts/provenance-first/source-browser/`: bounded native test runner and
  fictional tests, with build/test bindings and a read-only checkpoint verifier.
- This plan/report/resume/status set and `docs/provenance-first.md` document the
  new checkpoint without rewriting prior results.

Only retained extracted text and distinct user captions are searchable. Generated
titles, summaries, tags, rationales and metadata do not become evidence. Hits carry
source/revision/snapshot identity, source and extraction sequence/date, text-field
location, current/archive state, partial-extraction flag and imported-history gap.
Search does not verify original-file presence or reconstruct missing media locators.

Late enrichment remains attached to its named revision. Historical cutoffs exclude
later payloads, including later extraction. Rank-before-pagination prevents an early
enumeration limit from hiding a better later match. Ties use source sequence, field
and chunk ordinal deterministically; lexical weights are not confidence scores.

## Compatibility finding

The existing `ProjectViewModel.restoreRevision` writes a user note revision with
`referencedEventID`, but no `sourceRevisionID`. The earlier experimental index would
reject this shape. The new adapter/projection accepts this narrowly defined legacy
case only when the referenced source exists, belongs to the same memory, and its
original filename, extracted text and caption match the restored snapshot. It must
be an unarchived user text-note restoration with an existing current predecessor.
This creates a new searchable revision, not an overwrite of earlier history.

Tests cover valid restores, restoration after enrichment, forged/missing/cross-source
targets, and rejection of media revisions using the legacy note-only shortcut.
No stored records or old source files were modified to make the tests pass.

## Validation actually run

From repository root:

```sh
python3 -B scripts/provenance-first/source-browser/check.py --unit build
python3 -B scripts/provenance-first/source-browser/check.py --unit test
python3 -B scripts/provenance-first/source-browser/check.py --unit regression
git diff --check
```

- Native build: Apple Swift 6.4, Swift 5 language mode, default MainActor isolation,
  complete strict-concurrency checking and warnings-as-errors; exit 0.
- Native tests: 52 passed, 0 failed. Covers scopes, cutoffs, late enrichment, archive/
  restore, captions, generated-text exclusion, identity/order validation, pagination,
  imported gaps, partial extraction, cancellation, storage errors and size limits.
- Existing regression tests: 25 passed. These use frozen/mock fixtures, not new
  model requests. Prior source bindings and stopped Stage B artifact hashes verify.
- `git diff --check`: exit 0 for tracked changes. New checkpoint files were also
  checked separately for trailing whitespace/conflict markers before sealing.
- Pause-boundary check: a temporary `PAUSE` marker made `--unit test` refuse
  dispatch with the expected pause message. SHA-256 hashes of both build and test
  receipts were unchanged before/after. The test marker was then removed.

Build and test receipts are in `../runs/source-browser/`. The native harness compiles
the new core and real adapter/service, unchanged production model/Codable declaration
excerpts, and the existing text chunker. It replaces GRDB marker protocols and the
storage transport with explicit test fixtures. **This is not a full iOS app build,
GRDB integration test, device test or UI verification.** Those remain checkpoint 2.

## Limits and next gate

- These are deterministic engineering fixtures, not a new independent evaluation
  dataset. We have not measured improved retrieval accuracy or user satisfaction.
- This is lexical passage retrieval, not verified answers, semantic inference or
  project-relationship inference. A no-match result cannot establish factual absence.
- OCR/transcripts may themselves contain extraction errors. Retained text is not a
  guarantee that the original media says the same thing.
- Migration imports cannot recover pre-migration revisions that were never recorded.
  Earlier extraction snapshots within a revision are available only through a
  sequence cutoff; Include history enumerates source revisions, not every enrichment.
- The initial implementation rebuilds an in-memory projection per request. It is
  not an indexed/scalability-optimized implementation. Safety limits are 100,000
  ledger events, 4 MiB UTF-8 per searched field, 32 MiB total searched text, 512 query
  characters and 100 returned passages/page. Limits produce errors, never silent
  truncation; the ledger fetch still materializes records before projection limits.
- Exclusions are caller-supplied. They do not implement hard erasure.
- The native run workspace is approximately 30 MiB. Resource checks remain under
  the approved 21 GiB conservative-growth cap and above the 10 GiB free reserve;
  exact measurements are in the receipts. Original accounting baseline is unchanged.

**Recommendation: proceed to the UI/integration checkpoint after review**, retaining
the source-only contract. Estimate 4–8 active hours, with the Mac needed first and
the connected, unlocked phone only for later device checks. Inspect full integration
compatibility before exposing the entry point. Do not enable the failed verifier or
claim the earlier B/C ranking variants are qualified.
