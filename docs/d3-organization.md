# D3 thread organization — app integration

14 September 2026. The app's default organizer is now `D3ProjectOrganizer`, using
`d3-p2-seed29-corroborated-v1`. This integrates an existing trained candidate; it is
not another training run or a claim that the model passed production qualification.

## What runs

1. Capture immediately creates a separate thread. Existing extraction supplies text
   from notes, documents, OCR or speech; videos now contribute captions, on-device
   speech and bounded sampled-frame evidence through [video indexing](video-indexing.md).
2. Apple contextual embeddings and a frozen word/bigram TF-IDF index each retrieve
   five candidate memories. Reciprocal-rank fusion combines them into at most ten.
3. The trained MiniLM pair matcher scores each retrieved pair in both directions.
   A frozen logistic classifier combines the averaged neural score with ten existing
   features: contextual/sentence similarities, lexical overlap, numbers, identifiers
   and text-length signals. It is **not embeddings alone or a generative reasoner**.
4. Use the frozen threshold `0.9804276486193665`. Among the first three retrieved
   members of a thread, require two positive matches, or one for a singleton.
5. Attach only if exactly one thread qualifies. Otherwise retain the capture's
   separate thread. Record the model version, source revision, scores, rationale,
   prior/new memberships and supporting source-event references in the ledger.

All five steps run on-device. There is no D3 cloud fallback, no C7 verifier, no
automatic merge of existing threads and no newly generated batch split proposals.
Historical merge/split events and their existing review/undo controls still work.
Ambiguity appears in Activity & decisions; this integration does not add a new
multi-thread suggestion/acceptance screen.

## Existing libraries and safeguards

- The [completed Stage 2 iOS 27 grouping screen](../Evaluation/iOS27/quality-continuation/REPORT.md)
  retains identical FP16/FP32 decisions on 56 fresh pair controls, but neither
  generative reviewer nor any tested D3/reviewer policy passes the safety gate.
  In the context-rich challenge view, the boundary reviewer recognizes 12/32 true
  continuations versus D3's 25/32, falsely separates 15/32, and makes unsupported
  decisions on 15/16 uncertain cases. Do not add an automatic local-reviewer veto
  or split path based on this experiment. The exposed pair controls do not exercise
  the full organizer policy and are not representative whole-app accuracy.
- The [iOS 27 device checkpoint](../Evaluation/iOS27/CHECKPOINT-2026-09-16.md) executed
  23 selected tests against copied current sources and isolated real SQLite stores:
  organizer protections, readiness-cache behavior, append-only triggers and exact
  threshold semantics passed. This is not the full app suite or a new quality score.
  The separate local-generation smoke request initially timed out; a later
  [instrumented foreground check](../Evaluation/iOS27/generation-trace/REPORT.md)
  completed correctly in 3.52 seconds of generation. This establishes narrow
  evaluation readiness, not reasoning quality. No generative reviewer has been
  added to the production placement path.
- Sentence-model initialization retries once after a cancellation-aware 200 ms
  asynchronous wait, only if the first lookup fails. Successful models stay cached
  per language inside the embedding actor; persistent failure still defers matching.
  This addresses the observed iOS 27 readiness race without changing embedding
  spaces or D3 thresholds. See the [device recovery checkpoint](../Evaluation/iOS27/embedding-recovery-v2/REPORT.md)
  for tests, vector drift and outstanding numerical compatibility limitations.
- Existing placement events are not migrated, rescored or rewritten. Correcting a
  previous grouping remains a manual action; installing this does not fix old groups.
- Captures without a placement are processed in stable creation-time/ID order.
  Previously placed memories and earlier captures supply the candidate context;
  batch imports do not look ahead into still-unprocessed later captures.
- Explicit assignments, thread renames, archived/retired threads and blocked pairs
  are respected. Revising an already-placed memory does not reassign it; later matches
  use its current text. Cached embeddings are keyed by exact text and bounded to 512
  memories. They are an in-memory optimization, not a second persisted source of truth.
- Every placement has a sequence precondition. Concurrent edits invalidate the
  decision rather than committing evidence from an older snapshot.
- Cancellation preserves completed events and cannot commit a partial placement.
  Unavailable matching retains the thread and records a retryable failure; explicit
  retry/foreground refresh can retry it. Ordinary retries have a 60-second cooldown.
- No database migration, event-schema replacement or deletion of originals is needed.

## Scope and limitations

The [iOS 27 precision diagnostic](../Evaluation/iOS27/precision/REPORT.md) found
that an experimental FP32 conversion reproduces the original neural outputs more
closely than the current FP16 export, at approximately double model storage and
2.36× measured phone warm inference time. Sixteen reference decisions stayed
unchanged with either precision. This is not a quality benchmark or a production
replacement: this app still uses the existing FP16 artifact and frozen threshold.
Historical numerical compatibility remains an explicit open qualification item.

The matcher currently accepts automatically detected English text up to 16,000
Unicode scalars. Both Apple embedding vectors must be available and share the same
English model space recorded by P2 (`D3OrganizationPolicy.embeddingSpace`, two
512-dimensional revision-1 vectors). A future Apple asset revision defers matching
until separately checked, rather than silently changing calibrated feature values.
Empty extraction falls back to a nonempty caption or title;
that fallback is weaker evidence than a complete original. Unsupported text stays
separate. Language detection can reject short English notes. Supporting additional
languages requires evaluation, not simply removing this check.

