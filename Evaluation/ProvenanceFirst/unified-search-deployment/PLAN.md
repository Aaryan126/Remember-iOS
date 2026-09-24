# Approved unified-search main-app update — 23 September 2026

1. Preserve prior receipts; reuse archived deployment bindings and local GRDB.
2. Build/sign the real app and extension with their existing bundle/team/app-group
   identities, including the bundled D3 matcher. Use the prior SDK module cache;
   reserve 768 MiB for this cached build, continuously enforce the storage ceiling.
3. Stop Remember and copy both private app/group containers. Verify inventories,
   hashes, SQLite integrity and migration compatibility. Review pending imports,
   video requeue and cloud preference before allowing a first launch.
4. Install in place only after a verified backup and enough room for a full post
   snapshot. No uninstall, cleanup, data restore, model-policy change or Git writes.
5. Run one normal-app navigation test with a fictional no-match query. Do not open
   personal sources, invoke AI, mutate memories, or export personal screenshots.
6. Snapshot again, compare all memory rows, prior history events and original bytes,
   reopen the app, save the checkpoint and stop for user review.

The approved additional cumulative allowance is bounded to 1 GiB (32 GiB total);
the 10 GiB free reserve and original baseline remain unchanged. Insufficient actual
free space, a failed compatibility check or unexpected startup work stops deployment.
Private copies/logs are ignored and owner-readable only. PAUSE stops new units.
