# Comparison status — complete, stopped for review

**The final comparison is complete.** All 96 native replays and 143 Python tests
passed, but neither B nor C met the quality gates. Metrics reproduced identically
from saved predictions, pause/resume was verified, and the isolated simulator was
shut down. No production app behavior changed. See [REPORT.md](REPORT.md),
[result.json](result.json) and [checkpoint.json](checkpoint.json).

The next recommended direction is history-aware evidence retrieval and relevance
filtering/abstention, followed by fresh held-out evaluation—not promotion of these
variants. Work stops here for user review.

## Historical progress at the second resource stop

The user subsequently approved the [8 GiB resource-only amendment](BUDGET-AMENDMENT-8GIB.md).
The frozen experiment and all 1,732 JSON files saved at the second stop were
verified unchanged before resuming. The second stop below is historical; remaining
work subsequently completed with the same 10 GiB reserve and no new policy tuning.

At that stop, checkpoint 2 was **not complete**. Development selection was complete; held-out
evaluation inference is partially saved, with no evaluation policy predictions or
metrics yet. No production app changes, phone test, downloads or paid API calls.

## Completed

- 137 tests passed: 55 original checkpoint, 31 compatibility/control, 45 comparison,
  and 6 resource-amendment tests. `git diff --check` passed.
- Original comparison manifest/code, thresholds and fixture identities preserved.
- All 317 units saved before the 5 GiB amendment verified unchanged by hash/mtime.
- Development: 117 embeddings, 501 neural pair scores, 501 combined scores,
  and 120 library/order/policy traces complete.
- The selection was frozen before evaluation inference. Evaluation now has
  109/109 embeddings and 376/430 neural pair scores; 54 neural pairs remain.
- Model-cache pause/resume proof passed. Current experiment workers are stopped.

## Development findings only

The 12 development libraries each have two correlated event orders. The following
counts are not independent samples or estimates of real-user accuracy.

| Placement policy | Automatic edges | Correct | Wrong | Precision |
| --- | ---: | ---: | ---: | ---: |
| A: current-runtime D3 reference | 73 | 45 | 28 | 61.64% |
| C: production threshold | 73 | 45 | 28 | 61.64% |
| C: 0.99 threshold | 66 | 46 | 20 | 69.70% |
| C: 0.995 threshold | 52 | 39 | 13 | 75.00% |

None met the frozen >=95% precision / >=20 automatic-edge development gate.
Therefore `Coff`, the prescribed suggestions-only fallback, was selected. It makes
zero automatic attachments; this is **not** 100% precision or an automatic-policy
success. B's placement behavior is exactly A's. Evaluation thresholds will not be
changed after seeing evaluation outputs.

Development evidence recovery also shows a tradeoff: B and C's combined top-three
results increased library-macro recall from 50.46% to 67.13%, but their outside
suggestion precision was only 8.11% for B and 10.57% for the selected C fallback.
These do not meet the >=90% outside-suggestion precision gate. Current-source lexical
recovery, noisy suggestions and project identity need to be assessed separately.
These are preliminary development findings, not the final held-out verdict.

## Resource stop and remaining work

The user approved raising the cap from 4 to 5 GiB, with the 10 GiB free reserve
unchanged. The second stop occurred at approximately **5.22 GiB** conservative
growth, with **36.66 GiB free**. Directly tracked experiment/script files were about
0.30 GiB, plus 2.13 GiB registered simulator growth. The guard also counts the
whole-Mac free-space decline, including changes outside those tracked directories.
System swap allocation increased from 8 to 9 GiB during this work; that is evidence
of system-level disk activity, not a complete attribution of the difference.

No files were deleted and no baseline or cap was silently changed. The exact
receipts are `resource-stop-01.json`, `budget-5gib.json`, `resource-stop-02.json` and
`checkpoint.json`. The last contains the evaluation-specific resume command.

At that stop, before resume the approved resource check had to pass or the user had to explicitly
approve another budget amendment. Then finish the 54 neural pairs, combined scores,
48 evaluation policy traces and held-out metrics; run the 96 native ledger replays,
native pause/resume/invariant checks; and write the final report. Estimated remaining
active time: 20–40 minutes if no further blockers. Stop for user review afterwards;
do not start integration or further tuning automatically.
