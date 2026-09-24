# iPhone compatibility checkpoint

16 September 2026. **Phone parity collection complete; compatibility blocked.**
Stage 1 remains incomplete and Stage 2 has not started. The installed app is the
isolated `SimpleStudio.Remember.IOS27Compatibility` probe, not Remember. No personal
memories, production configuration, model weights or thresholds were changed.

## Results on the physical iPhone 17

iOS 27.0, build 24A437; the existing frozen Xcode 27 build, CPU-only D3 inference.
The device was reachable over its wired connection and unlocked. These observations
are from this probe, not an inspection of the main app's private container.

| Check | Result | Meaning |
|---|---:|---|
| Apple Foundation Models availability | Available; context size 4,096 | Local language-model runtime reports ready; no generation quality claim |
| D3 reference decisions unchanged | 16/16 (2 accept, 14 reject) | Same decisions on the small compatibility set |
| Tokenization / feature tolerance | 16/16 / 16/16 | Text processing and frozen-vector features remain consistent |
| Original combined-score gate, `1e-7` | **5/16 pass** | The strict compatibility failure reproduces on phone |
| Neural outputs within original PyTorch conversion bound, `0.002` | **31/32 directions** | One original conversion-bound failure reproduces |
| Phone neural outputs vs new Mac outputs | **32/32 exactly equal** | The observed discrepancy is not confined to the Mac |
| Phone combined scores vs new Mac | Maximum difference `1.04e-17` | Equivalent apart from negligible arithmetic difference |
| Contextual embedding assets | Available; revision 1, dimension 512; identifier matches | This is only one of D3's two embedding inputs |
| English sentence embedding | **Unavailable in environment check** | Revision/dimension returned null |
| Production embedding provider on first pair | **`unavailable`** | No complete dual-embedding result; remaining 15 embedding units not run |

The maximum score drift against historical Core ML is `0.000179205`. The maximum
neural probability drift against original PyTorch is `0.002117813`, again on
`parity-08`, direction 0. An independent Python combiner calculation reproduces the
phone scores within `5.34e-10`. No tolerance was relaxed and no reference replaced.

This is the same exposed 16-pair fixture set as the Mac diagnostic: all pairs share
one source. Decision agreement is **not grouping accuracy**, and these fixtures do
not qualify near-threshold behavior or end-to-end organization. Parity inference
uses saved reference embeddings; it can succeed even while fresh embedding creation
is unavailable. See the [Mac diagnostic](../parity-diagnostic/REPORT.md) for context.

## New blocker and user impact

