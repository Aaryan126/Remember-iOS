# Centered Memories search status

24 September 2026. UI update installed on the personal iPhone after authorization.

## Changes

- Ordinary no-result search says **No matching current memories**.
- The message is horizontally centered in a 220-point minimum-height area below
  the results header. Its replacement spinner uses the same position.
- Pending-query tracking covers debounce, so the empty message does not appear
  before the current search finishes. The header no longer has a second spinner.
- History/source-only scopes retain appropriate labels; saved-text errors retain
  their error message and Retry action. Larger text can wrap above the keyboard.

## Validation

The bounded runner uses fictional simulator data, the existing 32 GiB cumulative
allowance and 10 GiB free-space reserve. Previous deployed inputs were archived
before edits; no phone data, Git state, dependencies or database schema changed.

Commands:

```sh
python3 -B scripts/provenance-first/search-status/check.py preserve
python3 -B scripts/provenance-first/search-status/check.py prepare
python3 -B scripts/provenance-first/search-status/check.py status-ui
python3 -B scripts/provenance-first/search-status/check.py unit
python3 -B scripts/provenance-first/search-status/check.py ui
git diff --check
```

Two initial focused UI runs passed layout/error tests but failed the spinner
count assertion. Accessibility inspection showed SwiftUI's ProgressView and its
UIKit child at the identical frame; visual review confirmed one spinner. The
test now checks that every indicator occupies the intended shared center, then
checks that the empty message replaces it at the same coordinates.

- Unit checks: **28 passed**, no failures, covering unified search, source browsing
  and search handoff. Receipt: `../runs/search-status/1790257719801502000.xcresult`.
- Full UI suite: **15 passed**, no failures, on iPhone 17 / iOS 27 simulator.
  Includes new centered empty/loading/error checks and existing typo search,
  filters, history, keyboard submission, header spacing and repeated dismissal.
  Receipt: `../runs/search-status/1790257817436104000.xcresult`.
- The UI dispatch immediately after unit checks correctly refused changed source
  bindings after a final blank-query display preservation edit. Re-preparing the
  fixture and rerunning the full UI suite produced the successful final receipt.
- `git diff --check`: passed. Existing compiler/AppIntents/tool diagnostics remain.
- Empty-state screenshots were reviewed in light/dark appearance, with and without
  the keyboard and at accessibility text size. The loading and replacement
  captures show the same position. [Dark preview with keyboard](../runs/search-status/empty-previews/03B03430-9AFB-41DD-9866-93AE1201A50D.png).

The authorized follow-up signed build and physical iPhone smoke passed, including
the exact empty-state wording, centered placement and existing search interactions.
All 28 unit tests were rerun successfully against the final source before install:
`../runs/search-status/1790260118858199000.xcresult`. See [deployment details](DEPLOYMENT.md)
for the backup and preservation comparison. Simulator fixtures remain fictional.

## Changed files

- `Remember/Remember/UnifiedMemorySearchView.swift`: shared status layout/copy.
- `Remember/Remember/LibraryViewModel.swift`: query completion/failure state.
- `Remember/RememberUITests/UnifiedMemorySearchUITests.swift`: layout, loading
  replacement and error/retry checks.
- `scripts/provenance-first/search-status/`: bounded runner and deterministic
  fictional loading fixture; deployment wrapper and physical-phone smoke checks.
- `docs/unified-memory-search.md` and this evaluation directory: behavior,
  prior-checkpoint archive manifest and validation.
