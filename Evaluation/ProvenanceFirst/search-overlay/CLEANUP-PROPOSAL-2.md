# Additional project-only cleanup — approval required

Nothing in this proposal has been deleted. The previous 35-target approval was
fully used; this is a new, separate request.

Measured allocated size: **2,448,240,640 bytes (2.28 GiB)**. Actual free-space
gain can differ because of APFS sharing/snapshots. Free space after stopping the
simulator was approximately 9.84 GiB, below the retained 10 GiB test/build floor.

All paths below are relative to the repository root. Read-only checks confirmed
that each exists, resolves inside this project, is not a symlink, and contains
no Git-tracked files. Revalidate immediately before any approved deletion.

## Exact proposed targets

| Path | Allocated bytes |
|---|---:|
| `Evaluation/ProvenanceFirst/runs/search-transition-deployment/build` | 172,969,984 |
| `Evaluation/ProvenanceFirst/runs/search-spacing-deployment/build` | 173,088,768 |
| `Evaluation/ProvenanceFirst/runs/search-motion-deployment/build` | 172,945,408 |
| `Evaluation/ProvenanceFirst/runs/unified-search-deployment/build` | 143,921,152 |
| `Evaluation/ProvenanceFirst/runs/search-options-deployment/build` | 144,117,760 |
| `Evaluation/ProvenanceFirst/runs/source-browser-ui/build` | 148,774,912 |
| `Evaluation/ProvenanceFirst/runs/source-browser-media/build` | 164,130,816 |
| `Evaluation/ProvenanceFirst/runs/history-recovery/build` | 54,673,408 |
| `Evaluation/iOS27/safeguards/build` | 250,597,376 |
| `Evaluation/iOS27/embedding-recovery/build` | 240,599,040 |
| `Evaluation/iOS27/embedding-recovery-v2/build` | 240,775,168 |
| `Evaluation/iOS27/precision/build` | 104,603,648 |
| `Evaluation/ProvenanceFirst/runs/search-overlay/guarded-native-motion.mp4` | 65,921,024 |
| `Evaluation/ProvenanceFirst/runs/search-overlay/native-prepare-motion.mp4` | 64,897,024 |
| `Evaluation/ProvenanceFirst/runs/search-overlay/overlay-motion-retry.mp4` | 78,426,112 |
| `Evaluation/ProvenanceFirst/runs/search-overlay/overlay-motion.mp4` | 3,645,440 |
| `Evaluation/ProvenanceFirst/runs/search-overlay/query-reset-motion.mp4` | 76,173,312 |
| `Evaluation/ProvenanceFirst/runs/search-overlay/shared-scroll-motion.mp4` | 77,017,088 |
| `Evaluation/ProvenanceFirst/runs/search-overlay/stable-scroll-motion.mp4` | 70,963,200 |

## Consequences and preservation

- The first 12 targets are superseded generated build outputs, including old
  signed test/app binaries and compiler artifacts. They can be rebuilt from
  retained code and dependencies, but the exact old signed binaries would be
  unavailable; rebuilding may need compatible SDKs and renewed signing.
- The last seven targets are recordings of rejected animation experiments.
  Those original videos would be permanently unavailable. Their logs, reports,
  result bundles and already-extracted contact sheets remain.
- Preserve **both latest full phone backups**, the latest installed app's
  `search-dismissal-deployment` signed build, its project, and all receipts.
- Preserve the current simulator build, current candidate, new baseline/fix
  recordings (`traced-baseline.mp4`, `scoped-removal.mp4`,
  `scoped-full-suite.mp4`), frame traces and all tests/results.
- Preserve `main-app-deployment/build/ModuleCache.noindex`, both retained GRDB
  dependency trees, source code, models, datasets, evaluation predictions and
  reports. No app data or anything outside this project is proposed for deletion.
- No Git state changes. No lowering of the free-space floor or cumulative cap.

After approval: delete only these exact validated targets, measure actual space,
then rerun the full UI suite and perform a freshly backed-up device deployment
if the unchanged resource gates permit. If headroom is still insufficient, stop
and report it; approval does not authorize additional cleanup.
