# Compact search menu installed — 23 September 2026

## Outcome

Updated the main `SimpleStudio.Remember` app in place on the physical iPhone 17,
iOS 27.0 (24A437). The two search filters now live in a native Search options menu;
only enabled filters show a compact status and Reset. Open Memories → Search your
memories, then tap the filter icon in the results header.

The normal app and share extension retain their signing identities and app group.
The D3 matcher remains bundled. No uninstall, restore, forced regrouping, model or
threshold changes, paid AI request, preference change or Git state change.

## Checks actually run

All deployment actions used
`python3 -B scripts/provenance-first/search-options/deploy.py ACTION`:
`prepare`, `build`, `backup`, `inspect-backup`, `install`, `smoke` (two attempts),
`post-backup`, `compare`, `launch`, then `finish` after saving documentation.

| Check | Result |
|---|---|
| Signed normal app + extension build and identity checks | Passed |
| Fresh pre-install backup | 183 files verified; SQLite healthy; 11 migrations match |
| Startup safety | 8 indexed memories; no pending capture/inbox/video work; cloud assistance off |
| First phone smoke | Runner failed to initialize: timed out enabling automation; test did not start |
| Phone smoke retry | 1/1 passed; 0 failures/skips/reported runtime warnings |
| Post-install backup | 184 files verified; SQLite healthy |
| Memory records | All 8 rows unchanged |
| Provenance history | All 171 events unchanged |
| Original media | All 8 files byte-identical |

The phone test uses a fictional no-match query. It checks hidden-by-default filters,
opening the menu, changing both filters, resetting, and returning to Memories.
It does not open or modify personal sources or invoke AI. The first runner timeout
was retained rather than hidden; the successful retry used the same signed build
and test without changing production code or weakening assertions.

This is a bounded navigation smoke, not a full physical-device regression or a new
search/model-quality evaluation. The earlier implementation checkpoint separately
passed 18 native tests and 7 simulator UI tests, including light/dark accessibility
visual review. Zero runtime warnings refers to the successful xcresult summary,
not a claim that all compiler/tool warnings are absent.

## Receipts and recovery

Private ignored run root: `Evaluation/ProvenanceFirst/runs/search-options-deployment/`.

- Signed build: operation `1790173800327953000`.
- Pre-update backup: `backup-1790173846755269000`.
- In-place install: operation `1790173927976486000`.
- First smoke: `smoke-1790173948325830000.xcresult`, operation `1790173950229452000`.
- Successful retry: `smoke-1790174039603663000.xcresult`, operation `1790174041497190000`.
- Post-update snapshot: `post-install-1790174087200263000`.
- Aggregate data comparison: `preservation.json`.
- Final source/receipt bindings and storage snapshot: `checkpoint-stop.json` in this report's directory.

Backups are owner-readable and ignored, with inventory and SHA-256 verification.
Database inspection uses local copies, not the live database. No personal source
text or media is included in this report. No backup, cache or other files were
deleted; any future restore requires explicit direction, never automatic recovery.

The original storage baseline, previously approved 32 GiB cumulative ceiling and
10 GiB free-space reserve remain unchanged. Prior SDK caches were reused, with new
products and receipts kept separate. The earlier storage hold is documented in the
[implementation report](../search-options/REPORT.md).

No production-source edits were needed during this installation. Documentation
updated: this report, the implementation report, `docs/unified-memory-search.md`
and `docs/provenance-first.md`. Stop for user review after reopening Remember.
