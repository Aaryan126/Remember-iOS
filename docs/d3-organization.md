# D3 thread organization — app integration

14 September 2026. The app's default organizer is now `D3ProjectOrganizer`, using
`d3-p2-seed29-corroborated-v1`. This integrates an existing trained candidate; it is
not another training run or a claim that the model passed production qualification.

## What runs

1. Capture immediately creates a separate thread. Existing extraction supplies text
   from notes, documents, OCR or speech; videos still contribute captions only.
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
blind spots. There is no new vision, scene understanding or video transcription.

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

No live API evaluation was performed. Premium cloud organization is discussed
separately in [the API assessment](premium-organization-api.md).
