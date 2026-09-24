# Sentence embedding: first-call failure, not a persistently missing model

16 September 2026. **Diagnosis checkpoint complete. Production fix not implemented.**
The prior phone failure is preserved; Stage 1 is still incomplete and Stage 2 has
not started. D3's separate numeric-parity failure remains unresolved.

## What we found

On this physical iPhone 17 (iOS 27.0, build 24A437), the first English sentence-model
lookup in each of four fresh probe processes returned `nil`. Later lookups in the
same process succeeded. A controlled second call succeeded immediately, without
waiting, requesting assets, changing settings or changing revisions.

| Fresh-process test | Phone first lookup | Phone next relevant lookup | Mac control |
|---|---|---|---|
| Snapshot 0: default, metadata, explicit revision 1 | Default: unavailable | Revision 1: valid vector | Available from first call |
| Snapshot 1: repeat in new process | Default: unavailable | Revision 1: valid vector | Available from first call |
| Default-only control: no metadata or explicit revision first | Default: unavailable | Second default call: valid vector immediately | Available from first call |
| Revision-first control | Explicit revision 1: unavailable | Following default call: valid vector immediately | Available from first call |

Successful vectors were finite, nonzero, 512-dimensional, with model revision 1.
The phone advertised supported sentence revisions `[1]` and current revision `1`.
Subsequent calls after two seconds also succeeded. The tests used one fixed fictional
English sentence, not the personal memory library. These are availability controls,
not vector equality or grouping-quality qualification.

The data rules out **persistent model absence during this test** and shows that
pinning the revision alone does not fix the first-call failure. It is consistent
with a process-local initialization/readiness issue in this OS/runtime combination.
The exact Apple-internal cause is not established; this is not a claim about every
iOS 27 device, nor proof that no earlier iOS release has the same behavior.

Apple's documented APIs permit `nil` when a model is unavailable, but do not promise
that retrying will always work. Both overloads and the revision-inspection APIs are
documented; there is no justification to bypass unavailable-model safety checks.
[Default lookup](https://developer.apple.com/documentation/naturallanguage/nlembedding/sentenceembedding(for:)),
[explicit revision](https://developer.apple.com/documentation/naturallanguage/nlembedding/sentenceembedding(for:revision:)),
[supported revisions](https://developer.apple.com/documentation/naturallanguage/nlembedding/supportedsentenceembeddingrevisions(for:)).

## Why our earlier test stopped

`AppleProjectEmbedding.model(for:)` in `Remember/Remember/ProjectIntelligence.swift`
does one sentence-model lookup and returns `nil` immediately if it fails. The
compatibility harness uses a new process for each unit and stops on an unavailable
embedding. It therefore observed the failed first call and never reached the
successful second call. This explains the observed availability failure without
requiring a replacement embedding model.

The earlier description “sentence embedding unavailable” was accurate for the
recorded call, but should **not** be read as “the phone has no sentence model.”
That broader interpretation is contradicted by these controls.

## Expected effect in Remember

The app process is normally longer-lived than a one-unit probe. The provider caches
successful models and does not cache `nil`, so a later attempt can recover. The likely
user-visible risk is **delayed automatic matching for an early capture after launch**,
not permanent loss of all grouping. `D3ProjectOrganizer` preserves assignments and
marks unavailable work incomplete for a later eligible retry. This is inferred from
production code; we did not inspect, launch against, or mutate the user's vault.

## Small recommended fix

Add one bounded retry when the sentence-model lookup first returns `nil`, keeping
the successful model cached in the existing actor. If both attempts fail, retain the
current safe unavailable behavior. Do not switch vector spaces, force English for
non-English inputs, request cloud fallback, or weaken the D3 compatibility guard.
Revision pinning alone is not sufficient, as the revision-first control shows.

Test first-call failure followed by success, persistent failure, ordinary success,
and cached reuse. Then test the patched production provider in fresh phone processes
and rerun the 16 embedding fixtures under a new versioned checkpoint. That would
verify vectors and decisions, which these API-only controls do not establish.
Estimated implementation and focused verification: **45–90 minutes**, excluding
newly discovered compatibility failures. No production change was made during this
diagnostic-only task.

Only after that check should we return to the separate FP16/FP32 numeric investigation
and remaining Stage 1 safeguards. No new training or grouping-quality sweep is needed
to address this availability bug.

## Evidence and validation

New isolated bundles: `SimpleStudio.Remember.SentenceDiagnostic` and
`SimpleStudio.Remember.SentenceControls`. Each ran two processes on phone and two on
Mac: **four phone and four Mac observations total**. No generative model, paid API,
asset-download request, main-app update, settings change or Git mutation occurred.
The two-second wait is within each short process; each host unit saves independently.

- [Snapshot manifest](manifest.json), `units/`, `attempts/`: raw snapshots and hashes.
- [Call-order controls](../sentence-controls/manifest.json), sibling `units/` and
  `attempts/`: controlled default-only and revision-first results.
- [Audit summary](audit.json): assertions over all eight saved observations.
- Scripts: `scripts/ios27-sentence-diagnostic/` and `scripts/ios27-sentence-controls/`.

Both Mac builds and both signed iPhone builds/installations succeeded. All **33 runner
unit tests passed**: 5 new transport/checkpoint tests plus the existing 28. Both
manifests verified. Replaying saved phone units made no new calls. The controls share
the tested transport harness and freeze both the wrapper and parent driver hashes.
The first diagnostic build had a nonfatal Xcode destination warning; it returned
success and the signed app ran on the intended phone.

Commands run (from repository root):

```sh
python3 -B -m unittest discover -s scripts/ios27-sentence-diagnostic -p 'test_*.py'
python3 -B -m unittest discover -s scripts/ios27-phone-diagnostic -p 'test_*.py'
python3 -B -m unittest discover -s scripts/ios27-parity-diagnostic -p 'test_*.py'
python3 -B -m unittest discover -s scripts/ios27-evaluation -p 'test_*.py'
python3 -B scripts/ios27-sentence-diagnostic/run.py build --device <physical-device-id>
python3 -B scripts/ios27-sentence-diagnostic/run.py install
python3 -B scripts/ios27-sentence-diagnostic/run.py run --platform phone --unit snapshot-0
python3 -B scripts/ios27-sentence-diagnostic/run.py run --platform phone --unit snapshot-1
python3 -B scripts/ios27-sentence-diagnostic/run.py run --platform mac --unit snapshot-0
python3 -B scripts/ios27-sentence-diagnostic/run.py run --platform mac --unit snapshot-1
python3 -B scripts/ios27-sentence-controls/run.py build --device <physical-device-id>
python3 -B scripts/ios27-sentence-controls/run.py install
python3 -B scripts/ios27-sentence-controls/run.py run --platform phone --unit default-only
python3 -B scripts/ios27-sentence-controls/run.py run --platform phone --unit revision-first
python3 -B scripts/ios27-sentence-controls/run.py run --platform mac --unit default-only
python3 -B scripts/ios27-sentence-controls/run.py run --platform mac --unit revision-first
python3 -B scripts/ios27-sentence-diagnostic/run.py verify
python3 -B scripts/ios27-sentence-controls/run.py verify
```

All diagnostic work is saved. Each runner's `status` reports whether a phone request
remains unresolved. Do not rerun a reserved attempt after losing its console; use
`collect --unit <unit>` to recover its device checkpoint without another inference.
No diagnostic loop remains running; it is safe to disconnect or close the laptop.
