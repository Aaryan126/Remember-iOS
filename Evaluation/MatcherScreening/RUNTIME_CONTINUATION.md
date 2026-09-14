# Stage 2 performance-only continuation

Authorized after the user accepted the proposed runtime fix: “Okay u can carry on as you feel is best.” This is a separately frozen operational attempt, `fast-scan-attempt-01`, continuing the existing statistical experiment and its saved optimizer state.

The original Stage 2 scripts, manifest, settings and evidence remain unchanged. The supplemental manifest binds its own source snapshots and this document, the original manifest, all pre-existing immutable run records and permanent model exports. It records the starting recovery receipt. It does not duplicate large models, restart the statistical screen, select a different seed, change thresholds or open the final test.

Only two runtime behaviors change:

1. Enumerate files with `os.scandir` and cached directory-entry metadata rather than repeatedly constructing and examining `Path` objects. Every call still performs a fresh complete scan of both original screening roots. File sizes are logical bytes, including file links just as before; directory links are not traversed. There is no stale size cache, reduced check frequency or relaxed limit.
2. Record used, free and planned bytes when a storage check fails, so a later space recovery does not erase the diagnostic evidence.

The legacy modules import storage helpers by value. The continuation explicitly replaces only their `capacity` aliases for the duration of execution, restores them on exit, and calls the original training/evaluation driver. The original capacity inequalities remain unchanged: total screening assets plus planned save <=4 GiB; free space minus planned save >=10 GiB. Original locking, signal handling, checkpoint frequency, lossless exports, latest-two recovery retention, training, scoring, calibration, selection and final audit are reused.

Before restarting: regression tests, exact byte-count parity on the stopped live experiment, frozen lineage verification and a two-step cooperative pause/resume exercise. The timing comparison is a storage-scan benchmark, not a promise of an equivalent end-to-end speedup. No phone or new dependency is needed.

Use the existing feasibility venv Python with `screening2_runtime.py prepare|run|pause|verify --run Evaluation/MatcherScreening/runs/screen-attempt-01`. Running requires `--resume`; the live recovery exercise additionally uses `--pause-after-steps 2`. Subsequent resumes omit that flag. A completed run only verifies and exits. Final handoff must verify both the original and supplemental freezes via this driver, then stop for user review.
