# Source browser follow-up: media, navigation and accessibility

Approved by “Carry on with next stuff”, following checkpoint 2's recommendation.
Estimate: 1–2 hours of active work, subject to device/build issues. Stop for review
at completion; do not deploy over production Remember or start model work.

1. Verify and archive checkpoint 2's bound inputs before changing any of them. Keep
   its receipt/logs/results intact; new results belong to this follow-up.
2. Exercise fictional image, silent audio, silent video and text originals using
   the real source browser. Verify inline actions do not trigger adjacent buttons,
   Quick Look dismissal returns to the same source, corrupt playback fails honestly,
   and leaving/backgrounding playback does not auto-resume it.
3. Seed a replayed fictional project snapshot, without running organization. Check
   saved evidence → explicitly current River → Back → same evidence/search.
4. Make large-text scope and caveats easier to scan without capping Dynamic Type.
   Check default light and maximum accessibility dark layouts. Automated checks and
   screenshots are not a substitute for a human VoiceOver usability audit.
5. Run native regressions, simulator UI, production-entrypoint build-only, then
   separately bundled phone UI; inspect captures and document uncovered behavior.

The user approved 28 GiB on 20 September after the original 26 GiB stop. Use the
new scoped approval, original accounting baseline and 10 GiB reserve. No unrelated
cleanup, Git mutation, network models or personal-vault
access. New run directory, same isolated diagnostic bundle, no shared app groups.
Each command is bounded and monitored. A PAUSE file here stops dispatch and owned
workers at the next boundary; save receipts before reporting it safe to close.
