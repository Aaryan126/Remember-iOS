# Matcher feasibility resume checkpoint

## Current status

**Stages 1–5 are complete and stopped. Stage5 produced no qualifying neural candidate.** Read [checkpoints/stage-5.md](checkpoints/stage-5.md) and its [machine-readable receipt](checkpoints/stage-5.json). All nine candidates were evaluated; the independent audit passed. Test evaluation was deliberately skipped because none cleared development selection. Stage6 is not authorized or recommended with these weights. The laptop can be closed and the phone is not needed.

Large local assets: `~/Library/Application Support/RememberMatcherFeasibility/v1`.
Source/evidence: `Evaluation/MatcherFeasibility/` and `scripts/matcher-feasibility/`.

The environment is isolated from global Python packages. Stage 2 extracts Mac embeddings, fits only the small logistic baseline and creates an untrained MiniLM reference. No task-specific neural training, phone app installation, production changes or private-data access is authorized by Stage 2.

## Stage boundaries

| Stage | Hardware | Initial estimate | State |
| --- | --- | --- | --- |
| 1. Dataset/environment freeze | Mac | 3–5 hours | Complete; stopped |
| 2. Simple baseline/reference outputs | Mac | 2–4 hours | Complete; stopped |
| 3. Core ML conversion/probe | Mac | 3–6 hours | Complete; stopped |
| 4. Initial device measurements | Mac + phone | 1–3 hours | Complete; stopped |
| 5. Specialist training/evaluation | Mac | 6–12 hours | Complete; no qualifying candidate; stopped |
| 6. Trained device verification | Mac + phone | 2–4 hours | Deferred pending a quality-qualified candidate |

**Stage5 remaining work is zero.** Recommended next checkpoint, only after explicit approval: **2–4 active hours of Mac-only corrective analysis** before deciding on a revised pilot (provisionally another4–8 hours). Do not start either automatically. If a future candidate passes development and heldout quality gates, Stage6 remains approximately2–4 hours with the Mac and connected, unlocked phone. Overall remaining time is not fixed because these candidates failed the quality gate. The six-stage estimates in the table are historical planning allowances, not outstanding jobs.

Before any resume: read CONTRACT.md, the checkpoint report and freeze manifest; verify frozen hashes; check free disk space; preserve all older attempts. Never read private vault data or change Git state. A closed laptop interrupts local jobs; recover only from a verified saved state.

## Completed Stage 2 / next authorization

Stage 2 saved Mac embeddings, a training-only TF-IDF/logistic baseline, development retrieval/classification, and 416 original MiniLM reference cases with an untrained head. That head is for conversion parity only. Do not open test labels or run heldout test quality results for model selection.

Stage 3 converted the reference to one FP16 package with 256/512-token shapes, verified numerical/token parity, and built the unsigned isolated iPhone probe. A finite attention-mask sentinel is required for stable FP16 conversion; the change reproduced all original FP32 reference outputs exactly. The native tokenizer must preserve the pinned adapter's empty-second-string behavior. See the Stage 3 report before reusing or converting this architecture.

Stage4 added an isolated signed measurement app, reusing the frozen tokenizer/runtime/model; its phone results passed. Stage5 subsequently fine-tuned nine candidates with saved optimizer/random/data-position state and development-only selection. None qualified, so no selected weights were released to heldout evaluation. Keep all Stage1–5 source/model/evidence freezes intact. Further training requires a newly authorized, separately versioned attempt rather than editing these results.

## Completed Stage 5 saved state and pause/resume

Stage5 has completed and stopped. The [live checkpoint](checkpoints/stage-5-in-progress.md) is historical. Implementation files are frozen in the run's manifest and source snapshots. All76 recovery snapshots and nine epoch models are preserved; none were deleted. Any necessary correction requires a new attempt. For this completed run, `pause` reports already complete and `run --resume` only verifies completion; neither restarts training nor starts Stage6.

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage5.py pause --run Evaluation/MatcherFeasibility/runs/stage-5-attempt-01
# Completed run: reports already complete and stopped.
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage5.py run --run Evaluation/MatcherFeasibility/runs/stage-5-attempt-01 --resume
```

A cooperative pause finishes the current effective batch, saves model/optimizer state, CPU/MPS/Python/NumPy random state and exact next data offset, then exits. Recovery is also saved every 50 optimizer steps and at every epoch. Unexpected process termination/sleep resumes from the latest valid saved state and may repeat steps since that save; it does not promise zero lost computation. Model loading or checkpoint compression can delay pause acknowledgement. MPS bitwise reproducibility is not guaranteed.

All epoch models, development predictions, selection evidence and metrics remain immutable. Full recovery snapshots were retained with no cleanup authorization. During the run a disk guard protected the10GiB reserve. Never start a second worker. Test inputs/labels stayed behind the selection guard; `selection.json` now records no qualifying candidate. Stage5 stopped after its report and did not start Stage6. Completion SHA256: `316a288748307c4e1c8d4c4138e185c334ee42ed7573147be389cb577f954731`.

Read-only preflight:

```sh
python3 scripts/matcher-feasibility/experiment.py verify --freeze Evaluation/MatcherFeasibility/freeze.json
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage2.py verify --run Evaluation/MatcherFeasibility/runs/stage-2-attempt-01
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage3.py verify --run Evaluation/MatcherFeasibility/runs/stage-3-attempt-03
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/audit_stage4.py verify --run Evaluation/MatcherFeasibility/runs/stage-4-attempt-02
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/environment.py --workspace "$MATCHER_WORKSPACE" --output Evaluation/MatcherFeasibility --verify-only
df -h .
```

Do not rerun authoring, `project`, `finalize`, setup, or `freeze` against completed output paths. The configuration's `stageLimit: 1` records the initial authorization: Stage 2 records its new authorization in its separate run manifest, not by editing frozen configuration.

## Pause and resume during Stage 2

This protocol was exercised successfully during the completed run: it paused after 114 embeddings and resumed without rewriting them. Stage 2 is now complete, so `run --resume` verifies its checkpoint rather than collecting again. Future stages must retain equivalent safe-boundary behavior.

Tell the agent **“pause now”**, then wait for confirmation before closing the laptop. The following command requests a cooperative stop; it does not mean the worker has stopped yet:

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage2.py pause --run Evaluation/MatcherFeasibility/runs/stage-2-attempt-01
```

