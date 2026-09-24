# Frozen search-results handoff — 24 September 2026

**Current source passes 11 UI and 6 unit tests. Rendered-coordinate regression
checks and recorded intermediate-frame review support the container-jump fix.
Installed in place on the iPhone and opened normally. Device automation startup
timed out twice before assertions; manual smoothness review remains required.
No Git state changes. See `../search-handoff-deployment/REPORT.md`.**

Post-launch preservation passes: all 8 originals, 8 memory rows and 171 history
events unchanged; SQLite integrity intact. Both fresh backups verify 192 files.
No complete deployment checkpoint was issued because the physical UI automation
gate is still unmet. The app is ready for the user's manual review.

## Final simulator verification

- Final actor-annotated source: UI `1790246321537451000` **11/11 pass**, unit
  `1790246282358974000` **6/6 pass**. Both `final-actor-top-events.json` and
  `final-actor-scrolled-events.json` pass `verify-motion.py` again (4 populated
  and 3 empty controls each; zero extra displacement within numerical tolerance).
- The first signed build succeeded but reported two actor-isolation warnings
  in the injected callback types. `Snapshot` and `Animate` are now explicitly
  `@MainActor`; runtime sequencing is unchanged. Refreshed controller run
  `1790246282358974000` passes all six tests without those warnings. Full UI is
  being repeated against these exact source hashes before a signed rebuild.
  The uninstalled first build's source/receipts were archived, not discarded.
- Fresh phone backup `search-handoff-deployment/backup-1790246221062747000`
  verifies 192 files, SQLite integrity and all 11 expected migrations. It has
  8 indexed memories, 171 events, no pending captures and cloud assistance off.
  No private content was opened. Installation is still pending.
- Full UI: `1790245822707772000`, **11 passed**, zero failures/skips.
- Controller tests: `1790246128927448000`, **6 passed**, zero failures/skips.
- `verify-motion.py` passes on both `geometry-regression-top-events.json` and
  `geometry-regression-scrolled-events.json`. Each includes four populated
  clears/closes and three empty controls, with 18–27 intermediate samples per
  event. Extra rendered-container displacement is zero (scrolled numerical
  residual at most 5.7e-14 points). Normal native bounds motion remains.
- `geometry-regression.mp4` finalized successfully. Reviewed the overview and
  30 fps `geometry-matching-close.png`, `geometry-no-match-close.png`, and
  `geometry-empty-close.png`: results fade gradually, and the incoming library
  no longer appears above its native content position. Crossfade briefly shows
  both result and library cards; it is not a spatial morph between cards.
- `geometry-scrolled-close-reviewed.png` confirms the light/scrolled populated
  close also fades into the retained scroll position. The content visible behind
  the translucent navigation bar is the existing scrolled library, not the prior
  approximately 100-point container jump.
- Some earlier extracted sheets missed the close interval; they were locator
  attempts, not verification evidence. The scrolled trace independently checks
  the intermediate positions. No recording contains personal phone data.
- `git diff --check` passed. No Git mutations, new dependencies, data migrations,
  cloud calls or production tracing were introduced.

These checks establish removal of the measured artifact, not a guarantee of
subjective smoothness on every device. Phone smoke and user review remain.

The entries below are historical investigation checkpoints; stale preparation
and storage-blocked statements describe those earlier attempts, not current state.

## Geometry-boundary correction — current work

Approved A+B cleanup completed: **423.78 MiB net recovered**, newer backups
verified before/after. See `CLEANUP-RESULT-2.md`. No further deletion authorized.

The earlier traces measured scroll offsets but missed ancestor movement. New
fictional-only telemetry measures rendered window coordinates and ancestor layer
positions. Run `1790245329926370000` reproduced the extra displacement. Run
`1790245491410054000` narrowed it to the grid's `PlatformContainer`: while search
results are present its local y=-116 is balanced by an inherited parent's y=116.
When results disappear, that inherited parent is removed, but a position animation
interpolates the container from its old local coordinate toward zero. Rendered
grid placement jumps by approximately 100 points while its model frame stays at
zero. Empty cancellation has no such container-position animation. These are
observations of this app/runtime, not a general claim about every SwiftUI app.

