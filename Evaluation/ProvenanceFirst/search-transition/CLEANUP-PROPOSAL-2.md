# Second cleanup proposal — awaiting approval

23 September 2026. **No deletion is authorized or performed by this proposal.**
The user requested a second exact list after the first six-folder cleanup.

## Scope and measured size

Remove only the 54 exact cache/intermediate directories listed below, never their
parent build folders. All paths are relative to:

`/Users/aaryan/Desktop/Gemini Hackathon/`

| Group | Measured MiB |
|---|---:|
| Old iOS 27 diagnostic caches | 831.2 |
| Organization diagnostic caches | 253.6 |
| Earlier provenance experiment caches | 714.1 |
| Completed search deployment caches | 637.9 |
| **Total** | **2436.8 MiB (2.38 GiB)** |

Latest initial disk measurement: 10,782,828 KiB free (10.28 GiB). If all measured
allocation were reclaimed, free space would reach about 12.66 GiB. This is not a
guarantee: APFS sharing and concurrent disk usage can reduce net recovery. This
batch alone is less than the requested 3–4 GiB headroom and may still be insufficient
for the complete test-plus-install workflow. Measure actual recovery before starting.

## Preserved

- All source, datasets, evaluation predictions/results, logs and xcresult bundles.
- Model packages/weights, signed app binaries and original model exports.
- Every phone backup and before/after preservation snapshot.
- All archived checkpoint inputs, receipts and completed deployment records.
- The entire active simulator build at `Evaluation/ProvenanceFirst/runs/unified-search/build/`.
- The entire `Evaluation/ProvenanceFirst/runs/main-app-deployment/build/`, including
  the SDK module cache explicitly reused by the current signed-build workflow.
- All files outside this project and everything inside `.git/`.

These are compiler caches, precompiled SDK modules and intermediate object/build
files, not whole experiments. Rebuilding the affected older targets may be slower
and regenerate the caches. No research dataset or result is sacrificed.

## Read-only checks

Directory allocation measured with `du -sk`. `git ls-files -- <exact paths>`
returned no tracked files. `realpath <exact paths>` resolved every candidate to its
expected location inside the project. Current deployment/test scripts were checked
for reused cache paths; the active build trees above are excluded. Before any
approved removal, recheck paths, sizes, running builds and absence of tracked files.
Use explicit validated paths; never broad directory wildcards or recursive parent
cleanup. Do not increase resource caps or rewrite old receipts.

## Exact deletion list

