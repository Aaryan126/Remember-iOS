# Where Remember stands — source-first browsing

20 September 2026. Verification complete: 29 native tests, 10 simulator UI cases
and 10 physical-phone UI cases passed, with zero skips/reported runtime warnings;
both build checks passed. REPORT.md / STATUS.md retain exact runs and limitations.
This guide explains product scope, installation status and the next review.

## Big picture

Our approved goal is: **Save anything. Recover the right context. See how your
projects developed—with evidence.** We are moving value toward inspectable sources
and retained history, rather than promising infallible automatic grouping.

| Area | Current state |
| --- | --- |
| Capture, map and River | Existing app features; this checkpoint is not another map redesign. |
| Free-tier organization | Existing on-device D3 hybrid: embeddings/lexical retrieval, trained MiniLM pair matcher and feature classifier. No new model or threshold in this checkpoint. |
| Retained source/history foundation | Implemented and tested; source text, captions, revisions and archive context can be inspected without trusting generated summaries. |
| Saved-evidence search UI | Integrated into actual app sources, built and exercised in a separately bundled test app. Final status is in REPORT.md. |
| Media/navigation/accessibility follow-up | Inline actions, original previews, current-River round trips, large text and playback lifecycle checks; not a new search-quality evaluation. |
| Automatic relationship improvements / answer verifier | Experimental candidates failed their qualification gates; not integrated. |
| Pro cloud organization | Earlier promising diagnostic only; not enabled as a paid-user organization feature. |

The wider research is not “finished AI.” Source-first browsing is a concrete product
increment following experiments that did not justify stronger automated assertions.
Historical grouping precision, source-retrieval recall and UI test pass rates measure
different things and must not be combined into one app-accuracy percentage.

## Has the app changed?

**Yes in source code; not yet as an update to your everyday phone installation.**
The source-browser foundation, entry point and detail views live in Remember's
real Swift app, not just an evaluation script. The full production entrypoint was
built without installing or launching it. Device checks use **Evidence Check**,
bundle SimpleStudio.Remember.SourceBrowserUI, with fictional data in its own
container, no shared app groups and no model/cloud requests.

The regular Remember installation and personal library were not replaced or read
for this work. Existing unrelated app features may independently use configured
AI services; that is separate from this strictly local source-browser checkpoint.

User-visible changes in the source branch:

- Threads overflow menu → **Search saved evidence**, separate from Find a thread.
- **Current** defaults to current unarchived evidence; **Include history** also
  searches retained earlier revisions and archived sources.
- Results show saved passages, their revision and archive status; opening a result
  retains the selected version instead of silently substituting the newest one.
- Saved images display inline; audio/video have inline playback and a separate
  original-file action. Available image/text originals use native Quick Look.
- Current-River links explicitly open today's River. Back returns to the source,
  then the preserved query/scope, without an Imported history detour.
- Accessibility-size scope labels wrap; search limitations are expandable.
- Voice preparation and audio-session activation run off the UI thread. Cancelled
  requests cannot start later; voice completion/replay and background stop are tested.
  Pending video playback is cancelled on backgrounding.

No new migrations, automatic regrouping, answer generation, verified-answer badges,
training, paid API integration or retrospective recovery of never-saved history.
Missing originals and uncertain version-to-file identity remain explicit limitations.

## Try the isolated phone build

After automation finishes, open **Evidence Check**, not Remember. Normal launch
opens Saved evidence directly. Its fixture forces light appearance; dark/maximum
text variants are launched by the automated tests, not controlled by a new settings UI.

1. Search **receipt**. Current should show NOVA-42. Select Include history to also
   find ORBIT-27 and ARCHIVE-8. Open ORBIT-27: it should say Earlier revision and
   retain the older text. Back should preserve the query and selected scope.
2. Search **photo**. Open the source, inspect the cobalt image and tap Open saved
   original. Close the preview and go Back: you should return to the photo search.
3. Search **audio** or **brief**. Play inline; brief finishes almost immediately
   and can replay. These recordings are deliberately silent, not a speaker test.
4. Search **moving**. Play the moving test-pattern video inline. Search **corrupt**
   to see an explicit playback error while the retained source text stays readable.
5. Search **document**. Inspect its original, close it, scroll to its current thread
   and open the River. Back should return to Saved source, then the document query.
6. Search **unicorn**. It exists only in a generated fixture summary, so it should
   not appear as saved evidence. No match does not establish real-world absence.

The real-app entry point, once a separately approved update is installed, is
**Threads → top-right More (…) → Search saved evidence**. The default test-app
launcher does not expose the full normal Memories/settings/capture shell; automation
separately verifies entry from Threads using its fixture launch argument.

## Recommended next checkpoints (proposals, not started)

1. **Product acceptance / release hardening first.** Review this fixture walkthrough;
   test VoiceOver, audible fictional media, interruption/headphone routing, and a
   representative larger fictional library. Record cold/warm search latency, memory,
   cancellation and safety-limit behavior. Select a supported-OS regression matrix.
   Approximate active effort: 2–4 hours if no fixes are required; Mac plus phone,
   with some hands-on user checks. Stop with a pass/fix list, not a silent rollout.
2. **Controlled normal-app update after acceptance and explicit approval.** First
   agree a recoverable backup/restore procedure and the scope of personal-library
   access; do not assume a complete in-app backup feature exists. Preserve the
   existing library, verify installation identity/signing, then check source search,
   navigation and capture without migrations or regrouping. Budget 1–2 hours once
   backup/build prerequisites are verified; stop for user feedback. No release or
   App Store publication is implied.
3. **Measure usefulness before another model experiment.** With separately agreed
   data/consent, assess realistic “find this source / recover this earlier version”
   tasks: successful retrieval, time to correct evidence, mistaken-version opens,
   empty-result misunderstandings and latency. Freeze targets before evaluation;
   use fresh examples rather than tuning on the consumed research sets. Plan this
   checkpoint after the product review identifies the highest-cost failures.

Keep confirmation-first relationship suggestions, calibrated uncertainty and Pro
review in the later pipeline. Do not promote the failed local answer verifier or
restart broad model/threshold sweeps simply because this engineering check passes.
