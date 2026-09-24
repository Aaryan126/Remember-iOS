import AVFAudio
import Foundation
import Speech

nonisolated protocol LocalSpeechTranscribing: Sendable {
    func transcribe(audioURL: URL) async throws -> String
}

actor OnDeviceSpeechTranscriber: LocalSpeechTranscribing {
    nonisolated static let modelVersion = "Apple SpeechTranscriber (installed on-device model)"

    nonisolated static func needsModelDownload() async -> Bool {
        guard SpeechTranscriber.isAvailable,
              let locale = await SpeechTranscriber.supportedLocale(equivalentTo: .current) else { return false }
        return await installedLocale(equivalentTo: locale, in: SpeechTranscriber.installedLocales) == nil
    }

    /// Called only by the explicit model-download control; source audio is never uploaded.
    nonisolated static func installCurrentModel() async throws {
        guard SpeechTranscriber.isAvailable else { throw OnDeviceSpeechError.unavailable }
        guard let locale = await SpeechTranscriber.supportedLocale(equivalentTo: .current) else {
            throw OnDeviceSpeechError.unsupportedLocale(Locale.current.identifier)
        }
        let transcriber = SpeechTranscriber(locale: locale, preset: .transcription)
        if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
            try await request.downloadAndInstall()
        }
        try Task.checkCancellation()
    }

    func transcribe(audioURL: URL) async throws -> String {
        guard SpeechTranscriber.isAvailable else {
            throw OnDeviceSpeechError.unavailable
        }

        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: .current) else {
            throw OnDeviceSpeechError.unsupportedLocale(Locale.current.identifier)
        }
        let installedLocales = await SpeechTranscriber.installedLocales
        guard let installedLocale = Self.installedLocale(equivalentTo: supportedLocale, in: installedLocales) else {
            throw OnDeviceSpeechError.modelNotInstalled(supportedLocale.identifier)
        }

        let transcriber = SpeechTranscriber(locale: installedLocale, preset: .transcription)
        let analyzer = SpeechAnalyzer(modules: [transcriber])
        let audioFile: AVAudioFile
        do {
            audioFile = try AVAudioFile(forReading: audioURL)
        } catch {
            throw OnDeviceSpeechError.unreadableRecording
        }

        let resultTask = Task<String, Error> {
            var transcript = ""
            for try await result in transcriber.results {
                transcript += String(result.text.characters)
            }
            return transcript
        }

        do {
            if let lastSample = try await analyzer.analyzeSequence(from: audioFile) {
                try await analyzer.finalizeAndFinish(through: lastSample)
            } else {
                await analyzer.cancelAndFinishNow()
            }
            let transcript = try await resultTask.value
                .trimmingCharacters(in: .whitespacesAndNewlines)
            guard !transcript.isEmpty else {
                throw OnDeviceSpeechError.noSpeechDetected
            }
            return String(transcript.prefix(50_000))
        } catch {
            resultTask.cancel()
            await analyzer.cancelAndFinishNow()
            if error is CancellationError || Task.isCancelled { throw CancellationError() }
            if let speechError = error as? OnDeviceSpeechError {
                throw speechError
            }
            throw OnDeviceSpeechError.transcriptionFailed
        }
    }

    nonisolated private static func installedLocale(
        equivalentTo locale: Locale,
        in installedLocales: [Locale]
    ) -> Locale? {
        if let exact = installedLocales.first(where: { $0.identifier == locale.identifier }) {
            return exact
        }
        return installedLocales.first {
            $0.language.languageCode == locale.language.languageCode
        }
    }
}

nonisolated enum OnDeviceSpeechError: LocalizedError, Equatable {
    case unavailable
    case unsupportedLocale(String)
    case modelNotInstalled(String)
    case unreadableRecording
    case noSpeechDetected
    case transcriptionFailed

    var errorDescription: String? {
        switch self {
        case .unavailable:
            "On-device transcription is not available on this iPhone."
        case .unsupportedLocale(let locale):
            "On-device transcription does not support the current language (\(locale))."
        case .modelNotInstalled(let locale):
            "The on-device speech model for \(locale) is not installed. A video’s Memory Details offers a model download, followed by reindexing. Remember does not download speech models automatically."
        case .unreadableRecording:
            "Remember could not read the saved audio."
        case .noSpeechDetected:
            "No speech was detected in this recording."
        case .transcriptionFailed:
            "On-device transcription could not complete."
        }
    }
}
