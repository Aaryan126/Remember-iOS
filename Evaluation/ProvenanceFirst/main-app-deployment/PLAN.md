# Main Remember update — controlled development installation

User approved proceeding with the revised main-app update recommendation on
20 September 2026 ("Carry on"). This is an in-place development update to the
connected iPhone, not a public release, new model experiment or destructive reset.

## Existing evidence

Source-browser-media is complete: 29 native / 10 simulator UI / 10 physical-phone
UI passes, both builds passed. All 227 completion bindings were verified unchanged
before this checkpoint. Preserve that receipt, scripts, reports and screenshots.
No further source integration is necessary: normal ContentView opens ProjectView,
whose Threads overflow already links to SourceEvidenceSearchView.

## Preflight and resources

- Installed bundle: SimpleStudio.Remember, version 1.0/build 1. Data container is
  accessible; declared app group group.SimpleStudio.Remember matches source.
- Build must preserve normal entrypoint, app ID, team, share extension and app-group
  entitlements. Do not install the fictional fixture over the main app.
- User explicitly approved 31 GiB ("approved, and free") after the 28 GiB preflight
  hold. resource-amendment-31.json records the scoped allowance; original accounting
  baseline and 10 GiB reserve remain. Free space is measured, not assumed freed.
- Last metadata-only inventory: 181 non-directory app files, 217,575,624 bytes
  (~207.5 MiB); zero symlinks. Shared group has directories but no files currently.
  Recheck after stopping the app; these are not a completed backup or memory counts.
- Runtime pause must stop owned build/transfer workers and retain finished artifacts.
  Do not interrupt an in-place installation casually; wait for its bounded outcome.

## Execution after storage is resolved

1. **Recoverable local data snapshot.** Keep phone unlocked. Resolve/stop only the
   normal Remember process (and its share extension if running) so SQLite/WAL and
   originals do not change during copy. Copy the full app data container and shared
   group to a new private, ignored run directory, with restrictive permissions.
   Never print original content, credentials, captions or private filenames.
   Compare inventory/byte counts, create local hashes and verify a separate SQLite
   inspection copy with integrity_check. Preserve database, WAL, originals and
   preferences together. Check migration compatibility and pending-work counts
   without exposing text. Document exact data-restore procedure before installation;
   do not claim this is a whole-device/keychain backup or proven binary rollback.
2. **Signed normal-app build.** Snapshot relevant sources/build inputs into a new
   ignored deployment run directory. Use the existing local GRDB package via a
   generated project dependency reference if necessary, with normal app/extension
   targets retained. No fetch/resolve that mutates Git state, no lockfile rewrite.
   Build under an explicit disk reservation and monitored bounded process. Verify
   signatures, team, normal bundle IDs/entitlements, model assets and absence of
   fixture launcher. No Swift feature/model/threshold changes are planned.
3. **Install in place, then smoke check.** Never uninstall. Record installation
   result and installed bundle identity. Normal launch starts existing library
   synchronization and D3 observation: do not promise zero background writes.
   Inspect pending work/settings before launch; do not trigger paid/cloud features
   or change consent silently. Existing placements are not deliberately rescored;
   do not force regrouping, change captures, archive items or run fixture tests
   against the main bundle. Verify ordinary launch, Memories/Threads navigation,
   Search saved evidence/current-history scope and Back. Use privacy-minimizing
   checks; let the user choose real content if content-level inspection is needed.
4. **Handoff.** State exactly what was installed/tested, confirm preservation checks,
   describe the entry point and disclose any checks left for the user. Keep larger
   library, VoiceOver and audio-routing work as later hardening, not a new model
   research prerequisite. Stop for review, no publishing or Git mutations.

Estimated active time after preflight: 1–2 hours if backup/build/signing cooperate.
Private backups and machine-specific artifacts belong under the already ignored
Evaluation/ProvenanceFirst/runs/main-app-deployment tree, not beside this report.
No existing completed-checkpoint file may be edited without preserving its bindings.
