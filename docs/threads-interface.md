# Threads interface

Implemented 14 September 2026. This is a presentation/navigation change; organization policy, stored events, original files and user assignments are unchanged.

## Navigation and vocabulary

- Tabs: Memories, Threads, Settings.
- Threads opens directly to Map. There is no Timeline screen or view switch.
- The separate centered-node title under the counts has been removed; full names remain in the hold preview and search results.
- The map retains its 40-circle rendering bound, gestures, preview, centering and accessibility actions. Find a thread always offers every active thread, including those outside the rendered map.
- Find a thread is a native search field on the Threads root, matching the Memories search style. Focus shows all active threads as inline suggestions; typing filters them immediately. Closing search returns to the map without another navigation level. The map remains mounted while search results cover it.
- Inline search supports local name search, case/diacritic-insensitive matching of all entered words, full Dynamic Type titles and memory counts. Search never calls a hosted model. Empty queries browse all active threads; no-match and empty-library states are explicit.
- Inline results and map circles open the same named thread history. Stable internal IDs and the dormant `remember.project.homeView` preference remain compatible; the app does not rewrite that preference.
- Thread actions are Rename thread, Archive thread and View past state. Membership controls consistently say Threads and Save thread assignments. Archive preserves originals, history and other memberships.
- View past state lives in the three-dot Thread options menu. Selecting it reveals the date controls; the menu then offers Back to present and hides Rename/Archive. The menu remains available even at a date before the thread formed, so returning to the present is always possible.

## History and activity

The thread title sits directly on the page canvas, without a card background. Title and History share the same left margin. The reference layout uses a separate rail gutter beside individually rounded content cards, with consistent text/media padding and spacing between entries. The distinct-memory count sits beside the History heading (for example, `History · 2 memories`), keeping the title area compact. It reflects membership in the displayed snapshot, not the number of capture/revision entries.

The History heading has balanced space above and below it. The history rail starts at the first visible entry’s dot, runs outside the cards and continues through the gaps between them. Its starting point follows the title’s measured junction at every text size, including after unfolding earlier history. Dots have no horizontal connector into the cards. Each memory’s disclosure arrow aligns with the first line of its title, including wrapped titles. Card titles, dates and media share one content edge; the existing palette and media fitting behavior are retained.

The main History stream displays captures, imported originals, content revisions and compact merge/split markers in ledger order. Original media remains attached to its capture/revision, and Back from Memory returns directly to the thread. When a note's first line duplicates its displayed title, only the body is repeated beneath the header.

Activity & decisions is accessed from the three-dot Thread options menu; it has no permanent card in the reading view. It retains captures, metadata, processing, naming, placement, checkpoints, recaps, archive/restore and correction records. Open a record for evidence, note-revision restoration, undo or split acceptance where applicable. Threads with pending split suggestions show a small “N suggestions to review” link beside the History section. It opens activity with Suggestions to review already enabled. The link disappears when no suggestions remain; the activity destination stays open while a suggestion is resolved. Opening activity from the menu starts with the full record.

Global activity remains available from the Threads toolbar. Source/date/thread filters live inside activity and do not pretend to filter the map or finder. Thread-scoped activity is limited to that thread/lineage, including removal decisions that mention a prior assignment. Historical activity uses the same as-of snapshot; it cannot adopt future merge lineage.

`ThreadDirectory` and `ThreadHistory` are read-only presentation projections. Legacy stock user-action strings are mapped to the new vocabulary only for display and only for exact known strings; stored payloads, custom text and model evidence remain verbatim. No database migration, model/policy change, dependency addition or original-file rewrite is needed.

## Validation

Validation on 14 September 2026:

- Full unit suite: **115 tests in 9 suites passed** on the established Remember UI Review simulator (iOS 26.5), including the six new presentation tests, clustering, provenance replay and video validation.
- Light/dark appearance tours and the largest Dynamic Type finder/history check passed. Exported screenshots were inspected for map, finder, history and activity layout.
- Connected iPhone: existing-library media navigation, map focus/hold/drag/return, and finder → history → activity navigation passed. Phone tests did not create, rename, archive or restore captures. The updated app is installed in place.
- An initial fresh-simulator unit run failed two unchanged clustering tests (`groundedTermsRejectSharedStyleAndUnrelatedHandsOnTasks`, `realDeviceVectorsStayTopicPureAcrossArrivalOrders`). Both passed on the established simulator; local language/embedding asset availability differs between simulator environments. No grouping-policy change was made to accommodate this.
- Initial UI failures exposed test interactions with iOS's active search state and a stale native Clear text element. Tests now dismiss search through the native Close control before reusing the finder. An initial iPhone runner install failed because its cached XCTest frameworks were empty; rebuilding that generated runner fixed installation.

The simulator commands use the existing package cache and disable package resolution/updates:

