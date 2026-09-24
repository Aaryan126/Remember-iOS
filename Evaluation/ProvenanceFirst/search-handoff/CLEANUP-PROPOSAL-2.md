# Project-only cleanup proposal — awaiting approval, 24 September 2026

Nothing has been deleted for this proposal. Previous approvals are exhausted.
Choose A only, or A+B. Any approval covers only the nine exact targets below;
no recursive deletion of their parent project/run folders is proposed.

All paths below are relative to:
`/Users/aaryan/Desktop/Gemini Hackathon/Evaluation/ProvenanceFirst/runs/`.

## A — incomplete recording payloads and an obsolete index

| Exact target | Allocated bytes | MiB | Consequence |
|---|---:|---:|---|
| `search-handoff/edge-top.mp4.sb-61fc4779-9erjtv` | 46,292,992 | 44.15 | Unfinalized recording payload from the interrupted edge-effect trial. ffprobe cannot read it: missing moov atom. Removing it also rules out attempting later recovery of its partial frames. |
| `search-handoff/final-ui.mp4.sb-61fc4779-wpPM5Z` | 65,331,200 | 62.30 | Unfinalized payload from the earlier interrupted retained-host trial. Same ffprobe failure. Keep the separate final-ui.mp4, traces and logs; do not assume the payload duplicates that finalized file. |
| `search-overlay/overlay-motion.mp4.sb-61fc4779-rNnViX` | 3,641,344 | 3.47 | Unfinalized older recording payload; same ffprobe failure. |
| `answer-support/native-build/Index.noindex` | 23,339,008 | 22.26 | Rebuildable IDE symbol index from an earlier isolated answer-support build. Not the active search build cache or any build product. |

**A total: 138,604,544 bytes / 132.18 MiB.** Recommended low-cost cleanup.

## B — optional recordings of superseded animation trials

| Exact target | Allocated bytes | MiB |
|---|---:|---:|
| `search-handoff/top-dark.mp4` | 51,720,192 | 49.32 |
| `search-handoff/stable-host-dark.mp4` | 52,273,152 | 49.85 |
| `search-handoff/stable-layout-top.mp4` | 47,431,680 | 45.23 |
| `search-overlay/scoped-full-suite.mp4` | 76,472,320 | 72.93 |
| `search-overlay/scoped-removal.mp4` | 76,529,664 | 72.98 |

**B total: 304,427,008 bytes / 290.32 MiB.** These are real historical debugging
recordings, not caches. Their full playback would be permanently lost. Preserve
existing extracted frame sheets, traces, test bundles and written findings, but
those do not replace every recorded frame. The first three document rejected
handoff trials; the last two document an older approach already represented by
retained baseline and focused recordings.

## Space and recommendation

- **A+B: 443,031,552 bytes / 422.51 MiB / approximately 0.41 GiB.**
- Last measured free space: **18,103,898,112 bytes / 16.86 GiB**. It has recovered
  since the earlier storage stop; further deletion may not be needed to resume.
- The whole repository occupies approximately **5.55 GiB** by allocated-size
  inventory. There is not a multi-gigabyte disposable cache left in this scope.
- Recommend A; add B if full playback of the superseded trials is not worth
  retaining. Do not sacrifice source, research evidence or current caches for
  a larger headline recovery figure.
- Allocated sizes are not guaranteed net recovery on APFS. Concurrent system
  activity, sharing and snapshots can change the observed free-space difference.
- Deletion to reclaim space would be permanent, not moving files to Trash.

## Read-only checks and protections

All nine targets were checked to exist at literal, non-symlink paths inside this
project. They contain no Git-tracked files; all are ignored by Git. The index
contains no Git metadata. No build, simulator-recording or ffmpeg worker was
observed. Revalidate paths, sizes and worker state immediately before deletion.

Rehashed every manifest-listed file in the two protected newer phone backups:
189 files in `search-overlay-deployment/backup-1790230453931123000` and 192 in
`search-overlay-deployment/post-install-1790231053409891000`; all checks passed,
including the same eight original-file hashes. No phone backup is a target.

Preserve all app source, model assets, baseline source archives, research
datasets/predictions/ledgers, credentials, Git metadata, signed app/extension,
all backups and test result bundles. Also preserve the current
`unified-search/build` cache and shared phone module cache. Deleting those would
force the next verification to recreate them.

Retain the latest useful recordings (`bitmap-top.mp4`, `overlay-top-retry.mp4`,
`overlay-scrolled.mp4`) and older comparison references (`traced-baseline.mp4`,
`scoped-top-dark.mp4`). Keep all stills, traces, logs and reports.

After approval, delete only the selected exact paths, recheck the protected
backups and record actual net recovery. Then recheck the 10 GiB reserve and
32 GiB cumulative cap before preparing the current source and resuming debugging.
No phone installation until the animation fix passes visual and regression checks.
