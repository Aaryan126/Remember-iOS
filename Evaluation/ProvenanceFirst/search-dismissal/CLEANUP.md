# Approved cache cleanup — 24 September 2026

After the user approved the exact four paths, removed only:

- `Evaluation/ProvenanceFirst/runs/main-app-deployment/build/Build/Intermediates.noindex`
- `Evaluation/ProvenanceFirst/runs/main-app-deployment/build/SDKExplicitPrecompiledModules`
- `Evaluation/ProvenanceFirst/runs/search-spacing-deployment/build/Build/Intermediates.noindex`
- `Evaluation/ProvenanceFirst/runs/search-spacing-deployment/build/SDKExplicitPrecompiledModules`

`rm -r` succeeded for all four. Available filesystem space rose from
10,833,688 KiB to 11,434,456 KiB, about 587 MiB net. These files are not in Trash;
Xcode can regenerate them. Source, models, datasets, backups, signed products,
active simulator build and reused device module cache were preserved. No paths
outside the project or additional directories were deleted. Approval exhausted.

The existing 10 GiB reserve and 32 GiB cumulative ceiling remain unchanged.
