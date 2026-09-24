# Answer-format v2 checkpoint operations

This sibling experiment preserves the failed v1 qualification and its one spent
request. It permits preparation and at most eight fresh neutral local controls,
not benchmark inference or production integration. Cumulative ceiling: 145;
approved resource allowance: 21 GiB against the original baseline, with 10 GiB free.

## Safe pause

```sh
python3 -B scripts/provenance-first/answer-support-format-v2/v2_runner.py pause
python3 -B scripts/provenance-first/answer-support-format-v2/v2_runner.py status
```

Wait for `worker.running: false` and confirmation that its owned compiler/probe
exited before closing the laptop. A running native request has a 60-second deadline,
2-second cancellation grace and separate 75-second host watchdog. Interrupted or
unknown requests remain spent; they are never silently retried. Completed units,
raw receipts and reservations are saved before the next dispatch.

After an ordinary clean-boundary pause, the coordinator may use the same approved
command with `--resume`. A failed control or unresolved reservation is a review
stop, not an invitation to resume past the failure. Never change the prompt, rubric,
controls, original data or resource baseline to resume a frozen run.

## Verification without inference

```sh
python3 -B scripts/provenance-first/answer-support-format-v2/v2_runner.py verify
python3 -B -m unittest discover -s scripts/provenance-first/answer-support-format-v2 -p 'test_*.py'
```

`v2_qa.py tests` and `v2_qa.py audit` create immutable checkpoint receipts once;
do not rerun those publication commands over an existing receipt. Direct unittest
and `v2_runner.py verify` are repeatable. These checks do not request model outputs.

The final REPORT.md and STATUS.md describe the actual stopping point. Even eight
passing technical controls would only qualify a separately approved development
and held-out screen, not establish real-user accuracy or authorize integration.
