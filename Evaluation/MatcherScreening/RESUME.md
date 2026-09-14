# Matcher screening — current checkpoint

## Current: BOTH STAGES COMPLETE — 2026-09-13

**Stage 2 is complete and stopped for user review.** Read [the final report](checkpoints/stage-2.md). All 36 outer comparisons, six confirmation evaluations, all required fits and the full 68,400-row audit are complete. The worker exited successfully; no training process remains. It is safe to close the laptop. No work remains within this two-stage experiment.

Neither family met the every-seed qualification rule. C3 failed all three confirmation seeds (no qualifying threshold). D3 reached 95.03–95.10% precision and 55.65–62.57% macro recall; seed 29 passed all gates, while seeds 17/41 narrowly failed the precision-drop gate. The hybrid is a research lead, not an approved deployment. Outer-screen transfer failures and reused synthetic development data remain limitations.

Completion SHA256: `dbf644d321dd50f7a455161dcf9d9a04a25a234122092d08b5f1270b03e0cefd`. Original, fast-scan and headroom-retry freezes verify. Final tests: 183 matcher + 22 organization passed. Retained screening assets are about 3.88 GiB, under the restored 4 GiB limit; the 10 GiB free reserve passed. All permanent evidence remains; only superseded Stage 2 recovery blobs were rotated as authorized.

For future read-only verification, use the existing feasibility venv Python from the repository root:

```sh
python scripts/matcher-feasibility/screening2_headroom_v2.py verify --run Evaluation/MatcherScreening/runs/screen-attempt-01
```

Do not run preparation, edit frozen sources/results or start another experiment. `run --resume` on this completed attempt only verifies and exits. Any next validation, final-test access, conversion, phone work or integration requires a new user decision. The commands below are historical, not pending work.

## Historical: resumed with verified headroom amendment — 2026-09-12

Latest progress (2026-09-13 Singapore): **5/6 confirmation evaluations saved**, six of nine hybrid inner fits complete. **D3 seed29 passed all development gates**: precision0.9510489510, macro recall0.5565040650, AP0.9009791622, TP136/FP7 (all related), uncertain accepted3. D3 seed41's first inner fit is running. D3 still cannot meet the frozen every-seed family rule because seed17 narrowly failed; do not retroactively relax the gate. Estimate30–50 active minutes remaining for the last seed, full audit and handoff. A long wall-clock gap occurred within the preceding seed29 first inner fit; execution subsequently progressed, with no restart or result loss. All final-test and production restrictions remain unchanged.

Progress update: **4/6 confirmation evaluations saved.** All C3 seeds failed: no qualifying threshold at >=95% precision and >=30 accepted known pairs; abstention, macro recall0. AP: seed17 **0.7946613398**, seed29 **0.7683134048**, seed41 **0.7653878047**. Each scored all1,140 development pairs (all918 known), so this is not a missing-score failure.

D3 seed17 is more promising but **still fails the frozen precision-drop gate**: precision **0.9503105590**, macro recall **0.6256097561**, AP **0.9196166256**, TP153/FP8 (all eight false matches are related, not unrelated), accepted uncertain3. Baseline precision0.9605263158 and macro recall0.2993902439: the precision drop is1.0216 percentage points, slightly beyond the allowed1 point. No gate was relaxed. Three of nine hybrid inner fits are complete; seed29's first inner fit `C3-seed-29-fit-2d29a51ec9b006c9` is running. Continue all seeds, full audit, then stop. Estimate55–80 active minutes remaining from this checkpoint. Development calibration/report reuse and outer-screen failures still preclude a reliability/deployment claim.

The user requested resume. `checkpoint-headroom-attempt-02` is prepared and its source/evidence bindings verify. Manifest SHA256: `9136ee7c025bfc21f2db277ea18147f21526e8ffa6ee5b174c80c572d300fa9c`. The original statistical sources, fast-scan freeze and failed preparation01 remain preserved. The approved limits are temporary 4.5 GiB, final 4 GiB, and at least 10 GiB free.

