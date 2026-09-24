# Source-browser media follow-up — verification complete, stopped for review

Final phone run **1789916047531086000 passed 10/10**, zero skips, failures or
reported runtime warnings. Final saved sources also passed 29 native tests, 10
simulator UI tests, a full production-entrypoint build-only check and a signed
isolated phone build. Twelve final phone captures were directly inspected, alongside
the seven final simulator captures previously reviewed. This completes the bounded
engineering checkpoint, not production-release or model-quality qualification.

Read [USER-REVIEW.md](USER-REVIEW.md) for the big picture, installation distinction,
fixture walkthrough and proposed next steps. The real Remember installation and
personal vault remain untouched. No new Swift changes were needed during this resume.

## Continuation history

Evening continuation: phone unlocked and all 152 saved-hold bindings verified.
Attempt `1789915904610982000` was resource-interrupted before any test-case results,
exit -15. Whole-Mac free-space decline crossed the approved 28 GiB cap; scoped
artifacts barely changed. Removed ~644 MiB of regenerable compiler caches from the
current isolated media build (ModuleCache.noindex, Build/Intermediates.noindex,
SDKExplicitPrecompiledModules), not signed products/results/logs/source/captures.
Signed products match their saved hashes before/after. Baseline/cap/reserve unchanged;
the unchanged retry passed as recorded above. See USER-REVIEW.md for the product handoff.

User approved the explicitly proposed 28 GiB ceiling on 20 September (“Yes, carry
on”). The new scoped approval retains the original baseline and 10 GiB free-space
reserve; frozen historical approvals/runner/receipts remain unchanged. Final saved
sources passed all Mac-side and final device checks after resuming the unlock hold.
No production deployment or new model-quality claim is made.

## What this checks

This is a product-reliability checkpoint for **Save anything. Recover the right
context. See how your projects developed—with evidence.** It is not a new grouping,
ranking or model-quality evaluation. D3 and the paid/cloud experiments are unchanged.

All phone interactions use the separately signed **Evidence Check** app
(`SimpleStudio.Remember.SourceBrowserUI`), real production view implementations and
fictional fixtures. No production Remember install, private-vault reads, shared
app groups, organizer observation or cloud/model calls.

## Changes

App files: `SourceEvidenceSearchView.swift`, `ProjectViewModel.swift`,
`AudioMemoryPlayerView.swift`, `LocalVideoPlayerView.swift`, and new
`LocalPlaybackSession.swift` in Remember/Remember. Tests: SourceEvidenceBrowserTests,
VideoRiverTests and SourceEvidenceMediaUITests. The isolated fixture/runner,
resource approval and checkpoint documentation live in the source-browser-media
script/evaluation directories; the integration overview is docs/provenance-first.md.

- Independent inline playback and original-file actions in the evidence List.
- A multiline scope menu at accessibility text sizes, without limiting Dynamic
  Type; expandable search caveats and shorter empty-state guidance.
- Replayed project injection for testing source → explicitly current River → source
  → same search, without starting background organization.
- Audio-session setup off MainActor; iOS 27 uses asynchronous activation and older
  supported versions use the synchronous API on an actor executor. AVAudioPlayer's
  synchronous prepare/play/stop also run on a separate actor. Loading is cancellable;
  a stopped voice request cannot later start or overwrite a newer request's state.
- Pending video playback is cancelled when backgrounded. Existing playback pauses.
- Native cancellation/failure tests and fictional image, audio, video, text,
  corrupt-video and navigation/accessibility UI coverage. Added a 0.3-second silent
  recording to verify natural completion and replay after moving playback off the
  UI thread (final UI suite: ten cases).

