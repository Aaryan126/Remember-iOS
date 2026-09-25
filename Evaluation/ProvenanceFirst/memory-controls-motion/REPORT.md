# Library control motion — 25 September 2026

Installed on the personal phone; native Back and swipe-back checks passed.
See the [deployment report](DEPLOYMENT.md) for preservation verification.

The Add control and search presentation use UIKit's navigation transition
coordinator when returning to Memories. This supplies the native timing and
interactive swipe/cancellation progress. The Add control fades with a small
vertical movement. Reduce Motion skips the added effect.

UIKit detaches the live search field and temporarily removes its glass during
navigation. The host caches the settled inactive field's appearance in memory,
then fades that noninteractive image with the returning library at its settled
position in that page. It removes the overlay and restores the live search control on completion
or cancellation. Active queries continue using the live control. Appearance,
text size and window-size changes prevent reuse of an outdated image.

The collapsed capture control now uses only its hub and inset dimensions. This
keeps its UIKit host from intercepting taps on neighboring cards; the expanded
dial keeps its existing dimensions and presentation.

Reference: Apple's [transition-coordinator API](https://developer.apple.com/documentation/uikit/uiviewcontrollertransitioncoordinator/animatealongsidetransition(in:animation:completion:)).

## Files

- `Remember/Remember/ContentView.swift`: attach the animation host.
- `Remember/Remember/LibraryControlsTransition.swift`: coordinate both controls.
- `Remember/Remember/InAppCaptureViews.swift`: compact collapsed control bounds.
- `Remember/RememberUITests/MemoryReturnUITests.swift`: neighboring-card regression.
- `scripts/provenance-first/memory-controls-motion/check.py`: reuse the fictional
  fixture and bounded simulator runner.
- `docs/unified-memory-search.md` and this directory: behavior and validation.

## Verification

Commands run:

```sh
python3 -B scripts/provenance-first/memory-controls-motion/check.py preserve
python3 -B scripts/provenance-first/memory-controls-motion/check.py prepare
python3 -B scripts/provenance-first/memory-controls-motion/check.py return-ui
python3 -B scripts/provenance-first/memory-controls-motion/check.py regressions
git diff --check
```

Final `return-ui` run: **5 tests passed, zero failures**, including compilation of
all final app sources, on iPhone 17 / iOS 27 simulator. Receipt:
`../runs/memory-controls-motion/1790306049153651000.xcresult`. Its source hashes
were checked against the working files after the run and matched.
`git diff --check` passed.

Coverage includes Back, completed and cancelled swipe-back, light/dark appearance,
restored control positions, capture-menu opening/closing, neighboring-card taps,
retained scroll position, and preserving/closing a query after a result visit.
The earlier `regressions` run passed all 7 cases, including two repeated search
closure cases (`1790305548452655000.xcresult`), before the final live-field alpha
and snapshot-placement refinements; the five return tests were rerun afterward.

Final dark-mode return frames were reviewed: the search glass returns during
navigation and the placeholder stays aligned with the page. See the
[return preview](../runs/memory-controls-motion/return-preview.mp4).
The OS Reduce Motion setting was not toggled; the added effects explicitly skip
that preference. Physical-phone Back and swipe-back checks passed; the detailed
visual frame review was performed on the simulator.

An intermediate neighboring-card test exposed the larger UIKit host's empty
hit area; the compact bounds fixed it and the new test now passes. Intermediate
recordings also exposed delayed glass and overlapping text, resolved by retaining
the field's appearance on the library page. Two interim regression runs were
stopped while those visual refinements continued. Superseded receipts and
recordings remain in the ignored run directory. Temporary diagnostic logging
and image-file writes were removed from the app sources.

 The simulator fixture contains fictional
memories only. The prior installed checkpoint is archived in `baseline.json`;
the original 32 GiB cumulative allowance and 10 GiB free reserve remain active.
The update was installed after user authorization. No Git state changes were performed.
