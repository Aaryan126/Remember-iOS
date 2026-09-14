# Authorized temporary checkpoint headroom

The user explicitly approved temporary 4.5 GiB headroom on 2026-09-12, keeping the final 4 GiB screening-assets target and 10 GiB free-space reserve. This supplements, and never rewrites, the original Stage 2 and performance-continuation freezes.

`checkpoint-headroom-attempt-01` binds the new driver/tests and this document, the earlier runtime continuation's files, all pre-existing immutable run records, permanent model exports and the starting recovery receipt. Original scripts, data, training, thresholds, selected candidates and evaluation remain unchanged. No final-test access, phone, packages, app integration or Git mutation is authorized.

The new driver reuses the fresh full-folder scanner, one-worker lock, cooperative pause, lossless checkpoints and latest-two recovery policy. During confirmation, each existing planned-write check uses a 4.5 GiB ceiling and subtracts planned bytes from free space before requiring 10 GiB. At the original final-audit boundary it switches back to the 4 GiB ceiling, records a storage check, and keeps that stricter ceiling through the audit. If the final cap cannot be met, it pauses without deleting evidence or declaring completion. Completed-run verification also checks actual retained bytes against 4 GiB. Subsequent unrelated disk usage can alter current free space; the completion receipt records the free-space check at execution time.

Only capacity aliases and the original driver's final-audit boundary hook change at runtime; both restore on exit. The final audit and all statistical functions are reused unmodified. There is no checkpoint-frequency, seed, fit, score or label change. Prior manifests retain their historical 4 GiB execution limit; this separate authorization explains the temporary exception.

Use the existing feasibility virtual environment with `screening2_headroom.py prepare|run|pause|verify --run Evaluation/MatcherScreening/runs/screen-attempt-01`. Execution requires `--resume`; a recovery exercise additionally uses `--pause-after-steps 2`, omitted on ordinary resumes. Completed runs only verify. Preparation and execution take the existing worker lock. Tests and a two-step recovery exercise precede normal continuation. Wait for worker exit before closing the laptop.

Finish the already-selected C3/D3 confirmation for all three seeds, audit and report, then stop for user review. Confirmation uses already-inspected development libraries and does not override the observed outer-screen reliability failures.