Adding `.geometryGroup()` around the stable browsing branch preserves the geometry
boundary across results removal. Run `1790245625804634000` passed the focused top
test. `geometry-top-complete-events.json` has **zero extra container displacement**
in all seven measured clears/closes (four filled, three empty controls), while the
ordinary UIKit scroll-inset animation remains present. The trace export initially
failed because the simulator had shut down; rebooting without launching the app
allowed the completed trace to be preserved. `verify-motion.py` checks intermediate
rendered-vs-layout displacement, rather than relying only on settled UI assertions.

The full UI suite is now running against freshly prepared source. Top and scrolled
trace files are separate so later suite launches cannot overwrite them. All
snapshot experimentation with bitmaps, base-grid transaction suppression and
scroll-edge overrides has been removed. Production uses the original transient
snapshot fade plus the stable geometry boundary; no private-class manipulation.
Do not install until full source-matched UI/unit checks and visual review pass.

## Resume outcome — 24 September, evening

- `1790243734478875000`: bitmap candidate compiled; **6/6 unit tests passed**.
- `1790243814729764000`: top repeated-dismissal UI test passed, but
  `bitmap-top-matching-close.png` and `bitmap-top-no-match-close.png` still show
  the brief above-content artifact. Bitmap rendering did not fix it and was
  removed; the default factory again uses `resizableSnapshotView`.
- `1790244052571216000`: trial hiding the results scroll view's top edge effect
  reached test teardown, then the 10 GiB guard interrupted the run. **Not a pass.**
  `edge-top-live` trace was saved. `edge-top.mp4` is zero bytes/unusable; ffmpeg
  reported missing `moov` atom. No visual inference can be drawn from this trial.
  Its production modifier was removed instead of retaining an unverified change.
- Prepared project still includes that removed edge-effect modifier. **Re-run
  `check.py prepare` before any further test**, after clearing the dispatch hold
  on explicit user resume and satisfying the unchanged resource limits.
- No new cleanup or phone changes. No xcodebuild, recording or ffmpeg worker
  remained; no simulator booted. `git diff --check` passed.

Free space fell below the reserve (8.5 GiB observed, later 9.4 GiB). Read-only
`sysctl vm.swapusage` reported 23,552 MiB allocated / 22,411.25 MiB used swap on
a 24 GiB RAM Mac. This is substantial system disk usage and a plausible source
of fluctuating headroom, not proof that it accounts for the entire change.
No system files were deleted and no user apps were closed. Suggested user action:
save work and restart the Mac, then recheck free space before considering more
project cleanup. Restart is not a guarantee of sufficient lasting free space.

Next investigation should isolate the native search/scroll rendering interaction;
both fixed bitmaps and render-server snapshots exhibited the same artifact.
Do not repeat those trials or claim settled-coordinate tests establish smoothness.
The source remains an unverified work-in-progress, not a deployable fix.

## Latest pause checkpoint

Approved cleanup removed exactly the nine paths in `CLEANUP-PROPOSAL.md` and
recovered **1.19 GiB net**; both protected newer backups rehashed successfully.
See `CLEANUP-RESULT.md`. No further deletion is authorized.

After cleanup, conditional-overlay validation produced:

- `1790234681401842000`: six controller tests passed.
- `1790234766540038000`: scrolled repeated-dismissal test passed; video and
  `overlay-scrolled-live` trace retained.
- `1790234887864896000`: simulator launch failed with invalid device state;
  resource guard also tripped. Retried only after space recovered and boot settled.
- `1790234971555269000`: top/dark repeated-dismissal test passed. However,
  detailed `overlay-top-*-detail.png` frames still show a brief grid appearance
  too high. Settled positions and smooth scroll-offset traces are insufficient.
