# MiniLM matcher feasibility

Six-stage experiment, **not production integration**. Read [CONTRACT.md](CONTRACT.md) before interpreting or running it. **Stages1–5 are complete and stopped. Stage5 found no qualifying neural candidate.** Stage6 is not authorized or recommended with these weights. See [RESUME.md](RESUME.md) for the current state; the initial configuration's Stage1 limit is historical and subsequent authorizations live in separate run manifests.

## Isolation

- Fictional English inputs, local training, no personal-vault access or paid GPU.
- Two blind reviewers reconstruct groups from input-only files. Final labels require independent adjudication. Synthetic agent agreement is not human validation.
- Existing organization benchmark files and production code stay unchanged. [Historical baseline](../Organization/README.md) is context, not a new-dataset comparison.
- No Git commands that mutate state; public model assets download over HTTPS, not a repository checkout.
- Large assets and the venv live in `~/Library/Application Support/RememberMatcherFeasibility/v1`; shell commands below use an explicit task-specific variable, not a replacement HOME.

## Stage 1 tooling

Standard-library validation works without ML packages:

```sh
python3 -m unittest discover -s scripts/matcher-feasibility -p test_experiment.py -v
```

Environment preparation for a fresh experiment output directory (completed outputs must not be overwritten or re-created):

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
python3.11 -m venv "$MATCHER_WORKSPACE/venv"
"$MATCHER_WORKSPACE/venv/bin/python" -m pip install -r scripts/matcher-feasibility/requirements.in
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/environment.py --workspace "$MATCHER_WORKSPACE" --output Evaluation/MatcherFeasibility
```

For reproducing the **resolved** environment, install `Evaluation/MatcherFeasibility/environment.lock.txt` instead of the direct-dependency input. `environment.py` checks imports, pip consistency and MPS availability, verifies model assets against upstream hashes, and records all versions. It does not load weights or run inference. Upstream supplies PyTorch `.bin` weights; future loading must use `weights_only=True`, `trust_remote_code=False`, and verified local assets. The initial scikit-learn 1.7.1 setup produced an optional-converter compatibility warning; its original records are preserved in `setup-attempts/initial/`. The selected environment uses 1.5.1.

For the existing checkpoint, use this **offline, read-only** verification instead of repeating setup:

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/environment.py --workspace "$MATCHER_WORKSPACE" --output Evaluation/MatcherFeasibility --verify-only
```

Authoring projection (run once per new release):

```sh
python3 scripts/matcher-feasibility/experiment.py project --authors Evaluation/MatcherFeasibility/authoring/train.json Evaluation/MatcherFeasibility/authoring/development.json Evaluation/MatcherFeasibility/authoring/test.json --amendments Evaluation/MatcherFeasibility/authoring/amendments.json --output Evaluation/MatcherFeasibility/releases/v1
```

Author labels are provisional only. Reviewers read projected `inputs.json`, never neighboring label files. Review-only partial batches are retained as evidence; they cannot pass the complete 30-library freeze.

The retained review batches are: 01 = original development/test inputs, 02 = training, 03 = re-reviewed test inputs after six explicit scope clarifications. Aggregation uses `merge-reviews --inputs ... --batches ... --batch-inputs ... --output ...`, with paired batch paths in chronological order. Later reviews replace that reviewer's earlier library decisions; source hashes and all superseded reviews are preserved. The latest reviewed source content must equal the final input content. `finalize --release ... --decisions ...` applies the independent adjudication, publishes final labels, and binds their hashes to the sources and reviews. Neither reviewer consensus nor the author's provisional labels silently becomes gold.

After adjudication creates final `labels.json` and records source/review hashes:

```sh
python3 scripts/matcher-feasibility/experiment.py audit --inputs Evaluation/MatcherFeasibility/releases/v1/inputs.json --labels Evaluation/MatcherFeasibility/releases/v1/labels.json --historical Evaluation/Organization/inputs-reviewed.json --output Evaluation/MatcherFeasibility/releases/v1/audit
python3 scripts/matcher-feasibility/experiment.py freeze --release Evaluation/MatcherFeasibility/releases/v1 --output Evaluation/MatcherFeasibility/freeze.json
python3 scripts/matcher-feasibility/experiment.py verify --freeze Evaluation/MatcherFeasibility/freeze.json
```

Input-only split files are separate from host-only labels and pair gold. Stage 2 may read training/development gold; test gold is sealed for model development until the Stage 5 selection freeze. Stage 1 annotation necessarily sees test sources and labels; it does not see model predictions.

