# Approved cleanup completed — 24 September 2026

The user approved `CLEANUP-PROPOSAL-2.md`. All 19 exact targets were revalidated
inside the project, checked for tracked files, and removed. No additional target
was deleted and no Git state changed.

- Free bytes before: 10,861,551,616.
- Free bytes after: 11,936,473,088.
- Measured net gain: **1,074,921,472 bytes (1.00 GiB)**, versus 2.28 GiB allocated.
  Allocated size need not equal recovered space; APFS sharing/snapshots and
  concurrent disk activity can affect the difference.
- Both latest full phone snapshots were rehashed before cleanup: 187 and 188
  files verified. Current builds, source, models, data and new motion traces remain.
- Seven superseded recordings are permanently unavailable. The 12 build-output
  directories can be rebuilt, subject to SDK/signing availability; their exact
  old binaries are no longer retained.
- Detailed execution receipt: ignored
  `runs/search-overlay/cleanup-approved-2.json`.

This approval is exhausted. Further deletion requires a new proposal/approval.
The 10 GiB free-space reserve and 32 GiB cumulative cap remain unchanged.
