# Search handoff phone deployment — 24 September 2026

## Scope and safeguards

In-place update of `SimpleStudio.Remember`, using the existing signing team and
app group. No uninstall, reset, regroup, migration, AI request or personal source
inspection. Existing local startup still runs; verify data preservation afterward.

The change freezes outgoing result pixels in memory for a short opacity fade,
while a stable geometry boundary prevents an extra native scroll-container jump.
Empty search keeps its native dismissal. Source and fictional simulator evidence:
`../search-handoff/REPORT.md`.

## Current status

**Installed and normally launched; data preservation verified. Manual smoothness
review and a successful physical-device automated smoke test remain outstanding.**

Post-launch snapshot `post-install-1790247050804157000` verifies 192 files.
`preservation.json` confirms SQLite integrity, all **8 original files byte-for-byte
unchanged**, all **8 memory rows unchanged**, and all **171 history events unchanged**.
No uninstall, restore, reset or forced regroup occurred. `git diff --check` and
AST parsing of all seven handoff Python scripts passed. Git state was not changed.

Final source-matched checks: UI `1790246321537451000` **11/11**, unit
`1790246282358974000` **6/6**; both final motion traces pass. Signed rebuild
`1790246632666130000` succeeds with the production actor-isolation warnings
resolved. Test-only `UIWindow(frame:)` deprecation warnings remain.

First installation operation `1790246686734850000` failed with CoreDevice 3002 /
IXRemoteErrorDomain 6: the remote installation connection closed unexpectedly.
Space remained above reserve. After the user reconnected the cable, retry
`1790246739582466000` **installed successfully in place**, without uninstalling.
Smoke `1790246800814041000` failed before running the test: the runner timed out
enabling automation mode. Retry `1790246902065809000` hit the same startup timeout.
Read-only lock-state check reported `passcodeRequired=false`, `unlockedSinceBoot=true`.
Neither attempt ran an app assertion, and neither counts as a pass. Stop repeated
automation attempts; normal launch/data verification and manual UI review remain.
Do not call `finish` or create a completed checkpoint without a real smoke pass.
Backup remains protected.

Fresh backup `backup-1790246221062747000` verified **192 files**, SQLite integrity,
11 matching migrations, 8 indexed memories and 171 events. Cloud is disabled;
there are no pending captures/shared inbox entries requiring startup review.

Earlier signed build `1790246176423526000` passed but revealed actor-isolation
warnings in the new injected callbacks. Both callback types are now explicitly
main-actor-isolated. The uninstalled first build's source and receipts are retained
in `uninstalled-build-*`; source-matched tests and a rebuild are required. Current
unit run `1790246282358974000` passes 6 tests without those new warnings. Final UI
rerun and installation subsequently succeeded as recorded above.

A concurrent resource-status command encountered the active backup worker lock;
it made no change. The backup itself completed successfully. Worker/resource
guards remain enabled (10 GiB reserve, 32 GiB cumulative cap).

## Resume sequence

No rebuild or reinstall is needed for user review. Compare closing an empty query,
a matching query and a no-results query at the top and after scrolling. The
snapshot fade should replace the former abrupt content cut, with no additional
container jump. Note whether any remaining difference is in the results fade,
search bar, keyboard, or grid position.

If resuming phone automation, first resolve the XCTest automation-mode startup
failure. Do not simply keep retrying or mark the failed attempts passed. Existing
receipts are immutable; if app data has changed during user testing, archive the
previous backup approval and take a new verified baseline before another lifecycle
test. Record a new post-test comparison rather than overwriting preservation.json.
Only then may a fully verified deployment checkpoint be created. Never bypass
the smoke gate just because installation and data preservation succeeded.

Commands use `python3 scripts/provenance-first/search-handoff/deploy.py ACTION`.
User-perceived smoothness remains a manual check even after automated tests pass.
