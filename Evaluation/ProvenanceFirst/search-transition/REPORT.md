# Search transition correction — implementation verified

23 September 2026. Simulator verification now passes after approved cleanup.
Physical-phone deployment is now complete; see the
[deployment report](../search-transition-deployment/REPORT.md).

## Final implementation verification

- Focused repeated-close/scroll-position regression: **1 passed**, run
  `1790175870875792000`.
- Full unified search UI suite: **8 passed**, run `1790175981924628000`.
- Native search/source suite: **18 passed**, run `1790176196105775000`.
- Final UI/native xcresult summaries report zero failures, skipped tests or
  runtime warnings. This does not mean compiler/tool logs contain no warnings.
- All commands used `python3 -B scripts/provenance-first/search-transition/check.py`
  (`regression`, `ui`, `unit`). Logs, receipts and xcresults are under
  `Evaluation/ProvenanceFirst/runs/search-transition/`.
- Restored scrolled-library, ordinary light saved-passage, and dark accessibility
  XXXL screenshots were exported and inspected. Scroll-position checks allow at
  most 2 points difference after each of three blank/no-match/blank sessions.
- `xcrun swiftc -frontend -parse` and `git diff --check` passed.

The implementation keeps native keyboard/navigation animation and adds a 0.2s
crossfade for the content layers. Reduce Motion disables that added animation
through the system environment value; no separate automated Reduce Motion case
or frame-time/perceptual smoothness measurement has been run.

Both explicitly approved cleanup batches are documented in [Cleanup 1](CLEANUP.md)
and [Cleanup 2](CLEANUP-2-RESULT.md). No additional deletion was performed. The
original accounting baseline, 32 GiB limit and 10 GiB reserve remain unchanged.
Earlier interruptions below remain historical evidence, not current test failures.

## Cause and change

The Memories root previously swapped its browsing ScrollView for a different
search ScrollView as soon as native search became active, then recreated it on
Close. This can reset scroll position/insets during the keyboard/navigation-bar
transition. It also rendered browsing cards from filtered search results.

`ContentView.swift` now keeps the browsing layer mounted beneath search, renders
that grid from the full library, and crossfades the layers over 0.2 seconds. The
hidden layer has hit testing and accessibility disabled. Reduce Motion disables
the added animation. Native search/keyboard animation is not replaced. Search
options still belong to the search session, preserving reset-on-cancel behavior.

This addresses an identified structural cause. Repeated dismissal and control
position were verified on the physical phone, but no frame-time or subjective
smoothness measurement was performed. No model, retrieval, persistence or cloud
behavior changes.

## Checks and pause

- Preserved the completed compact-menu deployment's bound inputs before edits,
  using `python3 -B scripts/provenance-first/search-transition/check.py preserve`.
  Original receipts remain unchanged; copies live in ignored runs.
- `check.py prepare` passed with a separate fictional simulator launcher. The
  transition fixture adds 24 synthetic entries only when explicitly requested.
- `xcrun swiftc -frontend -parse` passed for ContentView, UnifiedMemorySearchUITests
  and the fictional launcher. `git diff --check` passed.
- `check.py ui` built successfully, then stopped at the unchanged 10 GiB free-space
  reserve. Partial run: `runs/search-transition/1790174634134023000.xcresult` and
  corresponding log. The current-passage/local-submission case passed before the
  interruption; this is not a passing suite.
- The new regression initially asserted that a hidden ScrollView no longer
  existed in the accessibility tree. UIKit retained that container, so the
  assertion failed before testing dismissal. Corrected the test to check the
  actual interaction contract (`isHittable == false`) and absent capture button,
  retaining the repeated dismissal/scroll-position assertions. Not yet rerun.

The new test scrolls a populated library, repeats blank and no-match search
sessions, and requires the same card to return at its original vertical position.
Existing seven UI cases remain enabled for search/menu/source navigation checks.

## Historical pause and resume instructions (resolved)

### Approved cleanup and retry

The user approved deletion of six exact old iOS 27 diagnostic build folders.
Removal is complete; see [the paths and measured recovery](CLEANUP.md). No other
files were deleted. Observed immediate net recovery was 0.648 GiB, not the full
2.650 GiB directory allocation; the resource check then passed with 11.340 GiB
free. Original exports, phone backups, active products and research records remain.

`check.py prepare` succeeded with the corrected test. The new `check.py regression`
action ran only the repeated-close/offset case, retaining all its assertions.
Run `1790175591797568000` was interrupted by the same 10 GiB free-space gate while
waiting for the search menu; no complete regression result was produced. No
assertion failure was logged before interruption. This is not a passing test.

The isolated simulator was already shut down when explicitly checked afterward
(`simctl shutdown` reported its state was Shutdown); no additional simulator-data
cleanup was performed. A subsequent disk check showed 10.48 GiB free. This is
insufficient working headroom for another simulator run plus phone deployment.
No phone installation or backup was attempted. Further deletion requires a new
explicit path list and user approval; the six-folder approval is exhausted.

Free another 2–3 GiB without deleting artifacts through this runner. Keep the
existing 32 GiB cumulative ceiling and 10 GiB free reserve unchanged.

1. Run `check.py resources`, then `check.py prepare` to copy the corrected test.
2. Run `check.py ui` and `check.py unit`; resolve any real regression before deployment.
3. Inspect transition appearance, including Reduce Motion and keyboard dismissal.
4. If proceeding to the connected phone, create separate deployment receipts and
   perform signed build, fresh backup/compatibility checks, in-place installation,
   phone smoke and post-install preservation checks. Do not overwrite completed
   compact-menu deployment receipts or reuse its old pre-install backup.

No phone update, deletion, Git state change or expanded storage approval occurred
in this checkpoint. The user was asked to free space; stop pending that change.