This is a procedural seal, not filesystem access control. Future model-facing scripts must use `inputs-train.json` / `inputs-development.json` and their corresponding host-side label files, never the combined author or adjudication files. Subsequent implementation belongs in new stage-specific scripts; do not edit the frozen Stage 1 contract, data or validation code. Any necessary change requires a new release and an explicit explanation.

## Resume and reporting

Use [RESUME.md](RESUME.md) and the stage checkpoint report for current status. No next-stage commands run automatically. Stage 2–6 tooling is not implemented by Stage 1 preparation; the next authorized turn implements only the requested stage.

## Stage 2 implementation and results

Stage 2 is complete and stopped; see [the checkpoint report](checkpoints/stage-2.md). The Mac-only runner is `scripts/matcher-feasibility/stage2.py`; its helper modules implement metrics and original-model reference collection. It copies the production embedding provider and normalization implementation verbatim into an isolated Swift command-line probe, without changing the production app.

Results live under `runs/stage-2-attempt-01/`: `manifest.json`, per-source `embeddings/`, `features.json`, three `baseline/C-*.json` candidates, `baseline-selected.json`, `baseline-summary.json`, `reference/`, `reference-summary.json`, and `complete.json`. The selected classifier is exported as JSON coefficients/scaling/TF-IDF state, not an executable pickle. Its exact probabilities were independently reproduced. Reference weights/config/tokenizer are under the dedicated external workspace's `stage2/stage-2-attempt-01/reference/` directory.

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage2.py verify --run Evaluation/MatcherFeasibility/runs/stage-2-attempt-01
```

`audit_stage2.py` independently checks gold joins, prediction coverage, train-only vocabulary/IDF, portable baseline probabilities, threshold selection by brute force, retrieval boundaries, preserved pause records and historical/production hashes. Its saved report is `checkpoints/stage-2-audit.json`; re-running it requires a new `--output` path, never overwriting that report. Pause/resume commands are in [RESUME.md](RESUME.md). The live pause test preserved 114 completed embeddings.

The development operating point is not an independent test result. MiniLM's seeded classification head is deliberately untrained and is not scored for semantic quality. Original-model CPU timings are not iPhone timings. Test labels were not parsed or used by Stage 2; integrity verification hashes their frozen bytes without exposing them to feature fitting or selection.

## Stage 3 conversion and isolated probe

Stage 3 is complete; see [the checkpoint report](checkpoints/stage-3.md). The accepted run is `runs/stage-3-attempt-03/`. Attempts 01 and 02 preserve an empty-pair tokenizer mismatch and a non-finite FP16 export respectively; do not use their models.

`stage3.py` orchestrates conversion, token parity, Core ML parity and the unsigned iOS build. Separate workers save immutable phase receipts and per-case results. The source snapshots and completion manifest bind the exact implementation. `audit_stage3.py` independently recomputes output differences, including both-orientation averages, and checks bundle identity/payload isolation. Verification:

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage3.py verify --run Evaluation/MatcherFeasibility/runs/stage-3-attempt-03
```

The converter uses a finite `-10000` additive mask to avoid FP16's `0 × -infinity` failure, verifying the representation against all 416 original FP32 cases before export. The single ML Program package has three int32 inputs, two float32 outputs and enumerated shapes `[1,256]` / `[1,512]`, with an iOS 18 deployment floor. The native `MatcherTokenizer.swift` implements only the pinned uncased BERT policy, verified against tokenizers 0.21.4—not an unrestricted tokenizer API.

The Stage 3 iPhone project is self-contained, with bundle ID `SimpleStudio.Remember.MatcherProbe`, no production source/package dependencies, no App Group or private-data permissions, and 104 fictional input pairs without benchmark labels. `app-build.json` records exact external project/app paths. Its frozen unsigned artifact remains unchanged; Stage 4 built and installed a separate signed measurement app using the same model/runtime, as described below.

See [RESUME.md](RESUME.md) for safe pause/resume commands. Do not modify frozen scripts to add later measurement/training stages; use new stage-specific files.

Save complete immutable run records and atomic completion markers. Future training saves optimizer/random/data-position state every 50 optimizer steps and each epoch. Timing batches interrupted by sleep or disconnection restart as new attempts; never erase failures. Stop heavyweight work below 10 GiB free and ask before any cleanup.

