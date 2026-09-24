import AVFoundation
import Foundation
import GRDB
import Speech
import Testing
import XCTest
@testable import Remember

private final class VideoFixtureBundle: NSObject {}

final class VideoSpeechDeviceTests: XCTestCase {
    @MainActor func testInstalledAppleSpeechFromVideo() async throws {
        #if targetEnvironment(simulator)
        throw XCTSkip("Apple speech model availability must be checked on a physical device.")
        #else
        guard SpeechTranscriber.isAvailable,
              let locale = await SpeechTranscriber.supportedLocale(equivalentTo: .current),
              await SpeechTranscriber.installedLocales.contains(where: { $0.language.languageCode == locale.language.languageCode }) else {
            throw XCTSkip("No installed Apple speech model for the current language; visual-only fallback is covered separately.")
        }
        let bundle = Bundle(for: VideoFixtureBundle.self)
        let url = try XCTUnwrap(bundle.url(forResource: "video-evidence", withExtension: "mp4")
            ?? bundle.url(forResource: "video-evidence", withExtension: "mp4", subdirectory: "Fixtures"))
        let result = try await VideoContentExtractor().extract(at: url, caption: nil)
        let transcript = result.chunks.filter { $0.extractionMethod == .transcript }.map(\.text).joined(separator: " ")
        XCTAssertTrue(transcript.localizedCaseInsensitiveContains("telescope"), result.analysisNote ?? "No video transcript")
        #endif
    }
}

