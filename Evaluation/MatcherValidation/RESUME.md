# Current stage: P2 complete; preparation checkpoint awaiting user confirmation

All twelve fits and evaluation in `runs/validation-02` are complete. The all-seeds gate failed: seeds 17 and 41 missed the 95% precision requirement; seed 29 passed. See [final results](P2_REPORT.md). Attempt 01 remains immutable and hash-bound in attempt 02. There are no production or phone changes.

The next authorized sequence is documented in [the diagnostic plan](../CheckpointSnapshot/NEXT_PLAN.md). **Stop at preparation for the user's manual commit and confirmation before diagnostic checkpoint 1.** Agents must not stage, commit, or otherwise change Git state. Raw runs remain local and ignored; consult [restore requirements](../CheckpointSnapshot/README.md) before moving to another Mac. Intermediate checkpoint notes below describe history, not active workers.

```sh
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/p2_english.py verify
python3 scripts/evaluation_snapshot.py verify
```

Verification requires the original local artifacts and environment; it is not a training command. Do not use `run --resume` to launch a new experiment. After the manual checkpoint, estimate 4–8 active hours for diagnostic checkpoint 1, then stop for approval; checkpoint 2 is a further 8–16 active hours. Both are Mac-only. These are estimates, not unattended wall-clock promises. New work must stay within 4 GiB including temporary writes and leave at least 10 GiB free.

## Historical attempt 01: coverage stop (preserved)

Read [the saved P2 preflight report](checkpoints/p2-preflight.md) first. The runner stopped before baseline/MiniLM benchmark fitting because two short English sources were automatically identified as Dutch/Indonesian, for which the sentence embedding model is unavailable. This leaves36 known training pairs without complete features. All480 training responses and the token/feature caches are saved. No workers are running; it is safe to close the laptop.

The recommended explicit-English amendment was subsequently approved; see attempt 02 above. Do not overwrite the frozen automatic-language attempt. Production language behavior is out of scope.

The two-process MPS pause/resume fixture passed; the planned real-MiniLM two-batch exercise has not run because the earlier coverage check stopped execution. P2 verification passed with zero benchmark fits. `p2.py run --resume` on the unchanged attempt will repeat the known coverage failure; do not use it as if the blocker were resolved.

## Authorized original attempt (preserved)

The user approved P2 with “cary on” after reviewing the P1 handoff. The runner and prospective settings are now frozen in `runs/validation-01/manifest.json`. Initial estimated peak additional storage is 3,205,796,772 bytes (about 2.99 GiB), including temporary recovery writes, below the 4 GiB limit. P1 remains unchanged.

P2 commands from the repository root:

```sh
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/p2.py pause
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/p2.py status
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/p2.py verify
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/p2.py run --resume
```

`pause` only requests a pause: wait for the active worker's saved-state/exit confirmation before closing the laptop. `status` and `verify` acquire the worker lock and therefore should run when no worker is active. During an active run, inspect the saved JSON receipts read-only instead. No worker starts from a status command. Do not edit frozen P2 sources after starting; preserve the attempt and record any necessary correction separately.

Before the first long fit, complete the live two-process exercise: `p2.py exercise --pause-after-steps 2`, wait for its paused exit, then `p2.py exercise --resume`. `pause-exercise.json` must show success before `run` is allowed. Tests include CPU uninterrupted-versus-resumed equivalence; MPS bitwise continuation is not promised.

Actual phase/progress is in `runs/validation-01/`: `embeddings/`, `tokens/`, `baseline.json`, `fits/`, `recovery/`, `hybrid-<seed>.json`, then `selection.json` and `evaluation/`. Large tokens, all final fit weights and the latest two recovery states are in the existing feasibility workspace's `validation/validation-01` directory. Final completion is only `runs/validation-01/complete.json`, not the older P1 receipt.

Estimate remains 8–16 active hours until real training throughput is measured. No phone, production app work or old-test access. Stop after P2; do not automatically proceed to P3.

## Previous checkpoint: P1

P0 and P1 are complete and immutable. Their dataset review stop was approved; see the current P2 section above for live pause rules. `P1_REPORT.md` describes the historical P1 handoff, not current worker status.

The P1 receipt SHA-256 is `a00ed7144b3fa443d6234ee39f4d0186c3d1cd1179f612108a5a7d4721f2ebcc`. Resume by verifying P0 and P1; never restart completed authoring or replace sealed artifacts. No verification command launches training. A future request to continue must be interpreted with the checkpoint-review stop in mind; do not silently start another stage from a status or pause request.

From the repository root, using the existing feasibility Python environment:

```sh
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/p1.py status
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/prepare.py verify
"/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python" scripts/matcher-validation/p1_release.py verify
```

## Saved locations

- `families.json` and `runs/p1-01/assignment-freeze.json`: assignments frozen before authoring.
- `authoring/<library>.json`: sealed original narratives, authored memberships and history expectations; final amendments are separate.
- `runs/p1-01/packets/<author>-pairs.json`: immutable label-free pair packets.
- `reviews/<reviewer>-pairs.json`: complete sealed pair-first judgments, preserved without retrospective context edits.
- `runs/p1-01/receipts/<author>-pair-review.json`: binds completed pair review; context packet is published only after this exists.
- `runs/p1-01/packets/<author>-context.json` and `reviews/<reviewer>-context.json`: context-informed second pass.
- `runs/p1-01/receipts/<author>-context-review.json`: binds complete context review.
- `runs/p1-01/issues.json`, `adjudication.json`: 131 preserved disagreements, individual decisions, one additional consensus-link correction and 35 final sampled-pair dispositions.
- `releases/v1/` and `runs/p1-01/complete.json`: completed split-specific release and integrity receipt.

Authorship/review cycle: author_c reviews author_a; author_a reviews author_b; author_b reviews author_c. Never show a reviewer another author's proposed labels before the corresponding review is saved. Do not retroactively edit pair-first judgments after context review.

All projection, review sealing, adjudication and release commands have completed. `p1_release.py verify` checks the finished receipt; repeating `freeze` now verifies rather than regenerates it. Amendments require a separately authorized new attempt, not edits to these frozen sources, scripts, tests or receipts.

No P1 command launches training, opens old final-test data or changes the production app. All phone work remains deferred. Sources that change after packet publication require a new reviewed attempt; do not repair integrity errors by rewriting a receipt.

## Historical P2 execution plan (completed; do not restart)

1. Recheck frozen inputs, existing local model assets and peak storage. Keep the new experiment within 4 GiB including temporary writes and at least 10 GiB free; the prior experiment's 4.5 GiB exception does not carry forward.
2. Build the isolated new-data runner without editing frozen P0/P1 or earlier screening code. Exercise save/exit/resume on a small training fixture before any long fit. Preserve optimizer, model, RNG, epoch and data offset; do not promise bitwise MPS continuation.
3. Refit the six-feature baseline. Run three family-grouped out-of-fold fits plus one final neural fit for each of seeds 17/29/41, then fit the D3 combiner on out-of-fold training scores only.
4. Select thresholds using calibration only. Freeze models, transformations and thresholds before opening new evaluation data in model-evaluation code. Keep the old final test sealed.
5. Evaluate once against the unchanged prospective gates, report all seeds and family-level uncertainty, then stop. Failure does not authorize tuning on evaluation.

Estimate: 8–16 active hours for P2, provisional until throughput is measured. Mac only. During that work, “pause” must save the current effective batch and verified recovery state, stop every worker and confirm completion before the user closes the laptop. No phone/integration work starts automatically afterward.
