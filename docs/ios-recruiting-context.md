# Remember — iOS project context for résumé and interview preparation

Prepared from repository source and recorded engineering reports on 16 September 2026.

## Instructions for the agent using this handoff

Help Aaryan Kandiah describe this project for an iOS graduate engineering application. The recruiter contacted him about TikTok's Singapore iOS/Android Engineer Graduate (Global Payment), 2027 start. Prioritize concrete native iOS implementation, reliability, persistence, concurrency, testing, and performance-aware design.

These are repository capabilities, not independent proof of Aaryan's individual contribution. Confirm his ownership, collaboration, project dates, and which parts he can explain before attributing every implementation or research result to him. Do not invent users, App Store publication, revenue, production deployment, payments experience, or performance improvements. The linked job description could not be retrieved during this review, so no detailed job requirements beyond the supplied recruiter message were verified.

The workspace is named “Gemini Hackathon,” but the current native app is **Remember**, with Apple on-device processing and optional OpenAI cloud features. Do not describe the current implementation as using Gemini merely because of the directory name.

## 1. Product and scope

Remember is a native iPhone personal memory vault. It preserves notes, photos/screenshots, videos, links, PDFs, and voice recordings, extracts searchable evidence, and connects related memories into “Threads.” Users can rediscover saved material, inspect its original source, and follow changes over time.

Current status: actively developed iOS prototype. The repository documents signed builds and installation on a physical iPhone 17, simulator testing, and physical-device testing. This is not evidence of an App Store release or a production user base. Automatic organization is experimental; paid/Pro organization is a research direction.

Implemented user-facing capabilities:

- **Capture:** typed notes, camera photos, Photos imports, Files imports, saved links, PDFs, videos, and voice recording. A radial capture dial exposes capture actions.
- **Share Extension:** receive supported content from other apps through the iOS share sheet and stage it for the main app.
- **Library:** local originals, image/video previews, native media playback, editable metadata and notes, tags, collections, and filters by content type, date, and tag.
- **Search:** local text search; explicit optional AI search adds query expansion and hosted semantic retrieval.
- **Threads:** an interactive circular map, local search across all active threads, a press-and-hold preview, and direct navigation into thread history.
- **History:** a continuous timeline with inline original media, content revisions, source evidence, organization decisions, historical snapshots, manual assignment, rename, and recoverable archive/restore.
- **AI Help / Ask Remember:** questions about saved material with retrieved evidence, validated source quotes, inspectable citations, and source-only fallback when an answer cannot be grounded.
- **Privacy and settings:** cloud capture assistance preference, local AI activity information, appearance controls, and model availability/retry states.

## 2. Native iOS stack and framework usage

| Technology | Concrete use in this project |
| --- | --- |
| Swift | App, extension, data layer, media processing, organization, model inference, and tests. |
| SwiftUI | Main interface, navigation, library, capture sheets, Threads map/history, assistant, settings, and native zoom navigation transitions. |
| Observation | `@Observable` view models and playback/recording state. |
| Swift concurrency | `async/await`, actors, `@MainActor`, `Sendable`, tasks, cancellation, and asynchronous database observations. |
| UIKit interoperability | `UIViewControllerRepresentable` and coordinator for `UIImagePickerController`; dynamic colors; UIKit-based Share Extension. |
| PhotosUI | System Photos selection for images and videos. |
| CoreTransferable | File-based video transfer from Photos using `Transferable` / `FileRepresentation`. |
| UniformTypeIdentifiers | Identify and validate images, movies, PDFs, links, and text/document formats. |
| Social / extension APIs | `SLComposeServiceViewController`, `NSExtensionItem`, and `NSItemProvider` for shared content. |
| App Groups | Shared file inbox between the app and its separately running extension. |
| GRDB.swift / SQLite | Persistent memories, search metadata, chunks, collections, activity, and provenance; migrations, foreign keys, observations, and database writes. |
| Vision | On-device OCR and image classification; OCR/classification over sampled video frames. |
| PDFKit | PDF text extraction. |
| Speech | On-device `SpeechAnalyzer` / `SpeechTranscriber`, model availability checks, explicit model download, and transcription. |
| AVFAudio | Microphone recording, audio session lifecycle, audio files, and playback. |
| AVFoundation / AVKit | Video validation, audio export, frame/poster extraction, and native video playback. |
| NaturalLanguage | Language detection, entity/linguistic tagging, sentence embeddings, and contextual embeddings. |
| FoundationModels | Available-device local metadata generation through `LanguageModelSession` and typed `@Generable` output. |
| Core ML | Bundled trained MiniLM pair matcher executed natively through `MLModel` and `MLMultiArray`. |
| ImageIO | Orientation-aware image downsampling to bound display decoding size. |
| QuartzCore | `CADisplayLink` for custom interaction motion. |
| QuickLook | Native source/document preview. |
| URLSession / Codable | Asynchronous HTTP, JSON decoding, structured model responses, and error handling. |
| Swift Testing / XCTest | Unit suites and UI automation, including simulator and physical-device checks. |

