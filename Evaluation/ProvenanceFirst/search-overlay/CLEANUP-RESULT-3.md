# Approved cleanup 3 completed — 24 September 2026

All nine exact targets in `CLEANUP-PROPOSAL-3.md` were revalidated inside this
project, checked for tracked files, and removed after the user's approval.

- Free bytes before: 12,338,778,112.
- Free bytes after: 13,024,784,384.
- Measured net recovery: **686,006,272 bytes (654.23 MiB)**. Small differences
  from the 652.89 MiB allocation estimate reflect concurrent filesystem activity.
- Both protected phone backups were fully rehashed: 187 and 188 files verified.
- Simulator caches are regenerable. Four older videos and two rejected-test
  result bundles are permanently removed; their logs, reports and extracted
  images remain. Current successful results, recordings and frame traces remain.
- Source, models, data, dependencies, current simulator products, installed
  signed build, phone-build cache and latest backups were not removed.
- Receipt: ignored `runs/search-overlay/cleanup-approved-3.json`.
- No Git state changed. No deletion outside the nine approved paths.

This approval is exhausted. No additional deletion is authorized.
