# Stage 4 complete — initial iPhone feasibility passed

11 September 2026. **Stopped at this checkpoint.** No measurement or training worker remains running. The phone may be disconnected and the laptop closed. Stage 5 requires explicit continuation.

## Outcome

The compact FP16 MiniLM architecture meets the initial latency, sampled process-memory, numerical-consistency and interruption gates on the connected **iPhone 17 (iPhone18,3), iOS 26.6.1 build 23G83**.

**Recommendation: proceed to the small Stage 5 specialist-training experiment. No corrective model conversion or device rerun is required first.** This is a feasibility pass, not evidence that the model groups memories well: the classification head remains untrained. Stage 5 must establish whether task-specific training beats the frozen simple classifier; integration remains out of scope.

## Measured results

Each timed shortlist contains ten fictional text pairs. Every pair runs in both directions, followed by probability averaging: **20 sequential model predictions per shortlist**. Timing includes tokenization, input-array allocation, prediction, averaging and cancellation checks; result-file serialization is excluded. It does not include embedding retrieval, OCR, transcription, video processing or the rest of Remember.

| Measurement | Actual result | Interpretation |
| --- | ---: | --- |
| Warm 256-token shortlist, 100 measurements | Median **79.7 ms**; p95 **85.3 ms**; maximum **86.3 ms** | Pass: p95 ≤1,000 ms |
| Warm 512-token shortlist, 100 measurements | Median **253.1 ms**; p95 **257.9 ms**; maximum **259.3 ms** | Reported separately; comfortably below 1 second in this run |
| Peak sampled process physical footprint | **163,546,008 bytes / 163.55 MB** | Pass: ≤500 MB |
| Peak sampled resident memory (RSS) | **261,849,088 bytes / 261.85 MB** | Different memory accounting; not interchangeable with footprint |
| Phone tokenizer parity | **416/416 exact input matches** | Both lengths, both directions, including edge cases |
| Phone output class agreement with original | **100%**, including all 208 direction-averaged pair/length cases | Untrained reference consistency, not label accuracy |
| Maximum absolute probability difference | **0.00039265** (about 0.0393 percentage points) | Pass: ≤0.01 |
| Timed pair averages independently checked | **3,100**, maximum difference **0.00033987** | The timed path also preserves original-model outputs |
| Cooperative pause/resume | **6 completed shortlists retained byte-for-byte**, then all 100 interruption-test shortlists completed | Pass: no lost completed records |

p95 uses the nearest-rank definition. These repeated fixture measurements are descriptive, not independent users or a production latency guarantee. Three warmup shortlists precede each warm/resumed measurement process and are saved separately, not counted in the 100.

### Cold preparation is a separate cost

The first preflight installation's observed model+tokenizer load took **3.631 seconds**. After the accepted build was installed, its first observed load took **3.203 seconds**. The following nine fresh-process loads had a median of **33.1 ms**. All ten accepted process-cold launches used distinct process IDs; their first twenty-pass shortlist took **91.6–94.0 ms**.

The initial preparation cost is real and must not be hidden by the faster restarts. Restarting a process does **not** purge iOS compilation/accelerator caches. No device reboot or cache purge was performed. These are model/tokenizer preparation timings and saved task-to-model-ready timings, not a measurement of pre-main launch or full UI startup; the host's launch/transport duration is also saved but is not an app-startup proxy.

