# Stage 3 complete — Core ML parity passed, isolated probe built

11 September 2026. **Stopped at the checkpoint. Stage 4 has not started.** No phone installation, task-specific neural training, heldout quality evaluation or production changes occurred.

## Outcome

The compact reference model converts successfully to one **FP16 Core ML package supporting both 256- and 512-token pairs**. Its outputs meet the frozen consistency gates. The isolated iPhone probe builds successfully, and its shared native Swift inference/tokenization implementation passes the Mac reference checks.

This establishes conversion feasibility—not phone performance or improved memory grouping. The classification head is still untrained. Actual device latency, peak memory, thermal behavior, startup and storage measurements remain Stage 4 work; specialist quality remains Stage 5 work.

| Check | Result |
| --- | --- |
| Native tokenizer vs original | **428/428 exact matches**: 416 saved reference cases plus 12 extra tokenizer-only cases |
| Finite-mask FP32 vs original FP32 | **416/416 checked; maximum probability difference 0.0** |
| Torch trace vs original | Exact checked probabilities at both 256 and 512 tokens |
| Core ML, CPU-only on Mac | 416 cases; **100% class agreement**, maximum probability difference **0.00040513** |
| Core ML, automatic compute on Mac | 416 cases; **100% class agreement**, maximum difference **0.00039265** |
| Shared native Swift runtime on Mac | 416 cases; **100% class agreement**, maximum difference **0.00039265** |
| Both-direction probability averages | 208 pair/length combinations per path; **100% class agreement**; maximum difference ≤0.00033987 |
| Unsigned iPhone probe | Release build passed, model bundled, not installed |

The gate is maximum probability difference ≤0.01 and class agreement ≥99%. All tested paths pass at both sequence lengths. Values above are absolute probability differences; the worst is about **0.041 percentage points**. Agreement refers to the original untrained reference's output class, not agreement with correct project labels.

`ALL` lets Core ML select compute hardware; passing that path does not prove Neural Engine execution. The Mac runtime is not an iPhone performance proxy.

## Issues found and resolved

**Attempt 01 — empty pair tokenization.** The pinned Transformers adapter treats a literally empty second string as a single input. The initial native encoder added an extra separator and segment. Ordinary source-pair checks had passed, but the empty-input case correctly failed. The fix preserves this exact adapter behavior; whitespace-only second strings still form a pair. New native regression tests cover both cases, special tokens, Unicode accents, overlong words and the fast tokenizer's truncation tie rules.

**Attempt 02 — non-finite FP16 outputs.** The original attention-mask representation uses the minimum FP32 value. Conversion to FP16 made that value negative infinity; multiplying it by a zero mask produced NaN. The parity gate rejected the export. The converter now uses a finite **−10000** additive mask, leaving weights and model architecture unchanged. Before conversion, it checks all 416 original FP32 references: output probabilities remained exactly equal. FP16 conversion then passed every numerical check, and the overflow warning disappeared.

Attempts 01 and 02, their source snapshots, failing results and model packages remain preserved. **Use only attempt 03.** No threshold, gold label or parity tolerance was weakened to get a pass. The expected tuple-output flattening and embedding-conversion notices did not prevent verified inference; the model-loading loss warning concerns an unused training loss, with no labels supplied.

## Size and isolation

| Artifact | Logical bytes | Decimal MB |
| --- | ---: | ---: |
| Single FP16 `.mlpackage` | 66,866,771 | **66.87 MB** |
| Compiled model in iPhone probe | 66,879,135 | **66.88 MB** |
| Entire unsigned iPhone probe bundle | 67,544,144 | **67.54 MB** |

These are Mac build artifacts, not measured installed storage, peak RAM, App Store download size or the final Remember app size. Signing, system compilation caches and runtime memory are separate. The earlier 70–130 MB planning estimate has not become a final app-size promise.

The probe's bundle ID is **`SimpleStudio.Remember.MatcherProbe`**. It has no production source dependencies, App Group, private-data permission descriptions, networking code or personal-vault access. Its 104 fictional input pairs contain only `id`, `first` and `second`; no benchmark memberships, gold labels, rationales or reference predictions are bundled. Vocabulary and the original model card are bundled alongside the model. Generic output class names are model metadata, not benchmark gold.