The Xcode project contains app, Share Extension, unit-test, and UI-test targets. It currently configures an **iOS 26.5 deployment target**, **Swift language version 5.0**, and **MainActor default isolation for the app**. Modern compiler APIs do not make “Swift 6 language mode” an accurate claim. GRDB is resolved through Swift Package Manager at **7.11.1**. The target device family includes iPhone and iPad, but the documented product/visual validation is iPhone-focused; do not claim comprehensive iPad optimization.

## 3. Architecture and concurrency

The architecture separates SwiftUI presentation, observable view models, processing services, persistence, and source files. “MVVM-style with actor-isolated services” is a reasonable description; do not invent use of a particular architecture framework.

Main components:

- `LibraryViewModel`: main-actor observable state for the library, search, assistant, filters, collections, capture, and processing progress.
- `ProjectViewModel`: main-actor observable state for Threads; consumes provenance observations, reconstructs snapshots, and schedules organization.
- `MemoryPipeline`: actor orchestrating import, extraction, analysis, indexing, retries, edits, and activity logging.
- `MemoryStore`: actor wrapping GRDB's `DatabasePool`; live consumers share a pool so database observations remain consistent.
- `CaptureImporter`: actor consuming the shared inbox and inserting captures idempotently.
- `MemorySearchService`: actor managing searchable records/chunks and local or optional semantic retrieval.
- `D3ProjectOrganizer` / `D3PairMatcher`: local organization and native model inference.
- `LibraryFileStore`: source-file vault, separate from SQLite metadata.

Engineering details worth discussing:

- Protocol-based injection makes capture, transcription, analysis, and matching replaceable for tests.
- Asynchronous work checks cancellation; processing can return an interrupted capture to a retryable state.
- Startup recovers interrupted processing/activity records, imports pending captures, and synchronizes indexes.
- Search is debounced in the UI; results are applied only if the request still matches the current filters/query, preventing stale responses from replacing current results.
- Organization work is coalesced rather than starting a separate competing task for every database observation.
- Sequence preconditions reject organization decisions computed before a concurrent edit changed the underlying state.
- Completed provenance events survive cancellation; interrupted work must not create a partial placement.
- This is foreground/opportunistic processing. Do not claim guaranteed background processing or a nightly `BGTaskScheduler` pipeline.

## 4. Cross-app capture, persistence, and data integrity

The Share Extension reads typed attachments using `NSItemProvider`, writes the selected payload and a versioned metadata record into an App Group inbox, and completes the extension request. The main app later imports it into its file vault and SQLite database. Expensive model processing is kept out of the extension.

The storage design includes:

- UUID identity and idempotent import so processing the same queued capture again does not create a duplicate memory.
- Staging/atomic file publication and ignoring incomplete inbox entries.
- Original media files stored separately from derived titles, summaries, tags, chunks, vectors, and activity metadata.
- SQLite migrations, foreign keys, indexes, collection-membership relations, and provider/model metadata for search records.
- File protection using `completeUntilFirstUserAuthentication`, including protected temporary media copies.
- Extension/filename normalization and scoped file operations.
- Security-scoped access for Files imports while validation/copy is in progress.
- Independent temporary Photos video copies because a Photos-owned URL may expire after transfer.
- Cleanup of newly created temporary files on cancellation/failure without deleting the user's original Photos asset.
- Recoverable archive/restore and preservation of originals referenced by historical revisions.

