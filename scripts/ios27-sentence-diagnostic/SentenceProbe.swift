import Foundation
import NaturalLanguage
import Darwin
#if os(iOS)
import SwiftUI
#endif

// Deliberately no asset requests, settings changes, private APIs or app-data access.
enum SentenceProbe {
    static let text = "The fictional Cedar project meeting is scheduled for Friday."

    static func describe(_ model: NLEmbedding?) -> [String: Any] {
        guard let model else { return ["available": false] }
        let vector = model.vector(for: text)
        return ["available": true, "revision": model.revision, "dimension": model.dimension,
            "vectorCount": vector?.count ?? 0, "vectorFinite": vector?.allSatisfy(\.isFinite) ?? false,
            "vectorNorm": vector.map { sqrt($0.reduce(0) { $0 + $1 * $1 }) } ?? 0]
    }

    static func snapshot() -> [String: Any] {
        // Observe default selection before asking for a specific revision.
        let initial = describe(NLEmbedding.sentenceEmbedding(for: .english))
        let revisions = Array(NLEmbedding.supportedSentenceEmbeddingRevisions(for: .english))
        let current = NLEmbedding.currentSentenceEmbeddingRevision(for: .english)
        let pinned = describe(NLEmbedding.sentenceEmbedding(for: .english, revision: 1))
        let contextual = NLContextualEmbedding(language: .english)
        return ["defaultBefore": initial, "supportedRevisions": revisions,
            "currentRevision": current, "explicitRevision1": pinned,
            "defaultAfter": describe(NLEmbedding.sentenceEmbedding(for: .english)),
            "wordEmbeddingAvailable": NLEmbedding.wordEmbedding(for: .english) != nil,
            "recognizedLanguage": NLLanguageRecognizer.dominantLanguage(for: text)?.rawValue ?? "none",
            "contextualAssetsAvailable": contextual?.hasAvailableAssets ?? false,
            "contextualIdentifier": contextual?.modelIdentifier ?? "none"]
    }

    @MainActor static func execute() async {
        let args = CommandLine.arguments
        guard let index = args.firstIndex(of: "--unit"), index + 1 < args.count,
              ["snapshot-0", "snapshot-1"].contains(args[index+1]) else { exit(2) }
        let unit = args[index+1]
        let first = snapshot()
        do {
            try await Task.sleep(for: .seconds(2))
            let result: [String: Any] = ["schemaVersion": 1, "unit": unit, "syntheticOnly": true,
                "os": ProcessInfo.processInfo.operatingSystemVersionString, "status": "ok",
                "result": ["immediate": first, "afterTwoSeconds": snapshot(), "assetDownloadRequested": false]]
            let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
            #if os(iOS)
            let destination = URL.documentsDirectory.appendingPathComponent("unit-" + unit + ".json")
            guard !FileManager.default.fileExists(atPath: destination.path) else { exit(3) }
            try data.write(to: destination, options: [.atomic])
            #endif
            print("IOS27_RESULT " + String(decoding: data, as: UTF8.self)); fflush(stdout); exit(0)
        } catch { fputs("Sentence probe failed: \(error)\n", stderr); exit(4) }
    }
}

#if os(iOS)
@main struct SentenceProbeApp: App {
    var body: some Scene {
        WindowGroup { Text("Sentence embedding diagnostic\nFictional input only").task { await SentenceProbe.execute() } }
    }
}
#else
@main struct SentenceProbeCommand {
    static func main() async { await SentenceProbe.execute() }
}
#endif