```sh
xcodebuild -project Remember/Remember.xcodeproj -scheme Remember \
  -destination 'platform=iOS Simulator,id=5741ED23-9F8F-4FB6-84E9-FE1E83225998' \
  -configuration Debug -derivedDataPath /tmp/RememberFeedbackReview \
  -clonedSourcePackagesDirPath /tmp/RememberProvenance/SourcePackages \
  -disableAutomaticPackageResolution -skipPackageUpdates CODE_SIGNING_ALLOWED=NO \
  -parallel-testing-enabled NO -only-testing:RememberTests test
```

The full unit selection above ran together with UI selections in `/tmp/remember-threads-review.xcresult`; that combined run failed overall because of the initial UI-test interactions described above, although all 115 unit tests passed. Corrected navigation and final-source validation are recorded below.

The signed iPhone build used `xcodebuild build-for-testing` with the same project/scheme, the connected iOS destination and existing development team. Read-only tests used `test-without-building`; the corrected finder test was rebuilt with `xcodebuild test`. Local result bundles: `/tmp/remember-threads-phone-final.xcresult` (two map/media passes and the initial finder-test failure), `/tmp/remember-threads-phone-search.xcresult` (corrected finder test passed).


Final-source regression run: **24 unit tests and 5 UI tests passed** in `/tmp/remember-threads-final.xcresult`. This includes all six presentation tests and 18 provenance tests, Photos video import/inline playback, past-state browsing and memory archive/restore, thread rename/archive/restore, finder/history/activity navigation, and rename/undo from Activity & decisions. Together with the earlier appearance and Dynamic Type passes, eight distinct simulator UI checks passed. `git --no-optional-locks diff --check` passed.

```sh
xcodebuild -project Remember/Remember.xcodeproj -scheme Remember \
  -destination 'platform=iOS Simulator,id=5741ED23-9F8F-4FB6-84E9-FE1E83225998' \
  -configuration Debug -derivedDataPath /tmp/RememberFeedbackReview \
  -clonedSourcePackagesDirPath /tmp/RememberProvenance/SourcePackages \
  -disableAutomaticPackageResolution -skipPackageUpdates CODE_SIGNING_ALLOWED=NO \
  -parallel-testing-enabled NO \
  -only-testing:RememberTests/ThreadPresentationTests \
  -only-testing:RememberTests/ProvenanceTests \
  -only-testing:RememberUITests/RememberUITests/testThreadCaptureHistoryArchiveAndMapHome \
  -only-testing:RememberUITests/RememberUITests/testThreadMenuEditDeleteRestoreAndDirectMemoryBack \
  -only-testing:RememberUITests/RememberUITests/testPhotosVideoImportAndInlineRiverPlayback \
  -only-testing:RememberUITests/ThreadNavigationUITests \
  -resultBundlePath /tmp/remember-threads-final.xcresult test
```
Use a fresh result-bundle path when rerunning; Xcode refuses to overwrite an existing bundle.

## Menu and count follow-up validation

Moved the distinct-memory count beside History and moved View past state from an inline toggle into Thread options. The simulator `xcodebuild test` run selected `RememberUITests/RememberUITests/testThreadCaptureHistoryArchiveAndMapHome` and `RememberUITests/ThreadNavigationUITests/testExistingThreadsFinderAndHistoryReadOnly`; both passed (`/tmp/remember-past-state-menu.xcresult`). The latter also passed on the connected iPhone using `xcodebuild test-without-building` after a signed `build-for-testing` (`/tmp/remember-past-state-phone.xcresult`). It verifies hidden date controls in the present, menu entry into the past, a changed date, unavailable Rename/Archive actions in historical mode, and return to the present. Normal and historical iPhone screenshots were visually inspected. `git --no-optional-locks diff --check` passed. The updated app is installed on the phone.

This follow-up changed `ProvenanceViews.swift`, the two UI-test files, `readme.md`, and this document. Existing matcher implementation work was preserved.

## Minimal reading layout follow-up

Removed the permanent Activity & decisions card, added the menu action, removed the title's card background, and tightened section/top spacing. The conditional review link opens activity with Suggestions to review selected; menu navigation opens the full record. Both routes use an independent destination so resolving the final suggestion does not remove the open screen.

Validation: `xcodebuild test` with `-only-testing:RememberTests/ThreadPresentationTests`, `-only-testing:RememberUITests/ThreadNavigationUITests`, and `-only-testing:RememberUITests/RememberUITests/testMemoryMapAccessibilityTextSize` passed six unit tests and three simulator UI tests (`/tmp/remember-minimal-history.xcresult`). The signed final build and read-only iPhone test passed (`/tmp/remember-minimal-history-phone-final.xcresult`). The first phone attempt was interrupted by a notification over the search Close control; the test now waits for notification banners before navigation taps. Light-mode, dark-mode iPhone and largest-text simulator screenshots were inspected. `git --no-optional-locks diff --check` passed. The app is installed on the phone.

This follow-up changed `ProvenanceViews.swift`, `ThreadActivityView.swift`, `ThreadNavigationUITests.swift`, `AppearanceReviewUITests.swift`, `readme.md`, and this document. Original files, organization policy and unrelated matcher work were preserved.