Describe this as protected local storage and careful file lifecycle management. Do not call it an encrypted database, end-to-end encryption, or a bank-grade security implementation.

## 5. Append-only history and provenance

The provenance system is one of the strongest general software-engineering features:

- Captures, revisions, enrichment, placements, corrections, and other supported organization actions are recorded as events.
- SQLite triggers reject updates/deletions to provenance rows, enforcing append-only history.
- Read projections replay events to derive current and historical thread state.
- Source evidence references a specific source revision/event, rather than only the latest mutable memory record.
- Placement writes check the expected event sequence to reject stale asynchronous decisions.
- Manual assignments, renames, archived threads, and blocked relationships are protected from automatic organization.
- Historical state can be explored without rewriting current state.
- Existing merge/split history and associated review/undo controls remain supported, although the current D3 organizer does not automatically merge threads or generate new batch split proposals.

This demonstrates event-based modeling, auditability, optimistic concurrency checks, and recovery semantics. It is relevant to correctness-sensitive applications, but it is not a payment transaction ledger.

## 6. Local extraction and media engineering

Images use Vision OCR and classification; PDFs use PDFKit text extraction; notes and links preserve source text/URLs. Saving a link does not establish a general web crawler or complete article extraction feature. Voice recordings use native audio capture and Apple's on-device transcription.

Where available, Foundation Models generates typed title/summary/tag metadata from bounded source content. Unsupported/unavailable generation retains deterministic source-derived metadata and local entity extraction. Source evidence remains distinct from generated metadata.

Video implementation details:

- Validate playable local videos and preserve original bytes.
- Export audio into a protected temporary M4A and transcribe up to the first **30 minutes**, retaining up to **50,000 characters**.
- Sample up to **12** evenly spaced interior frames, with orientation-correct extraction bounded to **1,280 pixels**.
- Run OCR and image classification independently so failure of one does not discard the other's evidence.
- Deduplicate repeated frame text; retain timestamps and explicitly probabilistic scene labels.
- Store captions, speech, frame text, and scene labels as distinct evidence chunks with citation locators.
- Explain partial coverage and support reindexing/model-download retry.
- Preserve caption/frame evidence when speech is unavailable or fails.
- Remove temporary audio on success, error, and cancellation.
- Keep video capture extraction local even when cloud capture assistance is enabled.

Media rendering and interaction:

- Native AVKit video player in details and thread history; user-initiated playback and pause on departure/backgrounding.
- Video poster selection tries multiple frame locations; failed posters do not block playback.
- Posters are bounded to **1,200 pixels**, with an in-memory cache capped at **24 MB / 32 images**.
- `LocalImageView` downsamples images through ImageIO, using a default maximum dimension of **1,200 pixels** and utility-priority detached work.
- Native audio session setup/teardown handles recording and playback lifecycle.

These are concrete resource bounds, not benchmark evidence of a particular speedup, frame rate, battery improvement, or memory reduction.

## 7. On-device search and experimental Core ML organization

Local search supports text matching, filters, persistent search records, and source chunks. Explicit AI search can use hosted embeddings/query expansion. Local thread matching uses a separate Apple-embedding/model path and does not call the cloud proxy.

The currently active organizer is **D3**, not the older `ProjectGraphService` implementation:

1. New captures initially receive a separate thread.
2. Apple contextual embeddings retrieve five candidate memories; a frozen word/bigram TF-IDF index retrieves another five.
3. Reciprocal-rank fusion produces at most ten candidates.
4. A fine-tuned MiniLM pair model scores candidate pairs in both orders.
5. A frozen logistic classifier combines the averaged neural score with ten lexical/embedding/numeric/identifier/length features.
6. An established thread needs two positive matches among its first three retrieved members; a singleton needs one. Attach only when exactly one thread qualifies.
7. Record versioned, source-bound evidence and the membership decision in provenance. Keep ambiguous captures separate.

Native ML integration:

