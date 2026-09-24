# Approved resource-only amendment

The user replied **“yes”** to raising this checkpoint's growth cap from 4 GiB to
**5 GiB**, retaining the **10 GiB free-space reserve**. The original stop, protocol,
resource baseline and comparison manifest remain unchanged as historical evidence.
This supplements only the protocol's resource limit; no model, policy, thresholds,
metrics, dataset or split changes are authorized. No cleanup or baseline reset.

The approved wrapper binds this amendment and its own code/tests by hash. It
verifies the original comparison manifest and all 317 pre-amendment saved units,
including their modification times. It replaces only the resource-check function
in the runner process, using the original accounting formula and original resource
baseline with a 5 GiB cap. Both model and native replay processes use this check;
the 10 GiB reserve and all identity, pause, chronology and quality checks remain.
Each invocation saves its approval hash, arguments, observed peak passing growth
and any failure. A failed resource check stops work; there is no automatic extension.

From the repository root, use the existing model interpreter with `-B`:

```sh
PYTHON='/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python'
APPROVED='scripts/provenance-first/checkpoint2/budget5/approved_run.py'
"$PYTHON" -B "$APPROVED" resources
"$PYTHON" -B "$APPROVED" model cache --resume
```

For subsequent commands from RESUME.md, replace `pc_runner.py` with
`approved_run.py model`, and `pc_ledger.py` with `approved_run.py ledger`.
Do not repeat the original preparation/freeze. Pause remains
`python3 -B scripts/provenance-first/checkpoint2/run.py pause`.
No phone, downloads, paid API, app integration or Git writes are needed.
