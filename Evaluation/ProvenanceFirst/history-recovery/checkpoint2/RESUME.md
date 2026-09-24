# Ranking checkpoint — pause/resume

**Completed and stopped for review.** See [report](REPORT.md). There is no pending
inference to resume and no qualified candidate to integrate. Commands below are
the preserved reproduction/recovery instructions, not approval for a new run or
threshold search. Saved-results audit (no model inference):

```sh
python3 -B scripts/provenance-first/history-ranking/qa/verify_checkpoint.py
```

Mac only. No phone, app changes, new weights, cloud calls or downloads. The original
shared disk baseline, 18 GiB growth cap and 10 GiB reserve remain in force.

Pause with:

```sh
python3 -B scripts/provenance-first/history-ranking/rk_runner.py pause
```

Wait for the active text/library unit to finish and worker.json to say running=false.
The marker alone is not confirmation that closing the laptop is safe. A stopped
worker has no background experiment process. Source hashes/caches verify on resume.

Initial preparation (do not alter existing frozen artifacts):

```sh
python3 -B -m unittest discover -s scripts/provenance-first/history-ranking -p 'test_*.py'
python3 -B scripts/provenance-first/history-ranking/rk_runner.py freeze
python3 -B scripts/provenance-first/history-ranking/rk_runner.py qualify
```

If compatibility.json has supported=true, cache a bounded development unit, capture
the pause proof, then resume:

```sh
python3 -B scripts/provenance-first/history-ranking/rk_runner.py cache --max-units 1
python3 -B scripts/provenance-first/history-ranking/rk_runner.py snapshot
python3 -B scripts/provenance-first/history-ranking/rk_runner.py pause
python3 -B scripts/provenance-first/history-ranking/rk_runner.py cache --resume
python3 -B scripts/provenance-first/history-ranking/rk_runner.py pause-verify
```

If C is unsupported, skip embedding caches; use a bounded score unit for the pause
proof instead. Do not substitute another model or turn resource failures into a
compatibility fallback. Complete development scoring and freeze selection:

```sh
python3 -B scripts/provenance-first/history-ranking/rk_runner.py score --resume
python3 -B scripts/provenance-first/history-ranking/rk_runner.py select
```

Only after selection.json and selection.seal.json exist, run held-out inference:

```sh
python3 -B scripts/provenance-first/history-ranking/rk_runner.py cache --split evaluation --resume
python3 -B scripts/provenance-first/history-ranking/rk_runner.py score --split evaluation --resume
python3 -B scripts/provenance-first/history-ranking/rk_runner.py evaluate
```

Skip evaluation cache if C was unsupported. Repeating completed commands verifies
and reuses immutable outputs. `evaluate` can recompute metrics from saved score
tables without inference; it must produce identical results. Do not rerun a search
on evaluation labels. A nonqualified development diagnostic remains nonqualified.

Finish by checking citation/scope binding, old checkpoint preservation, tests,
pause proof and worker shutdown; write the result report, then stop for user review.
Global-search results do not measure the outside-River or automatic-membership gate.
