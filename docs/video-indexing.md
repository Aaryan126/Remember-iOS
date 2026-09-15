# Video capture, playback and indexing

Implemented 14 September 2026.

## User experience

- Import videos from Photos, Files, or the Share Extension. Originals remain in the protected local vault.
- Memories cards show a poster and Video badge. Opening a card offers native playback. The map keeps its title-based circles; opening a video’s thread offers the same player inside History. Source details and the import preview also use that player.
- Playback is initiated by a tap, supports native seeking, and pauses when leaving or backgrounding. The poster tries an interior frame, the midpoint, then the opening; it prefers a non-black/non-white frame. Orientation is respected, dimensions are bounded to 1,200 pixels, and an in-memory cache is capped at 24 MB / 32 images. A poster failure does not prevent playback.
- Memory Details explains actual indexing coverage and offers **Reindex video**. When a supported speech model is missing, **Download speech model** explicitly downloads Apple’s model and then retries indexing. No speech-model download starts automatically.
- **Searchable video content** expands the extracted evidence in Memories. Thread source details also show the coverage note.

## Local evidence pipeline

`VideoContentExtractor` first validates a playable local video. It processes the caption, audio and visual samples into separate evidence chunks:

| Evidence | Extraction | Citation locator |
| --- | --- | --- |
| User caption | Saved text | Video caption |
| Spoken content | Audio exported to protected temporary M4A, then Apple SpeechAnalyzer / SpeechTranscriber | Video speech |
| Text in frames | Apple Vision text recognition | Video text at HH:MM:SS |
| Possible visual categories | Apple Vision image classification, filtered for high precision | Video scene at HH:MM:SS |

Visual sampling uses up to 12 evenly spaced interior points across the clip, exact requested frame times, and orientation-correct frames bounded to 1,280 pixels. Repeated frame text is deduplicated. Visual labels remain explicitly probabilistic and retain confidence. Text recognition and classification fail independently so useful evidence survives a failure of the other operation.

Speech covers at most the first 30 minutes and retains up to 50,000 characters. Silent videos skip transcription. Missing/unsupported speech models or audio errors preserve caption/visual evidence and produce a coverage note. Cancellation propagates rather than committing an interrupted extraction as complete. Temporary audio is removed on success, failure or cancellation; originals are never rewritten.

All video capture extraction and metadata stay local even when Cloud assistance is enabled. Explicit Ask and AI search can still use the resulting text under their existing policies. Apple model downloads transfer model assets, not the source video.

The full evidence enters the existing searchable text and chunk indexes and the provenance snapshot used by Threads. Metadata edits and archive/restore retain video evidence types and timestamps when source text is unchanged. Archive remains excluded from search. The D3 matcher still accepts only supported English evidence within its existing 16,000-scalar bound; this change does not relax matching thresholds or reassign previously organized videos. Very long transcripts can therefore be searchable while remaining outside automatic matching.

## Coverage and compatibility

Sampled frames are not continuous scene/action understanding. Brief scenes can be missed, OCR/transcription can be inaccurate, and language/model availability varies by device. Every video result remains marked partial. Coverage notices are metadata, never searchable evidence.

`addVideoAnalysisCoverage` adds a nullable `analysisNote` column. The matching optional field is backward-compatible with older provenance payloads. Existing extraction-method values and original-file formats are retained.

On synchronization, indexed, non-archived videos whose model version predates `apple-video-speech-vision-v1` are queued once. The normal pipeline saves upgraded evidence and that version, including partial results. Already-current or failed records are not repeatedly requeued. Original bytes, manual metadata, and thread assignments remain intact. A user can retry a partial result after installing a model.

## Validation

The synthetic `RememberTests/Fixtures/video-evidence.mp4` contains a black opening, two text slides (Lunar garden budget / Orbit greenhouse schedule), and locally synthesized speech about a cobalt telescope. It contains no user media. It was generated with macOS `say`, Pillow slide images, and ffmpeg at 640×360 / 24 fps with H.264 video and AAC audio; both tracks last 12 seconds.

`VideoIndexingTests` covers caption-independent audio/frame extraction, unavailable speech fallback, cancellation cleanup, poster selection, bounded sampling, evidence labels, search/provenance propagation, one-time upgrades, metadata preservation, archive/restore, and decoding older payloads. `VideoRiverTests` covers storage, source-event identity, no cloud calls, transfer isolation and playable/corrupt/missing files. `VideoSpeechDeviceTests/testInstalledAppleSpeechFromVideo` verifies real Apple transcription on an eligible physical device; simulator skips are explicit.

