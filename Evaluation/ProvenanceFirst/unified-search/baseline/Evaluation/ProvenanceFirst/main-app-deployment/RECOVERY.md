# Local recovery boundaries

The verified backup is private under runs/main-app-deployment/backup-TIMESTAMP.
It includes both the app data container and the shared capture group, including
the SQLite database and any WAL/SHM files, originals, preferences and caches.
The manifest records local SHA-256 hashes and the device inventories before/after
copy. This is not a whole-device backup, keychain export or old-app binary archive.

Before installation the deployment runner requires a successful backup hash check,
SQLite integrity_check on a separate copy and an exact migration-name match with
the current app. The original copied database files are never opened for writing.

If an in-place update fails, do not uninstall or automatically overwrite data.
Record the exact installation/launch failure and preserve the current device state
in another snapshot first; it may contain newer captures. Recover only after
explicitly choosing the recovery point and assessing any newer records.

For a separately approved data recovery:

1. Resolve and stop only Remember and its share extension. Keep them stopped while
   restoring; verify the same normal bundle and group identifiers are present.
2. Verify the selected backup manifest and a fresh SQLite inspection copy.
3. Use `xcrun devicectl device copy to` with the validated backup's `app` directory,
   domain appDataContainer and identifier SimpleStudio.Remember; use its `group`
   directory with appGroupDataContainer and group.SimpleStudio.Remember. Restore
   into the domain root, never a different app. The tool's destination/removal
   semantics must be confirmed on an isolated disposable container first.
4. Reconcile database/WAL/SHM as one snapshot. Do not overlay an old database with
   a newer WAL or leave post-backup database files active. Any exact replacement
   (`--remove-existing-content true`) is destructive, requires explicit recovery
   approval and a preserved newer snapshot. No restore operation is authorized by
   this document or executed during installation.
5. Verify the restored remote inventory and a downloaded SQLite inspection copy,
   original-file hashes and record counts before normal launch.

No phone restore/downgrade rehearsal has been performed. A successfully verified
local copy is a recovery asset, not a guarantee of a fully tested recovery workflow.
If the user requires a tested whole-device recovery route, arrange an encrypted
Finder backup and confirm its completion instead of representing this as equivalent.