The two-step live recovery exercise restored C3 seed17 step23, advanced to **step25**, saved and exited successfully. Its model, optimizer, RNG and step were loaded and verified, and all source/evidence checks passed. Recovery `recovery/1789226325034385000.pt.gz` has SHA256 `436c60d270dbb5c9eb14d97fc38524185efd5f0b6201599885f6f5c87fff47f6`. **One normal continuation worker has now been launched**, without the exercise flag. Request pause and wait for exit before closing the laptop. **36/36 outer comparisons remain complete; confirmation and the final audit remain.** Use only the v2 commands below for current pause/resume/verification. Ordinary resume omits `--pause-after-steps 2`. Do not edit any now-frozen source or execution document. Stop after Stage 2 for user review; no final test, phone or production integration. Initial remaining estimate: 2–3 active hours, updated from measured progress.

## Historical: user-requested pause before clean preparation retry — 2026-09-12

The user requested a temporary pause. **Training has not restarted.** The first headroom invocation exited before training because preparation captured the test file just before its fixture correction. All original model/results remain at the verified **C3 seed17 confirmation step23** checkpoint; the outer screen is still 36/36 complete and zero confirmation evaluations have completed.

The failed `checkpoint-headroom-attempt-01` is preserved with its original snapshots and failure receipt. A clean retry entrypoint, `screening2_headroom_v2.py`, and [retry explanation](CHECKPOINT_HEADROOM_RETRY.md) have been implemented but **not prepared or executed**. The corrected full test suite passed: **183 matcher tests** in 5.252 seconds; **22 organization tests** passed earlier in this turn. The test process exited successfully. A cooperative pause request remains recorded.

The user's approval for 4.5 GiB temporary headroom, final 4 GiB cap and 10 GiB free reserve remains valid. On a future explicit resume: inspect current state, prepare the clean attempt02 with the v2 entrypoint, verify its source bindings, run the two-step recovery exercise, verify saved state and exit, then resume normally. Do not run attempt01 or rewrite its manifest/snapshots. All older statistical and fast-scan freezes remain unchanged. Mac GPU access and writes to the existing Application Support experiment workspace require execution outside the current filesystem sandbox.

```sh
python scripts/matcher-feasibility/screening2_headroom_v2.py prepare --run Evaluation/MatcherScreening/runs/screen-attempt-01
python scripts/matcher-feasibility/screening2_headroom_v2.py run --run Evaluation/MatcherScreening/runs/screen-attempt-01 --resume --pause-after-steps 2
python scripts/matcher-feasibility/screening2_headroom_v2.py verify --run Evaluation/MatcherScreening/runs/screen-attempt-01
python scripts/matcher-feasibility/screening2_headroom_v2.py run --run Evaluation/MatcherScreening/runs/screen-attempt-01 --resume
```

Use the existing feasibility venv Python from the repository root. **Do not execute these steps until the user asks to resume.** Once running, request pause with the same v2 entrypoint's `pause` action and wait for actual exit. Estimated remaining confirmation/audit work is still about 2–3 active hours, excluding this pause. Stop after Stage 2 for user review; no final test, phone or production integration.

## Historical: temporary headroom approved — 2026-09-12

The user explicitly approved **4.5 GiB temporary headroom**, with the **4 GiB final-storage target and 10 GiB free reserve unchanged**. The separately frozen `checkpoint-headroom-attempt-01` implements that approval without changing original experiment sources, data, selection or settings. Read [the amendment](CHECKPOINT_HEADROOM.md). Tests: 181 matcher and 22 organization passed. A two-step recovery exercise is underway; wait for actual worker exit before closing the laptop. Completed outer comparisons remain 36/36; repeated-seed confirmation and the full audit remain.

Use the existing feasibility venv Python with the new driver for subsequent operations:

```sh
python scripts/matcher-feasibility/screening2_headroom.py pause --run Evaluation/MatcherScreening/runs/screen-attempt-01
python scripts/matcher-feasibility/screening2_headroom.py verify --run Evaluation/MatcherScreening/runs/screen-attempt-01
python scripts/matcher-feasibility/screening2_headroom.py run --run Evaluation/MatcherScreening/runs/screen-attempt-01 --resume
```

Do not edit frozen headroom, runtime or original source sets. The new driver verifies all three freezes and preserved evidence, restores the strict final cap before the audit, and only verifies if already complete. Ordinary resume omits the exercise's `--pause-after-steps` flag. Stop after Stage 2 for user review; final test, phone and app integration remain out of scope. Estimate 2–3 active hours excluding pauses, to be updated from measured confirmation progress.