- `1790235080926176000`: full UI run deliberately interrupted after this visual
  finding, **not a full-suite pass**.
- `1790235202449327000`: top test passed for a trial disabling base-grid SwiftUI
  animation, but recorded frames retained the artifact. That change was removed.
- `1790235350835092000`: top test passed with added fictional-only scroll-child
  telemetry. `child-layout-live` shows stable local content coordinates and the
  same native inset movement, narrowing investigation to the visible handoff.
  It does not conclusively establish the source of the artifact.

Latest source trial replaces `resizableSnapshotView` with a synchronously
materialized `UIGraphicsImageRenderer` / `drawHierarchy` image. This tests whether
the render-server snapshot is participating in the unwanted movement; it is a
hypothesis, **not a verified fix**. No experimental base-grid transaction remains.
`check.py prepare` completed for this latest source immediately before the pause.
No test/build/recording worker remained when checked. Simulator shut down for
the pause. `git diff --check` passed. Phone remains on the earlier installed build.

On resume: remove the dispatch `PAUSE` file only after user instruction, check
resources, confirm preparation source bindings, run controller tests and a
recorded top motion test first. Review intermediate frames before broader tests.
If the bitmap trial does not fix the artifact, remove it rather than accumulating
workarounds. Scrolled motion and all 11 UI tests still gate a new phone deployment,
which additionally requires fresh backups and post-install data verification.
Do not reuse any older passing result as validation of this latest source.

The remaining sections record earlier trials chronologically; their storage-block
and stale-preparation statements describe the earlier stop, not this pause.

## Problem and scope

The user clarified the remaining defect: Cancel first replaces populated/no-match
results with the empty-search library, then native search dismissal moves the bar
and restores the title/Ask AI controls. The abrupt content replacement, rather
than the native chrome motion, is the problem. The previous installed candidate
passed settled-position tests but did not solve that perceptual handoff.

## Implementation under validation

Before the search text binding clears, capture only the visible content region
as a transient UIKit snapshot. Remove live result content immediately, but
fade the frozen pixels over the retained library for 0.28 seconds. This avoids
both the hard content cut and the changing results insets observed with the old
live-view fade. Empty focus/Cancel does not create a snapshot. Query clearing,
filter reset and search cancellation are not delayed.

The latest candidate attaches conditional results through an overlay on the
stable browsing host, rather than as a sibling in the root stack. An intermediate
permanently mounted results container was rejected after scrolled-library
testing exposed competing inset updates and animation-idle stalls. This final
hierarchy adjustment is not verified yet. `UnifiedMemorySearchView.swift` has been
restored byte-for-byte to the preserved installed version (`cmp` passed).

The noninteractive, accessibility-hidden snapshot stays in memory only. It is
released on completion, new input, reopening search, navigation, leaving the
screen/window, or app inactivity. Reduce Motion uses a shorter 0.12-second
opacity-only handoff. Native search, keyboard and detail animations are untouched.
No search-controller delegate replacement, private class lookup or disk image
capture is involved. Failure to obtain a snapshot falls back to normal dismissal.