## Inline search and reference layout follow-up

Removed the centered-node caption and its unused state. `ProjectView` now owns native search, live inline results and result navigation; the old pushed finder screen is removed. Search focus offers all active threads, edits filter locally, and Close returns to the map on the same navigation level. The results retain full titles, counts, and access beyond the 40-node map window.

Matched the supplied River reference's layout using a shared page margin, an external rail gutter, individually rounded cards, consistent title/date/media alignment, and space between cards while the rail remains continuous. Existing colors and original-media aspect ratios remain unchanged.

Inline-search validation: 41 unit tests in `ThreadPresentationTests` and `GraphInteractionTests`, four simulator UI checks (map gestures, largest text, live search/history/activity, rename/undo), and two read-only iPhone checks passed. Bundles: `/tmp/remember-inline-thread-search.xcresult`, `/tmp/remember-inline-thread-search-phone.xcresult`. The `xcodebuild test` selections were `-only-testing:RememberTests/ThreadPresentationTests`, `-only-testing:RememberTests/GraphInteractionTests`, `-only-testing:RememberUITests/ThreadNavigationUITests`, `-only-testing:RememberUITests/RememberUITests/testMemoryMapAccessibilityTextSize`, and `-only-testing:RememberUITests/RememberUITests/testExistingMapFocusHoldDragAndReturn`. Phone runs used the two read-only map/search selections with `test-without-building` after a signed build.

Reference-layout validation: `xcodebuild test` selected `RememberUITests/RememberUITests/testMemoryMapAccessibilityTextSize` and `RememberUITests/RememberUITests/testExistingLibraryGraphNavigationWithoutCaptures`; both passed in `/tmp/remember-river-reference-fresh.xcresult`. The media-navigation check also passed on iPhone in `/tmp/remember-river-reference-phone.xcresult`. An initial cached test runner still referenced the removed `find-thread` button; fresh build directories `/tmp/RememberThreadsLayoutReview` and `/tmp/RememberThreadsLayoutPhone` resolved that mismatch. Phone photos were checked for equal header/media alignment and opening/return behavior. Search, normal River and largest-text screenshots were inspected. Final heading padding was adjusted to avoid grouped-list corner clipping, then the media-navigation check passed again on simulator and iPhone (`/tmp/remember-river-reference-final.xcresult`, `/tmp/remember-river-reference-phone-final.xcresult`). The final iPhone screenshot was inspected, `git --no-optional-locks diff --check` passed, and the updated app is installed.

History spacing and rail endpoint refinement: removed the extra section gap, balanced the heading’s surrounding whitespace, and anchored the rail start to the first visible title’s dot. `xcodebuild test` with the same two simulator selectors passed (`/tmp/remember-river-spacing-endpoint.xcresult`). The first iPhone `xcodebuild test` attempt failed waiting for `Find a thread`; its UI snapshot showed Settings selected. An unchanged `xcodebuild test-without-building` retry of `RememberUITests/RememberUITests/testExistingLibraryGraphNavigationWithoutCaptures` passed (`/tmp/remember-river-spacing-endpoint-phone-retry.xcresult`). Normal and accessibility-size screenshots were inspected, including the iPhone’s rail continuity between media cards. `git --no-optional-locks diff --check` passed. This refinement changes `ProvenanceViews.swift` and this document.

Dot and disclosure refinement: removed the horizontal connectors and changed memory header stacks to first-text-baseline alignment. `xcodebuild test` passed both simulator checks (`testExistingLibraryGraphNavigationWithoutCaptures`, `testMemoryMapAccessibilityTextSize`) in `/tmp/remember-river-dot-chevron.xcresult`, and the read-only library navigation check on iPhone in `/tmp/remember-river-dot-chevron-phone.xcresult`. Phone and large-text screenshots confirm the standalone dots and title-aligned arrows. `git --no-optional-locks diff --check` passed; the app is installed and launched on iPhone.

This follow-up changed `ProjectView.swift`, `ProjectGraphView.swift`, `ProvenanceViews.swift`, the three UI-test files, `readme.md`, `docs/provenance.md`, and this document. Unrelated matcher/cloud-matcher work was preserved.

## Changed files

- Navigation and copy: `Remember/Remember/ContentView.swift`, `ProjectView.swift`, `ProjectGraphView.swift`, `SettingsView.swift`, `MemoryDetailView.swift`, `PrivacyActivity.swift`, `PrivacyDashboardView.swift`.
- History and activity: `Remember/Remember/ProvenanceViews.swift`, new `ThreadPresentation.swift` and `ThreadActivityView.swift`.
- Tests: new `Remember/RememberTests/ThreadPresentationTests.swift`, new `Remember/RememberUITests/ThreadNavigationUITests.swift`, updated `RememberUITests.swift` and `AppearanceReviewUITests.swift`.
- Documentation: `readme.md`, `docs/provenance.md`, this file.

Existing Evaluation and organization-diagnostics work was left intact. No version-control changes were performed.
