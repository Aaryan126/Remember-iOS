# Memory return-transition deployment — 25 September 2026

User authorized installation on the personal iPhone. Remember and its Share
Extension were signed and verified, then updated in place. The build also includes
the previously requested larger neutral-gray search spinner.

## Validation

- Final simulator source bindings match the signed app: 6 UI regressions passed
  in `../runs/memory-return/1790303257381561000.xcresult`.
- `python3 -B scripts/provenance-first/memory-return/deploy.py prepare`, `build`
  and `ready`: passed, using the normal app entrypoint and existing local GRDB.
- `backup`, `inspect-backup`, `install`, `smoke`, `post-backup`, `compare`, `launch`
  and `finish`: completed through the same deployment wrapper.
- Phone smoke: 1 test passed, verifying hidden library controls in a memory,
  Back and swipe-back, restored search/header/tab controls and Add placement.
  Final result: `../runs/memory-return-device/smoke-1790304099222883000.xcresult`.
- Final signed build: operation `1790303938907521000`; final installation:
  `1790304084259730000`. App and extension identity/signatures verified.
- Final preservation comparison: SQLite integrity passed, all 8 memory rows,
  all 8 original files and all 172 history events unchanged. The first pre-install
  backup also matches the second backup, verifying preservation across both
  installation attempts. Remember was reopened afterward.
- `git diff --check`: passed. No Git state changes.

Two initial phone runs passed Back but the automated edge drag did not leave the
detail. The harness was changed to begin 1% inside the edge and drag slowly with
a short hold, and explicitly requires the detail to disappear. This passed;
production app sources were unchanged. The test rebuild re-signed the app, so
the product-equality gate correctly required a fresh backup and second in-place
installation. Original receipts, signed-build records and backup approvals were
archived instead of overwritten. This does not claim exhaustive gesture-speed or
physical-device animation profiling; the simulator recordings provide the visual
before/after review.

The existing 32 GiB cumulative allowance and 10 GiB free reserve were maintained.
Private logs, recordings and backups remain under ignored
`Evaluation/ProvenanceFirst/runs/memory-return-device/`. No uninstall, data reset,
restore, AI calls, forced regrouping or database migrations. Existing Xcode/tool
warnings remain.

Deployment files added/updated: `scripts/provenance-first/memory-return/deploy.py`,
`MainAppSmokeTests.swift`, this report, `REPORT.md`, `ready-to-install.json`,
`checkpoint-stop.json`, and `docs/unified-memory-search.md`.
