# Approved cleanup completed — 24 September 2026

Deleted exactly the seven generated-output paths and two older restore points
in `CLEANUP-PROPOSAL.md`, following approval of both groups. No other deletion
was performed. The proposal remains an immutable record of the approved scope.

- Allocated target size: 1,427,587,072 bytes (1.33 GiB).
- Actual net free-space increase: **1,273,466,880 bytes (1.19 GiB)**.
- Free space immediately afterward: **12,379,815,936 bytes (11.53 GiB)**.
- Both newer protected backups rehashed before and after: 189 and 192 files.
  All eight original-file hashes also match the older restore points.
- Source, current signed products, warm simulator build cache, source archives,
  research results and Git metadata remain untouched.

The two older full restore points are permanently unavailable. Generated build
output can be rebuilt, though byte-identical signed binaries are not promised.
The newer protected restore points remain available. Net recovery may differ
from allocated size because of APFS sharing and concurrent disk activity.

Execution: `python3 scripts/provenance-first/search-handoff/cleanup-approved.py`.
Private aggregate receipt: `runs/search-handoff/cleanup-approved.json`.
The script refuses to overwrite its receipt or silently repeat the deletion.
The 10 GiB free-space reserve and 32 GiB growth cap remain unchanged.
