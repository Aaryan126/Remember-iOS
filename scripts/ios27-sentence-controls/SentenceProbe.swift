import Foundation
import NaturalLanguage
import Darwin
#if os(iOS)
import SwiftUI
#endif

enum SentenceProbe {
    static let units = ["default-only", "revision-first"]
    static func describe(_ model: NLEmbedding?) -> [String: Any] {
        guard let model else { return ["available": false] }
        let vector = model.vector(for: "The fictional Cedar project meeting is scheduled for Friday.")
        return ["available": true, "revision": model.revision, "dimension": model.dimension,
            "vectorCount": vector?.count ?? 0, "finite": vector?.allSatisfy(\.isFinite) ?? false,
            "vectorNorm": vector.map { sqrt($0.reduce(0) { $0 + $1 * $1 }) } ?? 0]
    }
    @MainActor static func execute() async {
        let args = CommandLine.arguments
        guard let i = args.firstIndex(of: "--unit"), i+1 < args.count, units.contains(args[i+1]) else { exit(2) }
        let unit = args[i+1]
        var observations: [[String: Any]] = []
        if unit == "revision-first" {
            observations.append(["call": "explicitRevision1", "model": describe(NLEmbedding.sentenceEmbedding(for: .english, revision: 1))])
        }
        observations.append(["call": "defaultFirst", "model": describe(NLEmbedding.sentenceEmbedding(for: .english))])
        observations.append(["call": "defaultSecondImmediate", "model": describe(NLEmbedding.sentenceEmbedding(for: .english))])
        do {
            try await Task.sleep(for: .seconds(2))
            observations.append(["call": "defaultAfterTwoSeconds", "model": describe(NLEmbedding.sentenceEmbedding(for: .english))])
            let result: [String: Any] = ["schemaVersion": 1, "syntheticOnly": true, "unit": unit,
                "status": "ok", "os": ProcessInfo.processInfo.operatingSystemVersionString,
                "result": ["observations": observations, "assetDownloadRequested": false]]
            let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
            #if os(iOS)
            let url = URL.documentsDirectory.appendingPathComponent("unit-"+unit+".json")
            guard !FileManager.default.fileExists(atPath: url.path) else { exit(3) }
            try data.write(to: url, options: [.atomic])
            #endif
            print("IOS27_RESULT " + String(decoding: data, as: UTF8.self)); fflush(stdout); exit(0)
        } catch { fputs("Sentence control failed: \(error)\n", stderr); exit(4) }
    }
}
#if os(iOS)
@main struct SentenceProbeApp: App {
    var body: some Scene {
        WindowGroup { Text("Sentence lookup controls\nFictional input only").task { await SentenceProbe.execute() } }
    }
}
#else
@main struct SentenceProbeCommand {
    static func main() async { await SentenceProbe.execute() }
}
#endif
