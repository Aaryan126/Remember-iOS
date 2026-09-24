# Media follow-up — verification complete, stopped for user review

## Final outcome, 20 September 2026

| Check | Result | Run |
| --- | --- | --- |
| Native | 29/29, zero skips/runtime warnings | 1789872690275695000 |
| Simulator UI | 10/10, zero skips/runtime warnings | 1789872760870055000 |
| Production entrypoint, build-only | Passed | 1789873022274113000 |
| Signed isolated phone build | Passed | 1789873036048888000 |
| Physical iPhone UI | 10/10, zero skips/runtime warnings | 1789916047531086000 |

Five follow-up / three inherited Python tests and all 119 historical bindings pass.
Twelve final phone captures directly inspected (21 exported); seven final simulator
captures had already been reviewed. No app-source changes during the resume.
This is a completed bounded source/media/navigation check, not a full-release or
model-quality qualification. Original 28 GiB accounting and 10 GiB reserve remain;
post-pass free space ~14.35 GiB, conservative growth ~27.53 GiB.

Read USER-REVIEW.md for how to try Evidence Check and proposed next checkpoints.
Normal Remember installation/personal vault are unchanged. Stop for user review;
no automatic model experiment or production deployment. Earlier holds and in-progress
statements below are historical and superseded by this outcome.

## Latest continuation: 20 September evening

User requested resume and a whole-project/product handoff. Verified all 152 saved
hold bindings before edits, all 119 archived historical inputs and unlocked phone.
PAUSE is archived as pause-resumed-device-unlock-2026-09-20.txt. No Swift sources
changed, so prior final-source native29/simulator10/build results remain applicable.

Phone attempt `1789915904610982000` started its runner but the resource guard stopped
it before test-case results appeared. Receipt exit -15; not a device pass. Whole-Mac
free space dropped about 1 GiB during startup while scoped artifacts barely changed;
do not attribute that decline to this experiment. The approved 28 GiB cap and original
baseline are unchanged. Removed ~644 MiB of regenerable compiler output ONLY from
this isolated source-browser-media build: ModuleCache.noindex,
Build/Intermediates.noindex and SDKExplicitPrecompiledModules. Signed phone products
verified identical before/after; source/results/logs/screenshots preserved. Rebuilding
recreates those caches. No unrelated cleanup. Free bytes recovered to 15,405,445,120;
conservative growth 29,557,522,432 fits 28 GiB including the 256 MiB test reservation.
Unchanged test-without-building retry 1789916047531086000 subsequently passed as above.

See USER-REVIEW.md for product status, the fixture walkthrough and proposed next
checkpoints. These proposals do not authorize normal-app deployment or model work.

## Earlier device-unlock hold (superseded)

Final phone attempt `1789873053910253000` was stopped at destination preflight
after repeated lockState checks reported passcodeRequired true. No final device
test cases ran. Receipt exit code -15 records the deliberate stop, not a test pass.
PAUSE prevents new dispatch, the owned worker has exited, no matching follow-up
xcodebuild remains and no simulator is booted. Safe to close/disconnect. Resume
after unlocking the connected phone; expected remaining time 5–10 minutes if it
passes. Signed phone build and successful Mac-side results below are preserved.
Free space at stop: 18,056,691,712 bytes (~16.82 GiB); conservative growth
26,906,275,840 bytes (~25.06 GiB), within approved 28 GiB and 10 GiB reserve.

## 28 GiB continuation

User replied “Yes, carry on” to the explicit 28 GiB proposal. Recorded in
resource-amendment-28.json; original baseline and 10 GiB reserve remain. Frozen
CP2 runner and approvals are unchanged. All 142 saved-hold bindings verified before
editing; all 119 historical archive bindings and 5 follow-up / 3 inherited Python
tests passed. Phone is unlocked. PAUSE archived as pause-resumed-28gib-2026-09-20.txt.
Final-source native/UI/build/device verification is now in progress; no app-source
changes are planned in this continuation. Earlier results below remain historical.

Final-source native run `1789872690275695000`: 29/29 passed, zero skips/runtime
warnings. Simulator UI `1789872760870055000`: 10/10 passed, zero skips/runtime
warnings. Production-entrypoint build-only `1789873022274113000` and isolated signed
phone build `1789873036048888000` passed. Seven critical simulator captures reviewed:
visible image preview, source after Close, wrapped largest-text scope, Finished
voice, corrupt-video error, moving video (frame 16) and current River.

