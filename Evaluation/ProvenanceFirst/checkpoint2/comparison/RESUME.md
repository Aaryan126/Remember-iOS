# Current-runtime comparison: resume safely

Mac only. No phone, downloads, paid API, training, production app or personal vault.
The original run used a 4 GiB cap. After its resource stop, the user approved a
5 GiB cap, then an 8 GiB cap, each with the same 10 GiB free reserve. Use the latest
hash-bound wrapper in [BUDGET-AMENDMENT-8GIB.md](BUDGET-AMENDMENT-8GIB.md) for remaining
model/ledger commands. Earlier amendments and failures remain historical evidence.
The commands below document the original workflow; do not repeat preparation.
Do not delete prior artifacts or modify frozen code to bypass a failed check.

Run from the repository root using the existing interpreter:

```sh
PYTHON='/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python'
RUNNER='scripts/provenance-first/checkpoint2/comparison/pc_runner.py'
LEDGER='scripts/provenance-first/checkpoint2/comparison/pc_ledger.py'
```

Before the initial run, execute the tests in all three directories:

```sh
python3 -B -m unittest discover -s scripts/provenance-first -p 'test_*.py'
python3 -B -m unittest discover -s scripts/provenance-first/checkpoint2 -p 'test_*.py'
python3 -B -m unittest discover -s scripts/provenance-first/checkpoint2/comparison -p 'test_*.py'
```

The preparation command freezes comparison source/protocol hashes. Do not edit
those files afterwards; a necessary correction needs a preserved, distinct attempt.

```sh
"$PYTHON" -B "$RUNNER" prepare
"$PYTHON" -B "$RUNNER" cache --max-units 1
python3 -B scripts/provenance-first/checkpoint2/run.py pause
"$PYTHON" -B "$RUNNER" cache --resume
"$PYTHON" -B "$RUNNER" predict
"$PYTHON" -B "$RUNNER" select
"$PYTHON" -B "$RUNNER" prepare-evaluation
"$PYTHON" -B "$RUNNER" cache --split evaluation
"$PYTHON" -B "$RUNNER" predict --split evaluation
"$PYTHON" -B "$RUNNER" score --split evaluation
"$PYTHON" -B "$LEDGER" prepare
"$PYTHON" -B "$LEDGER" run --max-runs 1 --invariants
"$PYTHON" -B "$LEDGER" run
"$PYTHON" -B "$LEDGER" verify
```

Pause with `python3 -B scripts/provenance-first/checkpoint2/run.py pause`.
Wait until the active coordinator reports stopped before closing the laptop.
Model cache units save after each source or bounded pair batch; predictions and
native replay save at library/order boundaries. Use the same interrupted command
with `--resume` to acknowledge a pause only after checking its frozen identities.
Never run multiple coordinators at once. `--max-units` / `--max-runs` stop at a
bounded number of new units and retain existing receipts without rewriting them.

For a native resume, use `run --resume` without `--invariants` if invariant receipts
already exist. The native command boots only the registered fictional-only
simulator, checks the installed probe's binary, and never opens Remember's vault.
After native work, shut down only that simulator if this experiment started it:

```sh
xcrun simctl shutdown C530FCC2-DD67-4115-97D9-C4E34807EC57
```

Before final handoff, verify all model/prediction envelopes and native receipts,
repeat metrics from saved predictions, record resources and pause/resume evidence,
and stop for user review. No integration or fresh tuning follows automatically.
