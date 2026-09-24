# Retained history evidence audit

This checkpoint reads production source and compiles it unchanged in an isolated
simulator probe. It does not inspect a personal vault or claim original media
availability. The index is an experiment-only, rebuildable projection.

## What is retained

`Provenance.swift` records a complete `MemoryItem` snapshot for capture, import,
revision, enrichment, metadata, processing, archive and restore. The append-only
SQLite ledger assigns increasing sequences and immutable event UUIDs. Source
events are capture/import/revision. A revision's `sourceRevisionID` points to its
predecessor; later enrichment points to the source event it enriches. The index
uses the source event's own UUID as the version identity, and the evidence-bearing
snapshot event UUID as the snapshot identity. Source identity alone is insufficient.

`ProvenanceSnapshot.replay` rebuilds current memory and organization state, but its
memory dictionary overwrites earlier snapshots. The history projection scans the
retained source events separately, associating enrichment by explicit revision UUID
and validating memory UUID and original filename. It only reads evidence snapshots
at or before the requested ledger sequence. Late enrichment for an older revision
cannot become the current revision. Each source revision contributes its latest
available evidence snapshot at the boundary; previous same-revision extraction
snapshots remain in the ledger and can be projected using earlier boundaries.

`MemoryStore.updateNoteContent` records revisions and replaces current chunks;
`markIndexed` records enrichment and also replaces current chunks. `MemoryChunk`
IDs encode memory UUID and ordinal, without source revision or snapshot identity.
Those materialized chunks cannot serve as a historical index. The experiment
reuses `MemoryTextChunker` on retained `extractedText` and distinct `userCaption`
only, then derives IDs from source UUID, source-event UUID, snapshot-event UUID,
field and chunk ordinal. It never uses generated title/summary/tags as source
evidence. The production text chunker trims surrounding whitespace and normalizes
CRLF line endings; fixtures use canonical line endings.

## Boundaries and honest limitations

- Existing memories imported by migration have only the snapshot retained at
  upgrade. Earlier revisions cannot be reconstructed; imported candidates carry
  `importedHistoryGap=true`.
- Ledger snapshots contain original filenames, but no retained per-chunk page,
  image-region, audio-time or video-time locators. Rechunking cannot recreate them.
  Candidate locators identify a retained ledger text field/part only. The probe
  declares `mediaLocatorAvailability=unavailable` and does not invent page/time.
- Fictional probe inputs contain no original assets. The probe never opens the
  production library or media directories, and declares
  `originalAssetAvailability=unavailable`. Retained extracted text remains usable
  evidence even when an original is absent.
- Production `delete(id:)` delegates to archive; it is not erasure and emits no
  hard-delete tombstone. Current scope excludes archived memories. Explicit
  `includeHistory` includes archived sources and superseded revisions. A supplied
  external tombstone set excludes all candidates for those IDs in every scope and
  at every historical boundary. This is a fail-closed input contract, not a claim
  that production already implements an erasure registry.
- Organization corrections alter membership/pinning, not source evidence identity.
  The unchanged ledger harness verifies organization state separately.
- Results are ordered by source sequence, evidence field and chunk ordinal for
  deterministic enumeration. Query text is not scored, no model is invoked, and
  the coverage limit is not a relevance top-k. Ranking and abstention remain out
  of this checkpoint.

The raw ledger is retained with its original harness receipt. Projection receipts
bind input batch, source bindings, raw ledger and projection SHA-256. Each command
prefix is rebuilt after closing and reopening SQLite. Resume verifies hashes and
skips completed units. The coordinator runs one library per native invocation
(`--max-runs 1`) so the ledger and projection receipts complete as one bounded unit.
Before replay inspects existing receipts, the probe rejects symlinks in its output
tree and validates attempt directory names against the run hash plus UUID. Invalid
source chains, duplicate captures/imports, and archive snapshots without a valid
source revision fail closed.

`--invariants` runs the unchanged production invariant harness followed by the
history checks. A bound receipt hashes the input batch, compiled source bindings,
both invariant reports and their retained ledgers (including the synthetic history
ledger). Resume verifies those hashes before skipping completed invariant work.
