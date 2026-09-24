# Native empty-search behavior — phone deployment

23 September 2026. Updated `SimpleStudio.Remember` in place on the physical
iPhone 17, iOS 27.0 (24A437). No uninstall, restore, model/threshold change,
regrouping, AI request, Git state change or additional cleanup.

## Change

Empty search focus now leaves the browsing grid visible. Results and the compact
options menu appear after typing, instead of inserting a separate results layout
during native focus animation. The custom crossfade is removed; native iOS search
and keyboard animation remain. Filter state survives clearing/retyping but resets
on closing search. Populated searches retain the browsing scroll position.

The prior deployment's final-position tests did not establish perceived smoothness.
The user's continued report was valid. This follow-up added empty-focus assertions
and before/after fictional simulator recordings; subjective motion still requires
user confirmation on their phone, not just another passing test.

## Validation and receipts

Earlier implementation verification: 9 simulator UI cases and 18 native tests
passed, with no failures/skips/reported runtime warnings. See the
[implementation report](../search-motion/REPORT.md) for recordings and exact runs.

Deployment commands used
`python3 -B scripts/provenance-first/search-motion/deploy.py` in gated order:
`prepare`, `build`, `backup`, `inspect-backup`, `install`, `smoke`, `post-backup`,
`compare`, `launch`, then `finish` after documentation.

Private ignored run root: `Evaluation/ProvenanceFirst/runs/search-motion-deployment/`.

- Signed app/extension build: passed, operation `1790178625219603000`.
- Verified signing identities/app group and bundled D3 model.
- Pre-install backup: `backup-1790178676592258000`, 185 files verified.
- SQLite integrity passed; all 11 expected migrations matched. Eight indexed
  memories, no pending capture/inbox/video work; cloud assistance off.
- In-place install: operation `1790178793101903000`.
- Phone smoke: operation `1790178814730407000`, result
  `smoke-1790178812126324000.xcresult`; **1 passed**, no failures/skips/reported
  runtime warnings. Test duration 39.745 seconds, first attempt passed.

The phone case repeats blank/no-match/blank search sessions, requiring a hittable
browsing grid and no results menu during empty focus. It verifies the capture
button returns to its original position within 2 points and tests both menu
filters and Reset. It does not open or modify personal sources or export personal
screenshots. It is not a measured frame-rate guarantee or a new quality benchmark.

Post-install snapshot: `post-install-1790178884730424000`, 186 files verified.
`preservation.json` confirms healthy SQLite, all 8 memory rows unchanged, all 171
history events unchanged and all 8 originals byte-identical. Remember was reopened
after the checks. `git diff --check` passed. Final signatures, backup hashes,
resources and the passing phone test are gated by `finish` and saved in this
directory's `checkpoint-stop.json`.

## Limits and recovery

Original storage baseline, 32 GiB cumulative cap and 10 GiB reserve retained. The
earlier preparation hold was resolved by available free space, not by lowering
the 1.5 GiB working reservation. No further files were deleted. Both backups are
private/ignored with SHA-256 inventories; database inspection reads copies only.
Recovery is not automatic and requires explicit direction before a restore.

Production files: `ContentView.swift`, `UnifiedMemorySearchView.swift`. Regression
tests: `UnifiedMemorySearchUITests.swift`. Supporting scripts and records are in
the search-motion checkpoint directories. Stop for user review after verification.