The worker completes its current item/case, saves it atomically, records a `pauses/*.json` boundary, closes its Swift child process and prints `status: paused`. Completed embeddings are saved per source; baseline candidates are saved per C; reference outputs are saved per pair/length/orientation. Building or loading a model can delay reaching the next boundary. Sudden sleep/process termination can require repeating unfinished work, but completed artifacts remain.

After confirming the old worker is stopped, say **“resume”** or run:

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage2.py run --run Evaluation/MatcherFeasibility/runs/stage-2-attempt-01 --resume
```

Resume verifies code/data/model bindings, preserves the prior pause request in the control history and skips completed records. Never run two workers for the same attempt. A code/data change requires a new attempt, not overwriting the manifest. When `complete.json` exists, rerunning verifies completion rather than starting Stage 3.

## Stage 3 pause/resume protocol

The completed Stage 3 driver was paused at its initialization boundary with conversion/parity/build artifacts saved, then resumed and verified. This was **not** an in-flight export cancellation test. Workers check for pause between conversions, tokenizer cases, prediction cases and builds; completed receipts are reused. A conversion, model load or compiler operation may need to finish before acknowledging pause. Abrupt termination can require repeating the unfinished export/compile or pre-export reference sweep; no completed package is overwritten.

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage3.py pause --run Evaluation/MatcherFeasibility/runs/stage-3-attempt-03
# Wait for the worker's paused/safe-boundary confirmation before closing the laptop.
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage3.py run --run Evaluation/MatcherFeasibility/runs/stage-3-attempt-03 --resume
```

Because this attempt is complete, its pause command now reports already stopped, and resume only verifies it. It never starts Stage 4 automatically. The isolated app also has per-prediction saving and a Pause control; its behavior on a physical phone is still to be exercised in Stage 4.

## Completed Stage 4 and exercised pause protocol

Read [the final checkpoint](checkpoints/stage-4.md) and `runs/stage-4-attempt-02/manifest.json` for the completed phone protocol. [The earlier live note](checkpoints/stage-4-in-progress.md) is historical, not current status. Attempt 01 is preserved first-load/preflight evidence; reporting corrections and the expanded interruption exercise are in attempt 02. The runner is `scripts/matcher-feasibility/stage4.py`; the device entry point is `Stage4ProbeApp.swift`. Frozen Stage 3 tokenizer/runtime/model resources were reused unchanged. Do not append new measurements or reports to the completed attempt; use the read-only audit verification command above.

The phone probe saves each finished ten-pair shortlist (20 directional predictions) atomically. Each process launch has a unique receipt, memory samples and load timings. The Mac copies phone evidence after each job and rejects any changed completed records. Parity cases are saved individually. A pause during a shortlist discards only that unfinished timing, which is rerun after a fresh warmup on resume.

```sh
python3 scripts/matcher-feasibility/stage4.py pause --run Evaluation/MatcherFeasibility/runs/stage-4-attempt-02
```

This completed attempt's pause command reports that it is already stopped. During an active run, wait for the controller to report `paused` and `safeToDisconnect: true`. The host delivers a pause file to the **isolated** app, which checks it between predictions, saves an end receipt and exits. This was physically tested: six completed shortlists survived pause/resume byte-for-byte. The app's Pause button and leaving the foreground also request cancellation, but those paths were not separately exercised. A model load can delay acknowledgement. After an unexpected connection loss, do not assume a saved host end receipt: reconnect, collect device records, inspect the unfinished launch, and rerun only missing records under a new launch ID. Do not run two workers; the controller enforces a host advisory lock.

For a future unfinished attempt, resume the interrupted job with the same `--job`, `--mode`, `--length`, and `--count`, adding `--resume`. Completed jobs are not rerun; this no-op path was checked. No Stage 4 command starts Stage 5 automatically. **Stage 4 remaining work is zero.** Completion hash: `4891fadd62a504c687f347005a8a6e9e0e027b47295693a15dee74158adc749b`.
