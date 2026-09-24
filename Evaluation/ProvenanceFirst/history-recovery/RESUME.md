# History recovery checkpoint 1 — operating instructions

No phone is needed. Do not run checkpoint 2, train models, call APIs, change Git or
read the personal vault. The earlier experiments are frozen and remain unchanged.

## Pause

```sh
python3 -B scripts/provenance-first/history/control.py pause
```

This signals the Python coordinator and native probe. Wait for the current library
unit and active author/reviewer agents to stop and save their work. The marker alone
is not a safe-to-close confirmation. Builds can be cancelled and rebuilt; completed
library/projection receipts are immutable and checked on resume.

## Check resources and preservation

```sh
python3 -B scripts/provenance-first/history/control.py resources
python3 -B scripts/provenance-first/history/control.py verify
python3 -B -m unittest discover -s scripts/provenance-first/history -p 'test_*.py'
```

The approved 18 GiB guard retains the original shared baseline and 10 GiB reserve.
Resource failures require user action/approval, never automatic cleanup or reset.

## Resume sequence

Before freezing, complete independent reviews and resolve substantive findings.
Preserve earlier review findings and re-review changed labels. `validate` is not
an independent review. Freeze only after native sources build and inputs are ready.

```sh
python3 -B scripts/provenance-first/history/benchmark.py validate
python3 -B scripts/provenance-first/history/native_driver.py prepare --resume
python3 -B scripts/provenance-first/history/native_driver.py build --resume
python3 -B scripts/provenance-first/history/benchmark.py freeze --resume
python3 -B scripts/provenance-first/history/benchmark.py prepare --resume
python3 -B scripts/provenance-first/history/native_driver.py run --max-runs 1 --invariants --resume
```

The first native unit is used to prove pause/resume. Save receipt/artifact hashes
and modification times, request pause, verify workers stopped, then continue:

```sh
python3 -B scripts/provenance-first/history/native_driver.py run --resume
python3 -B scripts/provenance-first/history/verify_coverage.py --complete --save
```

Do not repeat `--invariants` once its receipt exists. The remaining run executes one
library per native invocation and verifies coverage after each. Errors retain logs,
incomplete attempts and earlier valid receipts. Never overwrite frozen inputs/code;
a substantive change after freeze needs an explicitly documented new attempt.

At completion verify all preserved hashes, shutdown only this experiment's simulator
if no other task is using it, write a report, and stop for user review. Coverage is
candidate availability, not relevance, precision, recall@k or app release readiness.