A future integration should load off the UI thread and account for first-use preparation, rather than assuming every request has the warm latency. That integration decision is not implemented here. Apple likewise treats model loading and prediction as separate performance concerns in [its Core ML integration guidance](https://developer.apple.com/videos/play/wwdc2023/10049/).

### Actual device-visible storage

| Artifact/snapshot | Logical file size |
| --- | ---: |
| Signed installed probe bundle, measured inside the phone | **67,780,939 bytes / 67.78 MB** |
| Compiled model within that bundle | **66,879,135 bytes / 66.88 MB** |
| Probe Library files at final snapshot, including caches | **4,427,217 bytes / 4.43 MB** |
| Probe Documents at final snapshot, including saved diagnostic records | **1,942,498 bytes / 1.94 MB** |
| Probe temporary files at final snapshot | **0 bytes** |

The phone-reported bundle size exactly matches the signed build's file total. These are logical file bytes, not APFS allocated blocks, Settings' installation figure, App Store download size, inaccessible system caches, or the final Remember app size. End snapshots precede writing their own small diagnostic receipt. The probe does not bundle another copy of the existing Apple embedding system. The earlier 70–130 MB estimate remains a planning range for a future configuration, not a measured total production-app size.

### Memory, thermal and hardware limits

The probe sampled `task_vm_info` physical footprint and resident size on a dedicated serial queue every **20 ms**, before model loading through job completion. There were **2,763 samples**, no sampling failures, a measured median interval of **20.00 ms**, and a maximum interval of **22.24 ms**. All sampled thermal states were nominal; Low Power Mode was off.

Physical footprint is the chosen process-memory gate; resident size is retained separately. Apple exposes these fields through [`task_vm_info_data_t`](https://developer.apple.com/documentation/kernel/task_vm_info_data_t). Sampling can miss shorter spikes; separate Core ML/system-service/accelerator allocations are not fully observable from this app. No claim about total device RAM consumption, battery endurance or sustained thermal throttling follows from this short test.

Compute units were `.all`. This permits Core ML to select available hardware; it does not prove Neural Engine execution. [Apple's prediction guide](https://apple.github.io/coremltools/docs-guides/source/model-prediction.html) explains this configuration. No device-specific accelerator optimization was added to obtain the result.

## Interruption and safe resumption

The Mac delivered a cooperative pause request during a live, separate 100-shortlist job. Six shortlists completed before the phone reached the pause boundary. It saved its end receipt and exited normally. Relaunching with `--resume` repeated warmup, preserved those six records exactly, and computed the remaining 94. Every phone export was checked for changed completed records. A completed warm-job resume also returned `job already complete` without starting inference.

The phone also has a Pause button and cancellation when it leaves the foreground; **those UI/background paths were implemented but not independently exercised**. The proven interruption is the host-requested cooperative pause. We did not deliberately unplug the cable, reboot, force an out-of-memory termination or simulate a crash. Unexpected loss of connection requires reconnecting and collecting the phone's records first; only an unfinished shortlist needs repeating, but a missing end receipt must be investigated, not converted into a successful measurement.

The overlapping-run guard was exercised: a premature second host command was rejected while the 512-token worker still held its lock. It did not launch a competing phone process. All 15 accepted-run phone processes have end receipts: 14 completed and one intentionally paused, all with exit code zero. No unaccounted crash or changed completed record was observed.

## Evidence and implementation

Accepted run: [`runs/stage-4-attempt-02`](../runs/stage-4-attempt-02/). Key files:

- `manifest.json`: frozen settings, candidate identity and source/project hashes.
- `build.json`, `installations/`, `commands/`, `console/`: signed isolated build and raw host/device logs.
- `device/`: cold, warm, parity and interruption records, plus per-launch memory/load/storage receipts.
- `exports/`: immutable raw copies; **3,383 exported JSON files** compared byte-for-byte with retained evidence.
- [Machine-readable measurement report](../runs/stage-4-attempt-02/reports/1789109119555357000.json), [independent audit](../runs/stage-4-attempt-02/audit.json), and `complete.json`.

Completion SHA-256: `4891fadd62a504c687f347005a8a6e9e0e027b47295693a15dee74158adc749b`. The verifier checked **4,273 accepted-run files**, preserved preflight evidence, source/project/app bindings and the Stage 1–3 checkpoint chain.

Preflight attempt 01 is retained. Before the full sweep, report review corrected chronological ordering and increased the separate interruption exercise from five shortlists to 100 so the fast phone could actually be paused mid-run. This required a new immutable attempt, not a changed model or relaxed gate. Its successful first-load measurement remains explicitly reported above. The Swift probe, frozen runtime/tokenizer and model are identical across both Stage 4 attempts.

New implementation files under `scripts/matcher-feasibility/`: `Stage4ProbeApp.swift`, `stage4.py`, `stage4_report.py`, `test_stage4.py`, and `audit_stage4.py`. The standalone probe has no production App Group, private-data permissions, personal vault or network requests. It contains 104 projected fictional pairs, never benchmark gold. The existing production sources and frozen Stage 1–3 implementation remain unchanged; test labels were not opened. No Git state was changed.

The isolated **Matcher Probe remains installed**, with fictional diagnostic records in its own container. No cleanup or uninstall was performed. The dedicated external experiment workspace is about **1.9 GiB**, with about **37 GiB free** on the Mac; the accepted Stage 4 evidence directory is about **18 MiB**.

## Validation actually run

```sh
MATCHER_WORKSPACE="$HOME/Library/Application Support/RememberMatcherFeasibility/v1"
"$MATCHER_WORKSPACE/venv/bin/python" -m unittest discover -s scripts/matcher-feasibility -p 'test_*.py' -q
python3 -m unittest discover -s scripts -p 'test_organization*.py' -q
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/environment.py --workspace "$MATCHER_WORKSPACE" --output Evaluation/MatcherFeasibility --verify-only
"$MATCHER_WORKSPACE/venv/bin/python" scripts/matcher-feasibility/audit_stage4.py verify --run Evaluation/MatcherFeasibility/runs/stage-4-attempt-02
```

**83 feasibility tests and 22 existing organization/audio tests passed.** Signed iOS Release builds, device installation, all required physical-device jobs, strict reporting and the independent audit passed. The audit additionally confirmed six historical evidence files and 51 production Swift files were unchanged. The environment check verified all 37 locked distributions and six original model assets. Exact build/device commands and output are retained under the run's `commands/` and `launches/` directories.

## Next checkpoint

**No corrective rerun is needed before Stage 5.** The main open risk is model quality, not this initial device budget. Stage 5 will train the small specialist, select using development data, freeze its weights/thresholds, and then evaluate the untouched test libraries against the frozen simple classifier. If it does not demonstrate sufficient benefit, we keep the simpler baseline rather than integrating the neural model.

Next hardware: **Mac only; no phone required**. Initial Stage 5 allowance: **6–12 active hours**, with resumable training checkpoints. Stage 6, if warranted, needs the phone for another **2–4 hours**. Total remaining allowance: **8–16 active hours**, excluding pauses or newly approved corrective work. Stage 4 finished faster than its original 1–3 hour allowance; that does not establish the training-stage duration.

**Stage 4 remaining work: none. Stopped; waiting for the user's continuation.**
