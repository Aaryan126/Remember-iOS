# Search spacing deployed — 24 September 2026

Installed the tested search-header spacing update in the main Remember app on
the connected physical iPhone 17 (iOS 27.0, 24A437). No uninstall, forced
regrouping, AI call, preference change or user-source edit.

## Safety and cleanup

- Removed only the four expressly approved compiler-cache/intermediate folders;
  about 585 MiB net was recovered. See [exact cleanup record](CLEANUP.md).
- Preserved prior checkpoint archives, signed products, models and backups.
- Verified all 107 prepared source bindings against the simulator-tested inputs.
- Kept the 32 GiB cumulative limit and 10 GiB reserve unchanged. Backup and
  install dispatch were each briefly blocked by fluctuating free space; guarded
  retries passed after space recovered. No additional files were deleted.
- Shut down the completed fictional test simulator. No physical-phone data was
  removed.

## Verification

All commands use `python3 scripts/provenance-first/search-spacing/deploy.py`:

| Command | Outcome |
| --- | --- |
| `prepare` | Passed; archived baseline and source binding checks |
| `build` | Signed normal app/share extension and bundled local model verified |
| `backup`, `inspect-backup` | 186 files verified; SQLite healthy, 11 migrations match, safe-launch checks pass |
| `install` | Updated `SimpleStudio.Remember` in place; no uninstall |
| `smoke` | First UI-automation startup timed out before test execution; retry passed 1/1 with no skips or reported runtime warnings |
| `post-backup`, `compare` | 187 post-install files verified; all 8 memory rows, 171 historical events and 8 original files unchanged |
| `launch` | Updated Remember reopened successfully |

`git diff --check` and a Swift syntax parse of the deployment smoke test also
passed. The final `finish` command binds these records into `checkpoint-stop.json`.

Phone smoke checks title/count/menu centers (within 1 point), 44-point minimum
button target, search-field-to-header distance, repeated focus/dismissal, filter
menu/reset and session behavior. It uses an artificial no-match query and never
opens a personal source. The preceding simulator suite passed 10/10, including
default-grid equal gaps, light/dark, keyboard open/closed and large-text checks.

Private receipts are under `Evaluation/ProvenanceFirst/runs/search-spacing-deployment/`:

- Build operation: `1790221089429932000`.
- Pre-backup: `backup-1790221169998852000`.
- Install operation: `1790221263704672000`.
- Passed smoke: `smoke-1790221364260859000.xcresult`.
- Post-backup: `post-install-1790221426661021000`.
- Data comparison: `preservation.json`.

The new deployment wrapper and smoke test are in
`scripts/provenance-first/search-spacing/`; documentation updated in
`docs/unified-memory-search.md`, `docs/provenance-first.md`, and the spacing
implementation report. No Git state was changed. Native inset changes in future
iOS versions should re-run the layout checks.
