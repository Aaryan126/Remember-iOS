# Project-only cleanup proposal — awaiting approval

24 September 2026. **Nothing listed here has been deleted.** Approval applies
only to these 35 exact directories, not their parents or any other paths.

## Recommendation and measured space

| Group | Allocated KiB | Approx. GiB |
|---|---:|---:|
| App-container copies from 12 older phone snapshots | 2,578,280 | 2.46 |
| 15 generated test/deployment project copies | 1,023,808 | 0.98 |
| 8 redundant generated dependency copies | 177,792 | 0.17 |
| **Total** | **3,779,880** | **3.60** |

That is approximately 3.87 decimal GB. Latest free-space measurement was
8,956,276 KiB (8.54 GiB). If all measured allocation is reclaimed, free space
would reach approximately 12.15 GiB. APFS shared blocks and concurrent disk use
mean actual recovery may be lower. Measure after cleanup; do not promise that
this alone guarantees enough space for both testing and deployment.

## What is lost, and what remains

- The 12 older snapshot **app containers** would be permanently removed, not
  moved to Trash. Those exact historical full-app restore points would no longer
  be available. Their manifests, inventory metadata, inspection reports, logs,
  shared-group snapshots and preservation reports remain. These records are
  evidence of prior checks, not replacements for a restorable full snapshot.
- Both complete snapshots from the **latest installed version** remain, including
  originals and databases. Every file was rehashed against its verified manifest:
  187 files in the pre-install snapshot and 188 in the post-install snapshot.
- Generated project/dependency copies can be recreated using the preserved
  source archives and preparation scripts. They include copied model assets;
  original model assets and archived source inputs remain. Historical generated
  paths cannot be inspected or rebuilt in place until regenerated. Exact older
  builds require the corresponding archived source, not today's source.
- Keep every signed app build, every test-result bundle, all motion recordings,
  research models/datasets/predictions, documentation, archived baselines and
  checkpoint receipts.
- Keep the active `search-overlay` project/dependency/partial build and its
  baseline archive, and the entire latest `search-dismissal-deployment` run.
- Specifically keep `runs/source-browser-media/dependency`: the signed-build
  preparation/verification scripts still use its GRDB copy. Keep the canonical
  `runs/answer-support/native-dependency/GRDB` and the reused
  `runs/main-app-deployment/build/ModuleCache.noindex` too.
- No files on the iPhone, files outside this project, Git metadata, source code,
  original model assets or user documents are deletion targets.

## Read-only checks completed

`du -sk` measured each target. `git ls-files -z` found no tracked files under any
target. All targets are real directories whose resolved paths remain exactly
inside this project; none contain symlinks or nested `.git` directories. None
directly overlaps a file bound by the latest deployment completion receipt.
Current preparation/build scripts were inspected for shared dependencies, which
are excluded. Latest backup manifests were independently rehashed successfully.

Before approved deletion, repeat target validation, check that no build/backup
worker is using them, and confirm the latest retained snapshots still verify.
Use exact paths, not wildcards. Preserve the 10 GiB reserve and 32 GiB growth cap.

## Exact deletion list

All paths below are relative to:

`/Users/aaryan/Desktop/Gemini Hackathon/Evaluation/ProvenanceFirst/runs/`

Only the named final directory and its contents are proposed for removal.

| Exact relative directory | Allocated KiB |
|---|---:|
| `main-app-deployment/backup-1789918416575368000/app` | 212564 |
| `main-app-deployment/post-install-1789918690324493000/app` | 213316 |
| `unified-search-deployment/backup-1790164868387628000/app` | 213320 |
| `unified-search-deployment/post-install-1790165013892788000/app` | 214072 |
| `search-options-deployment/backup-1790173846755269000/app` | 214112 |
| `search-options-deployment/post-install-1790174087200263000/app` | 214864 |
| `search-transition-deployment/backup-1790176313293979000/app` | 214864 |
| `search-transition-deployment/post-install-1790176492795897000/app` | 215616 |
| `search-motion-deployment/backup-1790178676592258000/app` | 215616 |
| `search-motion-deployment/post-install-1790178884730424000/app` | 216368 |
| `search-spacing-deployment/backup-1790221169998852000/app` | 216408 |
| `search-spacing-deployment/post-install-1790221426661021000/app` | 217160 |
| `main-app-deployment/project` | 68084 |
| `source-browser-ui/project` | 68056 |
| `source-browser-ui/dependency` | 22224 |
| `source-browser-media/project` | 70272 |
| `unified-search/project` | 68112 |
| `unified-search/dependency` | 22224 |
| `unified-search-deployment/project` | 68116 |
| `search-options/project` | 68112 |
| `search-options/dependency` | 22224 |
| `search-options-deployment/project` | 68116 |
| `search-transition/project` | 68116 |
| `search-transition/dependency` | 22224 |
| `search-transition-deployment/project` | 68120 |
| `search-motion/project` | 68116 |
| `search-motion/dependency` | 22224 |
| `search-motion-deployment/project` | 68120 |
| `search-spacing/project` | 68116 |
| `search-spacing/dependency` | 22224 |
| `search-spacing-deployment/project` | 68120 |
| `search-compact/project` | 68116 |
| `search-compact/dependency` | 22224 |
| `search-dismissal/project` | 68116 |
| `search-dismissal/dependency` | 22224 |

The retained latest full snapshots are:

- `search-dismissal-deployment/backup-1790223832209990000`
- `search-dismissal-deployment/post-install-1790224085878947000`

After approval and cleanup, report the measured net recovery before resuming the
pending animation comparison. Further deletion requires a new exact proposal.
