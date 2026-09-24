# Search transition fix installed — 23 September 2026

## Outcome

Updated the main `SimpleStudio.Remember` app in place on the physical iPhone 17,
iOS 27.0 (24A437). The library ScrollView stays mounted while search opens/closes,
and uses unfiltered library items so search results cannot reset its scroll offset.
The content layers crossfade for 0.2 seconds; Reduce Motion disables that added
animation. Native search/keyboard transitions and compact menu behavior remain.

No uninstall, restore, model/threshold change, forced regrouping or AI request.
App, share-extension, team and app-group signatures were checked, and the bundled
D3 model remains present. All personal memory rows, originals and history were
verified unchanged. Remember was reopened after verification for user review.

## Verification

| Check | Result |
|---|---|
| Focused repeated-dismissal regression | 1 passed |
| Full simulator search UI suite | 8 passed |
| Native search/source tests | 18 passed |
| Signed normal-entrypoint app and extension build | Passed |
| Pre-install backup | 184 files verified; SQLite healthy; 11 migrations match |
| Launch safety | 8 indexed memories, no pending captures/inbox/video work, cloud assistance off |
| Physical-phone repeated-dismissal/menu smoke | 1 passed; 0 failed/skipped/reported runtime warnings |
| Post-install snapshot | 185 files verified; SQLite healthy |
| Memory rows | All 8 unchanged |
| Provenance history | All 171 events unchanged |
| Original files | All 8 byte-identical |
| Swift parse and `git diff --check` | Passed |

The simulator regression preserves the same visible card's vertical position
within 2 points across blank/no-match/blank search sessions in a scrolled fictional
library. It also checks that the hidden browse layer cannot receive touches and
the capture button is absent during search. The full UI suite covers filters,
reset/help, current and historical passages, Back state, empty library, dark large
text and no duplicate Threads search action.

The phone smoke repeats those three query sessions, verifies capture-button
position on return (within 2 points), and exercises both menu filters and Reset.
It uses a fictional no-match query; it never opens, edits or deletes personal
sources or exports personal screenshots. The test passed on its first attempt.
The test duration was 40.085 seconds. These are engineering interaction checks,
not measured frame-rate/perceptual smoothness or a new retrieval-quality benchmark.
Reduce Motion uses the system environment value but has no separate automated
case in this checkpoint. Compiler/tool warnings are distinct from xcresult's
reported runtime-warning count.

## Commands and receipts

Implementation commands:
`python3 -B scripts/provenance-first/search-transition/check.py`
with actions `prepare`, `regression`, `ui`, `unit`.

Simulator receipts under `Evaluation/ProvenanceFirst/runs/search-transition/`:

- Focused regression: `1790175870875792000.xcresult`.
- Full UI suite: `1790175981924628000.xcresult`.
- Native tests: `1790176196105775000.xcresult`.
- Exported fictional screenshots in `regression-captures/` and `final-captures/`;
  scrolled-library, ordinary light search and dark accessibility layouts inspected.

Deployment commands:
`python3 -B scripts/provenance-first/search-transition/deploy.py`
with actions `prepare`, `build`, `backup`, `inspect-backup`, `install`, `smoke`,
`post-backup`, `compare`, `launch`, then `finish` after saving documentation.

Private ignored deployment root:
`Evaluation/ProvenanceFirst/runs/search-transition-deployment/`.

- Signed build operation: `1790176263014150000`.
- Backup: `backup-1790176313293979000`.
- Install operation: `1790176403192981000`.
- Phone smoke operation: `1790176429444401000`.
- Phone result: `smoke-1790176426802780000.xcresult`.
- Post snapshot: `post-install-1790176492795897000`.
- Data preservation proof: `preservation.json`.

Both backups are private/ignored with inventory and SHA-256 verification.
Database checks read copies, not the live database. No personal source text is
included in reports. Recovery is not automatic; retain both snapshots and obtain
explicit direction before a restore or downgrade.

## Cleanup and stop boundary

Only the two specifically approved project-only cleanup lists were removed:
six old diagnostic build folders, then 54 compiler-cache/intermediate folders.
See [batch 1](../search-transition/CLEANUP.md) and
[batch 2](../search-transition/CLEANUP-2-RESULT.md) for exact paths and observed
recovery (about 0.65 and 2.38 GiB respectively). Deleted generated files are not
in Trash; affected older builds can regenerate them. Research result records,
source/models and all phone backups remain. No outside-project deletion or Git
state change. The original accounting baseline, 32 GiB limit and 10 GiB free
reserve remain unchanged; final resource/binding checks are in checkpoint-stop.json.

Production change: `Remember/Remember/ContentView.swift`. Regression:
`Remember/RememberUITests/UnifiedMemorySearchUITests.swift`. Support:
`scripts/provenance-first/search-transition/`, checkpoint reports, and the unified
search/provenance documentation. Stop for user review; no further cleanup or model
experiments are authorized by this completed deployment.
