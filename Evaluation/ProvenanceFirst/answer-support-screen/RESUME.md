# Stage B pause, resume and review stop

This is the separately approved screen after v2 technical qualification. Existing
v1/v2 folders, data, prompts and results remain read-only. No app or phone work.

Ask the coordinator to pause, or request it with:

```sh
python3 -B scripts/provenance-first/answer-support-screen/sb_runner.py pause
python3 -B scripts/provenance-first/answer-support-screen/sb_runner.py status
```

Wait for `worker.running: false` and owned-process exit confirmation before closing
the laptop. Native work is bounded to 60 seconds plus two-second cancellation grace,
with a separate 75-second host watchdog. Every dispatched request is spent, including
timeouts/interruption. Unknown reservations are never automatically retried.

On a clean boundary, resume the current split:

```sh
python3 -B scripts/provenance-first/answer-support-screen/sb_runner.py run --split development --resume
```

Completed units are verified and skipped without rewriting. Known errors remain in
the original denominators. If an execution is unknown or a request is reserved but
has no receipt, stop for investigation; never remove the reservation or reset counts.

Only an all-pass, saved and recomputable development decision permits:

```sh
python3 -B scripts/provenance-first/answer-support-screen/sb_runner.py run --split evaluation --resume
```

A failed development decision is a terminal review stop, not a pause. No held-out
inference, tuning, alternate model, retry selection or automatic integration follows.
Both splits together are limited to136 new calls,145 cumulative including prior9.
The original21GiB accounting allowance and10GiB reserve still apply.

Read-only verification and repeatable deterministic tests:

```sh
python3 -B scripts/provenance-first/answer-support-screen/sb_runner.py verify
python3 -B -m unittest discover -s scripts/provenance-first/answer-support-screen -p 'test_*.py'
```

`sb_qa.py` and `sb_runner.py audit` publish immutable receipts once, so do not rerun
them over existing receipts. For a later read-only audit, import `sb_runner.audit()`
without invoking its publication command. See STATUS.md/REPORT.md for the final
stopping point and limitations. No version-control actions are performed by agents.
