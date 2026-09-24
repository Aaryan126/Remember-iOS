# Unified memory search

## Opening synchronization follow-up — installed and verified, 24 September 2026

The user confirmed the earlier closing fix, but reported the grid moving upward
before the native search bar. Per-frame tracing reproduced a 32–34 pt mismatch.
The new implementation uses one persistent native ScrollView for browsing and
results, replacing the geometry-group workaround. Only switching content gets
an unanimated transaction; empty focus retains native coordinated bar/grid motion.
Browsing position is restored after the returning layout is measured, including
after short/no-results pages. The existing in-memory closing fade is unchanged.

Final-source checks: **11/11 UI and 6/6 lifecycle tests pass**. Twelve sampled
openings stay aligned (numerical residual only); fourteen clears/closes have no
extra container displacement. Recorded opening and closing frames were reviewed.
The existing refresh actions are retained; UI tests cover filters, navigation/back,
header spacing and accessibility-sized text. Signed iPhone build and in-place
installation succeeded after a fresh verified backup. **The physical iPhone
smoke test passed**. Pre/post copies preserve all 8 memories, 8 originals and
171 history events unchanged. Remember is open for the user's final feel check.
See
[opening validation](../Evaluation/ProvenanceFirst/search-handoff/OPENING-FOLLOWUP.md).

## Content handoff follow-up — installed, manual phone review pending, 24 September 2026

The user confirmed the installed fix still cuts abruptly from results/no-results
to the empty-search library before native chrome dismissal. The new candidate
captures the visible result pixels before the binding clears, then fades that
temporary, noninteractive snapshot over the returning library. It does not delay
query clearing or animate a live results scroll view with changing insets.
Empty search retains native dismissal. Intermediate-frame tracing identified a
second issue: SwiftUI reparented the library's native scroll container and animated
its old local origin, introducing approximately 100 points of extra displacement.
A stable `.geometryGroup()` boundary prevents that movement without suppressing
the native search/keyboard animation. Rejected bitmap, scroll-edge and permanently
retained results-host trials are not part of the implementation.

After approved A+B cleanup recovered 423.78 MiB, current-source checks passed:
**11/11 UI tests and 6/6 handoff tests**. Top/dark and scrolled/light traces each
cover four populated clears/closes and three empty controls, with zero extra
container displacement (floating-point tolerance). Recorded intermediate frames
show gradual outgoing-results fading and native incoming-library movement.
These checks target the reported artifact; perceived smoothness still needs user
confirmation on the phone. The final signed build is installed in place and
opens normally. Two device test-runner attempts timed out enabling automation
before running assertions; phone UI automation is **not verified**. Fresh verified
pre/post-launch backups preserve all 8 original files byte-for-byte, all 8 memory
rows and all 171 history events. No uninstall or data reset occurred.
See [deployment status](../Evaluation/ProvenanceFirst/search-handoff-deployment/REPORT.md).
See [handoff validation](../Evaluation/ProvenanceFirst/search-handoff/REPORT.md).

## Earlier dismissal fix — installed but perceptually insufficient, 24 September 2026

Fictional frame tracing found the outgoing results scroll view changing its inset
twice during the installed crossfade. The candidate removes that fade and makes
only results removal unanimated, over the continuously mounted browsing grid.
Native search, keyboard and detail-navigation animations remain in place; no
timer, delegate override or forced scroll-position reset is used.

After the second approved cleanup, all **11 UI tests passed**, including the
dark-mode/top-of-library regression. An additional focused top test passed;
empty, matching and no-match closes show the same native scroll-offset spring,
with no outgoing results remaining after the browsing inset changes. Recordings
were reviewed, but the content handoff still differs from an unchanged empty
library; phone/user confirmation of perceived smoothness remains necessary.

The third approved cleanup recovered 654.23 MiB net and unblocked deployment.
The signed fix is **installed in place** after fresh verified backups. The final
physical-phone smoke passed all repeated-session/header/menu checks on the
unchanged build. Earlier attempts remain recorded: one harness assumption about
native empty-field values was corrected, and two subsequent failures coincided
with device orientation changes. The passing rerun does not prove their cause.
Post-install comparison confirms healthy SQLite and all 8 memory rows, 171 history
events and 8 original files unchanged. No further production workaround was
added; perceived smoothness still needs user confirmation. The 10 GiB reserve
remains unchanged; no further deletion is authorized.
See the [investigation and resume status](../Evaluation/ProvenanceFirst/search-overlay/REPORT.md).

## Earlier populated-search dismissal follow-up — superseded, 24 September 2026