## Historical: safely paused after the outer screen — 2026-09-12

**36/36 outer comparisons are complete. Stage 2 is not complete.** The frozen selection is C3 (full MiniLM) and D3 (its hybrid). Read [the outer-screen checkpoint](checkpoints/outer-screen.md) for results, checks and the storage decision required before proceeding.

The worker exited successfully after saving the first confirmation fit, `C3-seed-17-fit-3e9f12ffba4ae6f0`, at **step 23**, on 2026-09-12 at 22:07 Singapore time. No confirmation evaluation has completed. Process inspection confirms no screening worker; it is safe to close the laptop. The latest recovery is `recovery/1789222015913993000.pt.gz`, SHA256 `1e15e246f38dbf4d42684d45b3c36becb620fbacf4ad2d717798cf06c42b3e3a`. Its model, optimizer, RNG and step were loaded and verified. Both source freezes and preserved pre-continuation evidence verify, with `complete:false`.

**Leave training paused pending the user's storage direction.** Permission was requested for a temporary 4.5 GiB checkpoint allowance, while retaining the 4 GiB final-results target and 10 GiB free reserve; no response has been received. Estimated final retained assets are 3.90 GiB, but checkpoint-write headroom is projected at 4.19 GiB. Current limits remain unchanged. Any approved operational amendment must be recorded separately without editing either frozen source set. Do not infer approval from earlier authorization of the performance-only fix.

Next: repeated-seed C3/D3 confirmation, full-stage audit and recommendation, then mandatory stop for review. Estimate **2–3 additional active hours**, including a separately recorded headroom amendment if approved; no phone required. Final-test access and production changes remain out of scope.

## Historical performance-only restart — 2026-09-12

The user authorized proceeding with the recommended runtime fix. `fast-scan-attempt-01` is separately frozen under `runs/screen-attempt-01/runtime-continuations/`; the original experiment scripts, settings and saved evidence remain unchanged. Read [the runtime checkpoint](checkpoints/runtime-continuation.md). At this historical restart, one worker resumed from the verified step-252 recovery. It subsequently reached the paused checkpoint above.

Use the existing feasibility venv Python, from the repository root:

```sh
python scripts/matcher-feasibility/screening2_runtime.py pause --run Evaluation/MatcherScreening/runs/screen-attempt-01
python scripts/matcher-feasibility/screening2_runtime.py verify --run Evaluation/MatcherScreening/runs/screen-attempt-01
python scripts/matcher-feasibility/screening2_runtime.py run --run Evaluation/MatcherScreening/runs/screen-attempt-01 --resume
```

Use this driver for future resumes and final verification, so both source freezes and preserved pre-continuation evidence are checked. Do not start another worker or edit frozen runtime sources/documentation. The live two-step pause exercise already succeeded; **omit** `--pause-after-steps` for normal resumes. Historical recovery blobs may be rotated under the unchanged latest-two policy; use the latest receipt.

At restart: **31/36 comparisons saved**, third-fold C2 resumed from step 252/525. Tests: 170 matcher +22 organization passed. Whole-folder byte counts matched exactly over three comparisons; fresh scans averaged 0.122 seconds versus 0.364 seconds for the original traversal. These are scan timings, not an end-to-end speedup claim. Budgets remain 4 GiB screening assets and 10 GiB free reserve. Failed checks now save the exact used/free/planned measurements. Remaining-time estimates will be revised from measured continuation progress. The final test, phone and production integration remain out of scope; stop for user review after Stage 2.

## Historical automatic pause — 2026-09-12, 21:05 Singapore time

The worker **exited successfully and is stopped** after an automatic storage-safety pause at 13:05:39 UTC. It is safe to close the laptop. Stage 2 remains frozen as `runs/screen-attempt-01`; no source, label, model-setting or budget change has been made. Read [the execution plan](STAGE2_PLAN.md). Stage 1 and prior feasibility evidence remain immutable. No final test, phone work or production integration is authorized.

