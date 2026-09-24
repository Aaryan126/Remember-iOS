# Project-only cleanup — awaiting approval, 24 September 2026

**Nothing has been deleted.** This is a new proposal; prior cleanup approvals
are exhausted. Approve group A only, or both A and B. Approval covers only the
exact paths listed here, relative to `/Users/aaryan/Desktop/Gemini Hackathon`.

## Summary

| Group | Allocated size | Effect |
|---|---:|---|
| A — obsolete generated output and duplicate projects | 977,412,096 bytes / **932.13 MiB (0.91 GiB)** | Rebuildable output; preserve the current simulator cache and installed signed app. |
| B — two superseded phone restore points, optional | 450,174,976 bytes / **429.32 MiB (0.42 GiB)** | These older full backups would be permanently unavailable; newer verified backups remain. |
| Both | 1,427,587,072 bytes / **1.33 GiB** | Recommended for more working headroom if the older restore points are no longer needed. |

Measured free space: 11,123,703,808 bytes (**10.36 GiB**). If fully reclaimed,
both groups would bring it to approximately **11.69 GiB**. Actual recovery may
be smaller due to APFS shared blocks/snapshots or concurrent disk activity.
This is not a guarantee that every later build/install will fit. Recheck the
10 GiB reserve and 32 GiB cumulative guard after cleanup and before each step.

## A — exact generated targets

| Path | Allocated bytes | Consequence |
|---|---:|---|
| `Evaluation/ProvenanceFirst/runs/search-dismissal-deployment/build` | 479,707,136 | Old, superseded phone build and caches. Its binary would need rebuilding/re-signing to reinstall; byte-identical reproduction is not promised. Current installed build is elsewhere and retained. |
| `Evaluation/ProvenanceFirst/runs/search-dismissal-deployment/project` | 69,754,880 | Old generated deployment project; source archives, generator and receipts remain. |
| `Evaluation/ProvenanceFirst/runs/search-overlay/project` | 69,758,976 | Superseded generated simulator project; installed-source archive and current handoff project remain. |
| `Evaluation/ProvenanceFirst/runs/search-overlay/dependency` | 22,757,376 | Duplicate local dependency copy used by that old simulator project. Active handoff and shared GRDB copies remain. |
| `Evaluation/ProvenanceFirst/runs/search-overlay-deployment/build/Build/Intermediates.noindex` | 124,751,872 | Rebuildable phone compilation intermediates, not signed products. |
| `Evaluation/ProvenanceFirst/runs/search-overlay-deployment/build/ModuleCache.noindex` | 28,614,656 | Rebuildable private module cache; the separate shared phone-build module cache remains. |
| `Evaluation/ProvenanceFirst/runs/search-overlay-deployment/build/SDKExplicitPrecompiledModules` | 182,067,200 | Rebuildable private SDK modules. |

## B — exact older restore points, optional

| Path | Allocated bytes | Consequence |
|---|---:|---|
| `Evaluation/ProvenanceFirst/runs/search-dismissal-deployment/backup-1790223832209990000` | 224,702,464 | Permanently remove the older pre-install container snapshot, including its local inspection files/manifest. |
| `Evaluation/ProvenanceFirst/runs/search-dismissal-deployment/post-install-1790224085878947000` | 225,472,512 | Permanently remove the corresponding older post-install snapshot. |

These two were protected in the earlier cleanup, before a newer verified backup
pair existed. Removing them requires explicit new approval. They are not identical
whole containers: cache/OS files differ. Verification below concerns preserved
originals and memory/history records, not equivalence of every container file.

## Checks and protected data

Read-only audit: `python3 scripts/provenance-first/search-handoff/inspect-cleanup.py`.

- All nine targets exist, resolve to their literal directories inside the project,
  contain no `.git` directory/file and have no Git-tracked files. No overlapping
  parent/child deletion targets. Revalidate immediately before deletion.
- Rehashed every manifest-listed file in both older backups (187/188 files) and
  the newer protected backups (189/192 files); all hashes match.
- All four backups have the same **8 original-file hashes**. Recorded memory-row
  and history-row hashes match between deployment generations. Both preservation
  receipts passed SQLite integrity and preserved **8 memories / 171 events**.
- Retain these newer protected restore points:
  - `Evaluation/ProvenanceFirst/runs/search-overlay-deployment/backup-1790230453931123000`
  - `Evaluation/ProvenanceFirst/runs/search-overlay-deployment/post-install-1790231053409891000`
- Also leave the earlier successful backup within `search-overlay-deployment`
  untouched; it is not a target.
- Retain the installed signed app/extension in
  `search-overlay-deployment/build/Build/Products`, signing/install receipts,
  result bundles, current recordings/traces and frozen baseline archives.
- Retain all of `runs/unified-search/build` (the active warm simulator cache),
  `runs/search-handoff`, and `runs/main-app-deployment/build/ModuleCache.noindex`.
- Retain actual app source, original model assets, datasets, research ledgers,
  evaluation predictions, dependency lockfiles and all Git metadata. Deleting
  the obsolete build removes bundled *copies* of models, not their source assets.
- No current project build or recording worker was observed during the audit.

## After approval

Delete only the approved group(s), with protected-backup verification before
and after. Record actual net recovered space and recovery limitations. Removing
these files to free disk would be permanent, not moving them to Trash. Do not
silently expand the scope if space recovery is lower than estimated.

Then resume the search-handoff investigation from `check.py prepare`; the current
prepared project is stale and must not be used for validation/installation.
Re-run motion and regression checks before any phone update. No Git state changes.
