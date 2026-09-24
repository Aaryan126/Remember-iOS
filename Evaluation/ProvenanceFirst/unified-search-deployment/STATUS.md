# Unified-search main-app update — complete, user review next

23 September 2026.

- Signed normal-app/extension build passed: operation 1790164816667712000.
- Verified backup: 182 files; SQLite healthy; 11 migrations match.
- Pre-update library: 8 indexed memories, 171 provenance events; cloud assistance
  disabled, no pending imports/shared inbox/video requeue requiring launch review.
- In-place installation succeeded: operation 1790164936489249000. No uninstall.
- Normal-app navigation smoke passed 1/1, zero failures/skips/reported runtime warnings.
- Post-update snapshot verified: all 8 memory rows, 171 history events and 8 original
  files unchanged; SQLite integrity passed. No data restoration was required.

The app is ready for normal use. No deployment worker remains running after the
checkpoint is saved. Private backups, operation logs and test products are under ignored
`Evaluation/ProvenanceFirst/runs/unified-search-deployment/`.
No source-level organizer/model/threshold change or Git state change in this step.

Use Memories → Search your memories → Include history / Source text only. Ask AI
remains separate. Do not start another experiment or reinstall automatically.
