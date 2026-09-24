# Main-app deployment — completed, user review next

The normal Remember app has been installed in place and reopened. REPORT.md records
the passing normal-app navigation smoke, verified backup and exact data preservation.
No deployment worker is running. It is safe to disconnect the phone.

Do not rerun install, restore a backup, reinitialize the repository or start model
experiments automatically. The next action is the user's normal-app review at
Threads → More (…) → Search saved evidence. A subsequent change needs its own
bounded scope and must preserve the current checkpoint/source bindings first.

Verify this checkpoint's checkpoint-stop.json hashes before a subsequent change.
`deploy.py verify-old` verifies the previous media checkpoint, using the explicitly
archived prior docs/provenance-first.md bytes with the original hash; it does not
rewrite the earlier receipt. Current app/build source bindings are in the private
run preparation.json. Signed product checks use signed-build.json.

Private backups:

- runs/main-app-deployment/backup-1789918416575368000: before installation.
- runs/main-app-deployment/post-install-1789918690324493000: after normal-app smoke.

Paths are relative to Evaluation/ProvenanceFirst. Retain original manifests and raw
SQLite/WAL/SHM/original files. Any recovery is a separate explicitly approved data
operation; see RECOVERY.md. Do not expose private snapshot contents in tool output,
documentation or version control. No restore/downgrade rehearsal was performed.

Resource approval: 31 GiB conservative growth, original baseline, 10 GiB reserve.
Check actual headroom before future build/backup work. Current approval does not
authorize arbitrary cleanup or a new experiment. Previously recorded 28 GiB holds
remain historical; no original accounting or old approval was reset.