Phone UI `1789873053910253000` waited at Xcode destination preflight for unlock,
then was deliberately stopped as recorded above. No final device pass or completion
claim; do not substitute the earlier nine-case phone run.

Everything below is historical, including older statements that the 28 GiB proposal
was unapproved or PAUSE was active; the continuation above supersedes those states.

## Previous resource stop: 20 September, after device comparison

All owned workers have exited and no simulator is booted. PAUSE blocks dispatch.
Safe to close the laptop/disconnect the phone. No completion receipt was written.

- Initial physical-phone UI: **9/9 passed**, run `1789870520105611000`, before the
  playback/layout fixes. Reviewed captures show original image/text, moving video
  and River. The real Remember app/private vault were not touched.
- Intermediate native suites: **29/29 passed**, most recently
  `1789871460989703000`. A small finished-player cleanup and diagnostic-message
  edit followed; final saved sources must be rebuilt/retested.
- Full intermediate simulator run `1789871227909650000`: **8/9 passed**, image
  preview return failed, **zero reported runtime warnings** after actor-confined
  audio playback. Tests/fixture subsequently changed.
- Latest ten-case simulator run `1789871524122626000`: all **seven media cases
  passed in the log**, including image-canvas readiness/return, short voice
  completion/replay, background stop, video, corrupt media and large text. The
  storage guard interrupted the run before the three older regression cases
  finished. Receipt exit code **-15**. This is NOT a 10/10 pass.
- That interrupted xcresult lacks Info.plist; screenshot export failed. Preserve
  it and the log/receipt, but do not claim final image captures were inspected.

The guard briefly crossed the existing 26 GiB growth cap during the last run.
After exit, free space was 17,233,248,256 bytes (~16.05 GiB), conservative growth
27,729,719,296 bytes (~25.82 GiB), leaving only ~0.17 GiB headroom—insufficient for
the next test's 256 MiB or phone build's 1 GiB reservation. Scoped artifacts are
~3.01 GiB and registered simulator growth ~3.55 GiB; the whole-Mac free-space
decline controls the guard and is not all attributed to this work.

Removed only ~642 MiB of regenerable compiler artifacts from the completed CP2
isolated build: ModuleCache.noindex, Build/Intermediates.noindex and
SDKExplicitPrecompiledModules. Signed products/results/logs/captures and all 119
archived bindings remain. Original baseline, 26 GiB cap and 10 GiB reserve unchanged.

Next: user frees 2–3 GiB, or explicitly approves a new 28 GiB cap while retaining
the original baseline and 10 GiB reserve. The new cap is a proposal, NOT approved.
Then final 29 native / 10 simulator UI / production-launcher build-only / signed
phone build and 10 phone UI cases, capture review and completion gate. Estimate
15–25 minutes once headroom is stable, longer if another issue appears. See
REPORT.md and RESUME.md. No automatic real-app deployment or model experiment.

## Earlier 20 September work log (superseded by the stop above)

User reconnected the phone and authorized continuation. lockState now reports no
passcode required. Free space recovered to 18,483,896,320 bytes; the existing 26 GiB
cap accommodated the 1 GiB phone-build reservation. No cap increase, baseline reset
or deletion. The previous PAUSE marker is archived as `pause-resumed-2026-09-20.txt`.
All 119 historical bindings and both archive-verifier tests passed.

Signed phone build `1789870475396507000` passed. Unchanged phone UI run
`1789870520105611000` passed all nine cases. Exported phone captures visibly confirm
the cobalt PNG and original document text, plus inline moving video and the River.
Both Quick Look dismissal tests passed on hardware; previous simulator failures
remain recorded, not waived or rewritten.
The production Remember installation remains untouched. The installed iOS 27 SDK
confirms async AVAudioSession activation availability; any playback change will be
separate from this unchanged diagnostic run and needs its own rerun.

Phone inspection found the maximum-size history selector still clipped despite
passing automation. Replaced its menu-style Picker label with a multiline Menu
label containing a native selection Picker. No Dynamic Type cap. Both voice and
video now await audio-session activation outside MainActor; iOS 27 uses its async
API, older supported versions use synchronous activation on the session actor.
Voice loading is cancellable, and late completion cannot start playback after
stop/disappearance/backgrounding. Video cancels pending playback on background.
Two deterministic voice activation regression tests added (native total now 29).
Intermediate native run `1789870754789290000` passed all 29 tests. Simulator
UI run `1789870829629062000` later passed 8/9; further code/test edits followed.