Apple documents that `sentenceEmbedding(for:)` returns `nil` when unavailable.
The probe observed exactly that for English. It separately found contextual assets
available, then the copied production provider failed to produce the dual embedding
for the first fictional pair. This is consistent with the missing sentence model,
but does not distinguish transient asset readiness, OS behavior, or a probe-specific
issue. It is not evidence that Apple removed sentence embeddings in iOS 27.
[Apple API documentation](https://developer.apple.com/documentation/naturallanguage/nlembedding/sentenceembedding(for:)).

Code inspection shows that `AppleProjectEmbedding.model(for:)` requires this sentence
model before producing vectors. `D3ProjectOrganizer` retains existing assignments
and records an incomplete/unavailable placement when encoding fails; it does not
silently use another model or cloud fallback. **If the same condition occurs in the
main app**, newly eligible captures would not receive normal automatic D3 matching
until embeddings become available. We did not inspect or mutate the personal library
to demonstrate that condition there. Existing placement preservation is a code
observation, not a completed organizer-ledger integration test in this checkpoint.

## Timing observations, not a performance qualification

Each pair used a new process and two directional inferences:

| Measurement | Median | Observed range |
|---|---:|---:|
| Model load | 2.72 ms | 2.42–218.81 ms |
| First directional inference | 23.97 ms | 22.20–114.58 ms |
| Second directional inference | 17.32 ms | 16.85–22.02 ms |

Post-unit resident-memory samples were approximately 36.0–42.7 MiB. These are **not
peak memory**, and new-process measurements are not cold-boot measurements: OS caches
can persist between runs. Embedding generation and full organizer latency are not
included. [Raw timing summary](timing-summary.json).

## Work saved and checks run

There are 18 saved observations: environment, 16 parity pairs and one embedding
failure. Two observations came from the original Stage 1 phone attempt; this runner
made 16 additional requests (15 parity + one embedding). No generation, paid API,
PCC request, training, precision conversion or main-app installation occurred.

- [Manifest](manifest.json): frozen scripts, inputs, device identity and request cap.
- [Audit and evaluation pointer](audit.json): independently checked arithmetic and
  per-pair report, including all failures.
- [Pause/resume proof](pause-resume-proof.json): the first three saved observations
  retained their hashes and modification times across pause/resume.
- `attempts/` and `units/`: raw outputs, reservations and interpreted observations.

Commands actually run from the repository root:

```sh
python3 -B scripts/ios27-evaluation/run.py verify
python3 -B scripts/ios27-evaluation/run.py install --device <physical-device-id>
python3 -B scripts/ios27-evaluation/run.py resume --platform phone --device <physical-device-id> --max-units 2
python3 -B scripts/ios27-evaluation/run.py pause
python3 -B -m unittest discover -s scripts/ios27-phone-diagnostic -p 'test_*.py'
python3 -B -m unittest discover -s scripts/ios27-parity-diagnostic -p 'test_*.py'
python3 -B -m unittest discover -s scripts/ios27-evaluation -p 'test_*.py'
python3 -B scripts/ios27-phone-diagnostic/run.py freeze --device <physical-device-id>
python3 -B scripts/ios27-phone-diagnostic/run.py run --max-units 3
python3 -B scripts/ios27-phone-diagnostic/run.py pause
python3 -B scripts/ios27-phone-diagnostic/run.py run
python3 -B scripts/ios27-phone-diagnostic/run.py resume
python3 -B scripts/ios27-phone-diagnostic/run.py evaluate
python3 -B scripts/ios27-phone-diagnostic/run.py verify
python3 -B scripts/ios27-phone-diagnostic/run.py run
python3 -B scripts/ios27-phone-diagnostic/run.py pause
```

All **28 runner tests passed** (8 phone, 8 Mac diagnostic, 12 Stage 1). Both frozen
artifact checks passed. The paused run returned the expected exit 75. Stage 1 stopped
with exit 1 on numeric parity; the diagnostic stopped with exit 1 on the saved native
embedding error. Final replay stopped at that same failure without another request.
Independent arithmetic and preservation assertions passed. No unresolved remote
attempt remains; both runners report safe to close. No Git state was changed.

## Next checkpoint — review before proceeding

Prioritize **sentence-embedding availability**, before the optional FP32 comparison.
Use a separately versioned, minimal probe to inspect supported/current sentence
revisions, default versus explicit revision 1, and a fictional English vector request
in fresh processes. Check device asset/readiness behavior using documented APIs; do
not change language settings, delete system assets, reset the device, or substitute
a different embedding space. Record failures instead of silently retrying the frozen
run. Rough estimate: **1–2 hours** for diagnosis, excluding OS/model downloads; a fix
cannot be timed reliably until the cause is known.

Once that is resolved, complete embedding numeric checks, then the scoped FP32/FP16
comparison if warranted (**2–4 hours**, estimate), plus pending organizer safeguards.
FP32 cannot fix missing sentence embeddings. The local Foundation Models availability
is encouraging, but no grouping improvement has yet been measured. Stage 2 remains
a separate reviewed experiment, not an automatic continuation.

All work is saved and paused. Resume currently stops at the recorded embedding error;
do not edit frozen evidence or rerun completed device units. Recovery of a genuinely
lost console uses `collect --unit <unit>` without a new inference.
