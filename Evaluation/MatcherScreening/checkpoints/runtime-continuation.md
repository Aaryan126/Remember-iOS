# Performance-only continuation checkpoint

Implemented `screening2_runtime.py` and twenty focused regression tests. No original frozen experiment source, label, model setting, threshold policy or recorded prediction was edited. No package, phone or production change was made.

The separately frozen attempt is `fast-scan-attempt-01`, inside the existing run's `runtime-continuations/` directory. Its manifest SHA256 is `ee67d87b7b3e83a8b14c3025794aabfdb0c408374647ae3f43b1c52996ba8317`. It binds the new sources and execution document, original experiment manifest, pre-existing immutable records and permanent model exports. Existing models are reused, not duplicated. Only storage-guard aliases are replaced during execution; original training, scoring, audit and recovery functions are reused.

## Checks actually run

- `python -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q`: **170 passed**, 5.314 seconds.
- `python -m unittest discover -s scripts -p 'test_organization*.py' -q`: **22 passed**, 0.051 seconds.
- Runtime `prepare`: byte-count parity on all screening folders in three runs, **1,820,121,824 bytes each**. Original traversal: 0.383 / 0.348 / 0.362 seconds. New traversal: 0.126 / 0.122 / 0.117 seconds. This is approximately 3× faster scanning, not a promise of 3× faster training overall.
- Runtime `verify`: original and continuation freezes plus preserved artifacts verified.
- Runtime `run --resume --pause-after-steps 2`: restored C2 third-fold step 250, advanced to252, saved and exited successfully.
- Recovery blob loaded separately: model, optimizer, RNG and step252 verified. SHA256 `1e1ff12f9705ce800aa658304f01939884f65e68bc4c0d23503b531f308ebc76`.
- Normal `run --resume` restarted without the exercise flag; consult RESUME.md and live records for later progress.

Use the existing `RememberMatcherFeasibility/v1/venv` Python, not the system Python. The run argument for every runtime command is `--run Evaluation/MatcherScreening/runs/screen-attempt-01`.

## Unchanged safeguards and limitations

Every storage decision still scans both full roots afresh. No size cache, reduced check frequency or budget relaxation is used. The 4 GiB total screening cap, 10 GiB free reserve and planned-write allowance are unchanged. Failure telemetry now records the instantaneous used/free/planned bytes. The earlier transient storage pause cannot be reconstructed conclusively from its older logs.

Only superseded Stage 2 recovery blobs are rotated under the existing latest-two policy; all permanent fits, predictions and receipts remain. Previous feasibility and Stage 1 evidence are not removed. As before, an unexpected interruption may repeat work since the latest checkpoint and MPS continuation is not guaranteed bitwise identical.

This checkpoint does **not** complete Stage 2. At restart, 31/36 outer comparisons were saved; five comparisons, selected-family confirmation and the full audit/recommendation were still pending. No final test or deployment is authorized.
