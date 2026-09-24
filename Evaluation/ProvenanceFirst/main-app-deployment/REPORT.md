# Main Remember update — installed and verified

20 September 2026. The source-first browsing version is now installed **in place
in the normal Remember app** on the connected iPhone 17/iOS 27. No uninstall,
fixture replacement, Git mutation, model training or paid API test occurred.
The app was reopened normally after verification for the user's review.

## What the user can now use

Open **Remember → Threads → More (…) → Search saved evidence**. Search a name,
phrase or code retained in a source. Current shows current unarchived evidence;
Include history adds retained earlier revisions and archived sources. Open a result
to inspect its exact passage/revision, available original, inline media and explicitly
current River context. Back preserves the search. AI summaries are not source evidence.

This deploys the already-implemented source-browser/media work, including wrapping
accessibility-size scope labels and playback lifecycle fixes. The normal app shell,
share extension, app group and existing D3 matcher are included. No new Swift app
features or model/threshold changes were introduced for deployment. The existing
main app's normal local index/organizer services run on launch; this is not the
replayed, model-free Evidence Check launcher.

## Verified checks

| Check | Result / saved operation |
| --- | --- |
| Prior media checkpoint | All 227 historical bindings verified; overview archived before updating it |
| Backup | 181 files, 217,575,624 bytes; both containers copied with stable before/after inventory and local SHA-256 manifest |
| Database preflight | Integrity check passed; all 11 migration names match current app |
| Initial signed build | Passed, 1789918506383100000 |
| Final signed build | Passed, 1789918562089376000 |
| Main app and share extension | Signature/team/bundle ID/app-group checks passed; compiled D3 model included |
| In-place installation | Passed, 1789918586902688000; no uninstall |
| Normal-app navigation smoke | 1/1 passed, zero skips/failures/reported runtime warnings; 1789918620389280000 |
| Post-update data check | Integrity check passed; all memory rows, existing history and original bytes unchanged |
| Deployment harness tests | 3/3 passed; git diff --check passed |

The new smoke test navigates Memories → Threads → Search saved evidence, submits
a synthetic nonmatching query, switches to Include history and returns through
Threads to Memories. It does not create, edit, delete or archive captures, request
AI answers, export personal screenshots or exercise the artificial fixture suite
against the real library. The phone test took 26.9 seconds of test execution.
The earlier 29 native / 10 simulator / 10 isolated phone UI results remain valid
saved evidence, not tests rerun during this deployment.

During harness review, its app-bundle assertion was corrected to inspect the test
bundle instead of XCTest's runner main bundle. Preparation/build receipts were
preserved and an incremental rebuild passed before the test was run. No app behavior
was changed for this check. The initial build emitted existing Sendable/concurrency,
unreachable-default, test deprecation and AppIntents metadata warnings; it was not
a warning-free compile. These are distinct from the zero runtime warnings in the
completed smoke result. A read-only resource query initially encountered the active
worker lock; it was separated from the exclusive execution lock and succeeded.

## Preservation and privacy

Before launch, the backup showed cloud assistance disabled, no captured/processing
memories, no queued shared-inbox files and no video requeue candidates. No setting
was toggled and no cloud feature was invoked. Database queries inspected aggregate
counts/compatibility and hashes; private source text or secrets were not printed.

| Preserved data | Before | After | Comparison |
| --- | ---: | ---: | --- |
| Memory records | 8 | 8 | Every complete row identical |
| Provenance events | 171 | 171 | Every historical row identical |
| Saved originals | 8 | 8 checked | All bytes identical |

iOS changed the private app-container path during the update; shared-group identity
was retained. Content verification, not path equality, establishes preservation.
The post-update snapshot contains 182 files rather than 181; complete-memory and
provenance equality plus original-file hashes passed. Containers can gain normal
runtime files independently of library records.

Private snapshots are retained in the Git-ignored runs/main-app-deployment directory
with restrictive directory permissions. No backups, source originals or private
screenshots are placed in versionable documentation. See RECOVERY.md: local data
copies were verified, but no destructive phone restore or old-binary rollback was
rehearsed. This is not a whole-device/keychain backup.

## Resources, scope and next step

User explicitly approved 31 GiB while retaining the original baseline and 10 GiB
free reserve. Post-verification free space was ~13.39 GiB; conservative growth
~28.48 GiB. Whole-Mac decline contributes to that figure; it is not solely this
deployment's disk use. No additional cleanup was performed in this checkpoint.
PAUSE can stop owned build/transfer work; installation is treated as a bounded
critical operation allowed to finish before stopping. All test/build workers exited.

This is a user-approved development installation, not public release qualification
or a new model-quality result. Real-content retrieval relevance, real voice/video
playback in the normal app, VoiceOver, routing/interruption behavior, large-library
performance and additional supported OS versions remain follow-up checks. Normal
startup and menu integration passed; do not describe the single smoke as a full
production UI suite. D3 remains experimental; failed local answer/relationship
policies and Pro organization remain excluded.

**Next:** use the installed app normally and report friction. Run a focused hardening
checkpoint for accessibility/audio routes and representative larger fictional
libraries, guided by that feedback. Do not block personal use on a new model sweep.
Stop for user review; no publishing, further deployment or new paid calls implied.

## Reproduction and changed files

Commands run via scripts/provenance-first/main-app-deployment/deploy.py:
resources, backup, inspect-backup, prepare, build, refresh-smoke, install, smoke,
post-backup, compare-after, archive-overview, verify-signed and finish. Raw device
inventories, command receipts/logs, signed products, preparation/source/dependency
bindings and the xcresult stay in the private ignored run directory. Also ran
Python unittest discovery for this harness, xcresulttool summary, git check-ignore,
git diff --check and normal devicectl launch. No package fetch or Git state change.

Added deployment runner, focused MainAppSmokeTests and three inventory guard tests;
PLAN/STATUS/RECOVERY/REPORT/RESUME and scoped resource approval. Updated only the
product overview docs/provenance-first.md after archiving its prior bound bytes.
App source, lockfile, existing historical receipts and model assets are unchanged.