Current saved progress: **31/36 outer-fold comparisons**. Both first folds are complete; third-fold A1–A3, B1–B3 and C1 are complete. Third-fold C2 paused with latest valid recovery at **step 250/525**, epoch index 1 / offset 1200. The guard could not safely write a newer checkpoint, so resuming can repeat any work after step 250. Recovery `recovery/1789218181884605000.pt.gz` has SHA256 `f5e2224b98f13599b004f16be3f548a589969cfcf60b2f8e93ae380b729d819e`. Its model, optimizer, RNG and step were loaded and verified after exit. `screening2.py verify` passed with `complete:false`, and process inspection found no screening worker. No failures are recorded; this was a handled pause. No candidate selection or development confirmation has occurred.

The pause reason is `storage_before_checkpoint_latest_prior_state_retained`. After worker exit, retained screening assets measured **1.695 GiB**, free space **15.703 GiB**, and the capacity check passed again. The instantaneous failing byte/free-space measurements were not recorded; a transient free-space dip is plausible, not conclusively established. Do not raise the 4 GiB cap, lower the 10 GiB reserve, or delete older evidence without approval. Leave the worker stopped pending the user's direction on the performance-only continuation proposal below. If asked to continue unchanged, verify current capacity before resuming with the original driver.

Historical resume: the user requested resume after the safe 17:47 Singapore-time pause; one worker restored B3 step 33 and completed that fit before advancing to the current checkpoint.

Progress at the last pause: **17 of 36 outer-fold comparisons** (all twelve in fold 1; A1–A3, B1 and B2 in fold 2). The B3 fit in fold 2 stopped at **step 33 of 440**, epoch index 1 / offset 704, and has now resumed. Inspect `screen/`, the latest recovery receipt and worker log for live progress. No candidate selection or development confirmation had occurred at resume. No failures were recorded. Stage 2 is not complete.

Progress update at 2026-09-12 12:38 UTC: both first and second folds are complete, with **28/36 comparisons saved** after the four simple third-fold comparisons. The third-fold B2 fit is running. Both completed folds passed the partial independent count/threshold/prediction checks, including all completed hybrid OOF provenance. Full-stage audit and confirmation are still pending. C3 evaluation AP is 0.9109 / 0.9175 on folds 1 / 2 (prior control: 0.8015 / 0.6997), but operating-point precision is 94.22% / 83.70%. D3 precision is 92.22% / 83.75%; it has not resolved threshold transfer. These are provisional synthetic-data results, not a winner or deployment authorization. Current estimate: 3–4.5 active hours remaining, depending on selected confirmation families and save times. New screening assets measured about 1.62 GiB after small recovery states replaced the larger ones; continue enforcing the existing cap and reserve.

Runtime finding at 12:54 UTC: three read-only measurements of `capacity()` took 0.855 / 0.817 / 0.846 seconds each. It recursively scans growing evidence folders at every batch, so bookkeeping is materially slowing the run and the remaining-time estimate may be optimistic. A non-blocking question was sent to the user proposing a safe pause and separately recorded, performance-only continuation (estimated 30–60 minutes to implement/verify) with all model/data/settings/results preserved. No optimization or frozen-source change has been made. The worker initially continued pending the user's preference, then the automatic storage pause described above occurred. A read-only `os.scandir` prototype on the immutable Stage 1 run returned the same 34,531,640-byte total in 0.017 seconds versus 0.046 seconds for the original traversal; it was not applied to the runner. Inspect the latest conversation before acting on this proposal.

Last-pause recovery: `recovery/1789206440369121000.pt.gz` in the external Stage 2 workspace; SHA256 `bbf14754e094b562c38db35e8d7dba338d71a3bce5c0b1e7685b1463a6feb53f`. The blob was loaded and its model, optimizer, random state and step verified after worker exit. The new resumption receipt records restoration of that state. This historical blob may subsequently be rotated under the approved latest-two policy; use the latest recovery receipt for a later pause. Do not launch a second worker.

Interim audit: all twelve first-fold comparisons passed independent counts, brute-force thresholds, prediction reconstruction/bindings and hybrid OOF provenance checks. The full-stage audit remains pending. First-fold evaluation precision: C3 94.22%, D3 92.22%; these are partial results, both below the 95% target, not a selected winner. Remaining estimate: roughly **4–5 active hours** if both expensive families advance, excluding pauses. Reassess after the next complete fold and candidate selection. Monitor the 4 GiB screening budget before confirmation; do not expand it or remove prior evidence without approval.

