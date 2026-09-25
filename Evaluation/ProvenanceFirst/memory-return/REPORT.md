# Memories return transition — 25 September 2026

Installed on the personal iPhone after authorization. The signed build and phone
Back/swipe-back check passed; all 8 memories, 8 originals and 172 history events
were verified unchanged. See [deployment details](DEPLOYMENT.md).

## Change

The collapsed Add control was an overlay outside the navigation stack. Returning
from a detail inserted it over the outgoing page; the later tab-bar restoration
then changed its vertical position. The baseline simulator recording shows both
steps. The collapsed control now belongs to the library page and moves with the
native navigation transition. The expanded dial retains its existing overlay
above the blurred stack, including its background dismissal and accessibility.

The memory navigation path now carries the default SwiftUI animation, with no
added animation when Reduce Motion is enabled. Tab-bar visibility follows that
path explicitly: hidden inside a memory, visible at the library. The navigation
header and search control continue using their native presentation. No timers,
delayed appearance callbacks, custom navigation controller or data changes.
Reference: Apple's [SwiftUI bar-visibility API](https://developer.apple.com/documentation/swiftui/view/toolbar(_:for:)).

## Verification

Commands run:

```sh
python3 -B scripts/provenance-first/memory-return/check.py preserve
python3 -B scripts/provenance-first/memory-return/check.py prepare
python3 -B scripts/provenance-first/memory-return/check.py return-ui
python3 -B scripts/provenance-first/memory-return/check.py regressions
git diff --check
```

Final `regressions` run: **6 UI tests passed, zero failures**, on iPhone 17 / iOS 27
simulator, including compilation of the final app sources. Receipt:
`../runs/memory-return/1790303257381561000.xcresult`. `git diff --check` passed.
The earlier baseline return suite passed 2 tests before production edits.

The new cases cover photo detail, note detail, Back, completed and cancelled
swipe-back, light/dark appearance, hidden detail controls, restored controls,
opening/closing the capture dial, scrolled-library position, and retaining a
search query on return. Two existing repeated search-dismissal cases cover the
top and scrolled library.

Before/after simulator recordings were inspected frame by frame. The final
recording shows the Add control returning with the page at its proper height,
and the tab bar returning during navigation. The full-screen detail still hides
both controls. [Short return preview](../runs/memory-return/return-preview.mp4).
Recordings and intermediate frames remain in the ignored run directory.

During preparation, two fixture-only compile issues were corrected: immutable
memory identity construction and an attempted override of SwiftUI's read-only
Reduce Motion environment value. The final fixture does not override that value;
the OS Reduce Motion setting was not exercised. An intermediate visibility change
kept the tab bar visible in details; explicit path-based visibility and stronger
hidden-control assertions corrected it before the final run.

The previous installed checkpoint was preserved from its existing spinner-change
archive. The resource guard retains the original 32 GiB cumulative allowance
and 10 GiB free reserve. All simulator data is fictional. The implementation
checkpoint accessed no private phone data; the authorized deployment subsequently
backed up and verified the phone's app data. No cloud calls. Existing Xcode/tool
warnings remain.

## Files

- `Remember/Remember/ContentView.swift`: navigation animation, root Add placement
  and path-based tab-bar visibility.
- `Remember/RememberUITests/MemoryReturnUITests.swift`: four return regressions.
- `scripts/provenance-first/memory-return/`: bounded runner and fictional tabbed
  fixture, including a synthetic image for the immersive detail; deployment
  wrapper and read-only phone navigation check.
- `docs/unified-memory-search.md` and this evaluation directory: behavior,
  validation and the preserved checkpoint manifest.

No Git state changes were made.
