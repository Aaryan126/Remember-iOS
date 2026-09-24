# Sentence-model recovery implemented and device-checked

16 September 2026. **Availability fix verified on this iPhone. Stage 1 remains
incomplete; numerical D3 parity and organizer safeguards are still open.** Stage 2
has not started. Production source is updated; the main Remember app was not
reinstalled or launched against personal data.

## Fix and corrected diagnosis

`AppleProjectEmbedding` now waits asynchronously for **200 ms only after an initial
sentence-model failure**, then retries once. It caches successes, not failures,
respects cancellation, and rechecks the cache after suspension to reuse another
call's successful initialization. Model objects remain confined to the caller's
actor. Language selection, vector pooling, model weights, thresholds and persistent
unavailability safeguards are unchanged.

The immediate retry passed mock tests but failed inside the real provider. That
failed run is retained in `../embedding-recovery/`. An instrumented provider copy
(`../embedding-trace/`) showed that both sentence-model lookups failed before
contextual processing. No tracing was added to production.

Follow-up controls in `../sentence-context/` showed two tightly spaced lookups can
fail on either the main thread or a background actor; the background lookup after
200 ms succeeded. Earlier API-only tests showed recovery but **did not establish
that an immediate retry was reliable**. The evidence supports a brief initialization
window, not a main-thread requirement. Apple's internal cause and behavior across
other OS builds remain unproven. No assets were explicitly downloaded or settings changed.

## Fresh-process validation

The final probe copies the updated production embedding declarations verbatim and
uses unchanged Stage 1 embedding-check code and fixtures. Each pair runs in a fresh
process without an environment preflight that could warm the models.

| Measurement | iPhone 17, iOS 27.0 / 24A437 | Mac, macOS 27.0 / 26A428 |
|---|---:|---:|
| Complete dual embeddings | 16/16 pairs | 16/16 pairs |
| Expected embedding-space identifier | 16/16 | 16/16 |
| Decisions unchanged with frozen reference neural input | 16/16 | 16/16 |
| Minimum contextual cosine to reference | 0.999983536 | 0.999999857 |
| Minimum sentence cosine to reference | 1.0 | 1.0 |
| Maximum feature difference | 0.000301060 | 0.000009686 |
| Maximum score difference with reference neural input | 0.000309916 | 0.000005896 |
| Median full embedding unit duration | 490 ms | 277 ms |

All returned vectors were finite and 512-dimensional. Sentence components differed
by at most `7.40e-9`; contextual components differed by up to `0.001538` on phone.
**The vectors are not bit-identical.** Differences are reported, not suppressed or
used to relax the earlier `1e-7` fixed-input D3 score gate. The existing embedding
checks require matching spaces and unchanged decisions, not exact numeric equality.
Timings include both texts and any readiness wait; they are not organizer latency
or peak memory measurements.

This exposed 16-pair set shares one source and has two positive reference decisions.
It is compatibility evidence, not a new grouping-quality benchmark. These checks
use frozen original neural probabilities: fresh vectors plus fresh neural outputs
have not undergone a new end-to-end qualification. Core ML drift remains unresolved.

## Validation and evidence

- Seven Swift tests passed: success without waiting, delayed recovery/cache reuse,
  persistent failure bound, later recovery, language separation, cancellation, and
  cache recheck after suspension. Tests use injected callbacks, not timed sleeps.
- They ran against the copied production declarations in a dependency-free Swift
  package; only the test module import was adapted. All 33 existing Python runner
  tests also passed (12 Stage 1, 8 phone, 8 Mac diagnostic, 5 sentence diagnostic).
- Final Mac and signed iPhone builds succeeded. Installed the isolated
  `SimpleStudio.Remember.EmbeddingRecoveryV2`, not the main app. Full app tests were
  not run because no cached GRDB checkout was found; no dependency fetch was attempted.
- Initial immediate-retry failure and diagnostic traces remain saved separately.
  One Mac build preflight stopped at the storage guard while Swift tests were building;
  after tests finished, the unchanged limit passed. No limits were raised or files deleted.
- [Summary](summary.json), [manifest](manifest.json), raw `attempts/`, interpreted
  `units/`, and [pause/resume proof](pause-resume-proof.json) are saved. Pause/resume
  preserved the first phone result's hash and modification time. Final replay made
  zero new requests on either platform; final verification passed.

Old runners' current-source verification will correctly flag this authorized source
change. Do not rewrite old manifests. The new runner allows only the authorized
`ProjectIntelligence.swift` difference from Stage 1, verifies the old copied sources,
resources and binaries, and freezes the new source/tests separately. Old results
and tolerances are preserved.

Main commands actually run, from repository root:

```sh
python3 -B scripts/ios27-embedding-recovery-v2/run.py prepare
swift test --package-path Evaluation/iOS27/embedding-recovery-v2/build/unit-tests --disable-automatic-resolution
python3 -B scripts/ios27-embedding-recovery-v2/run.py build --platform mac
python3 -B scripts/ios27-embedding-recovery-v2/run.py build --platform phone
python3 -B scripts/ios27-embedding-recovery-v2/run.py freeze
python3 -B scripts/ios27-embedding-recovery-v2/run.py install --device <physical-device-id>
python3 -B scripts/ios27-embedding-recovery-v2/run.py run --platform phone --device <physical-device-id> --max-units 1
python3 -B scripts/ios27-embedding-recovery-v2/run.py pause
python3 -B scripts/ios27-embedding-recovery-v2/run.py run --platform phone --device <physical-device-id>
python3 -B scripts/ios27-embedding-recovery-v2/run.py resume --platform phone --device <physical-device-id>
python3 -B scripts/ios27-embedding-recovery-v2/run.py run --platform mac
python3 -B scripts/ios27-embedding-recovery-v2/run.py verify
```

The paused run returned expected exit 75. A nonfatal compiler warning recommends an
async alternative for the pre-existing contextual asset-request callback; that
unrelated path was not changed. `git diff --check` passed. No Git state was changed.

## Handoff

The fix is complete in source and tested in the isolated app. The installed main
Remember app needs a normal rebuild/install to receive it. Next, return to the
separately scoped numerical compatibility investigation and pending organizer
safeguards before Stage 2. No training, precision conversion, paid API call or
quality-screen escalation occurred. Work is saved and paused; safe to disconnect.
