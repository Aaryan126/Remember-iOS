# Completed media follow-up — review and future continuation

## Current state: verification complete, stop for review

Phone retry **1789916047531086000** passed all ten cases, zero skips/runtime warnings.
No Swift sources changed since the final native29/simulator10/production-build passes
listed below. Twelve final phone screenshots were directly inspected; REPORT.md
records results, failed attempts, cleanup and limits. USER-REVIEW.md explains what
is in the app's source versus the isolated phone installation and how to try it.

The final gate is `checkpoint-stop.json`. Verify its hashes before a subsequent
approved change. Keep old receipts/artifacts immutable; a later checkpoint must
archive bound inputs before editing and use its own run directory/approval. Do not
rerun this completed stage automatically or reopen the old holds below. PAUSE is
not active; the final receipt's stopForReview is the review boundary.

Recommended next work, only after user review: hands-on accessibility/audible-media
checks and fictional large-library performance, followed by an explicitly approved
normal-app update with a verified backup/recovery plan. No private-vault reads,
production installation, model changes, paid calls or Git mutation are authorized
by completion of this checkpoint. The 28 GiB cap retains little extra headroom;
check resources before any new build and discuss space if needed.

## Historical resume instructions (completed, do not dispatch)

## Current continuation — supersedes the older instructions below

Current state: PAUSE is active again for a device-unlock hold, not a storage hold.
Phone attempt 1789873053910253000 exited -15 before tests started. The worker is
stopped and the simulator shut down. Verify the latest resource-hold-*.json hashes
before editing, unlock the phone and check resources/archives. Then archive PAUSE
and rerun test-phone with the existing signed products if bindings still match.
Allow 5–10 minutes for device tests, capture review and completion, absent failures.

The user approved 28 GiB on 20 September; resource-amendment-28.json records it.
The original baseline and 10 GiB reserve remain. Do not change frozen CP2 approvals,
runner or receipt. Final saved-source checks already passed:

| Check | Run |
| --- | --- |
| Native 29/29, no skips/runtime warnings | 1789872690275695000 |
| Simulator UI 10/10, no skips/runtime warnings | 1789872760870055000 |
| Production-entrypoint build-only | 1789873022274113000 |
| Isolated signed phone build | 1789873036048888000 |

Seven critical simulator captures were inspected in
final-simulator-review-1789872760870055000 (21 exported PNGs). No source changes
are planned before finishing the device check; any invalidate these bindings.

1. Inspect owned processes and receipt/log for phone UI 1789873053910253000 before
   dispatching anything. It stopped at destination preflight because the phone
   relocked; no tests ran. Ask the user to unlock the connected phone. Confirm no
   unexpected worker is running before launching a fresh attempt.
2. `check.py resources` and `check.py verify`; original accounting and all 119
   historical archive bindings must pass. Verify any saved-hold hashes before edits.
   Archive any PAUSE only after the worker exits and these gates pass.
3. If the phone attempt was stopped, use `check.py test-phone`. The existing signed
   products may be reused only if the runner's preparation/product bindings match.
   Rebuild only if needed. Never install or launch real Remember. Isolated bundle:
   SimpleStudio.Remember.SourceBrowserUI, display name Evidence Check.
4. Require ten phone UI passes, zero skips/failures; inspect runtime warnings.
   Export completed xcresult PNGs to final-phone-review-RUNID and inspect image/text
   originals, preview return, current River, largest text, voice finish/replay and
   video. Silent fixtures do not check speaker quality/Bluetooth/calls; automation
   is not a human VoiceOver audit.
5. Update docs to actual outcome, then write the final receipt:
   `check.py checkpoint --unit-run 1789872690275695000 --ui-run 1789872760870055000 --phone-run PHONE_RUN --build-run 1789873022274113000`.
   Verify its hashes and worker exit. Stop for review; no production deployment or
   model experiment. Source changes require appropriate reruns before this gate.

Five follow-up/three inherited Python tests, 119 archive bindings and git diff
--check passed. All check.py commands refer to the source-browser-media runner.
Pause handling at the end of this file remains applicable.

## Historical instructions from the superseded 26 GiB resource stop

Read STATUS.md, REPORT.md and PLAN.md first. PAUSE is present; no completion receipt
exists. The initial nine phone tests passed before the newest playback/layout fixes.
Do not treat that device result or the interrupted seven-case log as final approval.

1. Obtain 2–3 GiB more free space under the existing 26 GiB ceiling, or explicit
   approval for a proposed 28 GiB ceiling. Retain the original baseline and 10 GiB
   reserve. `check.py resources` is read-only while paused. Do not delete unrelated
   files or rewrite old approvals. If a higher cap is approved, record a NEW
   follow-up approval and scoped harness override; the frozen CP2 runner/approval/
   receipt must remain unchanged. Test the new guard; retain whole-Mac accounting.
2. Verify all 119 archives with `check.py verify`; run Python unittest discovery in
   source-browser-media (2 tests) and source-browser-ui (3 resource guard tests).
   Inspect owned processes and phone lockState. Last phone check was unlocked, but
   verify again. Archive PAUSE only after these gates are resolved.
3. `check.py prepare-fixture`, `check.py test-unit`, `check.py test-ui`.
   Required totals: 29 native and 10 UI tests, zero skips/failures. Earlier native
   run `1789871460989703000` predates the final finished-player cleanup and diagnostic
   message edit; refresh copied inputs. No more speculative code changes are
   planned—first finish verification of the saved sources.
4. Inspect completed UI captures: visible image canvas before Close; source visible
   afterward; current River return; full large-text scope label; voice finish/replay;
   video progression. Interrupted run `1789871524122626000` passed seven media cases
   in its log, then received SIGTERM from the resource guard. Its xcresult lacks
   Info.plist and cannot export captures. Keep it as an interrupted attempt, not a
   pass. Do not weaken assertions or infer visual correctness from navigation.
5. `check.py prepare`, `check.py build` checks the full production entrypoint without
   launching/installing it. Then `check.py prepare-fixture`, `check.py build-phone`,
   `check.py test-phone`. Phone commands use only isolated Evidence Check bundle
   SimpleStudio.Remember.SourceBrowserUI, no shared groups or real memories. Signed
   build/fixture bindings must match; never reuse stale products. Keep phone awake.
6. Review completed phone screenshots and runtime warnings. Expect ten UI cases,
   including brief recording finish/replay. Check no audio-session main-thread
   warning recurs. Silent fixtures do not test speaker quality, Bluetooth or calls.
7. Update report/status/resume/docs before writing the final immutable receipt:
   `check.py checkpoint --unit-run ID --ui-run ID --phone-run ID --build-run ID`.
   It requires final-source 29/10/10 passes plus a production-entrypoint build and
   current signed products. Stop for review; no real-app deployment/model work.

All check.py paths above refer to scripts/provenance-first/source-browser-media/check.py.
Outputs: Evaluation/ProvenanceFirst/runs/source-browser-media/. Report contains the
attempt history; old CP2's completion record and archived inputs remain immutable.

Pause at any time: create PAUSE in this directory; the monitor stops owned work at
its next boundary. Wait for worker exit and call `check.py save-hold` before telling
the user it is safe to close/disconnect. Never mutate Git.
