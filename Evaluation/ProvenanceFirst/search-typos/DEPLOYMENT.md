# Typo-search iPhone deployment — 24 September 2026

The user explicitly authorized installation after reviewing readiness. The
reviewed signed app and Share Extension were installed in place as
`SimpleStudio.Remember`; product/source bindings were verified before each step.
No production code was changed or rebuilt during deployment. Remember is open
on the physical iPhone 17 (iOS 27).

## Checks and preservation

All commands use `python3 -B scripts/provenance-first/search-typos/deploy.py`:

| Action | Result |
| --- | --- |
| `resources` | Passed; original 32 GiB cumulative ceiling and 10 GiB reserve retained. |
| `backup` | Fresh app/shared-container backup, 193 files verified. |
| `inspect-backup` | SQLite integrity and 11 migrations matched; launch preflight passed. |
| `install` | In-place installation succeeded; no uninstall or data reset. |
| `smoke` | Third attempt passed, 1/1 tests, zero failures/skips/reported runtime warnings. Earlier failures are recorded below. |
| `post-backup` | Fresh post-install snapshot, 196 files verified. |
| `compare` | Healthy SQLite; all 8 memory rows and 8 original files unchanged, all 171 history events unchanged. |
| `launch` | Updated Remember opened successfully. |

The smoke covers repeated native search opening/closing, keyboard and clear
behavior, header alignment, both filters and reset. Typo matching and exact
historical passages were verified in the prior source-bound simulator/native
checks; the phone smoke does not inspect private passages or establish a new
on-device retrieval-quality/performance benchmark. No AI action was invoked.

## Phone-test attempts

1. `smoke-1790252923871585000.xcresult`: failed with “Not authorized for performing
   UI testing actions.” Orientation changes also appear in the log.
2. `smoke-1790252992981005000.xcresult`: the capture-button-return assertion failed
   after closing search. The log records a notification interruption near that
   interaction; this correlation alone does not prove the failure's cause.
3. `smoke-1790253094292265000.xcresult`: passed on the same installed build and
   unchanged harness. No assertion was weakened and no product workaround added.

The user was asked to keep the phone unlocked, in portrait and idle for the retry.
All attempts remain in the ignored `runs/search-typos-device` directory.

## Receipts

- Installation operation: `1790252884301518000`.
- Fresh backup: `backup-1790252821016172000`.
- Post-install snapshot: `post-install-1790253190896765000`.
- Passing smoke operation: `1790253096562178000`.
- `preservation.json` contains the aggregate comparison and backup bindings.
- `ready-to-install.json` remains the immutable earlier readiness record; its
  report bytes are retained in `runs/search-typos-device/readiness-report.md`.

Private backups, logs and test artifacts remain local and ignored. Git state was
not changed. Deployment changes are limited to the new `deploy.py` wrapper,
status documentation and receipts; no additional app code change was needed.
