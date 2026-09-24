# iOS 27: free-tier capability and evaluation assessment

Latest checkpoint: [Stage 2 reviewer screen complete — no-go](../Evaluation/iOS27/quality-continuation/REPORT.md).
The frozen comparison completed with 231 returned responses plus the one retained
transport-error outcome; no uncertain request was retried. Neither prompt nor any
D3 combination passes the safety gate. On the 80 context-rich challenge packets,
D3 recognizes 25/32 true same-project relationships, versus 10/32 for C7 and 12/32
for the boundary reviewer. The latter correctly separates 27/32 separate relationships
but falsely separates 15/32 true continuations and asserts decisions on 15/16 uncertain
cases. These exposed pair diagnostics are not whole-app accuracy. All 75 runner tests
pass; production remains unchanged and the phone is safe to disconnect. The next
useful step is an offline relation-contract/error review, not automatic integration
or another prompt/training sweep. Full qualification and historical FP16 numerical
compatibility are still separate open work.

Previous checkpoint: [Stage 2 phone controls and interrupted reviewer pilot](../Evaluation/iOS27/quality/REPORT.md).
All 56 fresh pair controls completed; FP16 and FP32 retain the same decisions on
this set. Eight reviewer requests completed (six structurally valid, two invalid
quotations), then the next launch lost the CoreDevice connection. No retry or
prompt change occurred. The screen is incomplete; no iOS 27 quality improvement
can yet be claimed. Evidence is saved and the probe is safely stopped for review.
The production organizer remains unchanged.

Previous checkpoint: [instrumented local-generation smoke passed](../Evaluation/iOS27/generation-trace/REPORT.md).
After explicitly waiting for active foreground state, the same fictional request
returned the correct code in 3.52 seconds of generation. The new isolated wrapper
records progress and has a separately tested independent deadline. This clears
the immediate generation-readiness blocker, not a grouping-quality gate; the old
timeout's cause remains unproven. The next step is the bounded Stage 2 reviewer
screen, with current D3 and the separate FP32 reference clearly identified. Neither
the production artifact nor the failed historical FP16 score gate was changed.

Previous checkpoint: [boundary checks and organizer safeguards passed; local generation blocked](../Evaluation/iOS27/CHECKPOINT-2026-09-16.md).
All 24 threshold-near decisions remain unchanged across both precisions on phone
and Mac, and 23 selected organizer/store/readiness-cache tests pass on the physical
phone. FP32 stays within the original neural tolerance for all 48 directions;
FP16 misses it three times. No quality uplift is claimed and production is unchanged.
The remaining Stage 1 blocker is a 120-second timeout on one tiny generation smoke
request despite Foundation Models reporting available. The isolated process was
safely stopped. Diagnose generation readiness before the Stage 2 reasoning screen.

Previous experiment: [FP16/FP32 comparison on the upgraded Mac and phone](../Evaluation/iOS27/precision/REPORT.md).
FP32 reproduces original PyTorch neural outputs within 0.000000283 on all 32
directions; existing FP16 reaches 0.002117813, exceeding the original 0.002 bound
once. Both retain 16/16 fixed and fresh-embedding decisions. FP32 requires ~133.6 MB
compiled model storage versus ~66.9 MB and median phone warm inference of 42.3 ms
versus 17.9 ms per direction. No quality gain is established. FP32 is an isolated
candidate, not the new production default, and its own conversion-reference parity
does not turn the failed historical FP16 score gate into a pass. Stage 1 remains
incomplete; review the candidate identity and remaining safeguards before Stage 2.

Previous implementation: [bounded readiness recovery verified](../Evaluation/iOS27/embedding-recovery-v2/REPORT.md).
The production provider now waits 200 ms asynchronously after an initial sentence-model
failure and retries once. Unlike the initial API-only controls, the real provider
needed a brief readiness wait; a tight immediate retry failed. All 16 phone and 16 Mac
embedding fixtures completed with matching spaces and unchanged reference-neural
decisions. Seven Swift regression tests passed. This fixes the observed availability
path, not the separate neural score-parity issue. Small contextual-vector differences
remain recorded. The main app was not reinstalled; full Stage 1 remains incomplete.

16 September follow-up: [physical iPhone compatibility results](../Evaluation/iOS27/phone-diagnostic/REPORT.md).
Foundation Models reports available with a 4,096-token context. All 16 D3 reference
decisions are unchanged, but numeric failures reproduce identically to the Mac.
The phone's English sentence embedding was unavailable, and the first production
embedding check failed. Investigate that availability blocker before a precision
conversion experiment. Stage 1 is still incomplete; no new grouping-quality score
or production behavior change is claimed.

