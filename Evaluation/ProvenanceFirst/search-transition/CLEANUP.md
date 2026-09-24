# Approved project-only cleanup — 23 September 2026

The user approved these exact six generated diagnostic-build folders after seeing
their paths, sizes and rebuild trade-off. No other cleanup was authorized or done.

Paths relative to the repository root:

| Deleted directory | Allocated KiB before deletion |
|---|---:|
| Evaluation/iOS27/boundary/build/native | 699140 |
| Evaluation/iOS27/precision/build/native | 697444 |
| Evaluation/iOS27/stage1/build | 307696 |
| Evaluation/iOS27/readiness/build | 307076 |
| Evaluation/iOS27/embedding-trace/build | 307020 |
| Evaluation/iOS27/quality/build | 460220 |

Read-only preflight confirmed exact real paths inside the project, no tracked Git
files in those directories, no nested xcresult bundles, and no active matching
build/research process. Removal used explicit absolute paths with `rm -r`; the
initial `rm -rf` command was rejected before execution, then retried without force.

Total measured directory allocation: 2,778,596 KiB (2.650 GiB). Disk free space
immediately before/after was 11,211,336 / 11,890,952 KiB: observed net recovery
679,616 KiB (0.648 GiB), leaving 11.340 GiB free. The net recovery is not a guarantee
of exclusive file allocation: APFS sharing and concurrent disk changes can affect
it. The files are not in Trash; generated artifacts require rebuilding if needed.

Preserved: app source/production models, original model exports, research reports
and result records outside these build folders, all phone backups, current search
test/deployment products, dependency copies, `.git`, and all files outside the
project. Old diagnostic build verification/reruns may need regeneration of deleted
artifacts; no historical receipt was rewritten to disguise the cleanup.

The current search-transition resource check passed afterward. The original
accounting baseline, 32 GiB cumulative limit and 10 GiB free reserve were unchanged.