The user confirmed empty-field dismissal is smooth, but closing after typing
still jerks. The previous identity transition removed populated results
immediately while native search chrome was closing. Source now applies a short
0.2-second opacity handoff only when leaving populated results; entering results
and empty-field focus/dismissal do not gain custom animations. Reduce Motion
disables the custom fade. The compact 10-point header spacing remains in source.

The regression now exercises matching/no-match queries with the keyboard open,
matching queries after keyboard dismissal, and empty sessions. The pre-fix run
passed its settled-position checks, illustrating why those checks alone did not
establish smooth motion. After the specifically approved cache cleanup, the
targeted regression passed and recorded before/after frames were inspected for
matching results, no results, empty search and keyboard-already-dismissed cases.
The full suite passed 10/10, including the compact spacing. **This change and the
compact spacing are installed on the physical iPhone.** The signed build and
phone smoke passed on the first attempt, covering empty/populated dismissal with
the keyboard open or already dismissed, header alignment and filter-menu use.
Pre/post snapshots preserve all 8 memory rows, 171 events and 8 original files
unchanged. Perceived smoothness still needs the user's confirmation. Reduce Motion's
enabled setting was not separately exercised in this recording; the code disables
the custom fade for it. See
[dismissal verification status](../Evaluation/ProvenanceFirst/search-dismissal/REPORT.md)
and [phone deployment report](../Evaluation/ProvenanceFirst/search-dismissal-deployment/REPORT.md).

## Compact header follow-up — 24 September 2026

At the user's request, source now halves the balanced header gaps from 20 to
10 points. The native search field already supplies the 10-point top inset, so
extra top padding is removed and the header-to-results gap becomes 10 points.
The centered controls, 44-point filter target, internal result-section spacing,
card spacing and search motion are unchanged. Validation and installation status:
[compact-header report](../Evaluation/ProvenanceFirst/search-compact/REPORT.md).

## Search-header spacing — installed, 24 September 2026

The title, result count and Search options button share a center-aligned row;
the count uses an explicit body font and tabular digits. The native search field
has a 10-point bottom inset, so results now add 10 points above the row rather
than 16. This matches the 20-point space below the row before the default grid,
without shrinking the filter button's 44-point touch target. Active-filter and
AI-result status rows still appear when applicable.

The earlier native-focus correction has now been confirmed smooth by the user.
This spacing-only change leaves focus, cancellation, scroll-position retention,
filter state and retrieval behavior untouched. The layout regression measures
title/count/button alignment and the visible field-to-header/header-to-card gaps
in light and dark mode, with the keyboard open and dismissed. Validation and
installation status are recorded in the
[spacing report](../Evaluation/ProvenanceFirst/search-spacing/REPORT.md).

Installed in place on the physical iPhone after the approved cache cleanup.
The signed build and phone spacing/menu/repeated-dismissal smoke passed; the
first automation startup timed out before running the test, and the retry passed.
Verified pre/post snapshots preserve all 8 memory rows, 171 events and 8 original
files unchanged. See the [deployment report](../Evaluation/ProvenanceFirst/search-spacing-deployment/REPORT.md).

## Native-focus correction — installed, 23 September 2026

The user still reported abrupt motion after the crossfade update below. The latest
source removes that custom fade and keeps the browsing grid visible when an empty
search field gains focus. Results/options appear after typing; filters survive
clearing/retyping and reset on cancellation. Nine UI cases and 18 native tests pass;
recorded simulator frames were inspected. The signed build and physical-phone
empty-focus/repeated-dismissal/menu smoke passed. This follow-up is **installed**;
all 8 memory rows, 171 history events and 8 originals were verified unchanged.
User confirmation of perceived smoothness is still needed. See
[motion follow-up evidence](../Evaluation/ProvenanceFirst/search-motion/REPORT.md)
and the [deployment report](../Evaluation/ProvenanceFirst/search-motion-deployment/REPORT.md).

## Earlier transition follow-up — superseded, 23 September 2026

That version kept the browsing grid mounted while search opened/closed,
with a short Reduce Motion-aware crossfade, to avoid recreating its scroll view
during native keyboard/navigation animation. The browsing grid uses the full
library even while search is active, so a no-match query cannot clamp its offset.
After the approved cleanup, the regression, 8 UI cases and 18 native tests passed.
The signed build and physical-phone repeated-dismissal/menu smoke also passed.
That build was installed in the main app; all 8 memory rows, 171 history events
and 8 originals were verified unchanged. See the
[transition checkpoint](../Evaluation/ProvenanceFirst/search-transition/REPORT.md)
and [phone deployment report](../Evaluation/ProvenanceFirst/search-transition-deployment/REPORT.md).

