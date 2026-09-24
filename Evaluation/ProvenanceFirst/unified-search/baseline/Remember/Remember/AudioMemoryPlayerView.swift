import AVFAudio
import Observation
import SwiftUI

struct AudioMemoryPlayerView: View {
    let url: URL
    var onOpenMemory: (() -> Void)? = nil
    @Environment(\.scenePhase) private var scenePhase
    @State private var player = AudioMemoryPlayer()

    var body: some View {
        HStack(spacing: 16) {
            Button {
                player.toggle(url: url)
            } label: {
                Image(systemName: player.isPlaying || player.isLoading ? "stop.circle.fill" : "play.circle.fill")
                    .font(.system(size: 44))
            }
            .accessibilityLabel(player.isLoading ? "Cancel voice playback" : player.isPlaying ? "Stop voice memory" : "Play voice memory")

            if let onOpenMemory {
                Button(action: onOpenMemory) { recordingLabel }
                    .buttonStyle(.plain)
                    .accessibilityLabel("Open voice memory")
            } else {
                recordingLabel
            }
            Spacer()
            Image(systemName: "waveform")
                .font(.title2)
                .foregroundStyle(RememberPalette.secondaryText)
                .accessibilityHidden(true)
        }
        .padding()
        .rememberCard(radius: 20, dark: Color.accentColor.opacity(0.1))
        .onDisappear { player.stop() }
        .onChange(of: url) { _, _ in player.stop() }
        .onChange(of: scenePhase) { _, phase in
            if phase != .active { player.stop() }
        }
    }

    private var recordingLabel: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Voice memory").font(.headline)
            Text(player.statusText).font(.caption).foregroundStyle(RememberPalette.secondaryText)
        }
        .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
        .contentShape(Rectangle())
    }
}

@MainActor
@Observable
final class AudioMemoryPlayer {
    private(set) var isPlaying = false
    private(set) var isLoading = false
    private(set) var statusText = "Stored on this iPhone"
    private var playback: VoicePlaybackEngine?
    private var requestID: UUID?
    private var preparationTask: Task<Void, Never>?
    private let activate: @MainActor () async throws -> Void

    init(activate: @escaping @MainActor () async throws -> Void = {
        try await LocalPlaybackSession.shared.activate()
    }) {
        self.activate = activate
    }

    @discardableResult
    func toggle(url: URL) -> Task<Void, Never>? {
        if isPlaying || isLoading {
            stop()
            return nil
        }
        let id = UUID()
        requestID = id
        isLoading = true
        statusText = "Opening recording…"
        let engine = VoicePlaybackEngine()
        playback = engine
        let task = Task { [weak self] in
            guard let self else { return }
            do {
                try await activate()
                try Task.checkCancellation()
                guard requestID == id else { return }
                try await engine.play(url: url) { [weak self] success in
                    guard let self, self.requestID == id else { return }
                    self.stop()
                    self.statusText = success ? "Finished" : "Playback stopped"
                }
                try Task.checkCancellation()
                guard requestID == id else { await engine.stop(); return }
                isPlaying = true
                statusText = "Playing locally"
            } catch {
                await engine.stop()
                guard requestID == id else { return }
                isPlaying = false
                statusText = error is CancellationError ? "Stored on this iPhone" : "Could not play this recording"
            }
            guard requestID == id else { return }
            isLoading = false
            preparationTask = nil
        }
        preparationTask = task
        return task
    }

    func stop() {
        requestID = nil
        preparationTask?.cancel()
        preparationTask = nil
        isLoading = false
        if let playback { Task { await playback.stop() } }
        playback = nil
        isPlaying = false
        statusText = "Stored on this iPhone"
    }

}

/// AVAudioPlayer's prepare/play/stop also negotiate hardware synchronously, even
/// after explicit session activation. Keep the player confined to this executor.
private actor VoicePlaybackEngine {
    private var player: AVAudioPlayer?
    private var delegate: VoicePlaybackDelegate?
    private var stopped = false

    func play(url: URL, completion: @escaping @MainActor @Sendable (Bool) -> Void) throws {
        try Task.checkCancellation()
        guard !stopped else { throw CancellationError() }
        let audio = try AVAudioPlayer(contentsOf: url)
        let delegate = VoicePlaybackDelegate(completion: completion)
        audio.delegate = delegate
        guard audio.prepareToPlay(), audio.play() else { throw AudioMemoryPlayerError.couldNotPlay }
        player = audio
        self.delegate = delegate
    }

    func stop() {
        stopped = true
        player?.stop()
        player = nil
        delegate = nil
    }
}

nonisolated private final class VoicePlaybackDelegate: NSObject, AVAudioPlayerDelegate {
    let completion: @MainActor @Sendable (Bool) -> Void

    init(completion: @escaping @MainActor @Sendable (Bool) -> Void) {
        self.completion = completion
    }

    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        let completion = completion
        Task { @MainActor in completion(flag) }
    }

    func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: (any Error)?) {
        let completion = completion
        Task { @MainActor in completion(false) }
    }
}

nonisolated private enum AudioMemoryPlayerError: Error {
    case couldNotPlay
}
