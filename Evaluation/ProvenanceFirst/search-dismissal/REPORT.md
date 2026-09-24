# Populated search dismissal — 24 September 2026

Status: source change implemented; targeted post-fix regression, motion-frame
review and full UI suite passed after approved cache cleanup.
Subsequently installed in place on the physical iPhone with the compact spacing;
phone smoke and pre/post data-preservation checks passed. See the
[deployment report](../search-dismissal-deployment/REPORT.md).

## Cause and scoped change

Empty search leaves the browsing grid mounted/visible. A nonempty query inserts
a separate results scroll view and hides the library. Previously query removal
used an identity transition, abruptly replacing populated results during native
search/keyboard dismissal. `ContentView.swift` now uses an opacity transition and
a 0.2-second ease-out animation only when `showsSearchResults` changes to false.
Empty-field focus/dismissal and result insertion remain unanimated by this rule;
Reduce Motion suppresses it. The outgoing layer loses hit testing/accessibility
when inactive. The existing library view and its offset remain mounted.

The compact header change from the previous checkpoint is retained. There are no
model, retrieval, persistence, filter-session or cloud behavior changes.

## Initial verification and storage hold

- Expanded `testClosingSearchPreservesScrolledLibraryAcrossRepeatedSessions` to
  cover empty → matching (keyboard open) → no-match (keyboard open) → matching
  (keyboard dismissed) → empty sessions.
- Pre-fix baseline test passed 1/1, run `1790222619386942000.xcresult`. It proves
  settled positions, not smoothness. Captured fictional `before.mp4` and inspected
  `before-close.png` contact frames at the matching-query dismissal.
- Swift syntax parse of `ContentView.swift` and `UnifiedMemorySearchUITests.swift`
  passed. `git diff --check` passed (read-only; does not check untracked files).
- Post-fix `prepare` passed. `check.py motion` was blocked **before dispatch** by
  `10 GiB free reserve would be exceeded` (256 MiB test reservation). Last check:
  10,754,908,160 bytes available, only about 17 MiB above the reserve.
- At that initial hold, the simulator recording was stopped and test simulator
  shut down; no after video or post-fix UI pass was yet claimed.

The initial archive command rejected changed live compact-spacing inputs, and
the dependent prepare therefore failed without a baseline manifest. The runner
was corrected to copy the exact installed checkpoint bytes from the existing
verified `search-compact/baseline` archive; preservation and preparation then
passed. Historical receipts were not modified or weakened.

## After the approved cleanup

- Removed only the four approved compiler-cache/intermediate folders; about
  587 MiB net was recovered. See [cleanup record](CLEANUP.md). They are rebuildable,
  but were not moved to Trash. Models, sources, signed products and backups remain.
- `check.py motion` passed **1/1**, no skips or reported runtime warnings:
  `1790223003614725000.xcresult`. All five empty/matching/no-match and keyboard
  sessions completed, preserving the original browsing position.
- Captured fictional `after.mp4`; inspected `after-close.png`,
  `after-no-match-close.png`, `after-keyboard-dismissed.png`, and
  `after-empty-close.png`. Populated results now fade through intermediate opacity
  frames into the preserved library, rather than the former immediate swap.
  The no-match label/count remained the no-match content while fading; no flash
  of an unfiltered results grid was observed. Empty closing stays native.
- Swift syntax parse and `git diff --check` passed again.
- First full-suite dispatch was blocked by the unchanged 10 GiB reserve. Space
  recovered without more deletions; the guarded retry passed **10/10**, no skips,
  failures or reported runtime warnings: `1790223191166016000.xcresult`.
  This includes compact 10-point geometry in light/dark with keyboard open/closed,
  repeated dismissal, clearing/retyping/filter reset, history/navigation,
  source-only, empty-library and large-text cases. Confirmed using
  `xcrun xcresulttool get test-results summary --compact`.
- Guard at completion: 10.58 GiB free, both limits satisfied. Recordings are
  stopped; the test simulator is shut down after verification.

This is simulator evidence, not a guarantee of perceived smoothness on every
physical device. Reduce Motion is respected by the code's animation condition;
its enabled setting was not separately exercised in the recording.

## Reproduction

```sh
python3 scripts/provenance-first/search-dismissal/check.py motion
python3 scripts/provenance-first/search-dismissal/check.py ui
```

Raw results and fictional videos are in the ignored
`Evaluation/ProvenanceFirst/runs/search-dismissal/` directory. The later signed
phone deployment includes both the compact 10-point spacing and this dismissal
follow-up. Perceived smoothness still needs the user's confirmation.

Changed files: `Remember/Remember/ContentView.swift`,
`Remember/RememberUITests/UnifiedMemorySearchUITests.swift`,
`scripts/provenance-first/search-dismissal/check.py`, this report, its baseline
manifest, and `docs/unified-memory-search.md`. No Git state changes.