MiniLM's fixed 512-token **pair** limit uses the frozen longest-first truncation.
Full-text lexical/embedding evidence does not eliminate the neural model's long-text
blind spots. D3 itself remains text-only. The separate [video extraction pipeline](video-indexing.md) now supplies speech and sampled-frame text/possible visual labels as source evidence; this does not change the matcher, its 16,000-scalar bound, or existing placement-preservation rules.

Inference starts on Core ML's CPU-only path, which is the conversion-verified path.
Up to twenty forward passes may be required per capture. Apple embedding extraction
and retrieval still scan eligible memories on a cold session. Large-library latency,
thermal behavior and this integrated build's phone memory peak remain to be measured;
earlier standalone feasibility timings are not end-to-end app measurements.

The Core ML package is **66,878,102 bytes** (66.9 MB / 63.8 MiB), plus vocabulary and
feature parameters. Compiled model size, total installed app size and runtime memory
are different measurements. Xcode includes `MatcherAssets` through the project's
existing synchronized file group. No Python runtime is included in the app.

## What the earlier results do—and do not—establish

| Historical evaluation | Control | Selected engineering candidate |
|---|---:|---:|
| P2 pair precision | 95.94% | 95.79% |
| P2 library-macro recall | 43.84% | 58.39% |
| C3 final grouping pair precision, same corroboration policy | 69.4% | 75.2% |
| C3 final grouping pair recall, same corroboration policy | 24.5% | 34.5% |
| C3 false attachment actions / 360 captures | 55 | 54 |

P2's baseline is a trained feature classifier, not raw cosine similarity. Its
evaluation comprised 240 fictional sources and 2,280 pairs (1,875 known-label pairs).
C3 tested chronological organization with different arrival orders and corrections.
These are different tasks: pair accuracy does not directly predict a clean River.

Seed 29 passed its individual P2 gate, but the **three-seed family failed**. Selecting
it for this user-approved experimental build does not repair that failed qualification
or establish that it is statistically the best seed. Boundary/context errors remain.
See [P2](../Evaluation/MatcherValidation/P2_REPORT.md),
[C3](../Evaluation/OrganizationDiagnostics/c3/REPORT.md) and
[C7](../Evaluation/OrganizationDiagnostics/c7/REPORT.md). Historical reports are unchanged.

## Reproducibility and validation

Assets derive from `microsoft/MiniLM-L12-H384-uncased`, revision
`44acabbec0ef496f6dbc93adadea57f376b7c0ec`, fine-tuned using the existing P2 seed-29
checkpoint. The checkpoint SHA-256 is
`f49d37c60f0b4336578df2475d12061d64c42acef4ba5b1f2f2a6147c5f7074b`.
The original frozen asset manifest and checkpoint remain the authority; no weights
were downloaded or fitted for this integration. Redistribution attribution is bundled
in `MatcherAssets/D3ModelNotice.txt`.

`scripts/app-matcher/export_d3.py` exports the existing local checkpoint, fixed
parameters and 16 saved-reference pairs. It refuses changed input receipts and keeps
the original export. Run it with the already prepared matcher-feasibility Python
environment; do not install Python dependencies into the app.

Saved evidence: [conversion](../Evaluation/AppMatcher/conversion.json),
[native parity](../Evaluation/AppMatcher/native-parity.json),
[verification log](../Evaluation/AppMatcher/VERIFICATION.md).

- Original PyTorch → FP16 Core ML: all 16 final decisions agree across 32 directional
  inferences; maximum neural-probability difference `0.0012633204460144043`.
- Native Swift → saved Python/Core ML: exact token parity; maximum feature difference
  `2.04e-9`, maximum combined-score difference `5.34e-10`; all decisions agree.
- These parity cases verify a port, **not fresh held-out quality**.

Run native parity from the repository root:

```sh
swiftc -parse-as-library Remember/Remember/D3Tokenizer.swift \
  Remember/Remember/D3Features.swift Remember/Remember/D3PairMatcher.swift \
  Remember/Remember/D3OrganizationPolicy.swift \
  scripts/app-matcher/D3ParityProbe.swift -o /tmp/RememberD3ParityProbe
/tmp/RememberD3ParityProbe Remember/Remember/MatcherAssets Evaluation/AppMatcher/parity-inputs.json
```

Run the app tests using an available simulator identifier:

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild \
  -project Remember/Remember.xcodeproj -scheme Remember -configuration Debug \
  -destination 'platform=iOS Simulator,id=<simulator-id>' \
  -derivedDataPath /tmp/RememberD3Integration CODE_SIGNING_ALLOWED=NO \
  -parallel-testing-enabled NO -only-testing:RememberTests/D3OrganizationTests test
```

No live API evaluation was part of this local integration. The subsequent isolated
GPT-5.4 pilot is recorded in [Remember Pro's API assessment](premium-organization-api.md);
it does not change this free-tier organizer. Pro cloud organization is not enabled.

The [15 September iOS 27 assessment](ios27-free-tier-assessment.md) records the
connected phone/toolchain checks, current local quality, and proposed experiments.
Upgrading the OS does not retrain the bundled MiniLM model or enable the rejected
local generative verifier. Check Apple embedding-space compatibility before assuming
unchanged calibrated behavior after an OS upgrade.
