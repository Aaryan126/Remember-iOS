# Threshold-near compatibility checkpoint

16 September 2026. Completed on the physical iPhone 17 / iOS 27 and Mac / macOS 27.
**No production model, threshold, library or historical result changed.**

## Frozen scope

Selected 24 previously evaluated fictional pairs using only the saved seed-29
scores: 12 nearest below the production threshold and 12 nearest above it, with at
most two per library per side and deterministic ID tie-breaking. This covers 11
libraries. Labels were not used in selection. The minimum historical threshold
margin is 0.0000472627, compared with about 0.01136 in the preceding diagnostic.
`selection.json` was published before new inference.

Original weights, tokenizer, 512-token inputs, CPU-only execution, classifier and
threshold `0.9804276486193665` remain fixed. Original PyTorch reference predictions
were recomputed, then both Core ML artifacts were evaluated. None of the recomputed
PyTorch decisions differed from the historical decisions. This is a deliberately
selected **regression stress test**, not fresh quality validation or a precision/
recall estimate. The examples are already exposed and cannot become a held-out set.

## Phone results

| Check | Current FP16 artifact | FP32 evaluation candidate |
|---|---:|---:|
| Fixed-vector decisions unchanged | 24/24 | 24/24 |
| Fresh-embedding decisions unchanged | 24/24 | 24/24 |
| Neural directions within original 0.002 bound | 45/48 | 48/48 |
| Maximum neural delta from PyTorch | 0.011778176 | 0.000000417 |
| Native scores within 1e-7 of freshly saved same-artifact conversion reference | 24/24 | 24/24 |
| Maximum native/conversion-reference score delta | 8.0721e-10 | 8.0830e-10 |
| Maximum fresh-vs-fixed combined-score delta | 0.000321250 | 0.000313017 |
| Smallest fresh-score margin from threshold | 0.000156780 | 0.000010548 |

Mac decision counts and neural outputs match the phone exactly for each precision.
Fixed feature values pass the original 1e-8 tolerance for all pairs on both
platforms (maximum delta 2.986e-9). These checks are saved in `audit.json`.

The FP16 24/24 conversion-reference result uses a **newly recorded same-runtime
reference**, because these boundary pairs had no saved historical FP16 Core ML
reference. It does not repair the old 5/16 historical score gate. The three neural
bound failures are differences from original PyTorch; without old FP16 outputs for
these particular pairs, they cannot be attributed specifically to the OS upgrade.

FP32 passes this bounded candidate gate. It does not establish production safety:
the closest fresh score remains only 0.000010548 from the threshold, and neither
future Apple embedding updates nor all possible decision boundaries were tested.
Do not recalibrate thresholds using these examples.

## Execution and controls

- 96 native units: 24 pairs × two precisions × two platforms. Each unit makes two
  directional predictions and one warm repeat: 288 native predictions, plus 48
  PyTorch and 96 Python Core ML reference predictions during preparation.
- All units completed without native errors. Tokenization matched the saved inputs.
  Current production provider supplied fresh embeddings; fixed vectors were a
  separate control, not a substitute when fresh embeddings were unavailable.
- Input/source/model/binary hashes are frozen in `manifest.json`, `reference-inputs.json`
  and the original precision export manifest. The FP32 evaluation identity is
  `d3-seed29-fp32-ios27-evaluation-v1`; the app's original artifact is unchanged.
- The first two completed phone units retained their exact hashes and modification
  times after pause/resume. A subsequent paused run returned exit 75; completed
  replay dispatched zero new native units. See the checkpoint receipts.
- During the simultaneous initial safety-app build, the storage guard briefly
  refused dispatch. No tolerance or storage cap was raised. After the build finished,
  the snapshot was ~3.83 GB experiment storage and ~49.5 GB free; collection resumed.
  The exact transient size was not retained, so this is not a peak-build-size claim.
- Three selection tests pass (balance/diversity/determinism, insufficient diversity,
  label independence). The inherited runner regression suites are also rerun and
  recorded at the final checkpoint.

## Inspect / resume

```sh
python3 -B scripts/ios27-boundary/run.py status
python3 -B scripts/ios27-boundary/run.py verify
python3 -B scripts/ios27-boundary/analyze.py
```

The completed run is paused at handoff. It does not start the reasoning-quality
experiment on resume. Never rebuild over the frozen attempt or rewrite historical
fixtures to make compatibility pass. Results: `summary.json`, `audit.json`,
`pause-resume-proof.json`, per-unit raw receipts and the parent checkpoint report.
