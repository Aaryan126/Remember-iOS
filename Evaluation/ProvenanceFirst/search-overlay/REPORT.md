# Search dismissal investigation — 24 September 2026

**Follow-up: traced fix installed after the third approved cleanup; 11/11
simulator UI tests, the extra top-of-library trace test and a full physical-phone
smoke run passed. Earlier failed phone attempts are retained; perceived smoothness
still needs user confirmation.** The earlier
rejected experiments below remain recorded.

## Latest checkpoint after the third approved cleanup

All nine approved paths were removed, recovering **654.23 MiB net**; protected
backups were rehashed. See [cleanup result](CLEANUP-RESULT-3.md). No additional
deletion is authorized. The signed candidate is now installed in place, without
uninstalling Remember or changing production source after simulator verification.

Physical verification passed on the final unchanged-build rerun. One initial harness assertion assumed
an empty native field must expose its placeholder as its value; it now accepts
nil/empty/placeholder only after verifying the field exists. Subsequent runs
failed waiting for the capture button after no-match cancellation, then waiting
for Close after tapping the initially empty search field. The latter was **not**
a library hit-testing failure (line 21 is the Close assertion). Device orientation
changed during these runs. This is a confounder, not proof of either an app defect
or harmless automation failure. No speculative production state workaround was
added. Final run `smoke-1790230950831239000.xcresult` passed **1/1**, with no
failures, skips or reported runtime warnings. It covers all six dismissal cases
and the compact header/filter menu. This pass does not erase the prior failures
or prove their cause. Post-install backup verified 192 files; comparison confirms
healthy SQLite and all **8 memory rows, 171 history events and 8 original files
unchanged**. See [phone verification](../search-overlay-deployment/REPORT.md).

## Earlier checkpoint after the second approved cleanup (superseded)

- Removed only the 19 targets in `CLEANUP-PROPOSAL-2.md`. Net measured recovery
  was **1.00 GiB**; both latest phone backups were rehashed and preserved.
  See [cleanup result](CLEANUP-RESULT-2.md). No approval remains unused.
- `python3 scripts/provenance-first/search-overlay/check.py ui` succeeded:
  run `1790228823706026000`, **11 passed, 0 failed, 0 skipped**. Includes
  light/scrolled and dark/top dismissal sequences, header geometry, filters,
  local submission, large text and exact-revision navigation/Back.
- `python3 scripts/provenance-first/search-overlay/check.py motion-top`
  succeeded: run `1790229148968578000`, **1 passed**. Archived complete trace:
  `top-focused-trace.jsonl` / `top-focused-events.json` in ignored runs.
- The top trace's empty, matching and no-match closes all move the browsing
  presentation offset from -116 to -170 with the same native spring overshoot
  (-170.819). No outgoing results remain after the browsing inset changes.
  This rules out an additional native scroll-offset reset in those runs, not
  every possible perceived discontinuity in switching results back to browsing.
- Reviewed `scoped-top-dark.mp4` using the overview and corrected `*-detail.png`
  contact sheets. Content changes when the results header disappears and the
  saved library returns. Phone/user confirmation of perceived smoothness is
  still required; do not label it confirmed from final-state tests alone.
- `top-dark-trace.jsonl` was captured after the next suite test relaunched and
  has no cancellation events. It is **not evidence** for top dismissal; use
  `top-focused-*`. Initial non-detail contact-sheet timing missed transitions
  and was superseded by the corrected detail windows.
- `python3 scripts/provenance-first/search-overlay/deploy.py prepare` stopped
  at its 1.5 GiB reservation: approximately **10.48 GiB free**, versus 11.5 GiB
  required to retain the 10 GiB floor. No device project/build, fresh phone
  backup, install or launch occurred. The paired phone answered the read-only
  connection check successfully.
- Python syntax checks and `git diff --check` passed. Simulator and recording
  are stopped. No Git state was modified.

Next: free roughly **2 GiB more** on the Mac, then run `deploy.py prepare`,
`build`, `backup`, `inspect-backup`, `install`, `smoke`, `post-backup`, `compare`,
`launch`, and `finish`, proceeding only after each succeeds. The wrapper requires
the source-matched 11/11 simulator pass and retains normal signing, fresh backup,
privacy/startup preflight and post-install data-preservation gates. Any additional
agent cleanup needs its own exact proposal/approval. No further production edits
were made after the verified runs.

## Frame-traced follow-up

The restored installed code passed the expanded settled-position test in run
`1790228091704962000`, but the fictional UIKit frame trace explains why that
was insufficient: the outgoing results scroll view remained alive during the
custom fade and changed its top inset from 116 to 170 and back to 116 points.
The browsing scroll view itself retained its position and followed the ordinary
native 54-point inset animation. These are simulator observations, not an iOS
framework-wide claim.

The new fix in `ContentView.swift` keeps the browsing layer visible behind an
opaque results surface, removes the custom root fade, and scopes an unanimated
identity removal to the results branch only. The search bar, keyboard, browsing
scroll view and detail navigation retain native animation. No timer, delegate
replacement, forced scroll restoration or private API is involved.

Targeted run `1790228308472763000` passed all six repeated-session cases. In
`baseline-events.json`, the matching and no-match cancellations retained the
outgoing results for 5 and 6 sampled frames after the browsing inset changed;
`scoped-removal-events.json` has zero such frames for those cases. The recorded
empty/populated contact sheets (`scoped-empty.png`, `scoped-populated.png`)
show the handoff without the previous overlapping-grid fade. Returning to a
previously scrolled library necessarily changes which cards are displayed;
the saved browsing position must not be discarded merely to hide that change.