| Relative directory (only this directory and its contents) | Allocated KiB |
|---|---:|
| `Evaluation/iOS27/embedding-recovery-v2/build/device-build/Build/Intermediates.noindex/` | 4228 |
| `Evaluation/iOS27/embedding-recovery-v2/build/device-build/ModuleCache.noindex/` | 5240 |
| `Evaluation/iOS27/embedding-recovery-v2/build/device-build/SDKExplicitPrecompiledModules/` | 51512 |
| `Evaluation/iOS27/embedding-recovery-v2/build/module-cache/` | 40436 |
| `Evaluation/iOS27/embedding-recovery-v2/build/unit-tests/.build/out/Intermediates.noindex/` | 2996 |
| `Evaluation/iOS27/embedding-recovery-v2/build/unit-tests/.build/out/ModuleCache.noindex/` | 7900 |
| `Evaluation/iOS27/embedding-recovery-v2/build/unit-tests/.build/out/SDKExplicitPrecompiledModules/` | 30376 |
| `Evaluation/iOS27/embedding-recovery/build/device-build/Build/Intermediates.noindex/` | 4188 |
| `Evaluation/iOS27/embedding-recovery/build/device-build/ModuleCache.noindex/` | 5240 |
| `Evaluation/iOS27/embedding-recovery/build/device-build/SDKExplicitPrecompiledModules/` | 51512 |
| `Evaluation/iOS27/embedding-recovery/build/module-cache/` | 40436 |
| `Evaluation/iOS27/embedding-recovery/build/unit-tests/.build/out/Intermediates.noindex/` | 2824 |
| `Evaluation/iOS27/embedding-recovery/build/unit-tests/.build/out/ModuleCache.noindex/` | 7900 |
| `Evaluation/iOS27/embedding-recovery/build/unit-tests/.build/out/SDKExplicitPrecompiledModules/` | 30368 |
| `Evaluation/iOS27/generation-trace/build/device-build/Build/Intermediates.noindex/` | 2060 |
| `Evaluation/iOS27/generation-trace/build/device-build/ModuleCache.noindex/` | 5160 |
| `Evaluation/iOS27/generation-trace/build/device-build/SDKExplicitPrecompiledModules/` | 50700 |
| `Evaluation/iOS27/safeguards/build/derived/Build/Intermediates.noindex/` | 95924 |
| `Evaluation/iOS27/safeguards/build/derived/ModuleCache.noindex/` | 17676 |
| `Evaluation/iOS27/safeguards/build/derived/SDKExplicitPrecompiledModules/` | 129504 |
| `Evaluation/iOS27/sentence-context/build/device-build/Build/Intermediates.noindex/` | 1940 |
| `Evaluation/iOS27/sentence-context/build/device-build/ModuleCache.noindex/` | 5188 |
| `Evaluation/iOS27/sentence-context/build/device-build/SDKExplicitPrecompiledModules/` | 51028 |
| `Evaluation/iOS27/sentence-context/build/module-cache/` | 30244 |
| `Evaluation/iOS27/sentence-controls/build/device-build/Build/Intermediates.noindex/` | 1832 |
| `Evaluation/iOS27/sentence-controls/build/device-build/ModuleCache.noindex/` | 5192 |
| `Evaluation/iOS27/sentence-controls/build/device-build/SDKExplicitPrecompiledModules/` | 51028 |
| `Evaluation/iOS27/sentence-controls/build/module-cache/` | 30244 |
| `Evaluation/iOS27/sentence-diagnostic/build/device-build/Build/Intermediates.noindex/` | 1836 |
| `Evaluation/iOS27/sentence-diagnostic/build/device-build/ModuleCache.noindex/` | 5196 |
| `Evaluation/iOS27/sentence-diagnostic/build/device-build/SDKExplicitPrecompiledModules/` | 51028 |
| `Evaluation/iOS27/sentence-diagnostic/build/module-cache/` | 30244 |
| `Evaluation/OrganizationDiagnostics/runs/c2-01/ledger/build/Build/Intermediates.noindex/` | 63524 |
| `Evaluation/OrganizationDiagnostics/runs/c2-01/ledger/build/ModuleCache.noindex/` | 133400 |
| `Evaluation/OrganizationDiagnostics/runs/c2-01/reference/module-cache/` | 30888 |
| `Evaluation/OrganizationDiagnostics/runs/c7-01/build/module-cache/` | 31824 |
| `Evaluation/ProvenanceFirst/runs/answer-support-format-v2/generation-build/module-cache/` | 39656 |
| `Evaluation/ProvenanceFirst/runs/answer-support/generation-build/module-cache/` | 39648 |
| `Evaluation/ProvenanceFirst/runs/answer-support/native-build/Build/Intermediates.noindex/` | 60388 |
| `Evaluation/ProvenanceFirst/runs/answer-support/native-build/ModuleCache.noindex/` | 11212 |
| `Evaluation/ProvenanceFirst/runs/answer-support/native-build/SDKExplicitPrecompiledModules/` | 125676 |
| `Evaluation/ProvenanceFirst/runs/checkpoint1/ledger/build/Build/Intermediates.noindex/` | 60008 |
| `Evaluation/ProvenanceFirst/runs/checkpoint1/ledger/build/ModuleCache.noindex/` | 41116 |
| `Evaluation/ProvenanceFirst/runs/checkpoint1/ledger/build/SDKExplicitPrecompiledModules/` | 125676 |
| `Evaluation/ProvenanceFirst/runs/history-recovery/build/Build/Intermediates.noindex/` | 61100 |
| `Evaluation/ProvenanceFirst/runs/history-recovery/build/ModuleCache.noindex/` | 11196 |
| `Evaluation/ProvenanceFirst/runs/history-recovery/build/SDKExplicitPrecompiledModules/` | 125676 |
| `Evaluation/ProvenanceFirst/runs/search-options-deployment/build/Build/Intermediates.noindex/` | 120864 |
| `Evaluation/ProvenanceFirst/runs/search-options-deployment/build/ModuleCache.noindex/` | 27944 |
| `Evaluation/ProvenanceFirst/runs/search-options-deployment/build/SDKExplicitPrecompiledModules/` | 177800 |
| `Evaluation/ProvenanceFirst/runs/source-browser/ModuleCache.noindex/` | 29916 |
| `Evaluation/ProvenanceFirst/runs/unified-search-deployment/build/Build/Intermediates.noindex/` | 120852 |
| `Evaluation/ProvenanceFirst/runs/unified-search-deployment/build/ModuleCache.noindex/` | 27944 |
| `Evaluation/ProvenanceFirst/runs/unified-search-deployment/build/SDKExplicitPrecompiledModules/` | 177800 |

Approval must refer to this list. Nothing else may be removed under that approval.
After removal, report actual recovered space and rerun the existing storage gate.

