# Stage A decision checkpoint — do not automatically resume inference

Stage A reached its required first-failure stop. Preparation, native replay,
retrieval, independent packet review, compilation and integrity audit are saved.
The first neutral control returned the correct cited sentence rather than the
frozen minimal span. See REPORT.md and `stage-a-stop.json`.

**Do not retry the failed control, run the remaining seven, start Stage B, tune the
prompt, alter gold/scoring, or move to phone/cloud inference without a new decision.**
No process is running; the laptop may be closed. Phone connection is unnecessary.

## Read-only verification

From the repository root:

```sh
python3 -B scripts/provenance-first/answer-support/as_approved.py runner status
python3 -B scripts/provenance-first/answer-support/as_approved.py runner verify
python3 -B scripts/provenance-first/answer-support/as_approved.py resources
git diff --check
```

The explicit adapter applies the approved 21 GiB allowance. The original controller,
native build, accounting baseline and 10 GiB reserve remain unchanged. All bindings
must match. `resource-policy-frozen.json` binds the amendment to the Stage A freeze.

## Next decision, not an active task

Decide whether the product accepts a concise verbatim supporting sentence as well
as a minimal answer. Recommendation: yes, with factual/citation correctness and
minimality reported separately. Estimate 30–60 minutes for a bounded contract and
scoring review. Any revised test must be versioned, predeclared, independently
reviewed and separately approved. Preserve this failed result; do not regrade it.
Benchmark capability remains unmeasured.

## Checks this continuation

- `as_approved.py runner native --resume`: completed; 16/16 total libraries.
- `runner retrieve --resume` and `runner packet-labels`: completed.
- `runner build-controls`: compiled with one non-fatal deprecation warning.
- `as_approved.py qa tests`: 276 passed, including all 80 answer-support tests.
- `runner freeze` and `qa audit`: passed (128 queries, 384 citation occurrences).
- `runner controls`: exit 1 at `control-extract-1`, exact-span mismatch; native
  execution and citation validation succeeded. No additional inference.
- `runner verify`, `resources` and `git diff --check`: passed after the stop.

Commands abbreviated above use the same `python3 -B scripts/provenance-first/answer-support/as_approved.py`
prefix. No Git state was changed. Raw inputs, outputs, failed attempts, all reviews,
the frozen dataset and code, test/audit reports and resource amendments are saved.

## Historical resource-hold checkpoint — superseded; do not execute its continuation list

19 September 2026. **Resource hold, not a model-quality failure.**

## Saved

- 16 independently cross-reviewed fictional libraries, 128 questions, 138 events;
  corpus, gold, split definitions and reviews frozen before any model output.
- Source-only exports and native batches prepared. Pause/resume preserved both
  existing first-library files, including their modification times.
- New isolated simulator launcher built from unchanged index/harness/production
  source copies and the already-local dependency. Original experiment preserved.
- Three complete native replays: dev01–03, 25 event prefixes, 24 queries and three
  database reopen checks. All original failed-attempt evidence is retained.
- Exact-span/provenance validation, conservative scoring, fixed retrieval runner,
  bounded neutral-control runner and Stage-A-only dispatch restrictions implemented.
- Mac readiness metadata: available, 8,192-token context. **Zero generation
  reservations; no model quality or generation readiness claim.**

Machine checkpoint: `resource-hold-checkpoint.json`. It binds code, corpus,
preparation, native build, completed output and prior preservation verification.
It records Stage A incomplete and Stage B disallowed, worker stopped, simulator
shutdown, and the recovered third host receipt. That receipt was verified from
the durable native ledger/projection/reopen artifacts, not rerun.

## Why stopped

`python3 -B scripts/provenance-first/answer-support/as_runner.py native --resume`
exited 1 with `19 GiB growth cap exceeded; preserve baseline and stop`.
The checkpoint measured 20,847,263,744 conservative-growth bytes (19.42 GiB),
above the 20,401,094,656-byte cap, with 24,115,703,808 bytes free (22.46 GiB).
The original baseline and 10 GiB free reserve are unchanged. Accounting includes
whole-Mac free-space decline, not just new experiment artifacts.

No cleanup or larger limit is authorized. Prefer freeing about 2 GiB elsewhere
and rechecking. Alternatively obtain explicit approval for a separately recorded
resource amendment; do not silently edit the cap or reset its baseline. Because
native build receipts bind controller source, any controller amendment also needs
an explicit provenance-preserving binding review, not overwritten build receipts.

The original binary also rejected the new input directory before replay and has
an output guard limited to its old workspace. That failure is preserved. The new
isolated launcher resolves it without weakening either workspace boundary.

## Coordinator continuation after resource preflight passes

1. Verify every checkpoint hash, frozen corpus, old checkpoint, new native build
   and current disk accounting. Confirm no live worker and simulator shutdown.
2. Resume native replay; completed dev01–03 are verified and skipped:
   `python3 -B scripts/provenance-first/answer-support/as_runner.py native --resume`.
3. Run fixed retrieval with `as_runner.py retrieve --resume`, then
   `as_runner.py packet-labels`. No fixture/scorer tuning against these outputs.
4. Ask the independent author/reviewer agents to review opposite-split packet
   labels and actual evidence. Save hash-bound `packet-reviews/*.json`.
5. Build the controls using `as_runner.py build-controls`; freeze all code, data,
   reviews and runtime via `as_runner.py freeze` before neutral inference.
6. Run `as_runner.py controls`: at most eight requests, stop on first failed
   technical control, no retries/prompt selection. Benchmark requests stay zero.
7. Run final `as_qa.py tests`, `as_qa.py audit`, `as_runner.py verify`, and
   `git diff --check`; save report and stop for user review. Do not start Stage B.

Estimated remaining Stage A effort: **1–2 active hours after resource clearance**,
assuming runtime and review checks pass. Stage B remains separately approved.
Phone connection is not needed.

## Checks actually run

- `python3 -B -m unittest discover -s scripts/provenance-first/answer-support -p 'test_*.py'`: 74 passed.
- Same command with `-s scripts/provenance-first/history-ranking`: 31 passed.
- Same command with `-s scripts/provenance-first/history`: 22 passed.
- `as_runner.py build-native`: completed; Xcode reported BUILD SUCCEEDED.
- `as_runner.py native --max-units 1 --resume`: completed.
- `as_runner.py native --resume`: stopped at resource guard; three total native
  libraries subsequently verified, not all 16 complete.
- `as_checkpoint.py`: completed; prior/corpus/build hashes and shutdown verified.
- `git diff --check`: passed. No Git state was changed.

The full combined regression receipt, retrieval coverage, packet review,
Foundation Models compilation and all eight generation controls remain pending.