- Base model: `microsoft/MiniLM-L12-H384-uncased`; the bundled experimental checkpoint is P2 seed 29.
- Converted PyTorch model to an FP16 Core ML package, with native Swift tokenizer, feature extraction, and scoring.
- Model inputs use fixed **512-token pair** sequences. Apple sentence/contextual representations are each **512-dimensional**.
- Input eligibility currently requires detected English and at most **16,000 Unicode scalars**.
- Native inference explicitly uses **CPU-only** Core ML for the verified execution path; do not claim Neural Engine or GPU acceleration.
- Up to twenty directional model forward passes per capture; exact-text embedding cache bounded to 512 memories.
- Model/embedding identities and dimensions are validated. Incompatible/unavailable models defer matching and preserve the capture.
- Bundled model package: **66,878,102 bytes**, approximately 66.9 MB / 63.8 MiB. Python is used for research/export tooling, not embedded in the iOS app.

Qualification caveat: the selected candidate was integrated experimentally. The three-seed P2 family failed its qualification gate, and grouping/context errors remain. Do not call the organizer production-qualified or turn pair-level evaluation into an “overall app accuracy” claim.

## 8. Optional cloud integration and grounded answers

The Swift client uses asynchronous `URLSession` calls to a small Python development proxy. The proxy holds the API key in its environment rather than placing it in the app. Current source defaults name `gpt-5.5` and `text-embedding-3-small`; these are configuration facts from the code, not independent verification of live service access.

Implementation includes JSON-schema structured output, `Codable` response decoding, a 90-second request timeout, HTTP status handling, cancellation handling, bounded inputs, and mappings for rate limiting, unavailable service, decoding errors, refusal, and context-window errors.

The answer flow retrieves bounded chunks, labels evidence, requests exact quotations, verifies returned labels and quote presence against source text, and displays source citations. It can use an extractive fallback or return source-only results. Context overflow retries with a smaller evidence budget. Source text is treated as untrusted data in prompting; quote checks do not prove that every interpretation is correct or establish complete prompt-injection prevention.

Privacy behavior:

- Cloud capture enrichment is off by default.
- Ask and AI search are independent explicit cloud actions; disabling capture assistance does not disable them.
- Video capture extraction and D3 organization remain local.
- The Share Extension makes no OpenAI calls.
- Responses requests use `store: false`.
- Selected text, excerpts, and operation-dependent images can leave the device during cloud actions. Do not claim the entire app is always offline or that no content ever leaves the phone.
- The proxy is development infrastructure. Production client authentication, rate limits, abuse controls, and paid entitlements are not established by this implementation.

## 9. Custom SwiftUI interface, motion, and accessibility

The Threads map uses a rigid hexagonal layout, pan translation, and position-based circle scaling. A size-only lens magnifies circles near the viewport center while preserving the underlying lattice. A short tap opens history; holding opens a preview. Search covers the entire active library even though the map displays at most forty circles.

The map's motion controller maintains one presentation offset through dragging and settling. `CADisplayLink` advances a deterministic smoothstep snap over approximately **0.32 seconds**. A new drag interrupts settling from the visible position. The display link requests up to **120 Hz only while settling**; iOS determines actual cadence. This does not substantiate a measured “120 FPS” claim.

Other concrete UI work:

- Custom radial capture dial and drag/momentum handling.
- Native zoom transitions and centralized typed thread navigation.
- Repeated-open/back/rapid-tap navigation regression coverage.
- Reusable appearance roles and adaptive UIKit semantic colors.
- Light/Dark Mode and Increased Contrast variants.
- Dynamic Type, including accessibility sizes and a complete list alternative to map browsing.
- VoiceOver labels and explicit preview/highlight actions.
- Reduce Motion adaptations and Reduce Transparency opaque alternatives.
- Native selection haptics when focus changes.
- Thread history implemented with native List reuse, inline media, a continuous rail, and baseline-aligned event markers.

## 10. Testing, validation, and defensible numbers

The following are **historically recorded results**, not tests rerun for this handoff. Different rows represent different snapshots; do not add them together into a unique test total.

