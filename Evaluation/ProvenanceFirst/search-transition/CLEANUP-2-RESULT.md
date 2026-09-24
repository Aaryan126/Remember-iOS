# Second approved cleanup — completed

23 September 2026. The user approved the exact 54-directory list in
[Cleanup proposal 2](CLEANUP-PROPOSAL-2.md). This execution does not authorize any
further cleanup.

All 54 candidates were revalidated against their expected absolute real paths,
listed allocation and absence of tracked Git files. No matching build/research
worker was active. Removed only these directories using `rm -r` with explicit
absolute paths; no parent folders, outside-project files or `.git` were changed.

Measured allocation: 2,495,288 KiB (2.380 GiB). Disk free space before/after was
10,937,380 / 13,434,712 KiB, an observed net gain of 2,497,332 KiB (2.382 GiB),
leaving 12.812 GiB free. Small differences reflect concurrent disk activity.

These files are not in Trash; affected compiler caches/intermediates regenerate
on a future build. Source, models, signed products, datasets, results, logs,
xcresult bundles, checkpoint archives, phone backups and active build caches were
preserved. The unchanged storage guard passed; the focused transition regression
was resumed. No claim of passing tests or installed fix follows from cleanup alone.
