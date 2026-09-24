# Quieter search menu — implementation verified

23 September 2026. The implementation checkpoint initially stopped before changing
the phone. The subsequently approved deployment is now installed and verified;
see the [deployment report](../search-options-deployment/REPORT.md). The original
storage hold and implementation-test evidence below are retained as history.

## Changes

- Removed the always-visible panel containing two toggles and explanatory text.
- Added one native filter menu in the results header. Include history and Source
  text only default off, with checked menu states; no global Settings preference.
- Only active filters show a brief status and Reset. Filters/query survive Back
  from a saved source. Search cancellation returns to the default session.
- Existing explicit Try AI search and How search works moved into the menu. The
  repeated explanatory footer is gone; saved-version detail warnings remain.
- Retrieval, local keyboard submission and Ask AI behavior are unchanged.

## Checks actually run

Using `python3 -B scripts/provenance-first/search-options/check.py`:

| Action | Result |
|---|---|
| preserve | Archived previous deployed checkpoint inputs; old receipts unchanged |
| prepare | Isolated fictional simulator project prepared with local dependencies |
| unit | 18 passed, no failures/skips/runtime warnings reported |
| ui | 7 passed, no failures/skips/runtime warnings reported |

Native receipt: `runs/search-options/1790170633349465000.xcresult`.
UI receipt: `runs/search-options/1790170738212814000.xcresult`.
Both use iPhone 17 / iOS 27 simulator; these are not physical-phone test results.
UI coverage includes default-hidden controls, menu toggle/reset/help, normal saved
passage links, exact historical version/Back state, empty library, source-only
metadata exclusion, dark accessibility text and the Threads menu regression.

Two simulator captures were exported and visually inspected: ordinary light search
and dark/accessibility XXXL source search. `git diff --check` and
`xcrun swiftc -frontend -parse Remember/Remember/UnifiedMemorySearchView.swift` passed.
Existing compiler/tool warnings remain; zero runtime warnings refers to xcresult.

## Initial phone update hold (subsequently resolved)

The phone was available, but
`python3 -B scripts/provenance-first/search-options/deploy.py prepare` stopped at
the 1.5 GiB build/two-backup reservation: `10 GiB free reserve would be exceeded`.
A subsequent `deploy.py build` also refused to run because preparation.json did not
exist; xcodebuild was not launched. The runner now reports that missing prerequisite
explicitly. No phone app termination, backup, installation or personal-content
access was performed. No cache/data deletion or storage-limit increase.

After the user freed storage and requested installation, deployment `prepare` and
`build` passed separately. Fresh backup, compatibility, install, phone smoke and
preservation checks are recorded in the deployment report. The existing 32 GiB
cumulative limit, original baseline and 10 GiB free reserve remain enforced.

## Files

Production: `UnifiedMemorySearch.swift`, `UnifiedMemorySearchView.swift`.
Tests: `UnifiedMemorySearchTests.swift`, `UnifiedMemorySearchUITests.swift`.
Support: `scripts/provenance-first/search-options/`, this checkpoint's plan/archive
manifest/report, `docs/unified-memory-search.md`, `docs/provenance-first.md`.
No Git state changes, model/policy changes or new AI calls.
