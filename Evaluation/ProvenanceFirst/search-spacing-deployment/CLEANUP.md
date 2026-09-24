# Approved deployment cleanup — 24 September 2026

The user approved these exact four project-only compiler cache/intermediate
directories after seeing the paths and measured size. Removed with `rm -r`:

- `Evaluation/ProvenanceFirst/runs/search-motion-deployment/build/Build/Intermediates.noindex`
- `Evaluation/ProvenanceFirst/runs/search-motion-deployment/build/SDKExplicitPrecompiledModules`
- `Evaluation/ProvenanceFirst/runs/search-transition-deployment/build/Build/Intermediates.noindex`
- `Evaluation/ProvenanceFirst/runs/search-transition-deployment/build/SDKExplicitPrecompiledModules`

All four deletions succeeded. Filesystem available space rose from 11,656,548 KiB
to 12,255,432 KiB (about 585 MiB net). Deleted bytes are not in Trash, but Xcode
can regenerate these build artifacts. No source, model, dataset, backup, test
result, signed product or out-of-project path was removed. The active simulator
build and reused device module cache were preserved. This approval is exhausted.

The spacing deployment's original 1.5 GiB headroom check subsequently passed;
the 10 GiB free-space reserve and 32 GiB cumulative guard remain unchanged.