Apple documents rendered snapshots as animation stand-ins in
[UIView snapshot APIs](https://developer.apple.com/documentation/uikit/uiview/snapshotview(afterscreenupdates:)).
Using one for this content handoff is our design choice, not an Apple-prescribed
search animation or a claim about every iOS search implementation.

## Verification plan and progress

1. Preserve the installed checkpoint before edits — completed, hashes verified.
2. Unit-test snapshot lifetime, geometry, rapid reentry, failure/detachment and
   Reduce Motion; existing UI regressions cover search, filters and navigation.
3. Record fictional matching/no-match/empty dismissals and trace snapshot opacity
   through intermediate frames, not only settled layout.
4. Run the full UI suite. Install only after validation and fresh phone backups;
   do not declare perceived smoothness confirmed without user review.

The first unit build found a missing main-actor annotation in the nested test
harness; corrected without changing production behavior. The corrected unit run
`1790232285230077000` passed **6/6**. First targeted UI run
`1790232387326376000` passed settled checks, and the trace showed fading snapshot
opacity at fixed y=116. However, `matching-transition.png` and
`no-match-transition.png` reveal the incoming library briefly jumping behind the
chrome. That first candidate is rejected as visually insufficient. Full-suite
run `1790232542046447000` was intentionally interrupted after this review and is
**not a full-suite pass**.

The candidate now retains the idle results scroll host to address this jump.
Targeted run `1790232797018182000` passed. Reviewed
`stable-matching-detail.png` and `stable-no-match-detail.png` show the large
behind-chrome jump removed and a gradual results-to-library blend. The frozen
pixels remain fixed while the browsing scroll view follows native chrome motion.
The initial animation trace entry can report model alpha=0 before a presentation
layer exists; it must not be interpreted as a rendered blank frame.

Review also identified early clipping of the snapshot's top edge as the safe-area
host resized. The latest source disables host clipping (native navigation chrome
still draws above it). Its full-suite verification is pending. The previous full
suite request was blocked before starting by the 10 GiB reserve. The simulator
was shut down to release resources, then preparation and validation were retried
without deleting files or relaxing limits.

Full-suite run `1790233080712009000` passed the first filter-reset test but stalled
in the scrolled dismissal case with repeated 60-second animation-idle waits. It
was intentionally interrupted; **not a full-suite pass**. The live fictional
`scrolled-idle-*` trace confirms the snapshot had already been released (~0.3 s),
while the retained scroll hosts underwent different inset updates. This suggests
an ownership interaction, but does not prove the cause of XCTest's idle timeout.
The subsequent resource check also failed the 10 GiB reserve.

The retained-host experiment was removed in favor of the conditional overlay
structure above. `check.py prepare` for that latest source stopped at its
256 MiB reservation, so **the generated project/preparation still describe the
previous retained-host candidate**. Do not run a stale test or install that build.
Latest Swift syntax parsing and `git diff --check` passed. The first six unit
passes exercise the snapshot controller's lifecycle/geometry, not the final UI
composition; they are not a substitute for its UI run.

Simulator is shut down. The final recording was finalized with SIGINT, but its
recorder process lingered after shutdown; SIGTERM stopped that exact process.
`ffprobe` validated `final-ui.mp4` (266.882 s). The video is an interrupted run,
not a successful verification artifact. No xcodebuild/test/recording worker remains.

## Resume

1. Free roughly 1–2 GiB extra headroom (any project cleanup needs a fresh exact
   proposal and approval). Last measured free space was about 10.23 GiB; the
   10 GiB reserve and 32 GiB cumulative cap have not been relaxed.
2. `check.py prepare` must succeed for the latest source before any test.
3. Run `unit`, `motion` (scrolled, including empty focus), `motion-top`, review
   new intermediate-frame recordings, and run `ui`. Do not infer motion quality
   from settled-position assertions alone. Stop if idle/inset behavior regresses.
4. Only then prepare a new deployment scope, take fresh phone backups, build,
   install in place, smoke-test and compare original data. No deployment wrapper
   for this candidate has been created and no install is approved by its tests.

This candidate is not installed yet. The first trace
export failed because the simulator had shut down; rebooting without launching
the app allowed the same trace to be archived as `top-dark-*`.

Runner: `python3 scripts/provenance-first/search-handoff/check.py`
(`preserve`, `prepare`, `unit`, `motion-top`, `motion`, `ui`).
Fictional traces/recordings stay in ignored `runs/search-handoff/`.
The 10 GiB reserve and 32 GiB cumulative cap remain in force. The approved cleanup
above is complete; no additional deletion or Git state changes are authorized.