The installed iOS 27 AVAudioSession header confirms activation availability;
[Apple's activation reference](https://developer.apple.com/documentation/avfaudio/avaudiosession/activate(options:completionhandler:))
describes the asynchronous operation. The AVAudioPlayer header separately documents
synchronous hardware acquisition/release; activating the session first was not
sufficient to remove its warning in the intermediate simulator run.

## Results and preserved attempt history

| Run | Check | Outcome |
| --- | --- | --- |
| `1789870475396507000` | Initial signed phone build | Passed |
| `1789870520105611000` | Unchanged phone UI suite | 9/9 passed; voice/video activation warnings |
| `1789870754789290000` | First playback/layout changes, native | 29/29 passed |
| `1789870829629062000` | Intermediate simulator UI | 8/9 passed; image preview dismissal assertion failed; voice warning remained |
| `1789871064794324000` | Actor-confined voice player, native | 29/29 passed |
| `1789871129815385000` | Observable preview-return check | Text passed, image failed; post-close capture shows image with hidden controls |
| `1789871227909650000` | Actor-confined voice player, simulator UI | 8/9 passed; image return failed; no audio-session responsiveness warnings |
| `1789871460989703000` | Native with expanded UI fixtures/tests | 29/29 passed; minor cleanup/diagnostic edits followed |
| `1789871524122626000` | Ten-case simulator UI | Seven media cases passed in log, then resource interruption; exit -15, NOT a full-suite pass |
| `1789872690275695000` | Final-source native rerun under approved 28 GiB cap | 29/29 passed, zero skips/runtime warnings |
| `1789872760870055000` | Final-source simulator UI | 10/10 passed, zero skips/runtime warnings |
| `1789873022274113000` | Final-source production-entrypoint build-only | Passed; not installed/launched |
| `1789873036048888000` | Final-source signed isolated phone build | Passed |
| `1789873053910253000` | Final-source phone UI attempt | Device locked at preflight; deliberately stopped, exit -15, no test pass |
| `1789915904610982000` | Evening phone UI attempt | Resource guard interrupted startup, exit -15, no test-case result |
| `1789916047531086000` | Final-source phone UI retry | 10/10 passed, zero skips/runtime warnings; 159.9 seconds of tests |

Final-source native, simulator UI, phone UI and both builds passed. The earlier
unlock and storage holds remain recorded above; they are not counted as passes.
Follow-up Python tests (5), inherited resource guard tests (3),
119 archived-input verification and `git diff --check` passed.

## Visual review and interpretation

Initial phone captures show the cobalt image and original document text in Quick
Look, inline moving video (frame 14 at 1.167 seconds), and a current River. Both
preview dismissal/navigation tests passed on hardware. Phone review—not the test
assertions—found clipping in the largest-text scope selector. The replacement label
visibly wraps completely in the intermediate simulator capture.

Simulator image Quick Look has shown blank captures and a retained preview view
after tapping close. The updated test measures disappeared close controls and a
hittable source Back button, captures the post-close screen, then actually navigates
back and verifies the query. This tests observable behavior instead of requiring
an internal native view to be deallocated. The targeted image failure's post-close
capture actually shows the cobalt image with hidden controls: the image did load,
but the expected return did not happen. This suggests a presentation-shell/content
handover race, not merely a retained accessibility node. The image test now waits
for the native image canvas before interacting with close; this passed in run
`1789871524122626000` before the resource interruption. That interrupted xcresult
has no Info.plist and attachment export failed. Its missing captures were not
treated as visual evidence. The later complete runs and separately inspected
captures below resolve final verification. No production Quick Look workaround
was added and blank rendering was never accepted as correct.

Final simulator run `1789872760870055000` resolves the remaining simulator check:
all ten cases passed. Exported 21 PNGs to final-simulator-review-1789872760870055000.
Direct inspection confirms the cobalt original in Quick Look, the source page
after closing it, a fully wrapped largest-text scope selector, Finished/replay
voice state, an honest corrupt-video error, a visible video frame at 1.333 seconds
(frame 16), and the current River. The earlier
failed and interrupted runs above remain part of the attempt history.

Final phone run exported 21 PNGs to final-phone-review-1789916047531086000.
Twelve directly inspected captures confirm: cobalt original in Quick Look and its
source after close; the entire largest-text Include history label; visible video
at 1.167 seconds (frame 14); Finished/replay voice state; original document text
and source after close; current River; ORBIT-27's explicit Earlier revision state;
ARCHIVE-8 retained text with unavailable original; honest corrupt-video error; and
the real Threads overflow entry. Search text horizontally scrolls at extreme sizes;
no Dynamic Type cap was added. Screenshot inspection does not replace VoiceOver or
real audible-media/route testing.

An attempt to open the Simulator GUI failed (`open -a Simulator`: application not
found; the usual Xcode Developer/Applications/Simulator.app path is also absent).
No GUI/package installation or other simulator reset was performed. Tests continue
through the installed CoreSimulator runtime; do not describe these as GUI-open runs.

## Limits and safety

- One connected iPhone 17, iOS 27 build 24A437; simulator build 24A434 differs.
- Silent fictional audio/video verify player state and visible video progression,
  not speaker quality, Bluetooth routing, phone calls or a full interruption matrix.
- Large-text/dark/light captures and accessibility identifiers are not a human
  VoiceOver audit. Native search-field text can horizontally scroll at huge sizes.
- iOS 26 fallback compiles but has not been rerun on iOS 26 hardware in this checkpoint.
- No claim of better matching accuracy, semantic understanding or answer quality.
- Earlier successful CP2's 119 inputs remain archived and hash-verified. Failed
  attempts are retained. No Git mutations.
- Removed ~642 MiB of regenerable compiler cache/intermediate output from the
  completed CP2 isolated build. Its signed products, logs, results, source archive
  and screenshots remain. Targets: `ModuleCache.noindex`, `Build/Intermediates.noindex`
  and `SDKExplicitPrecompiledModules`. Rebuilding recreates those caches. All 119
  historical bindings still passed after cleanup.
- Original resource baseline and 10 GiB reserve remain; user approved the increase
  from 26 to 28 GiB. Evening cleanup removed only the ~644 MiB of current isolated
  build caches listed above. Post-pass free bytes: 15,403,110,400 (~14.35 GiB),
  conservative growth 29,559,857,152 (~27.53 GiB), within the approved limits.

Stopped for review after final verification. Do not automatically deploy over the
real Remember app or start a new model experiment.

## Previous resource stop and approved continuation

The existing guard stopped the latest simulator run when conservative growth
briefly exceeded 26 GiB. After stopping, measured free bytes were 17,233,248,256
(~16.05 GiB), conservative growth 27,729,719,296 (~25.82 GiB). Only ~0.17 GiB
headroom remained; the next test reserves 256 MiB and phone build reserves 1 GiB.
The whole-Mac decline—not just scoped artifacts (~3.01 GiB) plus registered
simulator growth (~3.55 GiB)—controls the cap. Do not attribute all decline to this
checkpoint. At that historical stop all workers exited and PAUSE prevented dispatch.

The user subsequently approved 28 GiB, recorded in resource-amendment-28.json.
Five follow-up Python tests (including new-cap/reservation/invalid-input coverage)
and three inherited resource tests passed. All 142 saved-hold bindings verified
before edits and all 119 historical inputs still verify. Initial continuation free
space: 19,362,095,104 bytes (~18.03 GiB). PAUSE was archived after gate checks.
Saved-source checks have now completed; RESUME.md describes the review stop and
preserved run bindings. The real Remember installation remains untouched.

## Commands and handoff

This continuation ran `check.py resources`, `verify`, and `test-phone` twice (first
resource-interrupted, then passed); Python unittest discovery in source-browser-media
(5) and source-browser-ui (3); `xcresulttool get test-results summary` and attachment
export; signed-product/hash verification; and `git diff --check`. Final checkpoint
uses the four successful run IDs below and binds source, fixtures, reports and captures:

```sh
python3 -B scripts/provenance-first/source-browser-media/check.py checkpoint \
  --unit-run 1789872690275695000 --ui-run 1789872760870055000 \
  --phone-run 1789916047531086000 --build-run 1789873022274113000
```

No app-source changes this continuation. Documentation updated: this report,
STATUS.md, RESUME.md, USER-REVIEW.md and docs/provenance-first.md. Prior implementation
files are listed under Changes. No Git mutation or cloud inference was performed.