The test UI has Run/Resume and Pause controls and saves each completed prediction into its own app container. App-level pause/background behavior still needs actual phone testing in Stage 4. The app is currently **unsigned and uninstalled**.

## Pause/resume verification

The live Stage 3 driver accepted a pause request, stopped at its **initialization boundary**, reported `safeToCloseLaptop: true`, then resumed with the completed conversion/parity/build receipts retained. The final integrity audit verified those artifacts after resume. This test was performed after phase results existed; it was **not an in-flight export cancellation test**.

During future active work, say **“pause now”** and wait for the saved-boundary confirmation. Workers check between conversion phases, tokenizer cases, inference cases and builds. A current conversion, model load or compiler call may need to finish first. If the laptop closes unexpectedly, completed files remain, but the unfinished export/compile or pre-export consistency sweep may need to repeat. Partial exports are never treated as completed models. Resume never starts the next stage automatically.

Exact commands are in [RESUME.md](../RESUME.md). All experiment processes are now stopped; the laptop can be closed.

## Validation actually run

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q
python3 -m unittest discover -s scripts -p 'test_organization*.py' -q
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/stage3.py verify --run Evaluation/MatcherFeasibility/runs/stage-3-attempt-03
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/audit_stage3.py --run Evaluation/MatcherFeasibility/runs/stage-3-attempt-03 --output Evaluation/MatcherFeasibility/checkpoints/stage-3-audit.json
```

**78 feasibility tests passed** (including 22 new Stage 3 tests); **22 existing organization/audio tests passed**. Native tokenizer/runtime Swift compilation and the unsigned generic-iOS Release build passed. The exact `xcodebuild` command and output are saved in the run's `build-logs/` directory.

The independent audit recomputed all 1,248 Core ML/native case comparisons and both-orientation averages, checked token identity against frozen references, and validated the label-free bundle. **1,704 run artifacts, 27 external files and 12 implementation files** passed completion-manifest verification. Stage 1 and Stage 2 checkpoints remain intact; six historical evidence files and 51 production Swift files remained unchanged. No Git-state changes occurred.

Completion SHA-256: `babcc16a0aebced158e38b1aa6e9a5f981b386545c9e2253ebd8da5fb992b39c`.

## Saved checkpoint and next step

- Accepted evidence: `Evaluation/MatcherFeasibility/runs/stage-3-attempt-03/` (about 18 MiB).
- Key receipts: `conversion.json`, `tokenizer-summary.json`, `parity-summary.json`, `app-build.json`, `complete.json`.
- Independent audit: [stage-3-audit.json](stage-3-audit.json).
- Large package/project/app paths are recorded relative to the dedicated workspace in `conversion.json` and `app-build.json`.
- External workspace: `~/Library/Application Support/RememberMatcherFeasibility/v1`, approximately **1.5 GiB total** including prior stages and preserved attempts.
- Latest audit disk availability: **38,690,594,816 bytes**, approximately **36.0 GiB**. No cleanup was needed.

Implementation additions are confined to the experiment directories: Stage 3 driver/common/conversion/parity/build/audit scripts, regression tests, tokenizer/runtime/probe Swift files and the standalone Xcode template. Existing frozen scripts and production code were not edited; README/resume documents were updated.

**Verdict: ready for Stage 4 when authorized. No further corrective rerun is currently required.** Stage 4 adds device-measurement modes, signs/installs the isolated probe, and measures actual startup, warm shortlist latency, memory, storage and interruptions using fictional inputs.

Next hardware: **Mac + connected, unlocked iPhone**. Initial Stage 4 estimate: **1–3 active hours**. Remaining Stages 4–6: approximately **9–19 active hours**, excluding pauses or unexpected corrections. Stage 3 finished much faster than its original allowance; the accepted export itself took about 3.6 seconds, but implementation, two diagnosed failures, checks and build were separate work. Phone feasibility and model quality are still open questions.

Technical references: [Apple's flexible input shapes](https://apple.github.io/coremltools/docs-guides/source/flexible-inputs.html) support matched enumerated shapes across multiple inputs from iOS 18; [Core ML input/output types](https://apple.github.io/coremltools/docs-guides/source/model-input-and-output-types.html) describe the typed conversion interface. The native tokenizer is a narrow implementation of the pinned BERT policy, checked against the installed tokenizer rather than assumed equivalent. All measurements above come from the saved local artifacts.
