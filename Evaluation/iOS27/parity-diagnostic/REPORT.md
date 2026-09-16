# Cross-runtime D3 parity diagnostic

15 September 2026. **Diagnostic complete; compatibility not passed. Stage 1 remains
incomplete and Stage 2 has not started.** No production code, model, threshold or
historical result was changed. No phone inference, generative inference, paid API,
training or personal-library access occurred.

## What was tested

The frozen Stage 1 Mac executable ran the existing 16 D3 reference pairs on
macOS 27 / Xcode 27, CPU-only, using the existing FP16 Core ML package and classifier.
These are compatibility fixtures, not a new grouping-quality benchmark: all pairs
share `hv19a-i01`. Only two reference decisions accept a match; fourteen reject it.
Agreement with a reference decision is not accuracy against a user-reviewed label.

We reused the saved Stage 1 `parity-00` failure, collected the other 15 pairs, then
repeated pairs 00 and 15 in separate processes: **17 new native requests, 18 saved
observations, 16 unique pairs**. Each pair scores both text directions. Historical
PyTorch probabilities and historical Core ML combined scores are distinct references;
the original export did not retain its per-direction Core ML probabilities.

## Results

| Check | Result | Interpretation |
|---|---:|---|
| Tokenization exact | 16/16 | No observed tokenization change |
| Feature delta within original `1e-8` limit | 16/16; maximum `2.0338e-9` | Feature calculation remains consistent |
| Final accept/reject decision unchanged | 16/16; 2 accept, 14 reject | No decision changed on this small fixture set |
| Original combined-score gate (`1e-7`) | **5/16 pass** | Strict compatibility still fails |
| Maximum combined-score drift vs saved Core ML | `0.000179205` | About 0.0179 percentage points, but over the frozen limit |
| Neural outputs within original conversion bound (`0.002`) | **31/32 directions** | Original conversion bound also fails |
| Maximum neural probability drift vs original PyTorch | `0.002117813` | Original conversion maximum was `0.001263320` |
| Independent Python combiner vs native score | Maximum `5.34e-10` | Combining the new neural outputs reproduces native scores |
| Repeats 00 and 15 | Identical probabilities and scores | No variability observed in these two repeated pairs |
| Pause/resume | Completed hashes and modification times preserved | Resume skipped saved work; final replay made zero requests |

The neural-bound exception is `parity-08`, direction 0:
original PyTorch `0.0731385350`, current native `0.0752563477`, absolute difference
`0.0021178126` (about 5.9% over the `0.002` limit). This is a comparison with the
original model, not a measurement of old-Core-ML-to-new-Core-ML directional drift.

The smallest saved combined-score distance from the unchanged decision threshold
(`0.9804276486193665`) is `0.011367516`, larger than the maximum observed score drift.
That helps explain the unchanged decisions; it does not establish safety for unseen
pairs close to the threshold or for downstream thread placement.

## What the evidence means

The mismatch is localized to the neural inference path, rather than a meaningful
tokenizer, feature or logistic-combiner difference. Source, model and resource hashes
verify, and an independent Python calculation using the new neural probabilities
reproduces the native combined scores. FP16/Core ML compiler or runtime variation is
a plausible explanation, **not a proven root cause**: we have not rerun the old
toolchain under controlled conditions or performed a precision ablation.

There is no evidence here that iOS 27 improves or worsens grouping quality. These
are Mac results. The physical iPhone's device tunnel remained disconnected at the
follow-up check. The Stage 1 Mac Foundation Models observation remains
`modelNotReady`; no new availability claim is made by this diagnostic.

## Recommended next checkpoint — review required

Do not loosen tolerances, retrain, overwrite references, or proceed to the quality
screen based on 16 unchanged decisions. Keep the current app and original failure.

1. Reconnect/unlock the iPhone and collect the same frozen compatibility observations
   in the isolated probe, retaining all numeric failures. Check Apple model readiness
   and embedding representation separately. This identifies whether the drift also
   affects the deployment device. Allow roughly **1–2 hours** for harness/device work,
   excluding model downloads or connection troubleshooting.
2. If the device reproduces the mismatch, scope one controlled CPU-only FP32 versus
   existing FP16 conversion comparison using unchanged weights and inputs. Check
   original tolerances, size, latency and memory before considering any app change.
   Allow approximately **2–4 hours**, subject to availability of the frozen export
   environment. FP32 is an investigation candidate, not an assumed improvement.
3. Only after resolving or explicitly reviewing compatibility can the remaining
   Stage 1 embedding/organizer safeguards and model-readiness checks be completed.
   Stage 2 still requires its own review/start decision. A fresh near-threshold fixture
   set would strengthen later validation; do not turn this exposed set into a quality
   claim or use it to tune the production threshold.

## Saved evidence and validation

- [Frozen diagnostic manifest](manifest.json), [per-pair summary](summary.json),
  [independent audit](independent-audit.json), [pause/resume proof](pause-resume-proof.json).
- `units/` contains observations; `attempts/` contains reservations and raw native output.
- Original [Stage 1 report](../stage1/REPORT.md) and failure remain intact.
- No new dependencies. Approximately 0.30 GiB Stage 1 artifacts and a small diagnostic
  directory; over 56 GiB Mac space free at final measurement, above the 10 GiB reserve.

Commands actually run:

```sh
python3 -B -m unittest discover -s scripts/ios27-parity-diagnostic -p 'test_*.py'
python3 -B -m unittest discover -s scripts/ios27-evaluation -p 'test_*.py'
python3 -B scripts/ios27-parity-diagnostic/diagnose.py freeze
python3 -B scripts/ios27-parity-diagnostic/diagnose.py run --max-units 2
python3 -B scripts/ios27-parity-diagnostic/diagnose.py pause
python3 -B scripts/ios27-parity-diagnostic/diagnose.py run
python3 -B scripts/ios27-parity-diagnostic/diagnose.py resume
python3 -B scripts/ios27-parity-diagnostic/diagnose.py evaluate
python3 -B scripts/ios27-parity-diagnostic/diagnose.py run
python3 -B scripts/ios27-parity-diagnostic/diagnose.py verify
python3 -B scripts/ios27-evaluation/run.py verify
```

Eight diagnostic tests and twelve Stage 1 tests passed. The paused run returned the
expected exit 75; final replay saved zero new units. Both manifests verified. Native
requests executed successfully, but numeric compatibility checks failed as reported
above. Independent arithmetic and pause-proof assertions also passed. Device status
was checked with `xcrun devicectl --timeout 15 --quiet --json-output - list devices`.

The diagnostic is finished, so there is nothing left to resume in this collection.
Do not edit frozen scripts or re-freeze inputs to bypass failures. The report is a
review checkpoint, not permission for the next experiment. No Git state was changed.