Use the existing feasibility venv Python from the repository root:

```sh
python scripts/matcher-feasibility/screening2.py pause --run Evaluation/MatcherScreening/runs/screen-attempt-01
python scripts/matcher-feasibility/screening2.py verify --run Evaluation/MatcherScreening/runs/screen-attempt-01
python scripts/matcher-feasibility/screening2.py run --run Evaluation/MatcherScreening/runs/screen-attempt-01 --resume
```

The intentional pause after two B2 optimizer steps succeeded and the worker exited. The resumed worker restored the optimizer and random state and completed that fit. Screening is progressing without the `--pause-after-steps` flag; completed comparisons are in `screen/fold-*/`, with individual fit exports and recovery receipts saved separately. Inspect those records for current progress rather than treating this document as a live counter. An ordinary `pause` only requests a stop: wait for the worker's paused message and process exit before closing the laptop. Do not launch a second worker. A resume verifies frozen bindings, reuses completed fits/predictions and restores the active optimizer/random/epoch/offset state. Unexpected interruption may repeat work since the last checkpoint.

Preflight: 150 matcher tests and 22 organization tests passed. The prior Stage 1 completion verifies. MiniLM trainable parameter counts: C1 770; C2 3,549,698; C3 33,360,770. No new packages installed. Stage 2 initial estimate remains 4–8 active hours; update from measured training progress. Both storage limits are enforced: 4 GiB total new screening assets and 10 GiB free reserve. Only superseded recovery blobs from this Stage 2 run may be rotated; all fit exports/predictions and older experiments remain.

## Completed Stage 1 — historical checkpoint

**Stage 1 is complete and stopped** as `audit-attempt-01`. At that checkpoint Stage 2 was not yet authorized; the new authorization is recorded above. Read [the checkpoint report](checkpoints/stage-1.md). All 60 pair-first/contextual reviews, twelve ablation results, diagnostics, sanity training and the independent audit are saved. Its worker is stopped; use the active Stage 2 status above before closing the laptop.

Run: `runs/audit-attempt-01`. Scripts: `scripts/matcher-feasibility/screening*.py`. Use the existing feasibility virtual environment. Large new assets belong under its existing workspace's `screening/` directory, separate from prior runs.

From the repository root, use the existing feasibility venv's Python:

```sh
python scripts/matcher-feasibility/screening.py pause --run Evaluation/MatcherScreening/runs/audit-attempt-01
python scripts/matcher-feasibility/screening.py verify --run Evaluation/MatcherScreening/runs/audit-attempt-01
python scripts/matcher-feasibility/screening.py run --run Evaluation/MatcherScreening/runs/audit-attempt-01 --resume
```

`pause` requests a stop; wait for the worker's `status: paused` and process exit before closing. `verify` checks frozen bindings; completed runs also verify all retained file hashes. Never use the system Python for this experiment. The venv is `~/Library/Application Support/RememberMatcherFeasibility/v1/venv/bin/python`.

Validation: 124 matcher tests and 22 organization tests passed; 37 pinned packages and six model assets verified offline. The independent audit recounted 45,600 prediction rows and passed. A real pause at sanity step 2 and subsequent state restoration succeeded; the sanity test passed at step 160. No dependencies added. Reviews are executing-agent diagnostics, not an independent blind review.

Completion SHA256: `90961460de28a80e53801b99724d24414e50bf9aec7702144c54a4ecc391e344`. Running `run --resume` on this completed attempt only verifies it; it does not train again or launch Stage 2. Do not edit frozen scripts or run artifacts. A later stage needs a separate implementation/source freeze and explicit user continuation.

Say **pause** and wait for confirmation before closing. During implementation the agent saves source/doc progress; during a run it requests a cooperative stop and waits for all workers to exit. A future resume verifies immutable run sources/data/configuration before continuing. Do not edit frozen run code; a necessary correction requires a preserved new attempt.

Stage 1 remaining work: **zero**. Stage 2 estimate: **4–8 additional active hours**, only after review. No phone is required. One ambiguity-policy concern is documented; labels remain unchanged. A separately approved policy review would add roughly 1–2 hours. Read PLAN.md for the agreed boundaries and storage policy.