UI checks cover Photos import, video details, playback from Memories and History, playback progress, empty/whitespace thread search, matching suggestions, and accessibility text sizes. Only synthetic captures are added in the simulator. Phone unit tests use their own temporary data; phone UI tests read the existing library.

Initial testing exposed coupled OCR/classification failure and an incorrectly timed synthetic fixture. The extractor now retains independent results, and the fixture’s audio/video durations were verified with ffprobe. Simulator scene classification can lack a working inference context; coverage notes correctly report that while OCR remains available. Real speech and visual extraction were also exercised on iPhone.

Completed checks:

- `xcodebuild test` on Remember UI Review: all **135 unit tests**, plus `testMemoryMapAccessibilityTextSize`, `testPhotosVideoImportAndInlineRiverPlayback`, and `ThreadNavigationUITests/testExistingThreadsFinderAndHistoryReadOnly` passed in `/tmp/remember-video-search-regression.xcresult`.
- `xcodebuild test` on the connected iPhone: **12 video unit tests**, real `VideoSpeechDeviceTests/testInstalledAppleSpeechFromVideo`, and the thread-search/history UI test passed in `/tmp/remember-video-complete-phone.xcresult`. This final run includes preservation of evidence after metadata edits and archive/restore, and compiles the explicit model-download control. No download was needed on the phone, so the actual download operation remains unexercised.
- Final targeted simulator `xcodebuild test`: all seven `VideoIndexingTests` and the expanded Photos → video details → Memories playback → History playback UI check passed in `/tmp/remember-video-complete-simulator.xcresult`. This includes the final video-details controls and metadata/archive evidence preservation. The final device build is installed and launched.
- Earlier video runs (`/tmp/remember-video-evidence-tests.xcresult`, `/tmp/remember-video-evidence-modern-tests.xcresult`, `/tmp/remember-video-evidence-phone.xcresult`) failed the frame-extraction assertions before the independent-request and fixture/timing corrections. `/tmp/remember-video-evidence-phone-final.xcresult` passed video checks but a notification interrupted the UI menu tap; the final phone run above passed.
- `plutil -lint Remember/RememberShareExtension/Info.plist` and `git --no-optional-locks diff --check` passed. The share extension was built and signed; a live third-party share-sheet round trip, iCloud-only assets, and the missing-model download remain manual coverage limits.

Builds used `Remember/Remember.xcodeproj`, scheme `Remember`, Debug configuration, `-disableAutomaticPackageResolution -skipPackageUpdates`, and existing package checkouts at `/tmp/RememberProvenance/SourcePackages`. Simulator builds used `/tmp/RememberThreadsLayoutReview`, `CODE_SIGNING_ALLOWED=NO`, and destination `platform=iOS Simulator,id=5741ED23-9F8F-4FB6-84E9-FE1E83225998`. Device builds used `/tmp/RememberThreadsLayoutPhone`, `DEVELOPMENT_TEAM=397P48LWC5`, and destination `platform=iOS,id=00008150-000A123A2EC0C01C`. Tests disabled parallel execution and selected only the suites listed above when running on the personal phone.

## Apple API references

- [SpeechAnalyzer](https://developer.apple.com/documentation/speech/speechanalyzer) and [AssetInventory](https://developer.apple.com/documentation/speech/assetinventory).
- [Apple M4A export preset](https://developer.apple.com/documentation/avfoundation/avassetexportpresetapplem4a).
- [RecognizeTextRequest](https://developer.apple.com/documentation/vision/recognizetextrequest) and [ClassifyImageRequest](https://developer.apple.com/documentation/vision/classifyimagerequest).

## Changed files

- Extraction/playback: `VideoContentExtractor.swift` (new), `LocalVideoPlayerView.swift`, `MemoryContentExtractor.swift`, `OnDeviceSpeechTranscriber.swift`, `LocalAI.swift`, `ProjectIntelligence.swift`.
- Indexing/storage: `MemoryItem.swift`, `MemoryChunk.swift`, `MemoryPipeline.swift`, `MemorySearch.swift`, `MemoryStore.swift`, `Provenance.swift`.
- UI/capture: `ProjectView.swift`, `MemoryDetailView.swift`, `InAppCaptureViews.swift`, `ProvenanceViews.swift`, `RememberShareExtension/ShareViewController.swift`, `RememberShareExtension/Info.plist`.
- Tests: `VideoIndexingTests.swift` (new), synthetic `Fixtures/video-evidence.mp4` (new), `VideoRiverTests.swift`, `RememberUITests.swift`, `ThreadNavigationUITests.swift`, `AppearanceReviewUITests.swift`.
- Documentation: `readme.md`, `docs/threads-interface.md`, `docs/provenance.md`, `docs/d3-organization.md`, and this file.

No package dependency or Git-state changes were made.
