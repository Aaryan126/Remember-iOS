# Search-header spacing — 24 September 2026

Scope: align the Memories title, count and filter control and balance the space
between the search field, header and default card grid. No data, model, search
semantics or focus-animation changes. No Git operations or cleanup.

The installed motion checkpoint was archived before editing with
`python3 scripts/provenance-first/search-spacing/check.py preserve`.

## Reproduction

The initial simulator layout test reproduced a 6-point imbalance: search field
bottom to header center = 48 points; header center to grid top = 42 points.
Title/count/button center alignment already passed within 1 point, and the filter
button retained a 44-point target. The initial run intentionally failed the gap
assertion (`1790220597736239000.xcresult` in the private runs directory).

## Change

- Keep the existing centered row and make the count's body font explicit, with
  tabular digits to avoid width jitter when the number changes.
- Change results top padding from 16 to 10 points. With the native field's
  10-point bottom inset, both sides of the 44-point row have 20-point gaps.
- Preserve horizontal/bottom padding, native focus motion and existing filters.
- Add a geometry regression for light/dark and keyboard open/dismissed, plus
  screenshots for visual inspection. Existing large-text and cancellation tests
  remain in the UI suite.

## Validation

Final suite: **10 passed, 0 failed, 0 skipped**, with no reported runtime warnings
in the result summary. Result: `1790220701674795000.xcresult` in the private runs
directory. The new geometry test passed for light/dark mode with the keyboard
open/dismissed: centers within 1 point, equal gaps within 2 points, and a minimum
44-point filter target. All four corresponding screenshots were visually reviewed.
Existing repeated-dismissal, filter/session, history/navigation and large-text
tests also passed.

Commands run successfully:

- `python3 scripts/provenance-first/search-spacing/check.py preserve`
- `python3 scripts/provenance-first/search-spacing/check.py prepare`
- `python3 scripts/provenance-first/search-spacing/check.py ui`
- `xcrun swiftc -frontend -parse Remember/Remember/UnifiedMemorySearchView.swift Remember/RememberUITests/UnifiedMemorySearchUITests.swift`
- `git diff --check` (read-only; does not include untracked files)
- `xcrun xcresulttool get test-results summary` and attachment export for the
  result above, followed by visual inspection.

After the suite: 11.11 GiB available; growth and reserve guards remained satisfied.
This change is now **installed on the physical iPhone** after the approved cache
cleanup. The signed build and phone spacing/menu/repeated-dismissal smoke passed
(one automation-startup retry), and pre/post snapshots preserve all 8 memories,
171 history events and 8 originals unchanged. See the
[deployment report](../search-spacing-deployment/REPORT.md).
Layout was also verified on iPhone 17 / iOS 27 simulator; future changes to native
search-field insets should re-run this test.

Changed files: `Remember/Remember/UnifiedMemorySearchView.swift`,
`Remember/RememberUITests/UnifiedMemorySearchUITests.swift`,
`scripts/provenance-first/search-spacing/check.py`,
`docs/unified-memory-search.md`, this report, and the preserved baseline manifest
`Evaluation/ProvenanceFirst/search-spacing/baseline.json`.

Re-run with:

```sh
python3 scripts/provenance-first/search-spacing/check.py prepare
python3 scripts/provenance-first/search-spacing/check.py ui
```

The harness preserves the existing 32 GiB growth limit and 10 GiB free reserve.
