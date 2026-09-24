# Native search motion follow-up

23 September 2026. The user still observed abrupt focus/dismissal after the
previous transition deployment. That checkpoint proved final positions and
navigation, not perceptual smoothness; its success did not resolve this report.

## Evidence and correction

Read-only comparison with the earlier library implementation showed that empty
search focus originally left the library visible. The unified search changes
instead inserted a second ScrollView and results heading as soon as focus began.
The first correction added a custom fade while native search/keyboard animation
was also running. A simulator recording of that installed implementation confirms
the extra heading and card-layout change during empty focus.

The follow-up:

- Keeps the same browsing grid visible on empty focus and dismissal.
- Shows the results layer only for an active query/filter request from the library
  model, not merely because the search bar has focus.
- Removes the custom content crossfade; iOS owns search/keyboard motion.
- Keeps the unfiltered browsing grid mounted so populated searches still preserve
  the original scroll position when closed.
- Moves the search options state to the session owner. Clearing/retyping a query
  preserves filters, while cancelling search resets them. Opening a saved passage
  with a retained query does not reset the options.
- The compact search-options icon appears with results after typing, not during
  empty-field focus. No search/AI/model/persistence behavior is otherwise changed.

## Checks so far

Commands use `python3 -B scripts/provenance-first/search-motion/check.py`.
The previous installed checkpoint was archived with `preserve` before edits.

- `prepare`: passed with the existing fictional long-library launcher.
- `regression`: passed, run `1790177198728631000`; now requires the browse grid
  to remain hittable and the extra results header/menu to remain absent on empty
  focus. A populated query must still own interaction. Repeated dismissal still
  preserves the same card position within 2 points.
- `ui`: **9 passed**, no failures/skips/reported runtime warnings, run
  `1790177285448192000`. Includes a new clear/retype/filter/cancel regression and
  the existing passage, history, empty-library and accessibility cases.
- `unit`: **18 passed**, no failures/skips/reported runtime warnings, run
  `1790177486995643000`.
- Swift frontend parse and `git diff --check`: passed.

Private ignored artifacts: `Evaluation/ProvenanceFirst/runs/search-motion/`.
`before.mp4` and `after.mp4` record fictional simulator UI, not personal phone
content. Contact sheets inspected: `before-overview.png`, `before-focus.png`,
`after-overview.png`, `after-focus-39.png`. These show the new grid remaining in
place through native keyboard movement without inserting a second results layout
until typing. The first attempted after-focus crop captured fixture startup and
is retained, but is not transition evidence. Recordings are qualitative simulator
evidence, not a measured frame-rate guarantee or a physical-phone smoothness test.

## Phone status and limits

This correction is now installed and the phone smoke/data-preservation checks
passed. See the [deployment report](../search-motion-deployment/REPORT.md). No
additional deletion was required. Stop for the user's assessment of actual motion.

Historical storage hold: `deploy.py prepare` was attempted after
verification and stopped before preparing/building/installing because the 1.5 GiB
working reservation would cross the 10 GiB reserve. Approximately 11.1 GiB was
free; the user was asked to free about 1 GiB. No dependent build or phone action
was attempted after that failed prerequisite. All owned workers have stopped.
Resume with successful `deploy.py prepare`, then `build`, fresh `backup` and
`inspect-backup`, `install`, `smoke`, `post-backup`, `compare`, `launch` and `finish`.
Do not reuse an older phone backup or overwrite previous deployment receipts.

Separate deployment tooling and a
normal-app smoke test are prepared under `scripts/provenance-first/search-motion/`.
The phone smoke requires the browsing grid during empty focus, no extra results
menu, consistent capture-button position after closing, and working query filters.

The original storage baseline, 32 GiB cumulative cap and 10 GiB free reserve remain
unchanged. No further deletion, Git mutation or paid call was performed. Personal
phone access was limited to the approved backed-up deployment and navigation smoke.
Old failed/limited transition evidence is
preserved rather than overwritten. If deployment preparation lacks its 1.5 GiB
working reservation, stop and request headroom; do not silently lower it.