## Search-menu refinement — 23 September 2026

The latest source removes the always-visible filter panel. A compact **Search
options** filter icon sits in the results header. Include history and Source text
only are native checked menu items, both off by default. An active filter shows
a short status plus **Reset**; cancelling search does not leave a hidden global
preference behind. Returning from a saved passage preserves the current session.

The existing explicit Try AI search action and How search works explanation also
live in that menu, removing repeated prompts/help paragraphs from default results.
Ask AI and retrieval/version semantics are unchanged. This UX refinement is now
installed in the main Remember app on the physical iPhone.
Checks and the original deployed-source archive are in
`Evaluation/ProvenanceFirst/search-options/` and its ignored runs directory.
Verification: 18 native and 7 simulator UI tests passed; default light and dark
accessibility layouts were visually reviewed. After the earlier storage hold was
resolved, the signed app/extension build and physical-phone menu smoke passed.
The first phone-test runner timed out enabling automation; the retry passed (1/1).
Pre/post snapshots preserve all 8 memory rows, 171 history events and 8 original
files unchanged. See the [deployment report](../Evaluation/ProvenanceFirst/search-options-deployment/REPORT.md)
and [implementation report](../Evaluation/ProvenanceFirst/search-options/REPORT.md).

## Plan — 23 September 2026

Unify finding memories and inspecting retained source versions in Memories. Keep
Ask AI separate: no new cloud calls, answer generation or grouping-policy changes.

1. Preserve the previous deployment checkpoint and inspect existing search paths.
2. Keep ordinary current-memory search as default. Add Include history and Source
   text only options to the same search experience. Show saved-text matches with
   cards where available, and clearly distinguish historical/archived passages.
3. Reuse exact-version source detail, including original availability checks and
   direct back navigation. Support an empty active library with retained history.
4. Remove the redundant Threads menu entry. Return on the keyboard performs local
   search; existing AI assistance requires an explicit action.
5. Test scope changes, metadata-only matches, history, cancellation, navigation and
   empty/error states. Build with local dependencies, preserving the 10 GiB reserve.
6. Record validation and limits here. Do not install over personal phone data as
   part of this checkpoint or change Git state.

`.gitignore` protects local secrets, dependencies, model weights and private run
artifacts. Ignore rules do not remove files already tracked by Git.

## Implemented behavior

- Tap **Search your memories** in Memories, including when the current library is
  empty. Type a name, phrase or reference; Return performs local search.
- By default, current indexed memories match titles, summaries, tags, captions and
  extracted text. Cards retain their normal Memory-page navigation. A matching
  current saved passage gets a separate **View saved passage** action when loaded.
- **Include history** adds saved-text matches from retained earlier revisions and
  archived sources. These are labelled passages, not duplicate current cards.
- **Source text only** replaces metadata/card results with saved extracted text and
  caption matches. Combine it with Include history to search both scopes.
- Sources without a current indexed card remain discoverable. Passages are paged;
  **Show more saved passages** retrieves the next page at the same ledger boundary.
- A source link resolves the exact saved revision. Back preserves the query and
  options. Original media availability/version checks are unchanged. Current thread
  context is available when supplied by the app's shared project model.
- The Threads menu no longer duplicates this search. Its thread finder, Activity &
  decisions, Archive and River behavior remain unchanged.
- Ask AI remains independent. The existing explicit **Try AI search** option is
  offered only in ordinary current-memory search, never as historical/source-only
  retrieval. Search submission itself no longer implicitly requests AI assistance.

This is word/phrase retrieval, not answer verification or a new semantic model.
Generated text may help find a current card but is never substituted for a saved
passage. A missing hit is not proof of absence. Unretained revisions, absent media,
OCR/transcription errors and existing local search safety limits still apply.

## Reproducible checks

The runner uses a separately bundled, fictional simulator fixture and local GRDB
sources. It preserves the previous deployment's 139 input bindings under
`Evaluation/ProvenanceFirst/unified-search/baseline/`; old receipts are not rewritten.
Private run artifacts and archived copies of run artifacts are ignored by Git.

```sh
python3 -B scripts/provenance-first/unified-search/check.py resources
python3 -B scripts/provenance-first/unified-search/check.py prepare-ui
python3 -B scripts/provenance-first/unified-search/check.py unit
python3 -B scripts/provenance-first/unified-search/check.py ui
python3 -B scripts/provenance-first/unified-search/check.py prepare
python3 -B scripts/provenance-first/unified-search/check.py build
git diff --check
```