| Recorded check | Result | What it establishes |
| --- | --- | --- |
| D3 integration suite, 14 September | 128 unit tests passed; 250 runs including parameterized cases; 13 new D3 tests | Functional coverage for that integration snapshot. |
| Subsequent video/search regression | 135 simulator unit tests and 3 UI checks passed | Coverage for that later source snapshot. |
| Physical iPhone video validation | 12 video unit tests, real Speech transcription test, and thread navigation UI check passed | Real-device execution for the recorded selections. |
| PyTorch → Core ML parity | 16/16 final pair decisions agree across 32 directional inferences; max neural probability delta ≈0.00126332 | Consistency of model conversion on those cases. |
| Native Swift parity | Exact tokenizer parity; all 16 decisions agree; max feature delta ≈2.04e-9 and combined-score delta ≈5.34e-10 | Consistency of the Swift port on those cases. |
| Appearance review | Light/Dark tours with 21 screenshot checkpoints per appearance; physical-device checks recorded | Visual and interaction review for that snapshot. |

Tests cover idempotent import, incomplete captures, persistence/edits, search filtering and fallback, vector encoding, source citation verification, cancellation and recovery, append-only history, historical replay, stale decisions, manual assignment, archive/restore, unavailable models, ambiguous matching, video evidence, protected media copies, playback, and accessibility interactions.

Tooling includes `xcodebuild`, `xcrun simctl`, `xcrun devicectl`, `.xcresult` test reports, Swift Testing, XCTest UI automation, Python evaluation/export scripts, and saved model-conversion/parity artifacts. Signed device builds and in-place installation are recorded. There is no basis here to claim a configured CI/CD service, Instruments profiling, App Store deployment, or measured large-library latency.

Recorded limitations include simulator/model-asset sensitivity, some UI interruptions from phone notifications, unexercised missing-model download behavior, and incomplete live third-party share-sheet/iCloud-only asset coverage. Integrated phone cold/warm grouping latency, thermal load, and peak memory remain unmeasured.

Optional ML evaluation context, if the résumé agent needs it: P2 evaluated 240 fictional sources and 2,280 pairs, with 1,875 known-label pairs. The selected candidate recorded 95.79% pair precision and 58.39% library-macro recall versus 95.94% and 43.84% for the trained-feature control. These are different metrics from end-to-end grouping, and the multi-seed qualification failed. Prefer conversion parity and engineering integration over a headline accuracy claim in a short iOS résumé.

## 11. How to position this for the recruiter

Lead with native iOS application engineering, then storage/reliability and media/concurrency, with on-device ML as a differentiator. Useful skill keywords supported by this project are:

**Swift, SwiftUI, UIKit interoperability, Swift Concurrency, actors, async/await, Observation, iOS Share Extensions, App Groups, SQLite, GRDB, Swift Package Manager, Core ML, Vision, NaturalLanguage, Foundation Models, AVFoundation, AVKit, Speech, PhotosUI, URLSession, XCTest, Swift Testing, accessibility, and physical-device testing.**

For Global Payment, the transferable strengths are correctness under retries and concurrent edits, traceable state changes, careful local persistence, explicit network failures, platform integration, and tested UI behavior. No payment processing, Apple Pay, StoreKit billing, wallet, financial compliance, or transaction processing implementation was found. Do not imply those features exist.

No app-owned C/C++/Objective-C implementation files were found in this review. UIKit use from Swift is not Objective-C programming experience, and using Core ML is not evidence of writing C++. Answer the recruiter's C++ question based on other actual experience.

## 12. Résumé bullet candidates

Use only bullets reflecting Aaryan's actual ownership; select three or four rather than placing this whole list on a résumé.

- Built Remember, a native SwiftUI iPhone memory vault supporting notes, photos, videos, PDFs, links, and voice recordings, with an iOS Share Extension and App Group capture pipeline.
- Implemented actor-isolated processing and SQLite persistence with GRDB, including idempotent imports, interrupted-work recovery, and an append-only history that rejects stale organization decisions.
- Developed on-device media indexing with Vision, Speech, PDFKit, and AVFoundation, turning OCR, audio transcripts, and timestamped video-frame evidence into searchable source chunks.
- Integrated a fine-tuned MiniLM matcher through Core ML, porting tokenization and feature scoring to Swift and verifying agreement on all 16 saved conversion-parity cases.
- Created an accessible SwiftUI thread map with custom gesture handling, interruptible display-link motion, native zoom navigation, Dynamic Type, VoiceOver, and reduced-motion support.
- Implemented evidence-grounded question answering with asynchronous API integration, structured responses, source-quote validation, and graceful fallback when a grounded answer is unavailable.
- Validated capture, persistence, media indexing, organization, and navigation through Swift Testing and XCTest; a recorded regression run passed 135 simulator unit tests and three UI checks, supplemented by physical-iPhone testing.

