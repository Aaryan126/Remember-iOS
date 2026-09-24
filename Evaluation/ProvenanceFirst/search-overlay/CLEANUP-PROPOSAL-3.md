# Project-only cleanup proposal 3 — awaiting approval

No deletion has been performed under this proposal. Previous approvals are
exhausted. Scope: only the nine exact paths below, relative to the repository root.

Measured total: **684,601,344 allocated bytes (652.89 MiB / 0.64 GiB)**.
Actual recovered space may be smaller because of APFS sharing/snapshots and
concurrent disk activity. Current free space fluctuates around **11.50 GiB**,
up from the previous 10.48 GiB observation but barely at the 11.5 GiB device
preparation threshold. This cleanup would provide extra headroom; it does not
guarantee the entire deployment will fit. Recheck resource gates after deletion.

## Exact proposed targets

| Path | Allocated bytes | Consequence |
|---|---:|---|
| `Evaluation/ProvenanceFirst/runs/unified-search/build/Build/Intermediates.noindex` | 130,179,072 | Regenerable simulator compilation intermediates; a future simulator build takes longer. |
| `Evaluation/ProvenanceFirst/runs/unified-search/build/ModuleCache.noindex` | 28,880,896 | Regenerable simulator module cache; a future simulator preparation uses the cold-build reservation. |
| `Evaluation/ProvenanceFirst/runs/unified-search/build/SDKExplicitPrecompiledModules` | 180,592,640 | Regenerable simulator SDK modules. |
| `Evaluation/ProvenanceFirst/runs/search-dismissal/before.mp4` | 62,111,744 | Permanently remove an older animation recording; extracted images, logs and reports remain. |
| `Evaluation/ProvenanceFirst/runs/search-dismissal/after.mp4` | 66,162,688 | Permanently remove an older animation recording; extracted images, logs and reports remain. |
| `Evaluation/ProvenanceFirst/runs/search-motion/before.mp4` | 50,585,600 | Permanently remove an older animation recording; extracted images, logs and reports remain. |
| `Evaluation/ProvenanceFirst/runs/search-motion/after.mp4` | 44,888,064 | Permanently remove an older animation recording; extracted images, logs and reports remain. |
| `Evaluation/ProvenanceFirst/runs/search-overlay/1790226731745875000.xcresult` | 60,260,352 | Permanently remove detailed attachments/result bundle for the rejected native-delegate candidate; its `.log`, `.json` receipt and report remain. |
| `Evaluation/ProvenanceFirst/runs/search-overlay/1790226862722547000.xcresult` | 60,940,288 | Permanently remove detailed attachments/result bundle for the rejected guarded-delegate candidate; its `.log`, `.json` receipt and report remain. |

Group totals: simulator caches **323.92 MiB**, older videos **213.38 MiB**,
failed-candidate test bundles **115.59 MiB**.

## Validation and preserved items

- All nine targets currently exist, resolve to their literal paths inside this
  project, are not symlinks, and contain no Git-tracked files (`git ls-files`).
  Revalidate immediately before any approved deletion.
- The two rejected runs' logs confirm their failed scroll-restoration assertion.
  These are not the current successful verification runs.
- Preserve current successful result bundles `1790228823706026000.xcresult`
  (11/11) and `1790229148968578000.xcresult` (focused top test), their logs,
  receipts, source bindings, frame traces and current comparison recordings.
- Preserve the current simulator `Build/Products` and prepared project. Only
  its three named cache/intermediate directories are proposed for deletion.
- Preserve both latest full phone backups, the latest installed signed build,
  `main-app-deployment/build/ModuleCache.noindex`, GRDB dependency copies,
  all source code, models, training/evaluation data and experiment results.
- The phone deployment explicitly uses the separate retained
  `main-app-deployment/build/ModuleCache.noindex`, not the simulator caches above.
  Its simulator-verification gate reads the retained result bundles and receipts.
- Do not delete the large remaining research ledgers, predictions or frozen
  baseline archives merely to reach an arbitrary storage target.
- No `.git` changes, no outside-project cleanup, and no relaxed resource limits.

## On approval

Delete only these exact targets, record the actual net space recovered, then
recheck the phone-deployment preflight. If space is still insufficient, report
that without expanding the deletion scope. An approval here does not authorize
any other deletions.
