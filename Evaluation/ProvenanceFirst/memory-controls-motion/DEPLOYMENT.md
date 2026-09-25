# Control-motion deployment — 25 September 2026

Installed in place on the user's iPhone after explicit authorization. Remember
was reopened after verification. The app was never uninstalled.

The signed build passed, and its sources matched the final five passing simulator
return-navigation tests. The physical-phone smoke passed native Back and slow
swipe-back, checking restored search, Add and tab controls and stable Add position.
Detailed animation frame review remains simulator-based.

Verified pre-install and post-install snapshots confirmed SQLite integrity,
unchanged rows for all 8 memories, unchanged bytes for all 8 originals, and all
172 historical events unchanged. No pending-work or cloud-assistance preflight
blockers were found.

Commands run successfully with the prefix
`python3 -B scripts/provenance-first/memory-controls-motion/deploy.py`:

- `prepare`, `build`, `ready`
- `backup`, `inspect-backup`, `install`
- `smoke`, `post-backup`, `compare`, `launch`

Receipts are under `../runs/memory-controls-motion-device/`:

- Signed build operation: `1790306800094831000`.
- Verified backup: `backup-1790306855454405000` (200 files).
- In-place install operation: `1790306906184054000`.
- Passing physical-phone smoke: `1790306933750080000`.
- Verified post-install snapshot: `post-install-1790306984780489000` (201 files).
- Preservation comparison: `preservation.json`.

The prior build cache was copied using an APFS copy-on-write clone; the six prior
signed product hashes remained unchanged. The original 32 GiB cumulative growth
allowance and 10 GiB free-space reserve remained active. No caches were deleted
and no Git state was changed. Deployment tooling is in this task's `deploy.py`
and `MainAppSmokeTests.swift`; prior deployment tooling was preserved.
