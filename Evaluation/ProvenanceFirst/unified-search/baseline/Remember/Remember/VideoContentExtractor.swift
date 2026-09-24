import AVFoundation
import Foundation
import Vision

nonisolated protocol VideoContentExtracting: Sendable {
    func extract(at url: URL, caption: String?) async throws -> ExtractedMemoryContent
}

nonisolated struct VideoFrameEvidence: Sendable {
    let seconds: Double
    let text: String
    let labels: [VisionImageLabel]
}

/// Bounded local evidence extraction. Frame samples are never represented as a complete scene transcript.
actor VideoContentExtractor: VideoContentExtracting {
    nonisolated static let modelVersion = "apple-video-speech-vision-v1"
    nonisolated static let maximumSpeechDuration: Double = 30 * 60
    nonisolated static let maximumFrames = 12
    private let speechTranscriber: any LocalSpeechTranscribing

    init(speechTranscriber: any LocalSpeechTranscribing = OnDeviceSpeechTranscriber()) {
        self.speechTranscriber = speechTranscriber
    }

    func extract(at url: URL, caption: String?) async throws -> ExtractedMemoryContent {
        try await LocalVideoAsset.validate(url)
        let asset = AVURLAsset(url: url)
        let duration = try await asset.load(.duration).seconds
        guard duration.isFinite, duration > 0 else { throw VideoImportError.unplayable }
        var notes: [String] = []
        var frames: [VideoFrameEvidence] = []
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 1_280, height: 1_280)
        generator.requestedTimeToleranceBefore = .zero
        generator.requestedTimeToleranceAfter = .zero
        defer { generator.cancelAllCGImageGeneration() }

        for seconds in Self.sampleTimes(duration: duration) {
            try Task.checkCancellation()
            do {
                let frame = try await generator.image(at: CMTime(seconds: seconds, preferredTimescale: 600))
                // Text and classification can fail independently; retain whichever evidence succeeds.
                var text = ""
                var labels: [VisionImageLabel] = []
                do {
                    var request = RecognizeTextRequest()
                    request.recognitionLevel = .accurate
                    request.usesLanguageCorrection = true
                    text = try await request.perform(on: frame.image)
                        .compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
                } catch {
                    try Task.checkCancellation()
                    notes.append("Some frame text could not be recognized.")
                }
                do {
                    labels = try await VisionImageClassifier.normalizedLabels(ClassifyImageRequest().perform(on: frame.image)
                        .filter { $0.hasMinimumRecall(0.01, forPrecision: 0.9) }
                        .map { VisionImageLabel(identifier: $0.identifier, confidence: $0.confidence) })
                } catch {
                    try Task.checkCancellation()
                    notes.append("Some scene labels could not be generated.")
                }
                frames.append(VideoFrameEvidence(seconds: frame.actualTime.seconds, text: text, labels: labels))
            } catch {
                try Task.checkCancellation()
                notes.append("Some video frames could not be analyzed.")
            }
        }
        notes.append("Visual search uses \(frames.count) sampled frames across the video; it may miss brief scenes or text.")

        var transcript: String?
        do {
            let audioTracks = try await asset.loadTracks(withMediaType: .audio)
            if audioTracks.isEmpty {
                notes.append("This video has no audio track.")
            } else {
                transcript = try await transcribe(asset: asset, duration: duration)
                notes.append(duration > Self.maximumSpeechDuration
                    ? "Speech is indexed from the first 30 minutes."
                    : "Speech was transcribed on this device.")
            }
        } catch is CancellationError {
            throw CancellationError()
        } catch let error as OnDeviceSpeechError {
            notes.append(error.errorDescription ?? "Speech could not be transcribed.")
        } catch {
            try Task.checkCancellation()
            notes.append("The audio could not be transcribed. Caption and available visual evidence are still searchable.")
        }
        try Task.checkCancellation()
        return Self.content(caption: caption, transcript: transcript, frames: frames, notes: notes)
    }

    private func transcribe(asset: AVURLAsset, duration: Double) async throws -> String {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("video-speech-\(UUID())", isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true,
            attributes: [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication, .posixPermissions: 0o700])
        defer { try? FileManager.default.removeItem(at: directory) }
        let audioURL = directory.appendingPathComponent("audio.m4a")
        guard let exporter = AVAssetExportSession(asset: asset, presetName: AVAssetExportPresetAppleM4A) else {
            throw OnDeviceSpeechError.unreadableRecording
        }
        exporter.timeRange = CMTimeRange(start: .zero,
            duration: CMTime(seconds: min(duration, Self.maximumSpeechDuration), preferredTimescale: 600))
        try await exporter.export(to: audioURL, as: .m4a)
        try Task.checkCancellation()
        return try await speechTranscriber.transcribe(audioURL: audioURL)
    }

    nonisolated static func sampleTimes(duration: Double) -> [Double] {
        guard duration.isFinite, duration > 0 else { return [] }
        let count = min(maximumFrames, max(1, Int(min(duration / 5, Double(maximumFrames))) + 1))
        // Interior samples avoid title slates/fades at the exact start and end.
        return (0..<count).map { duration * (Double($0) + 0.5) / Double(count) }
    }

    nonisolated static func content(caption: String?, transcript: String?, frames: [VideoFrameEvidence], notes: [String]) -> ExtractedMemoryContent {
        var chunks: [MemoryChunkDraft] = []
        func append(_ text: String, locator: String, method: MemoryExtractionMethod) {
            chunks += MemoryTextChunker.chunks(from: String(text.prefix(50_000)), locatorPrefix: locator,
                startingOrdinal: chunks.count, extractionMethod: method)
        }
        if let caption { append(caption, locator: "Video caption", method: .plainText) }
        if let transcript { append(transcript, locator: "Video speech", method: .transcript) }
        var seenTexts = Set<String>()
        var labels: [VisionImageLabel] = []
        for frame in frames {
            let timestamp = timestamp(frame.seconds)
            let text = frame.text.trimmingCharacters(in: .whitespacesAndNewlines)
            if !text.isEmpty, seenTexts.insert(text.lowercased()).inserted {
                append(text, locator: "Video text at \(timestamp)", method: .visionOCR)
            }
            if !frame.labels.isEmpty {
                append("Possible visual labels: " + frame.labels.map(\.evidenceText).joined(separator: ", "),
                       locator: "Video scene at \(timestamp)", method: .visionClassification)
                labels += frame.labels
            }
        }
        let uniqueNotes = notes.reduce(into: [String]()) { if !$0.contains($1) { $0.append($1) } }
        return ExtractedMemoryContent(text: chunks.map(\.text).joined(separator: "\n\n"), chunks: chunks,
            isPartial: true, visualLabels: VisionImageClassifier.normalizedLabels(labels),
            analysisNote: uniqueNotes.joined(separator: " "))
    }

    nonisolated private static func timestamp(_ seconds: Double) -> String {
        let total = seconds.isFinite ? Int(max(0, min(seconds, Double(Int32.max)))) : 0
        return String(format: "%02d:%02d:%02d", total / 3600, total / 60 % 60, total % 60)
    }
}