For bounded storage headroom, removed only the completed source-browser-ui run's
`build/ModuleCache.noindex` and `build/Build/Intermediates.noindex` (about 296 MiB of
regenerable compiler output). No signed products, receipts, results, captures or
bound inputs were removed. All 119 archived bindings still verified afterward.
Original accounting baseline/cap/reserve are unchanged; no unrelated cleanup.

## Previous hold (superseded by continuation above)

The final full simulator run `1789831648283747000` completed with **7 passed,
2 failed, zero skipped**. Both failures are preview-dismissal assertions after
tapping the native Quick Look close control. The targeted text/River flow passed
once, but the full rerun failed; it is not yet a reliable regression pass. Do not
attribute this conclusively to iOS or to the app before device diagnosis.

`python3 -B scripts/provenance-first/source-browser-media/check.py build-phone`
exited 1 before dispatch: `26 GiB growth cap reached; preserve original baseline
and stop`. Measured free bytes: 17,592,909,824 (~16.38 GiB); conservative growth:
27,370,057,728 (~25.49 GiB). The next phone build reserves 1 GiB, exceeding the
26 GiB ceiling although the 10 GiB free reserve remains intact. Scoped study/scripts
are 3,343,962,112 bytes, registered simulator growth 3,667,075,072 bytes; whole-Mac
free-space decline controls the gate and is not all attributed to this work.

No phone build/install occurred in this follow-up. The previous checkpoint's
Evidence Check installation remains unchanged. Device lockState reported
`passcodeRequired: true`; the user was asked to unlock it. All owned workers have
exited. Simulator reports Shutdown. No cleanup, Git state changes or real-vault
access. PAUSE prevents another build/test dispatch. Safe to close/disconnect.

To continue: free approximately 2–3 GiB, or explicitly authorize a revised ceiling
without resetting accounting; unlock the phone. See RESUME.md. Current code is
saved, but **not fully verified or ready for production deployment**.

The UI result also records an existing AVAudioSession runtime warning: synchronous
activation on the main thread can hurt responsiveness. Review the supported async
activation API in a bounded follow-up within this checkpoint, with playback and
background/cancellation tests. Do not silently suppress the warning.

## Work and earlier attempts

Checkpoint 2 was verified and its 119 bound inputs archived before edits. Its
completion receipt remains unchanged. New work is in this directory and
`../runs/source-browser-media/`, not appended to the old completion record.

Implemented:

- Independent borderless inline audio/original-file actions in the evidence List.
- Accessibility-size scope menu and expandable search limitations; Dynamic Type
  remains uncapped. Shorter empty-state guidance.
- ProjectViewModel can start from an explicit replayed snapshot without observing
  the organizer. Default production initialization is unchanged.
- Fictional PNG, silent WAV, silent MP4, text and corrupt-video fixtures; six new
  UI cases plus the previous three source-browser flows.
- Archived-input verifier with two passing Python tests and existing resource guard.

Native run `1789830989615678000`: 27 tests passed (12 source-browser, 6 presentation,
4 appearance, 5 video). Fixture launcher subsequently gained old UI fixtures for
fresh-install reproducibility; UI/device verification is still in progress.

First simulator UI run `1789831085926823000`: 7/9 passed. Two preview tests assumed
the old Done label. Targeted run `1789831373101265000` captured the native hierarchy:
text uses `QLOverlayDoneButtonAccessibilityIdentifier` (label “close”), and image
controls can be hidden. Targeted run `1789831522722171000` passed text preview and
the full current-River round trip; image failed an immediate disappearance assertion.
The test now reveals image controls when needed and waits for dismissal to finish.

Full simulator rerun: `1789831648283747000` (outcome above). No phone rerun yet. One earlier image
Quick Look capture was blank despite a valid inline image; final simulator/phone
visual review must resolve this rather than equating navigation with rendering.

Pause: create `PAUSE` here; the owned build/test process stops at the monitored
boundary. Save a hold with `check.py save-hold`, record worker exit, then close the
laptop. On resume inspect receipts/processes and resource headroom first.

The cap remains 26 GiB and reserve 10 GiB, original baseline retained. No unrelated
cleanup, Git mutation, production Remember installation or personal-vault reads.
