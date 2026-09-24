# Search opening synchronization deployment — 24 September 2026

**Installed, physical smoke passed, data preservation passed; open for user review.**

Current source is validated by handoff runs `1790249130721671000` (6 unit tests)
and `1790249157837450000` (11 UI tests), with no skips. See
`../search-handoff/OPENING-FOLLOWUP.md` for geometric/recorded verification and
rejected trials. Signed normal-app build `1790249474175674000` succeeded.

Uses the existing app identity, signing team and shared group, without uninstall,
reset, migration, forced regrouping, AI calls or opening personal sources.
The existing guarded deployment implementation and phone smoke harness are reused
from `scripts/provenance-first/search-handoff`; the thin entry point is
`scripts/provenance-first/search-opening/deploy.py`. Receipts and fresh backups
are isolated under `runs/search-opening-deployment`, not overwriting the earlier
installed update. Storage limits remain unchanged; no cleanup this turn.

Fresh backup `backup-1790249522371724000` verifies 192 files, SQLite integrity,
11 matching migrations, 8 indexed memories and 171 history events. Cloud is off
and no pending capture/shared inbox/video requires startup review. In-place
installation `1790249570934058000` succeeded, with no uninstall. Physical smoke
`1790249619083777000` passed (1 test, no skips), without the earlier checkpoint's
automation-startup timeout. Post snapshot `post-install-1790249723598639000`
verifies 193 files. `preservation.json` confirms all **8 original files identical**,
all **8 memory rows unchanged**, all **171 history events unchanged**, and SQLite
integrity intact. The normal app was reopened after comparison. Existing dependency/test deprecation warnings remain;
no warning was reported in the two changed production views.

## Files changed

- `Remember/Remember/ContentView.swift`: single native scroll owner, conditional
  content transaction, layout-aware browsing-position restoration, refresh routing.
- `Remember/Remember/UnifiedMemorySearchView.swift`: content rather than a second
  scroll container; shared source model for the parent's refresh action.
- `scripts/provenance-first/search-handoff/FixtureApp.swift`: fictional-only bar
  coordinates in motion traces.
- `scripts/provenance-first/search-handoff/verify-opening.py`: intermediate-frame
  synchronization regression check (the installed baseline fails, final source passes).
- `scripts/provenance-first/search-opening/deploy.py`: fresh receipts using
  existing signing, source-matched tests, backups and preservation safeguards.
- This report, `search-handoff/OPENING-FOLLOWUP.md`, `docs/unified-memory-search.md`,
  and `docs/provenance-first.md`: current evidence and deployment status.

`SearchResultsHandoff.swift` and its six lifecycle tests are unchanged from the
previous installed fix. All unsuccessful production trials were removed.
No Git state changes, unrelated file edits or deletion occurred.

## Checks actually run

- `python3 scripts/provenance-first/search-handoff/check.py unit`: 6/6 passed.
- `python3 scripts/provenance-first/search-handoff/check.py ui`: 11/11 passed.
- `verify-opening.py` and `verify-motion.py` on both `opening-final-top` and
  `opening-final-scrolled` exports: passed. Reviewed fictional recorded frames.
- `python3 scripts/provenance-first/search-opening/deploy.py build`: passed.
- The same entry point's `backup`, `inspect-backup`, `install`, `smoke`,
  `post-backup`, `compare`, and `launch`: passed.
- Python AST parsing (9 scripts) and `git diff --check`: passed.

These tests establish functional/geometric checks, not a universal frame-rate or
subjective-smoothness guarantee. User should compare opening, empty cancellation,
matching/no-results cancellation, and returning to a scrolled browsing position.