The normal-entrypoint build is compile-only, not a personal-phone installation.
`Evaluation/ProvenanceFirst/unified-search/PAUSE` stops further check dispatch and
terminates an active bounded build/test unit; completed receipts remain resumable.
Resource checks retain the original accounting baseline, approved 31 GiB growth
ceiling and 10 GiB free-space reserve. No package fetching or Git state changes.

## Validation — 23 September 2026

**Deployment follow-up completed:** after the user's approval, the signed normal
app/extension build passed and the update was installed in place on the physical
iPhone 17 (iOS 27). The normal-app smoke passed 1/1, zero failures/skips/reported
runtime warnings. All 8 memory rows, 171 history events and 8 original files were
verified unchanged. No uninstall, data restore or forced regrouping. The earlier
build hold below is resolved by this signed device build; no redundant simulator
normal-entrypoint build was needed. [Deployment report](../Evaluation/ProvenanceFirst/unified-search-deployment/REPORT.md).

- Native tests: **17 passed**, zero failures/skips, including five new unified-search
  policy/integration cases and twelve source-browser regression cases. Receipt:
  `runs/unified-search/1790164003570083000.xcresult`.
- Simulator UI: **6 passed**, zero failures/skips, on iPhone 17 / iOS 27. Covers
  current passage links, local keyboard submission, history/exact-version/direct
  Back, metadata-only exclusion, empty-library entry, large-text dark appearance,
  and removal of the duplicate Threads action. Receipt:
  `runs/unified-search/1790164261477119000.xcresult`.
- Two final UI captures were inspected (light/current and dark/accessibility text).
  A subsequent copy-only heading correction avoids mentioning history when the
  option is off; the UI suite predates that final wording correction.
  `xcrun swiftc -frontend -parse Remember/Remember/UnifiedMemorySearchView.swift`
  passed on the final file; this is syntax verification, not a full app build.
- Both successful test-result summaries report zero runtime warnings. Build/tool
  logs still contain existing compiler/AppIntents and simulator diagnostics; this
  is not a claim that every tool log is warning-free.
- The initial compile exposed file-private card/layout components; making those
  existing components module-internal resolved it, and the native/UI builds passed.
- `git diff --check` passed. `git check-ignore -v --no-index` verified secret,
  dependency, model and private-run examples, including archived run receipts;
  `.env.production.example` stays eligible for version control. Read-only tracked
  file checks found no matches for the tested `.env`/model/node_modules patterns.
- **Initial normal-entrypoint build hold (subsequently resolved above):**
  `python3 -B scripts/provenance-first/unified-search/check.py build` was refused
  before xcodebuild launch with `31 GiB ceiling would be exceeded; preserve baseline`.
  Its 768 MiB reservation exceeded remaining cumulative headroom. The limit and
  original baseline were not weakened. No compiler failure from this final command.
- A simulator shutdown request reported it was already Shutdown after testing;
  no device reset, data deletion or cleanup was performed.

The initial implementation checkpoint made no personal-phone installation,
private-library read, AI call, new retrieval-quality benchmark or Git state change.
The separately approved deployment subsequently backed up the private app data,
installed in place and verified preservation. No AI calls or Git state changes
were made in that deployment. The bounded resource allowance is now 32 GiB with
the original baseline and 10 GiB reserve unchanged; historical approvals stay intact.

## Files changed in this checkpoint

- `.gitignore`: additional model/private-artifact patterns; environment examples.
- `Remember/Remember/ContentView.swift`: unified search entry, explicit local submit,
  shared card/layout visibility, no capture dial over active search.
- `Remember/Remember/ProjectView.swift`: removed redundant search menu entry.
- `Remember/Remember/SourceEvidenceSearchView.swift`: shared saved-passage row/detail.
- `Remember/Remember/UnifiedMemorySearch.swift` and `UnifiedMemorySearchView.swift`:
  presentation policy and combined search UI.
- `Remember/RememberTests/UnifiedMemorySearchTests.swift`: policy/store regression cases.
- `Remember/RememberUITests/UnifiedMemorySearchUITests.swift` and
  `SourceEvidenceUITests.swift`: new unified-flow checks and updated menu expectation.
- `scripts/provenance-first/unified-search/`: bounded check runner and fictional launcher.
- `Evaluation/ProvenanceFirst/unified-search/`: previous-input archive and saved status.
- `readme.md`, `docs/provenance-first.md` and this document: current behavior/status.

Pre-existing unrelated work was preserved; no staging, commits or other Git state
changes were performed. The earlier deployment/model evaluation reports stay intact.

## Next, separately evaluated

Ask AI may later retrieve these same version-bound sources and cite them. That
requires answer-support and historical-consistency evaluation; this checkpoint
does not claim the assistant already uses the new history retrieval.
