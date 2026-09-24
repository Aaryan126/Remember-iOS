# Second approved resource-only amendment

The user replied **“Yes u may”** to raising this checkpoint's cap to **8 GiB**,
retaining the **10 GiB free-space reserve**. This replaces only the operational
cap in the previous 5 GiB amendment. Original accounting, starting free-space
baseline, registered simulator accounting, frozen experiment, selection and saved
results remain unchanged. No cleanup, training, integration or other scope expansion.

The separate `budget8/approved_run8.py` wrapper verifies the previous approval,
all frozen experiment hashes, its own code/tests, and every JSON file saved in the
development/evaluation runs at the second stop, including hash and modification
time. Every command checks resources before acknowledging a pause and throughout
model or native work. It records its approval hash and peak passing resource usage.
The original 4/5 GiB failures remain failures and are preserved.

Use this wrapper for remaining commands from RESUME.md:

```sh
PYTHON='/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python'
APPROVED='scripts/provenance-first/checkpoint2/budget8/approved_run8.py'
"$PYTHON" -B "$APPROVED" resources
"$PYTHON" -B "$APPROVED" model cache --split evaluation --resume
"$PYTHON" -B "$APPROVED" model predict --split evaluation
"$PYTHON" -B "$APPROVED" model score --split evaluation
"$PYTHON" -B "$APPROVED" ledger prepare
"$PYTHON" -B "$APPROVED" ledger run --max-runs 1 --invariants
"$PYTHON" -B "$APPROVED" ledger run
"$PYTHON" -B "$APPROVED" ledger verify
```

Pause remains `python3 -B scripts/provenance-first/checkpoint2/run.py pause`.
Resume an interrupted command with `--resume` after verification. Do not repeat
preparation/freeze or change evaluation thresholds. Stop for review after the final
checkpoint report. No physical phone, downloads or paid API is required.
