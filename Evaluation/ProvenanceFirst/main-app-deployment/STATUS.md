# Main-app update — installed, verified, stopped for user review

## Final outcome

Main Remember (SimpleStudio.Remember) installed in place with normal share extension
and app-group entitlements; no uninstall. Final build 1789918562089376000,
installation 1789918586902688000, real-app smoke 1789918620389280000 all passed.
Smoke: 1/1, no skips/failures/reported runtime warnings. Normal app reopened afterward.

Post-update snapshot verified all 8 memory rows, all 171 historical events and all
8 originals unchanged, with SQLite integrity passing. iOS relocated the app's
private container but preserved its contents; group identity remained. No new
capture, deletion, regrouping request, cloud request or preference change made.
Three deployment guard tests and git diff --check passed. Prior 227 historical
bindings preserved, including the explicitly archived overview before its update.

See REPORT.md for exact scope, limitations and commands; RESUME.md for preservation.
No test/build worker remains. User can disconnect and try Remember → Threads → … →
Search saved evidence. Stop for review; no automatic further model/deployment work.

Everything below records the earlier in-progress/preflight states, not current status.

## Approved continuation

User approved the proposed 31 GiB cap ("approved, and free"). New scoped approval
retains original baseline and 10 GiB reserve; old approvals unchanged. Deployment
runner monitors bounded owned operations and honors WORK/PAUSE. No Git mutation.

Private backup backup-1789918416575368000 verified 181 files against stable device
inventories and local hashes. Separate SQLite inspection copy passed integrity_check;
all 11 migration names match current source. Eight indexed memories, 171 events,
cloud assistance false, no pending captures/shared-inbox files, no video requeue.
No private source text or preference secrets printed. Both containers were copied
while the main app was stopped. See RECOVERY.md for limits; no phone restore rehearsed.

Normal signed app/share-extension build 1789918506383100000 passed. The navigation
test's bundle check was corrected to inspect its test bundle instead of the runner's
main bundle before running it. Preparation/build receipts were archived, and rebuild
1789918562089376000 passed. App/extension IDs, signing team, app group and compiled
trained matcher verified; production entrypoint unchanged. Three runner guard tests
and git diff --check passed. Existing test-only deprecation/AppIntents build warnings
are not suppressed. In-place installation has been dispatched; await its receipt.

## Historical preflight hold (superseded)

20 September 2026. User approved proceeding with an in-place normal-app update.
No normal-app build, data backup, install or launch has been performed yet.

Completed read-only checks:

- Phone connected/unlocked; installed normal Remember bundle verified, with
  accessible app and shared-group containers matching source identifiers.
- Source-browser-media completion's 227 file hashes all verified.
- Main-app entrypoint/Threads source-browser wiring confirmed.
- Backup inventory counted metadata only: 181 files totaling 217,575,624 bytes,
  zero symlinks; group currently contains no files. Personal content not read.
- Source uses app-private Application Support/Remember for database and originals;
  share-extension inbox uses the shared container. Both must be preserved.
- No new source-search migration is needed. Normal app's existing startup can
  process pending captures/organization; inspect settings/work before launch.

Resource check: freeBytes 15,354,888,192, conservativeGrowthBytes 29,608,079,360,
approved capBytes 30,064,771,072, reserveBytes 10,737,418,240. ~0.43 GiB growth
headroom is insufficient for backup plus fresh signed compilation. This accounting
includes whole-Mac free-space decline, not only experiment output.

Asked user asynchronously to free 2–3 GiB or approve 31 GiB while keeping original
baseline and 10 GiB reserve. **31 GiB is proposed, not approved.** No cleanup or
budget override performed. No workers are running; safe to disconnect while waiting.

Resume: recheck resources and phone lockState, record any explicit approval in a
new scoped artifact, then follow PLAN.md. Keep the completed media checkpoint
immutable. The installed main app remains unchanged; no Git mutations.
