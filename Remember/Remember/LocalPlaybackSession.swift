import AVFAudio

/// Session setup must not block the UI while iOS negotiates the audio route.
actor LocalPlaybackSession {
    static let shared = LocalPlaybackSession()

    func activate(movie: Bool = false) async throws {
        try Task.checkCancellation()
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playback, mode: movie ? .moviePlayback : .default)
        if #available(iOS 27.0, *) {
            guard try await session.activate() else { throw ActivationError.declined }
        } else {
            // This actor's executor keeps the older synchronous API off MainActor.
            try session.setActive(true)
        }
        try Task.checkCancellation()
    }

    private enum ActivationError: Error { case declined }
}