Read-only frame recording lives exclusively in the fictional simulator launcher
`scripts/provenance-first/search-overlay/FixtureApp.swift`. It records scroll
geometry and query length, not query contents or personal memories. Production
contains no tracing. The archive/summarizer is `trace.py`.

Added a dark-mode, top-of-library repeated-dismissal test alongside the light-mode
scrolled test. Full-suite run `1790228468943116000` passed the first filter test,
then was terminated by the resource guard during the repeated-scrolled test.
It is **not a full-suite pass**; the new top-of-library test did not run.
The current production code is unchanged from the targeted passing run; only
the additional test/helper was added afterward. The video was finalized and the
simulator shut down. Free space remained approximately 9.84 GiB. No device build,
backup, install or launch was attempted. No additional files were deleted.

That earlier stop was resumed after approval of
[the exact new cleanup proposal](CLEANUP-PROPOSAL-2.md). See the latest checkpoint
above for successful simulator verification and the remaining deployment hold.

Storage: the initial cold simulator reservation was 1.5 GiB. The now-existing
compiled product and module cache allow the runner's normal 256 MiB warm-test
reservation. The 10 GiB free-space floor and 32 GiB cumulative cap are unchanged.

The user reports that populated-search closing remains abrupt compared with
empty-field closing. Passing tests of final geometry did not prove this fixed.
The previous 0.2-second crossfade visibly blended differently positioned grids.

## Cleanup

The user approved the exact 35-directory list. All targets were validated and
removed; **3.13 GiB net** recovered. Both latest full phone snapshots were fully
rehashed and retained (187/188 files). The 12 older app-container restore points
are permanently unavailable; generated project/dependency copies can be rebuilt.
No further deletion is authorized. See [result](CLEANUP-RESULT.md) and
[exact approved scope](CLEANUP-PROPOSAL.md).

## Recorded comparison, not just final-state assertions

Added a manual-clear-before-close control and a native-query-clearing assertion
to `testClosingSearchPreservesScrolledLibraryAcrossRepeatedSessions`. Cases
include empty, matching, no-match, keyboard-open and keyboard-dismissed search,
with a scrolled browsing anchor checked after each close.

All identifiers below refer to logs and result bundles in ignored
`Evaluation/ProvenanceFirst/runs/search-overlay/`.

| Candidate | Run | Outcome |
|---|---|---|
| Conditional overlay, no custom root crossfade | `1790225932156471000` | Targeted test passed; recording still showed a transient content-position change during populated cancellation |
| Both scroll views kept mounted | `1790226136252912000` | Targeted test passed; recording did not establish equivalent empty/populated motion; discarded |
| Unanimated empty-query transaction | `1790226268477210000` | Targeted test passed; populated cancellation still visibly differed; discarded |
| Shared scroll view with explicit browsing-offset restoration | `1790226454114293000` | Targeted test passed; recording still showed a reset during cancellation; discarded |
| Native dismissal delegate preparation | `1790226731745875000` | Failed restored-anchor hit testing in keyboard-already-dismissed case |
| Same callback guarded against already-inactive search | `1790226862722547000` | Same failure; discarded |

The cold rebuild `1790224798801674000` was interrupted by the 10 GiB reserve
before cleanup. A full-suite attempt for the first candidate
(`1790226078761359000`) was intentionally interrupted after motion review showed
it inadequate. **No full-suite pass is claimed.**

Recordings: `overlay-motion-retry.mp4`, `stable-scroll-motion.mp4`,
`query-reset-motion.mp4`, `shared-scroll-motion.mp4`,
`native-prepare-motion.mp4`, and `guarded-native-motion.mp4`. Contact sheets
were reviewed for the first five, including empty/populated/manual-clear
comparisons. Some initial time selections missed transitions and were superseded
by wider/finer contact sheets. Settled-only frames are not evidence of smooth
motion. The guarded candidate was rejected on its regression failure without
claiming a visual pass.

Apple's [search guidance](https://developer.apple.com/videos/play/wwdc2021/10176/)
recommends overlays to preserve the main UI's state. It informed the first
candidate, but does not prove an overlay fixes this iOS 27 timing issue. These
experiments have **not established a definitive native root cause**.

## Earlier stopped handoff (superseded by the frame-traced follow-up above)

- Removed the experimental production changes, including the native delegate
  observer and shared-scroll refactor. `ContentView.swift` and
  `UnifiedMemorySearchView.swift` are byte-identical (`cmp` passed) to the
  installed checkpoint's preserved archive. This retains the known issue, not
  a claimed fix, and avoids shipping the new scroll-restoration bug.
- Retained the expanded UI regression and diagnostic runner. The current test
  parses, but its exact restored-production combination has not been rerun.
  Earlier candidate passes do not count as a pass for it.
- Removed unused new deployment wrappers. No signed build, phone backup,
  install or launch was attempted in this follow-up; the phone is unchanged.
- Swift syntax parse of both restored views and the UI test passed.
  `git diff --check` passed. No Git state changed.
- Recordings are stopped; the simulator was shut down successfully.
- Preserve the current generated project/preparation: they contain the last
  failing candidate for diagnosis. The runner refuses stale prepared sources.
  `prepare` is required before testing restored live sources; archive any
  failing candidate needed for analysis before regenerating that fixture.
- The 10 GiB reserve and 32 GiB cumulative guard were never relaxed.

## Earlier diagnostic plan (now executed above)

Instrument a fictional native-search reproducer to record query clearing,
search deactivation, content-inset and content-offset changes. Compare Cancel
with explicit clear-then-Cancel, at the top and after scrolling, with the keyboard
open and already dismissed. Locate the first divergent frame and callback before
adding another timing workaround. Proceed to full regressions and fresh backed-up
phone deployment only after both motion review and behavioral checks succeed.
Do not mark this fixed from a settled-position test, or weaken the browsing
position assertion to accept a regression.
