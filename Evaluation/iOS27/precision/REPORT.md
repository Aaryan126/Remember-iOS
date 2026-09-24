# iOS 27 precision comparison — checkpoint for review

16 September 2026. **Collection complete; stopped for review. Stage 1 remains
incomplete and Stage 2 has not started.** No production model or threshold changed.

## Outcome

An FP32 conversion of the original trained weights closely reproduces the original
PyTorch outputs on both the Mac and physical iPhone. The existing FP16 package still
has the previously observed numerical discrepancy. Both precisions preserve every
reference decision in this small diagnostic, including with freshly generated
Apple embeddings. This is compatibility evidence, **not a grouping-quality gain**.

| Physical iPhone measurement | Existing FP16 | Experimental FP32 |
|---|---:|---:|
| Fixed-input decisions unchanged | 16/16 | 16/16 |
| Fresh-embedding decisions unchanged | 16/16 | 16/16 |
| Neural directions within original 0.002 bound | 31/32 | 32/32 |
| Maximum neural difference from original PyTorch | 0.002117813 | 0.000000283 |
| Scores within 1e-7 of that export's own conversion reference | 5/16 | 16/16 |
| Maximum score difference from that export's own reference | 0.000179205 | 0.000000000534 |
| Maximum fresh combined-score difference from original PyTorch | 0.000865049 | 0.000309811 |
| Compiled model storage, decimal MB | 66.89 | 133.60 |
| Median first inference in a fresh process | 21.64 ms | 48.86 ms |
| Median repeated warm inference | 17.91 ms | 42.33 ms |
| Median process peak resident memory, decimal MB | 127.60 | 174.18 |
| Maximum process peak resident memory, decimal MB | 210.16 | 343.02 |

FP32 costs approximately 66.7 MB more compiled model storage and 2.36× the measured
warm inference time. These timings are for **one direction of one pair**, not a
complete capture or all retrieved candidates. The comparison app contains both
models; its total size is not the production app size.

The Mac matched the phone's neural probabilities exactly for all 32 directions at
each precision. The fresh PyTorch reference matched its historical outputs exactly.
Fresh features across FP16/FP32 runs agreed to 5.56e-17 on each platform, isolating
the precision comparison from meaningful embedding differences. Independent Python
recomputation of the native combined scores agreed within 1.12e-16.

### Do not conflate two reference checks

The **original strict gate compares against the historical FP16 Core ML export**:
FP16 passes 5/16, and FP32 passes 0/16. That gate remains failed, not waived.
The candidate-specific check compares FP32 native scores with the newly saved FP32
conversion reference, using the same 1e-7 score tolerance; it passes 16/16. The
original 0.002 neural-to-PyTorch tolerance also passes for FP32 without adjustment.

Adopting FP32 as an evaluation candidate requires explicitly recognizing a new
export/reference identity. It is not evidence that the historical FP16 artifact
became compatible. No historical reference, tolerance, or decision threshold was
rewritten. Fresh Apple contextual-vector drift remains a separate source of small
combined-score differences even with FP32.

## Method and limits

- Same trained seed-29 weights, tokenizer, fixed 512-token inputs, feature combiner,
  threshold and CPU-only compute path; FP32 was exported from original FP32 weights,
  not obtained by upcasting the FP16 package. Hashes bind all inputs and artifacts.
- Sixteen existing fictional parity pairs, evaluated in both directions, at two
  precisions, on two platforms: 64 saved native units, each with two directional
  predictions and one repeat (192 native predictions). Export validation separately
  recorded 32 PyTorch and 32 converted Core ML predictions.
- These are correlated pairs sharing one anchor, with two positive and fourteen
  negative reference decisions. They are not a fresh representative quality dataset
  or a comprehensive near-threshold stress test. The smallest fresh phone score
  margin from the threshold was about 0.01136, so unchanged decisions do not prove
  that borderline cases are safe.
- Each unit used a new process; this is not a device-cold-boot measurement. OS caches
  persisted, FP16/FP32 order was interleaved rather than randomized, and only one
  extra warm prediction per unit was collected. Model-load medians (~1.4 ms) are
  cache-influenced; the first FP16/FP32 phone loads were 135/170 ms.
- Memory is the kernel-reported **whole-process peak resident size**, including
  embeddings and frameworks. It is neither iOS physical footprint nor the memory
  peak of the full Remember app. No sustained thermal/battery qualification occurred.
- No private memories, generation requests, paid API calls, training, database
  changes, or main-app reinstall occurred. Only the isolated probe was installed.

## Environment issue and reproducibility

The first export attempt failed before inference: the old SciPy 1.15.3 PROPACK
binary could not load after the OS upgrade (`__thread_bss` zero-fill section error).
The original failed attempt and traceback remain saved. An isolated SciPy 1.17.1
override was installed under this experiment with `--no-deps`; the existing Python
environment, NumPy, Torch, Core ML Tools and trained assets were not upgraded.
`export-fp32/environment-override.json` records the override and launcher identity.
This was an environment failure, not a failed model-quality result.

Key artifacts: `manifest.json`, `export-fp32/export-inputs.json`,
`export-fp32/pytorch-reference.json`, `export-fp32/export-result.json`, `summary.json`,
`audit.json`, `pause-resume-proof.json`, and `checkpoint.json`. Large build/model
assets remain local and ignored. Frozen experiment sources are in
`scripts/ios27-precision/`; do not edit them or rebuild over this saved attempt.

Validation performed:

```sh
python3 -B -m unittest discover -s scripts/ios27-precision -p 'test_*.py'
python3 -B -m unittest discover -s scripts/ios27-evaluation -p 'test_*.py'
python3 -B -m unittest discover -s scripts/ios27-phone-diagnostic -p 'test_*.py'
python3 -B -m unittest discover -s scripts/ios27-parity-diagnostic -p 'test_*.py'
python3 -B -m unittest discover -s scripts/ios27-sentence-diagnostic -p 'test_*.py'
python3 -B scripts/ios27-precision/analyze.py
python3 -B scripts/ios27-precision/run.py verify
git diff --check
```

All 39 Python tests passed; Mac and signed phone probe builds passed; all 64 native
units completed without errors. Pause/resume retained hashes and modification times
of the first two saved phone units. Replaying completed Mac and phone runs saved
zero new units. Seven Swift readiness regression tests passed in the previous
checkpoint, not rerun here. Full Remember app tests were not run in this checkpoint.

## Recommendation and next boundary

Keep the production FP16 artifact unchanged for now. Accept FP32 **only as an
explicitly versioned evaluation candidate/reference**, then finish Stage 1's
organizer safeguards and a bounded boundary-sensitive regression check against the
current baseline. Do not start another broad model/precision search or claim quality
uplift from these sixteen pairs. Candidate qualification is separate from shipping.

After that review, Stage 2 can test whether the upgraded phone's local language model
actually improves grouping: current D3 control versus the old C7 reviewer and one
frozen boundary-focused reviewer, on the planned 112 unique inputs / 160 scored
packets. Promotion still needs precision-first gates and later fresh validation.

Work is stopped at this checkpoint. To inspect without inference:

```sh
python3 -B scripts/ios27-precision/run.py status
python3 -B scripts/ios27-precision/run.py verify
```

Wait for `safeToClose: true` before disconnecting. Resuming this completed diagnostic
does not start Stage 2; that needs its own approved scope and frozen manifest.
