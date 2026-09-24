# Approved cleanup completed — 24 September 2026

The user approved the [35-directory proposal](CLEANUP-PROPOSAL.md). All 35 exact
targets were revalidated and removed successfully; this approval is exhausted.
No other directories were deleted, and no Git state was changed.

- Before removal: 11,383,263,232 bytes free.
- After removal: 14,740,930,560 bytes free (13.73 GiB).
- Net recovered: 3,357,667,328 bytes (3.13 GiB).

Net recovery differs from the 3.60 GiB measured directory allocation because of
filesystem sharing and concurrent disk use. Free space had also changed since
the proposal's initial measurement.

Before deletion, every target was checked for project containment, symlinks,
nested `.git`, tracked files and overlap with latest completion bindings. Both
retained latest snapshots were fully rehashed: 187 pre-install files and 188
post-install files matched their verified manifests. No build/backup worker was
running on the targets.

The 12 older app-container snapshots were permanently deleted, not moved to
Trash; those exact historical restore points are no longer available. Their
metadata and reports remain. The 15 generated project copies and 8 duplicate
dependency copies can be recreated. Latest backups, active work, signed builds,
original assets, research data, archived baselines, motion recordings and test
results remain intact, including the dependency/cache used by signed builds.

The existing 10 GiB free-space reserve and 32 GiB growth cap remain unchanged.
