# Search status UI deployment — 24 September 2026

User authorized installation on the personal iPhone. The normal Remember app and
Share Extension were signed, verified and installed in place, without uninstall,
data reset or restore. The previous deployed checkpoint remains archived.

## Checks completed

- `python3 -B scripts/provenance-first/search-status/check.py unit`: 28 passed
  against final source. The previously completed full simulator UI suite passed
  15 tests; both source bindings were matched against the signed device build.
- `python3 -B scripts/provenance-first/search-status/deploy.py prepare`, `build`
  and `ready`: passed. Signed normal app/extension identities and entitlements
  verified; local GRDB reused without package fetching.
- Same deployment runner: `backup`, `inspect-backup`, `install`, `smoke`,
  `post-backup`, `compare`, `launch`, `finish`.
- Fresh pre-install backup: 196 verified files; SQLite integrity and migration
  compatibility passed. Launch preflight passed.
- Physical iPhone smoke: 1 passed on the first attempt. Checks the exact text
  **No matching current memories**, horizontal centering, lower placement, no
  residual spinner, and existing search dismissal/filter/navigation behavior.
- Post-install comparison: all 8 memory rows, all 8 original files and all 172
  history events unchanged; SQLite integrity passed.
- `git diff --check`: passed. No Git state changes.

Receipts and private snapshots stay under ignored
`Evaluation/ProvenanceFirst/runs/search-status-device/`. The signed build operation
is `1790260129857836000`; installation is `1790260271423424000`; phone smoke is
`smoke-1790260300998207000.xcresult`. Final-source unit receipt:
`../runs/search-status/1790260118858199000.xcresult`.

The existing 32 GiB cumulative allowance and 10 GiB free-space reserve were
preserved. Existing Xcode/tool diagnostics remain; no claim of warning-free logs.
No AI requests, forced regrouping, original-file edits or database migrations
were introduced. Remember was reopened after preservation checks.

Changed deployment files: `scripts/provenance-first/search-status/deploy.py`,
`MainAppSmokeTests.swift`, this report, `REPORT.md`, `ready-to-install.json`,
`checkpoint-stop.json`, and `docs/unified-memory-search.md`.