Implementation follow-up: the toolchain upgrade is complete. The
[Stage 1 checkpoint](../Evaluation/iOS27/stage1/REPORT.md) records successful probe
builds and safety tests, but a small Mac numeric-parity failure, an unready Mac language
model and disconnected phone. Stage 1 is paused/incomplete; no grouping-quality uplift
has been measured. The subsequent [16-pair numeric diagnostic](../Evaluation/iOS27/parity-diagnostic/REPORT.md)
found unchanged decisions but 11 strict score failures and one neural-output
conversion-bound failure. It localizes the discrepancy to the neural inference
path without proving the runtime/compiler cause; compatibility remains unresolved.
The environment snapshot below describes the earlier assessment.

15 September 2026. Research and read-only device/toolchain inspection; **no new
model-quality benchmark, app installation, migration, paid call or training run**.
The local organizer and all historical results remain unchanged.

## Bottom line

iOS 27 gives us worthwhile new experiments, especially a renewed **on-device context
reviewer** and **visual understanding of images and sampled video frames**. An OS
upgrade is not evidence that either improves Remember. Keep D3 as the current local
default until a bounded comparison demonstrates better grouping without harmful
overrides. Separate free-to-use cloud services from strictly offline processing.

## What was verified on this setup

| Item | Observed result |
|---|---|
| Physical phone | iPhone 17, iOS 27.0, build 24A437 |
| Connection | Paired, wired, tunnel connected |
| Device testing readiness | Developer Mode enabled; developer disk services available; no passcode required at check |
| Active Xcode | 26.5, build 17F42 |
| Installed active iOS SDK | 26.5; no iOS 27 SDK shown |
| Mac OS | macOS 26.2, build 25C56 |
| Available Mac storage | Approximately 13 GiB at inspection |

Commands run: `xcodebuild -version`, `xcodebuild -showsdks`, `sw_vers`, `df -h .`,
`xcrun devicectl list devices`, and `devicectl device info details` / `lockState`
for the connected phone. Device identifiers and serial numbers are intentionally
omitted here. No personal vault contents were inspected.

