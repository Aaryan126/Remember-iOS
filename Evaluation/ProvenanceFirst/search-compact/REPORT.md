# Compact search header — 24 September 2026

Request: halve the now-balanced gaps above and below the Memories/count/filter
row. Source changes both gaps from 20 to 10 points, accounting for the existing
native 10-point inset below the search field. The 44-point touch target and
center alignment remain intact. Other result-section gaps stay at 20 points;
grid/card spacing, search behavior, data and motion are unchanged.

The installed spacing deployment was archived before editing using the new
`scripts/provenance-first/search-compact/check.py` wrapper. Historical receipts
and signed products remain untouched; no cleanup or Git changes were performed.

Changed source: `Remember/Remember/UnifiedMemorySearchView.swift` and the geometry
assertions in `Remember/RememberUITests/UnifiedMemorySearchUITests.swift`.
Also added this runner/report and baseline manifest, and updated
`docs/unified-memory-search.md`.

## Validation

- Swift syntax parse of the changed view and UI tests: passed.
- `git diff --check`: passed (read-only, excludes untracked files).
- `python3 scripts/provenance-first/search-compact/check.py ui`: **10 passed,
  0 failed, 0 skipped**, no reported runtime warnings. Result:
  `Evaluation/ProvenanceFirst/runs/search-compact/1790221728110194000.xcresult`.
- `xcrun xcresulttool get test-results summary` confirmed the result; attachment
  export captured four geometry-check screenshots. Visually reviewed the dark
  keyboard-open and light keyboard-dismissed screenshots; compact gaps and
  centered controls look consistent.
- Geometry assertions passed for 10-point gaps on both sides in all four
  light/dark and keyboard-open/closed combinations. Filter/cancellation, retained
  navigation, source-only, empty-library and large-text checks also passed.
- Simulator shutdown request returned code 149: `Unable to shutdown device in
  current state: Shutdown`; the simulator was already stopped, not left running.

At test completion, the guard reported 10.62 GiB free and both resource limits
were satisfied. No phone deployment or cleanup was attempted for this follow-up.

Subsequently installed on the physical iPhone together with the populated-search
dismissal fix. Signed build, phone smoke and data-preservation checks passed;
see the [deployment report](../search-dismissal-deployment/REPORT.md).

Reproduction:

```sh
python3 scripts/provenance-first/search-compact/check.py prepare
python3 scripts/provenance-first/search-compact/check.py ui
```

The UI geometry check requires 10-point gaps above/below the header's touch target,
in addition to equal spacing and control-center alignment, in light/dark with
the keyboard open/closed. Existing cancellation, filters and large-text coverage
remain in the same suite. The 32 GiB cumulative and 10 GiB free-space guards apply.
