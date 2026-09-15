import AVKit
import SwiftUI

nonisolated enum VideoImportError: LocalizedError {
    case unplayable

    var errorDescription: String? {
        "This video could not be opened. Choose a playable, unprotected video."
    }
}

nonisolated enum LocalVideoAsset {
    static func validate(_ url: URL) async throws {
        guard url.isFileURL else { throw VideoImportError.unplayable }
        let asset = AVURLAsset(url: url)
        let playable = try await asset.load(.isPlayable)
        let tracks = try await asset.loadTracks(withMediaType: .video)
        try Task.checkCancellation()
        guard playable, !tracks.isEmpty else { throw VideoImportError.unplayable }
    }

    static func poster(_ url: URL) async throws -> CGImage {
        let asset = AVURLAsset(url: url)
        let duration = try await asset.load(.duration).seconds
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 1_200, height: 1_200)
        defer { generator.cancelAllCGImageGeneration() }
        let times = duration.isFinite && duration > 0
            ? [min(1, duration * 0.1), duration * 0.5, 0] : [0]
        var fallback: CGImage?
        for seconds in times {
            try Task.checkCancellation()
            do {
                let frame = try await generator.image(at: CMTime(seconds: seconds, preferredTimescale: 600)).image
                fallback = fallback ?? frame
                if hasVisibleContent(frame) { return frame }
            } catch {
                try Task.checkCancellation()
            }
        }
        guard let fallback else { throw VideoImportError.unplayable }
        return fallback
    }

    private static func hasVisibleContent(_ image: CGImage) -> Bool {
        var pixels = [UInt8](repeating: 0, count: 32 * 32)
        let drawn = pixels.withUnsafeMutableBytes { bytes -> Bool in
            guard let context = CGContext(data: bytes.baseAddress, width: 32, height: 32, bitsPerComponent: 8,
                bytesPerRow: 32, space: CGColorSpaceCreateDeviceGray(), bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return false }
            context.draw(image, in: CGRect(x: 0, y: 0, width: 32, height: 32))
            return true
        }
        guard drawn else { return true }
        let average = pixels.reduce(0.0) { $0 + Double($1) } / Double(pixels.count)
        return average > 8 && average < 247
    }
}

private actor VideoPosterCache {
    static let shared = VideoPosterCache()
    private let images: NSCache<NSURL, CGImage> = {
        let cache = NSCache<NSURL, CGImage>()
        cache.countLimit = 32
        cache.totalCostLimit = 24 * 1_024 * 1_024
        return cache
    }()

    func image(for url: URL) async throws -> CGImage {
        if let image = images.object(forKey: url as NSURL) { return image }
        let image = try await LocalVideoAsset.poster(url)
        try Task.checkCancellation()
        images.setObject(image, forKey: url as NSURL, cost: image.bytesPerRow * image.height)
        return image
    }
}

struct LocalVideoPosterView: View {
    let url: URL
    @State private var thumbnail: UIImage?

    var body: some View {
        ZStack {
            Color.black
            if let thumbnail {
                Image(uiImage: thumbnail).resizable().scaledToFit()
            } else {
                Image(systemName: "video").font(.largeTitle).foregroundStyle(.white.opacity(0.7))
            }
        }
        .aspectRatio(16 / 9, contentMode: .fit)
        .task(id: url) {
            thumbnail = nil
            do {
                let image = try await VideoPosterCache.shared.image(for: url)
                try Task.checkCancellation()
                thumbnail = UIImage(cgImage: image)
            } catch {
                // A missing poster does not prevent native playback.
            }
        }
        .accessibilityHidden(true)
    }
}

/// Creates a player only after an explicit tap. Leaving the river or backgrounding pauses it.
struct LocalVideoPlayerView: View {
    let url: URL
    @Environment(\.scenePhase) private var scenePhase
    @State private var player: AVPlayer?
    @State private var isLoading = false
    @State private var wantsPlayback = false
    @State private var failure: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            ZStack {
                if let player {
                    VideoPlayer(player: player)
                        .aspectRatio(16 / 9, contentMode: .fit)
                        .accessibilityLabel("Saved video player")
                } else {
                    LocalVideoPosterView(url: url)
                    if isLoading {
                        ProgressView("Opening video…").tint(.white).foregroundStyle(.white)
                    } else {
                        Button {
                            wantsPlayback = true
                        } label: {
                            Image(systemName: "play.fill").font(.title2)
                                .frame(width: 60, height: 60)
                                .foregroundStyle(.white)
                                .background(.black.opacity(0.65), in: .circle)
                        }
                        .buttonStyle(.borderless)
                        .accessibilityLabel(failure == nil ? "Play video" : "Retry video")
                    }
                }
            }
            .clipShape(.rect(cornerRadius: 16))
            if let failure {
                Label(failure, systemImage: "exclamationmark.triangle")
                    .font(.footnote).foregroundStyle(RememberPalette.secondaryText)
            }
        }
        .task(id: wantsPlayback) {
            guard wantsPlayback else { return }
            isLoading = true
            failure = nil
            defer { isLoading = false }
            do {
                try await LocalVideoAsset.validate(url)
                try Task.checkCancellation()
                try AVAudioSession.sharedInstance().setCategory(.playback, mode: .moviePlayback)
                try AVAudioSession.sharedInstance().setActive(true)
                let newPlayer = AVPlayer(url: url)
                player = newPlayer
                if scenePhase == .active { newPlayer.play() }
            } catch is CancellationError {
                return
            } catch {
                failure = "Video unavailable. Try again or open the saved original in details."
                wantsPlayback = false
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: AVPlayerItem.failedToPlayToEndTimeNotification)) { notification in
            guard let item = notification.object as? AVPlayerItem, item === player?.currentItem else { return }
            player?.pause()
            player = nil
            wantsPlayback = false
            failure = "Playback interrupted. Try again."
        }
        .onChange(of: scenePhase) { _, phase in
            if phase != .active { player?.pause() }
        }
        .onDisappear {
            player?.pause()
            player = nil
            wantsPlayback = false
        }
        .onChange(of: url) { _, _ in
            player?.pause()
            player = nil
            wantsPlayback = false
            failure = nil
        }
    }
}
