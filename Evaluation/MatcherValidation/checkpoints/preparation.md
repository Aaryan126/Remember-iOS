# P0 saved — stopped for review

Date:2026-09-13. No worker is running. It is safe to close the laptop; no phone is required.

## Completed

- Wrote the prospective hybrid-versus-baseline plan and numerical contract.
- Implemented a shared acceptance gate for calibration selection and evaluation, fixing the previous threshold/gate mismatch **for new experiments only**. Historical verdicts remain unchanged.
- Authored and executing-agent-reviewed four fictional development-only libraries:40 text sources,180 pairs (52 same,36 related,56 unrelated,36 uncertain). This is a policy fixture, not the full benchmark or independent review.
- Implemented source/gold separation, all-pair projection, membership/ID checks, split/template leakage checks, cross-split near-duplicate screening, no-overwrite resumable publication and source/artifact integrity checks.
- Saved `runs/preparation-01/complete.json`, pilot input/gold files and structural audit. `benchmarkComplete` and `trainingStarted` are both false.

## Checks actually run

Using the existing feasibility virtual environment's Python:

| Command (repository-relative arguments) | Result |
| --- | --- |
| `-m unittest discover -s scripts/matcher-validation -p 'test_*.py' -q` |27 passed |
| `-m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q` |183 passed |
| `-m unittest discover -s scripts -p 'test_organization*.py' -q` |22 passed |
| `scripts/matcher-validation/prepare.py prepare` |P0 published |
| `scripts/matcher-validation/prepare.py verify` |Source/artifact hashes verified |
| `scripts/matcher-feasibility/screening2_headroom_v2.py verify --run Evaluation/MatcherScreening/runs/screen-attempt-01` |Original completion, runtime continuation and headroom continuation verified |

The first new-test run exposed a faulty test fixture: its low-score tail contained too few negatives, so accepting the whole fixture legitimately passed. Added low-scoring negatives to represent the intended failing tail; the selector was unchanged. All final checks passed.

The original screening completion SHA256 remains `dbf644d321dd50f7a455161dcf9d9a04a25a234122092d08b5f1270b03e0cefd`. No prior experiment artifacts, production code or Git state were changed. New files are confined to `Evaluation/MatcherValidation/` and `scripts/matcher-validation/`.

New directories occupied about196 KiB before this report; below1 MiB in total. The latest `df -h .` observation showed approximately14 GiB free, still above the10 GiB reserve. Recheck before the next stage; background disk usage can change independently of this experiment.

## Next decision

No newly trained model or accuracy result exists yet. P0 is ready to move to **P1: full benchmark authoring, review and release freeze**, estimated4–8 active Mac-only hours. It must not simply replicate the pilot topology with renamed entities. P1 will stop before training; label ambiguity, narrative leakage or inadequate review may require correction first.

P2 will then implement/run the fixed comparison and one-time evaluation: approximately8–16 additional active hours, provisional until throughput and retained-checkpoint storage are measured. Combined P1/P2 estimate12–24 active hours, excluding pauses/corrections. A trained-model pause exercise and storage preflight are required before long training. No old held-out evaluation, phone work or app integration follows automatically.

Resume instructions and limitations: [README](../README.md). Detailed staged scope: [PLAN](../PLAN.md).
