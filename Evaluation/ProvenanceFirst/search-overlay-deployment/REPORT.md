# Search overlay dismissal — phone deployment, 24 September 2026

The frame-traced candidate is installed in the normal Remember app, in place,
on the physical iPhone 17 running iOS 27. **The final phone smoke passed on the
unchanged build. Post-install preservation checks passed; perceived
smoothness still needs the user's confirmation.**

## Changes and preserved behavior

The production change removes the outgoing results fade and scopes unanimated
removal to that branch only. The browsing grid remains mounted and visible behind
the opaque results surface. Native search/keyboard/detail navigation animations,
the compact header, retrieval, models and schema are unchanged. No production
instrumentation, timer, delegate override or forced scroll reset was added.

## Checks and attempts

Commands use `python3 scripts/provenance-first/search-overlay/deploy.py`.
Raw receipts and private backups remain in ignored
`Evaluation/ProvenanceFirst/runs/search-overlay-deployment/`.

- `prepare`: matched the successful 11/11 simulator UI receipt; 107 source files.
- `build`: signed build `1790230063300742000` passed. Harness-only rebuild
  `1790230371220752000` also passed; it changed signed product bytes, so it was
  followed by a fresh backup and explicit reinstall rather than silently reusing
  the earlier installation receipt.
- `backup`: first attempt failed reading the OS SplashBoard snapshot directory;
  full retries succeeded without excluding files or relaxing safeguards.
  Verified backups `backup-1790230199184777000` and
  `backup-1790230453931123000` contain 188 and 189 files, respectively.
- `inspect-backup`: SQLite healthy, 11 migrations matched, 8 memories and 171
  history events, cloud disabled and no pending capture/shared-inbox work.
  Memory/history row hashes match between both backups.
- `install`: current installation `1790230515254347000`, normal bundle identity,
  `uninstalled: false`. Prior install receipts are retained.
- `smoke-1790230277635286000.xcresult`: failed an overly strict native empty-value
  assertion. The harness was corrected to wait for the field and allow native
  nil/empty/placeholder representations; retained text still fails.
- `smoke-1790230535233861000.xcresult`: failed waiting for capture to reappear
  after no-match cancellation. Device orientation changed during this run.
- `smoke-1790230650974704000.xcresult`: failed waiting for Close after the initial
  empty-field tap, not library hit testing. No production changes between runs.

- `smoke-1790230950831239000.xcresult`: **1 passed, 0 failed/skipped, no reported
  runtime warnings**, operation `1790230953273599000`. No production/harness
  change after the previous two failures. All six dismissal cases and compact
  header/menu assertions passed. Orientation settled to portrait at startup;
  no subsequent orientation change was logged during this test.
- `xcrun swiftc -frontend -parse scripts/provenance-first/search-overlay/MainAppSmokeTests.swift`
  and `git diff --check` passed.
- `post-backup`: `post-install-1790231053409891000`, **192 files verified**.
- `compare`: SQLite integrity passed; **all 8 memory rows, 171 historical events
  and 8 original files unchanged**, including exact original-byte hashes. Different
  total backup file counts reflect auxiliary container files, not extra memories.
- `launch`: updated Remember reopened successfully on the phone.
- Python AST parsing passed for all five overlay scripts. Final completion is
  recorded in `checkpoint-stop.json` after binding reports, receipts and sources;
  this is a deployment/behavioral checkpoint, not proof of perceived smoothness.

The earlier failures are not counted as passes, and the final pass does not prove
their root cause. Read-only failure inspection used control
identifiers and geometry, not personal source content. No personal sources were
opened/edited or AI invoked by the test.

## Storage

The nine-path third cleanup recovered 654.23 MiB net. Regenerable simulator caches,
four old recordings and two rejected result bundles were removed permanently;
sources/models/data and protected phone backups were retained. See
[exact cleanup record](../search-overlay/CLEANUP-RESULT-3.md). No further deletion
is authorized. The 10 GiB reserve and 32 GiB cumulative guard remain in force.
No Git state was changed.
