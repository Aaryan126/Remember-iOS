# Search opening synchronization — 24 September 2026

The user confirmed the installed closing fix works almost entirely, but the
browsing grid moves upward before the search bar when entering empty search.
The installed app and its verified backups remain untouched during this work.

## Measurement

Fictional-only `FixtureApp.swift` tracing now records the search field's rendered
window coordinate as well as the native scroll bounds/container coordinate.
`verify-opening.py` measures change in the bar-to-content gap throughout empty
focus transitions, requiring multiple openings with intermediate frames. It
complements the existing `verify-motion.py` closing-jump check; a settled UI test
pass alone is insufficient.

Baseline `1790247304547636000` (installed production source): the ordinary focused
UI test passes, but `opening-baseline-fresh-trace.jsonl` fails the new opening
check. Repeated openings show approximately 32–34 points of bar/content mismatch:
the grid bounds reach -116 while the search field is still moving from y116 to
y62. The earlier `opening-baseline` export was stale and is not baseline evidence.

## Rejected trials

- `1790247419768138000`: transparent backing, no geometry group. Opening aligns;
  populated closing regresses by about 100 points. Removed.
- `1790247535824401000`: geometry group around the combined overlay. Opening
  still fails. Removed.
- `1790247626275646000`: scope unanimated results removal to dismissed search.
  Closing passes but opening still fails. Removed.
- `1790247723946161000`: compositing group instead of geometry group. Same
  opening failure; removed.
- `1790247811968595000`: attach handoff surface directly to the base library.
  Opening passes, closing regresses. Removed.
- `1790247937566206000`: retain an invisible results layout for the snapshot fade.
  Opening passes, closing still regresses. Removed, including observable state.
- `1790248052272201000`: direct ScrollView root instead of Group/ZStack. Opening
  passes, closing regresses. Removed; empty-state behavior left unchanged.

Partial trace exports which lack all required cases are diagnostic only; an
insufficient-samples error is not a complete verification result. Recordings were
finalized normally; no cleanup was performed in this follow-up.

- `1790248167945825000`: group only the results overlay. Opening passes but
  closing still regresses. Removed.
- `1790248274609060000`: GeometryReader root. Same closing regression; removed.

## Retained implementation

One persistent ScrollView now owns both browsing and search content. The existing
in-memory snapshot fade remains unchanged; geometry/compositing workarounds and
temporary results-retention state are absent. Browsing offset is recorded before
the first nonempty query and restored when browsing content is laid out again.
Source-search state is owned by the parent to preserve source refresh behavior;
ordinary search/refresh does not gain AI or cloud calls.

`1790248429587615000`: top repeated-close test passes; opening and closing traces
both pass. Scrolled trials `1790248547830621000`, `1790248657119104000`,
`1790248820482468000`, `1790248908493486000` caught a genuine no-results regression:
native content-size animation clamped scroll restoration before the longer
browsing layout was ready. Child-only transactions/grouping did not fix it.

The final correction scopes an unanimated transaction to **changes in results
presence on the scroll container itself**. Empty focus does not change that value,
so native opening is unaffected. `1790249006959958000` passes the scrolled repeated
case, including no results, manual clear, keyboard dismissal and empty controls.
`opening-root-transaction` passes both frame checks: six openings have bar/content
gap error below 3e-13 points (floating-point residual), and seven clears/closes
have zero extra container displacement. Browsing anchor positions are preserved.

## Final-source validation

- `1790249130721671000`: **6/6 lifecycle tests pass**.
- `1790249157837450000`: **11/11 UI tests pass**, no skips. Includes restored
  browsing offsets, empty/matching/no-match dismissal, header spacing, filters,
  source navigation/back and large text.
- `opening-final-top` and `opening-final-scrolled`: both opening and closing
  frame checks pass. Twelve openings stay aligned within floating-point residual
  (<3e-13 pt); fourteen clears/closes show zero extra container displacement.
  These are sampled geometric checks, not a frame-rate benchmark.
- `opening-final-regression.mp4` finalized. The overview and 30 fps
  `opening-final-focus-detail.png` show native synchronized bar/grid movement.
  `opening-final-close-detail.png` missed the actual closing interval and is
  only a locator; it is not closing verification evidence.
- `opening-final-close-reviewed.png` covers the matching-results close: the
  existing outgoing-pixel fade and native bar movement remain visible, without
  the old container jump. No claim of universal frame-rate performance is made.
- `git diff --check` and syntax parsing of nine Python scripts pass.
- `SearchResultsHandoff.swift` is byte-identical to the installed closing fix.
  No retained-layout trials, custom timing curve or production trace remains.

Signed build `1790249474175674000` succeeded. Fresh backup
`backup-1790249522371724000` verifies 192 files, SQLite integrity and 11 matching
migrations (8 memories, 171 events). Installation `1790249570934058000` succeeded
in place. Physical smoke `1790249619083777000` **passed** this time, without a
startup retry. Post-launch comparison preserves all 8 originals byte-for-byte,
all 8 memory rows and all 171 events, with SQLite integrity intact. Remember is
open for user review. See `../search-opening-deployment/REPORT.md` for receipts.