struct VideoIndexingTests {
    private func fixture() throws -> URL {
        let bundle = Bundle(for: VideoFixtureBundle.self)
        return try #require(bundle.url(forResource: "video-evidence", withExtension: "mp4")
            ?? bundle.url(forResource: "video-evidence", withExtension: "mp4", subdirectory: "Fixtures"))
    }

    @Test func videoExtractsAudioAndFrameTextWithoutCaptionAndCleansTemporaryAudio() async throws {
        let speech = FixtureVideoSpeech()
        let url = try fixture()
        let original = try Data(contentsOf: url)
        let content = try await VideoContentExtractor(speechTranscriber: speech).extract(at: url, caption: nil)
        #expect(content.text.contains("cobalt telescope"))
        #expect(content.text.localizedCaseInsensitiveContains("lunar garden budget"))
        #expect(content.text.localizedCaseInsensitiveContains("orbit greenhouse schedule"))
        #expect(content.chunks.contains { $0.extractionMethod == .transcript && $0.locator == "Video speech" })
        #expect(content.chunks.contains { $0.extractionMethod == .visionOCR && $0.locator.hasPrefix("Video text at 00:00:") })
        #expect(content.isPartial)
        let audioURL = try #require(await speech.audioURL)
        #expect(!FileManager.default.fileExists(atPath: audioURL.path))
        #expect(try Data(contentsOf: url) == original)
    }

    @Test func unavailableSpeechStillIndexesVisualsAndReportsReason() async throws {
        let speech = FixtureVideoSpeech(failure: .modelNotInstalled("en-US"))
        let content = try await VideoContentExtractor(speechTranscriber: speech).extract(at: fixture(), caption: "")
        #expect(content.text.localizedCaseInsensitiveContains("greenhouse"))
        #expect(!content.chunks.contains { $0.extractionMethod == .transcript })
        #expect(content.analysisNote?.contains("not installed") == true)
        let audioURL = try #require(await speech.audioURL)
        #expect(!FileManager.default.fileExists(atPath: audioURL.path))
    }

    @Test func cancelledSpeechDoesNotCommitPartialResultAndRemovesAudio() async throws {
        let speech = FixtureVideoSpeech(cancelled: true)
        await #expect(throws: CancellationError.self) {
            try await VideoContentExtractor(speechTranscriber: speech).extract(at: fixture(), caption: "caption")
        }
        let audioURL = try #require(await speech.audioURL)
        #expect(!FileManager.default.fileExists(atPath: audioURL.path))
    }

    @Test func posterSkipsBlackOpeningAndIsBounded() async throws {
        let poster = try await LocalVideoAsset.poster(fixture())
        #expect(poster.width <= 1_200 && poster.height <= 1_200)
        var pixel = [UInt8](repeating: 0, count: 4)
        pixel.withUnsafeMutableBytes { bytes in
            let context = CGContext(data: bytes.baseAddress, width: 1, height: 1, bitsPerComponent: 8,
                bytesPerRow: 4, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)
            context?.draw(poster, in: CGRect(x: 0, y: 0, width: 1, height: 1))
        }
        #expect(pixel.prefix(3).contains { $0 > 20 }, "The poster must show a scene, not the fixture's black opening.")
    }

    @Test func frameSamplingIsBoundedAndEvidenceRemainsDistinct() {
        #expect(VideoContentExtractor.sampleTimes(duration: .infinity).isEmpty)
        #expect(VideoContentExtractor.sampleTimes(duration: 0).isEmpty)
        #expect(VideoContentExtractor.sampleTimes(duration: 0.1).count == 1)
        let long = VideoContentExtractor.sampleTimes(duration: 7_200)
        #expect(long.count == 12 && long.first! > 0 && long.last! < 7_200)
        let content = VideoContentExtractor.content(caption: "My video", transcript: "cobalt telescope",
            frames: [
                VideoFrameEvidence(seconds: 5, text: "Orbit greenhouse", labels: [.init(identifier: "garden", confidence: 0.95)]),
                VideoFrameEvidence(seconds: 10, text: "Orbit greenhouse", labels: [])
            ], notes: ["Sampled visuals"])
        #expect(content.chunks.filter { $0.extractionMethod == .visionOCR }.count == 1)
        #expect(content.chunks.contains { $0.extractionMethod == .visionClassification && $0.text.contains("95% confidence") })
        #expect(content.chunks.map(\.ordinal) == Array(content.chunks.indices))
        #expect(!content.text.contains("Sampled visuals"), "Coverage notices must not become search evidence.")
    }

    @Test func evidenceReachesSearchAndThreadInputsAndLegacyUpgradeRunsOnce() async throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("VideoIndexingTests-\(UUID())")
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = try MemoryStore(databaseURL: directory.appendingPathComponent("db.sqlite"))
        let date = Date(timeIntervalSince1970: 1_800_000_000)
        let memory = MemoryItem(id: UUID(), kind: .video, createdAt: date, importedAt: date, updatedAt: date,
            state: .indexed, originalFilename: "retained.mp4", userCaption: "Unrelated caption", title: "My edited title",
            summary: nil, extractedText: "Unrelated caption", tagsJSON: "[]", processingError: nil, modelVersion: "deterministic-basic-mode-v1")
        try await store.insertIfNeeded(memory)
        try await store.updateEditableFields(id: memory.id, title: "My edited title", summary: "My summary", tags: ["personal"])
        try await store.requeueLegacyVideoAnalysis()
        let firstCount = try await store.provenanceEvents().count
        try await store.requeueLegacyVideoAnalysis()
        #expect(try await store.provenanceEvents().count == firstCount)
        let claimed = try #require(await store.claimNextCaptured())
        let extracted = VideoContentExtractor.content(caption: claimed.userCaption, transcript: "cobalt telescope",
            frames: [.init(seconds: 6, text: "Orbit greenhouse", labels: [])], notes: ["Sampled visuals"])
        try await store.saveExtraction(id: claimed.id, filename: claimed.originalFilename, extracted: extracted)
        let result = DeterministicMemoryAnalyzer.result(memory: claimed, extracted: extracted)
        try await store.markIndexed(id: claimed.id, analysis: result, expectedFilename: claimed.originalFilename)
        let indexed = try #require(await store.fetch(id: claimed.id))
        #expect(indexed.title == "My edited title" && indexed.tags == ["personal"])
        #expect(indexed.analysisNote == "Sampled visuals")
        let snapshot = try ProvenanceSnapshot.replay(await store.provenanceEvents())
        #expect(snapshot.memories[claimed.id]?.extractedText?.contains("cobalt telescope") == true)
        let search = MemorySearchService(memoryStore: store)
        #expect(try await search.search(MemorySearchRequest(query: "cobalt telescope")).first?.memory.id == claimed.id)
        #expect(try await search.searchEvidence(MemorySearchRequest(query: "Orbit greenhouse")).first?.chunk.extractionMethod == .visionOCR)
        let finalCount = try await store.provenanceEvents().count
        try await store.requeueLegacyVideoAnalysis()
        #expect(try await store.provenanceEvents().count == finalCount)
        #expect(try await store.fetch(id: claimed.id)?.state == .indexed)
        try await store.updateEditableFields(id: claimed.id, title: "Renamed video", summary: "", tags: [])
        #expect(try await search.searchEvidence(MemorySearchRequest(query: "Orbit greenhouse")).first?.chunk.locator == "Video text at 00:00:06")
        try await store.setArchived(id: claimed.id, archived: true)
        #expect(try await search.search(MemorySearchRequest(query: "cobalt telescope")).isEmpty)
        try await store.setArchived(id: claimed.id, archived: false)
        #expect(try await search.searchEvidence(MemorySearchRequest(query: "cobalt telescope")).first?.chunk.extractionMethod == .transcript)
    }

    @Test func oldMemoryPayloadWithoutCoverageNoteStillDecodes() throws {
        let date = Date(timeIntervalSince1970: 1_800_000_000)
        let memory = MemoryItem(id: UUID(), kind: .video, createdAt: date, importedAt: date, updatedAt: date,
            state: .indexed, originalFilename: "old.mp4", userCaption: nil, title: nil, summary: nil,
            extractedText: nil, tagsJSON: "[]", processingError: nil, modelVersion: nil)
        let encoded = try JSONEncoder().encode(memory)
        var object = try #require(JSONSerialization.jsonObject(with: encoded) as? [String: Any])
        object.removeValue(forKey: "analysisNote")
        let decoded = try JSONDecoder().decode(MemoryItem.self, from: JSONSerialization.data(withJSONObject: object))
        #expect(decoded.analysisNote == nil && decoded.originalFilename == "old.mp4")
    }
}

private actor FixtureVideoSpeech: LocalSpeechTranscribing {
    let failure: OnDeviceSpeechError?
    let cancelled: Bool
    private(set) var audioURL: URL?
    init(failure: OnDeviceSpeechError? = nil, cancelled: Bool = false) {
        self.failure = failure; self.cancelled = cancelled
    }
    func transcribe(audioURL: URL) async throws -> String {
        self.audioURL = audioURL
        #expect(audioURL.pathExtension == "m4a")
        #expect(try AVAudioFile(forReading: audioURL).length > 0)
        if cancelled { throw CancellationError() }
        if let failure { throw failure }
        return "The cobalt telescope is ready for tomorrow's astronomy workshop."
    }
}

struct RejectSpeech: LocalSpeechTranscribing {
    func transcribe(audioURL: URL) async throws -> String {
        Issue.record("A silent video must not request transcription")
        throw OnDeviceSpeechError.noSpeechDetected
    }
}