Apple lists **macOS 26.6 or later** for Xcode 27. This Mac therefore needs an OS
upgrade as well as Xcode 27 to use that supported toolchain. With only ~13 GiB free
and our 10 GiB reserve, do not begin large downloads or delete caches automatically.
Recheck installer/unpacked sizes and available storage before an approved upgrade.
[Apple Xcode requirements](https://developer.apple.com/xcode/system-requirements).

The phone being visible does not prove that every test/debug workflow works with
the older Xcode. Existing iOS 26-compatible binaries can be candidates for runtime
smoke tests; compiling the new APIs needs the newer SDK. Apple Intelligence model
availability/download state, actual context capacity and embedding revisions have
**not** been measured on this phone in this assessment.

## Current best integrated local system

The selected engineering build uses `d3-p2-seed29-corroborated-v1`:

1. Extract source text locally from notes/documents, image OCR, voice and video speech
   or sampled-frame evidence. Preserve originals and source revisions.
2. Retrieve candidates through Apple embeddings plus lexical search.
3. Score pairs with the trained English MiniLM matcher plus the frozen feature
   classifier. This is a neural/embedding hybrid, not embeddings alone.
4. Require corroboration from two of the first three retrieved members of an
   established thread, or one for a singleton. Attach only if exactly one qualifies.
5. Keep uncertain captures separate, protect existing/manual placements, and append
   evidence to the provenance ledger. Never automatically merge existing threads.

The whole organization decision stays local. Separate optional cloud enrichment,
Ask and AI search already exist; “local organization” is not a claim that every
feature of the app is offline. Foundation Models may generate capture metadata,
but the rejected C7 local verifier is **not** in the D3 placement path.

### Quantitative position before a new iOS 27 benchmark

| Historical measurement | Simple baseline | Selected D3 seed 29 |
|---|---:|---:|
| P2 precision of accepted known-label pairs | 95.94% | 95.79% |
| P2 library-macro recall | 43.84% | 58.39% |
| C3 final grouping pair precision, same corroboration rule | 69.4% | 75.2% |
| C3 final grouping pair recall, same corroboration rule | 24.5% | 34.5% |
| C3 incorrect attachment actions / 360 eligible captures | 55 | 54 |
| C3 missed attachment actions / 279 eligible continuation captures | 224 | 202 |

P2 evaluated 240 fictional sources and 2,280 pairs (1,875 known-label pairs) from
12 held-out evaluation libraries. Its precision excludes uncertain pairs, and its
recall is averaged by library. C3 used 12 fictional stories across 36 chronological/
shuffled streams; final grouping metrics include scripted corrections/restores.
Actions and final co-membership pairs are different units, so do not blend their
percentages. Sources/templates are correlated, not independent user trials.

Sources: [P2 report](../Evaluation/MatcherValidation/P2_REPORT.md),
[C3 report](../Evaluation/OrganizationDiagnostics/c3/REPORT.md).

The gain is principally **more genuine connections recovered**: +14.55 percentage
points in P2 macro recall and +10.0 points in C3 final grouping recall. It is not a
dramatic reduction in wrong online attachments: C3's count improved by only one.
The all-three-seeds P2 qualification **failed**. Seed 29 was selected for an explicitly
approved experimental integration; it is not a statistically established universal
winner, and other seeds lead individual diagnostic metrics.

### What users should expect

Useful automatic organization of supported English captures, offline after required
assets are available, with more genuine connections than the simple classifier.
The tradeoff is conservative, fragmented threads and remaining boundary mistakes:
similar topics need not be one project, and a shared planning note can relate to two
projects without making those projects identical. Previously incorrect groups do not
repair themselves when the app or OS is upgraded. Manual correction still matters.

The matcher package is **66,878,102 bytes** (~66.9 MB / 63.8 MiB). The earlier signed
debug bundle occupied ~90.7 MiB on the Mac; that is not an App Store download or the
phone's total storage use. Sixteen port-parity pairs agreed in their final decisions.
Integrated phone cold/warm latency, peak memory, thermal behavior and large-library
quality remain unmeasured. Do not substitute the old Mac local-LLM timings for D3
phone latency. [Integration evidence](../Evaluation/AppMatcher/VERIFICATION.md).

## What iOS 27 changes, and what it does not

### 1. Re-evaluate the on-device language model — highest quality priority

Apple reports a new `SystemLanguageModel` with improved instruction following and
explicitly calls for retesting prompts after the OS update. Our earlier C7 verifier
ran on **macOS 26.2**, not iOS 26 on this phone. Apple also changed the model in 26.4,
so those old results are not representative of every 26.x release.
[Foundation Models updates](https://developer.apple.com/documentation/updates/foundationmodels).

C7's context reviewer had 49.2% same-project precision, 90.6% recall, 18 wrong matches
on 32 separate cases, unsupported decisions on 15/16 uncertain cases, and 6/80 errors.
It failed four of five exploration checks. This is the behavior to retest, not a
reason to silently re-enable it. [C7 report](../Evaluation/OrganizationDiagnostics/c7/REPORT.md).

First compare the unchanged source-only prompt/schema and exposed diagnostic on
iOS 27. Then test fresh families if it improves. Preserve D3 as a control and score
harmful overrides, abstention and quotation validity separately. A Mac-26.2 versus
iPhone-27 comparison is **cross-OS and cross-hardware**, not a controlled iPhone
upgrade experiment. A matched iPhone still on 26.x would be needed for that; do not
downgrade this phone or overwrite its library to manufacture a control.

Potential: a local reviewer may understand explicit project boundaries and unresolved
references better than D3 pairs. **No percentage improvement is established yet.**
Bundled MiniLM weights, threshold and corroboration logic do not change with the OS.

### 2. Native image understanding — highest media opportunity

Foundation Models now accepts image attachments and can return structured visual
descriptions. This is a new avenue beyond OCR and broad scene labels: try screenshots,
diagrams, photographed objects and sampled video frames with little readable text.
[Apple multimodal prompting](https://developer.apple.com/documentation/foundationmodels/analyzing-images-with-multimodal-prompting).

Test whether added visual evidence improves retrieval and grouping, not merely whether
captions sound good. Keep observations distinct from model guesses; never turn a
guessed client/project name into authoritative provenance. Keep originals, frame
timestamps and uncertainty. Image support does not establish full video-temporal
understanding or a new audio-transcription capability. Existing speech/frame extraction
already works on iOS 26; it is not all newly unlocked by iOS 27.

### 3. Core AI — performance experiment, not automatic accuracy improvement

Apple's iOS 27 Core AI framework offers custom neural-model deployment, specialization,
and CPU/GPU/Neural Engine execution with new conversion/debugging tools.
[Core AI](https://developer.apple.com/documentation/coreai).

D3 currently uses the conversion-verified **Core ML CPU-only** path. First measure
existing Core ML compute-unit alternatives with the same weights and parity fixtures;
GPU/Neural Engine options are not new to iOS 27. Only then consider a separate Core AI
export if the profiler justifies it. Faster inference or lower memory is plausible,
but no speedup or accuracy gain is measured. Recheck probabilities and decisions near
the frozen threshold before changing the production compute path.

### 4. Local retrieval and evaluation tooling — secondary priorities

The new `SpotlightSearchTool` lets a model search an app's donated Core Spotlight
content. It is an alternative retrieval experiment, not proof that Apple's search
understands our project identities. Remember's current candidate retrieval does not
use this tool. Indexing and full-item recovery need explicit design, with archive,
revision and visibility behavior preserved. Measure candidate recall separately
from final grouping. [Apple's Spotlight session](https://developer.apple.com/videos/play/wwdc2026/246/).

The Evaluations framework provides native metrics/reporting for probabilistic features.
It can wrap our frozen cases; it does not replace independent labels, held-out families
or deterministic evidence validation. Keep the existing pause/resume harness and
checksummed results. [Apple Evaluations](https://developer.apple.com/videos/play/wwdc2026/298/).

Context-size/token-count APIs already arrived in 26.4; do not credit them as entirely
new 27 capabilities. Query runtime capacity rather than assuming a universal 8K or
32K on-device window: Apple's current overview gives a 4K local comparison, while
session sample code mentions 8K on newer 27 devices. **32K refers to PCC**, not a
guaranteed offline context upgrade for this iPhone.
[Apple's model/context comparison](https://developer.apple.com/videos/play/wwdc2026/319/).

### 5. Private Cloud Compute — potentially free to us, not offline

Apple offers eligible Small Business Program developers PCC access at no cloud API
cost, subject to download limits and a managed entitlement. Eligibility is account-wide
and must be verified, not inferred from having a developer certificate. Apple describes
App Store use and testing through TestFlight/ad hoc distribution. Losing eligibility
requires an alternative within six months. No entitlement request was submitted here.
[Apple PCC access rules](https://developer.apple.com/private-cloud-compute/).

PCC offers a larger context and reasoning levels, but requires connectivity and has
daily user quotas, with higher access through iCloud+. It could eventually be offered
to free users as an **optional cloud enhancement**, if we qualify and it passes our
tests. That is a separate product/privacy decision from the strictly on-device tier,
and a user's iCloud+ subscription is not Remember Pro.
[Apple PCC integration and quota handling](https://developer.apple.com/documentation/foundationmodels/adding-server-side-intelligence-with-private-cloud-compute).

The verified GPT pilot remains the evidence for the proposed
[Remember Pro experience](premium-organization-api.md). Neither Apple's marketing
nor GPT's pilot establishes PCC quality on our task.

## Recommended next experiment and checkpoints

Do not begin another training sweep. First establish whether the OS-provided model
can now solve the context task our current model struggles with.

| Checkpoint | Work | Hardware / rough active time after prerequisites |
|---|---|---|
| A. Compatibility | Separate fictional-data probe: Apple Intelligence availability, context capacity, embedding identities/vectors, bundled D3 parity, capture preservation | Mac + phone; 1–2 hours |
| B. Text screen | Frozen C7-style 112-input rerun, D3 controls, fixed/damaged decisions, ambiguous/bridge slices; checkpoint each response | Mac + phone; 2–4 hours including harness adaptation and analysis |
| C. Fresh validation, only if B earns it | New held-out families and small chronological River replay with the same candidate retrieval | Mac + phone; scope separately, approximately 1–2 working days |
| D. Optional media/performance probes | Image/frame evidence ablation; CPU versus permitted accelerated paths, parity and latency/memory | Mac + phone; approximately 0.5–1 day per bounded probe |

Times are planning estimates, not measured run durations or promises. Toolchain/OS
installation and model downloads are excluded. Stop for review after A and B; no
automatic escalation to C/D. All probes use separate temporary stores/bundle identities,
fictional data, no cloud fallback, resumable outputs, and a 10 GiB Mac free-space floor.

An embedding revision/dimension/identifier mismatch is an important **stop condition**:
D3 intentionally defers rather than reuse a calibrated classifier in a different vector
space. Even matching identifiers require numeric/decision checks. Do not remove the
guard or silently refit thresholds. Repair compatibility as a separately recorded
experiment if needed. Other stop conditions include unavailable model assets, unsafe
output rate, and harmful overrides that erase gains.

No experiment above has run in this assessment. There is no new iOS 27 uplift score.
The next prerequisite is user-managed storage/macOS/Xcode preparation, followed by
the isolated compatibility checkpoint—not a change to automatic organization.