Compact project description:

> **Remember — Native iOS Memory Vault**  
> Swift, SwiftUI, Swift Concurrency, GRDB/SQLite, Core ML, Vision, AVFoundation, Speech  
> A native iPhone app that captures multimodal memories, extracts searchable evidence on-device, and organizes related material into traceable threads, with optional source-grounded AI assistance.

## 13. Interview stories to prepare

1. **Import lifecycle:** why a Share Extension writes an inbox, how temporary file URLs expire, how retries avoid duplicates, and what happens if import is interrupted.
2. **Concurrency:** what belongs on the main actor, why services use actors, how cancellation/relaunch works, and how stale search/organization results are rejected.
3. **History correctness:** why mutable current state is insufficient, how event replay works, and how manual decisions remain authoritative.
4. **Media resource limits:** why images are downsampled and video sampling/transcription are bounded, and how partial results remain useful.
5. **Core ML deployment:** conversion, tokenization parity, fixed input shapes, CPU-only execution choice, model metadata checks, and unavailable-model behavior.
6. **UI engineering:** preserving gesture continuity when an animation is interrupted, repeated navigation, and accessibility alternatives to a spatial map.
7. **Testing:** deterministic injected services versus real Apple-model checks; simulator limitations versus physical-device validation.

## 14. Source map

Paths are relative to the repository root.

- Product/status: `readme.md`.
- Xcode targets/settings: `Remember/Remember.xcodeproj/project.pbxproj`; resolved dependency: `Remember/Remember.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved`.
- Presentation: `Remember/Remember/ContentView.swift`, `LibraryViewModel.swift`, `ProjectViewModel.swift`, `ProjectView.swift`, `ProjectGraphView.swift`, `ProjectGraphMotion.swift`, `ProjectGraphLayout.swift`, `RememberAppearance.swift`.
- Capture: `Remember/RememberShareExtension/ShareViewController.swift`, `Remember/Shared/CaptureInbox.swift`, `Remember/Remember/CaptureImporter.swift`, `InAppCaptureService.swift`, `InAppCaptureViews.swift`, `PhotoVideoTransfer.swift`.
- Persistence: `Remember/Remember/MemoryStore.swift`, `LibraryFileStore.swift`, `MemoryPipeline.swift`, `Provenance.swift`.
- Extraction/media: `Remember/Remember/MemoryContentExtractor.swift`, `MemoryAnalyzer.swift`, `VideoContentExtractor.swift`, `OnDeviceSpeechTranscriber.swift`, `VoiceRecorder.swift`, `LocalImageView.swift`, `LocalVideoPlayerView.swift`.
- Local ML: `Remember/Remember/ProjectIntelligence.swift`, `D3ProjectOrganizer.swift`, `D3PairMatcher.swift`, `D3Tokenizer.swift`, `D3Features.swift`, `D3OrganizationPolicy.swift`.
- Retrieval/answering: `Remember/Remember/MemorySearch.swift`, `MemoryChunk.swift`, `RememberAssistant.swift`, `OpenAIAPI.swift`; proxy: `server/openai_proxy.py`.
- Technical contracts: `docs/d3-organization.md`, `docs/video-indexing.md`, `docs/provenance.md`, `docs/threads-interface.md`, `docs/appearance.md`.
- Recorded model verification: `Evaluation/AppMatcher/VERIFICATION.md`, `conversion.json`, `native-parity.json`; quality limitations: `Evaluation/MatcherValidation/P2_REPORT.md`.
- Tests: `Remember/RememberTests/` and `Remember/RememberUITests/`.

## Review scope

This handoff was prepared through read-only source/configuration/test/report inspection. No application code was changed and no build, test, network API inference, or device installation was performed for this review. The only file added is this document. No Git state was changed.
