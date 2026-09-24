# Compact spacing and populated-search dismissal — phone deployment

24 September 2026. Installed in place in the normal Remember app on the physical
iPhone 17, iOS 27. No uninstall, schema/model/retrieval change or AI invocation.

## Shipped changes

- Equal header gaps reduced from 20 to 10 points; title/count/filter centers and
  the 44-point filter touch target remain intact.
- Populated results fade out over 0.2 seconds into the preserved browsing grid
  during search dismissal. Empty-field motion remains native. Reduce Motion
  disables the custom fade.

Source changes are in `ContentView.swift` and `UnifiedMemorySearchView.swift`;
regressions are in `UnifiedMemorySearchUITests.swift`. This deployment adds the
`scripts/provenance-first/search-dismissal/deploy.py` wrapper and normal-app
`MainAppSmokeTests.swift`, plus this report and the cleanup record.

## Checks actually run

Using `python3 scripts/provenance-first/search-dismissal/deploy.py`:

- `prepare`: 107 source bindings verified against simulator-tested preparation.
- `build`: signed app/extension and bundled local model verified; operation
  `1790223778651672000` passed.
- `backup` / `inspect-backup`: 187 files verified; SQLite integrity and 11
  migrations matched; launch preflight passed.
- `install`: operation `1790223897369787000` passed; normal bundle identity,
  `uninstalled: false`.
- `smoke`: **1 passed, 0 failed/skipped, no reported runtime warnings**, first
  attempt. Result: `smoke-1790223922492964000.xcresult`. Empty, matching and
  no-match dismissal ran with keyboard-open and keyboard-dismissed variants;
  restored control position, compact header alignment and menu/reset checked.
- `post-backup`: 188 files verified in the post-install snapshot.
- `compare`: SQLite healthy; **all 8 memory rows, 171 history events and 8
  original files unchanged**. The file-inventory count difference does not mean
  an added memory; preservation was checked against rows, events and original
  file hashes rather than total cache/container file counts.
- `xcrun xcresulttool get test-results summary --compact` confirmed phone results.
- `xcrun swiftc -frontend -parse scripts/provenance-first/search-dismissal/MainAppSmokeTests.swift`
  and `git diff --check` passed.
- `launch`: updated Remember reopened successfully. An early `finish` attempt
  was rejected by the worker lock while launch was still running; it performed
  no checkpoint write. Finalization was retried only after launch completed.

Simulator evidence: **10/10 UI tests** plus before/after fictional motion-frame
inspection; see [verification report](../search-dismissal/REPORT.md). Phone
automation checks behavior and settled positions, not subjective smoothness.
User confirmation is still needed. Reduce Motion enabled was not separately
exercised. No private source was opened/edited or explicitly screenshotted;
phone containers/results remain local in ignored `runs/`.

## Storage and handoff

Only the five approved project directories were removed: about **887 MiB net**
recovered. Simulator outputs are rebuildable; two old failed/interrupted result
bundles and their attachments were permanently removed, not sent to Trash.
See [exact cleanup record and recovery limits](CLEANUP.md). No further cleanup is
authorized. Original assets, sources, datasets and phone backups were retained.
The 10 GiB free-space reserve and 32 GiB growth guard were not relaxed.

Raw receipts/backups are in
`Evaluation/ProvenanceFirst/runs/search-dismissal-deployment/`. Final completion
is recorded by `checkpoint-stop.json` after reopening the app and binding these
documents. No Git state changed. Stop for the user's review of the installed UI.