After every stage: report results and limitations, where state is saved, whether corrections are needed and their estimated effort, next stage/hardware/time, and updated overall remaining work. Then stop for user instruction.

## Stage 4 physical-phone feasibility

See [the completed checkpoint](checkpoints/stage-4.md). The accepted run is `runs/stage-4-attempt-02`; attempt 01 preserves preflight and first-load evidence. On iPhone 17, warm ten-pair decisions (20 directional predictions) had p95 latency **85.3 ms at 256 tokens** and **257.9 ms at 512 tokens**. Sampled physical footprint peaked at **163.55 MB**; the installed signed probe measured **67.78 MB** in logical bundle bytes. All 416 original-output parity cases passed; six completed shortlists were retained across the physically exercised pause/resume. These are device-feasibility results, not grouping accuracy.

New files `stage4.py`, `Stage4ProbeApp.swift`, `stage4_report.py`, `test_stage4.py` and `audit_stage4.py` provide isolated signing/building, per-shortlist persistence, process-cold launches, memory sampling, strict reporting and an independent integrity audit. `device/` contains per-launch load/memory/storage receipts and predictions; `exports/` preserves raw copies. `complete.json` freezes 4,273 run files and binds the source/project/app and previous checkpoints.

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/audit_stage4.py verify --run Evaluation/MatcherFeasibility/runs/stage-4-attempt-02
```

Do not rerun build/install/new measurement jobs or create additional reports inside a completed attempt. Any new measurement or harness revision needs a new attempt and explicit scope. The probe remains installed but is not running. Stage 5 is Mac-only and must show that specialist training improves on the simple classifier before further integration is considered.

## Stage 5 specialist experiment

The completed run is `runs/stage-5-attempt-01`; read [the final checkpoint](checkpoints/stage-5.md) and [saved-state instructions](RESUME.md). Nine candidates were trained and evaluated. None met95% development precision with at least30 accepted known pairs. The highest-precision diagnostic reached94.12% precision /19.59% recall, below the frozen simple baseline's96.05% /29.80%; it is not an approved operating point. Test evaluation was correctly skipped and the test release remains unused for model evaluation. The independent audit,105 feasibility tests and22 existing regression tests passed. Stage6 is deferred; a separately approved corrective analysis is recommended first.

New stage-specific modules implement offline MPS training, atomic compressed recovery state, epoch safe-tensor models, development-only selection, a guarded heldout evaluation, unchanged-baseline reconstruction and library-level uncertainty reporting. No existing production or frozen Stage1–4 code was changed. `audit_stage5.py` independently verifies the completed evidence; `stage5_diagnostics.py` explains development errors without changing selection. Their reports and source hashes are bound in `checkpoints/stage-5.json`.

The completed candidate set is three seeds × three epochs. Training used known same/related/unrelated pairs in both orientations; ambiguous pairs remained in evaluation, not supervised loss. Dynamic padding preserved the512-token maximum and truncation policy. All nine epoch models,76 full recovery states and evidence are retained. No rolling policy was authorized and nothing was deleted. Stage5's large Mac assets occupy21.87GB in logical bytes; this is not app size.

The live pause exercise saved at optimizer step2 / nextOffset32 and restored model, optimizer and random state before continued training. Unexpected closure can repeat work since the last valid save; it is not a guarantee of bitwise-identical MPS execution. The runner pauses before exhausting the disk reserve and does not start Stage 6.

`selection.json` must bind chosen weights, threshold and the unchanged baseline before test access. The heldout split is never a model-selection input. If no development candidate qualifies, test labels remain sealed. Subsequent test-driven tuning would need a new independent test release. Test files contain fictional data; phone access is unnecessary for Stage 5.

Checkpoint state follows [PyTorch's guidance to save optimizer state as well as model weights](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html), with CPU/MPS random states and data position saved in addition. The installed, pinned PyTorch 2.7.0 implementation was inspected for MPS RNG support; no package upgrade was performed.

## Sources and licensing

[Microsoft MiniLM](https://huggingface.co/microsoft/MiniLM-L12-H384-uncased) is the selected English pretrained backbone (MIT license according to its model card); it requires task-specific fine-tuning. `model-manifest.json` records immutable provenance and hashes. The downloaded original model card is kept with the weights. The app bundles none of these assets at Stage 1.

[Apple Core ML Tools](https://github.com/apple/coremltools) supports the conversion path to test in Stage 3. Package installation/import success is not conversion success, and conversion success is not model-quality success.
