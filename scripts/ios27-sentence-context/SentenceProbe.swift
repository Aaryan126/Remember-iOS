import Foundation
import NaturalLanguage
import Darwin
#if os(iOS)
import SwiftUI
#endif

struct Observation: Codable, Sendable {
    let name: String
    let available: Bool
    let mainThread: Bool
    let revision: Int?
    let dimension: Int?
}
nonisolated func lookup(_ name: String, explicit: Bool = false) -> Observation {
    let model = explicit ? NLEmbedding.sentenceEmbedding(for: .english, revision: 1) : NLEmbedding.sentenceEmbedding(for: .english)
    return Observation(name: name, available: model != nil, mainThread: Thread.isMainThread,
                       revision: model?.revision, dimension: model?.dimension)
}
actor Worker {
    func check() async throws -> [Observation] {
        _ = NLLanguageRecognizer.dominantLanguage(for: "The fictional Cedar meeting is scheduled for Friday.")
        var results = [lookup("actor-first"), lookup("actor-second")]
        try await Task.sleep(for: .milliseconds(200))
        results.append(lookup("actor-after200ms"))
        results.append(lookup("actor-explicit", explicit: true))
        return results
    }
}
enum SentenceProbe {
    @MainActor static func execute() async {
        let args = CommandLine.arguments
        guard let i = args.firstIndex(of: "--unit"), i+1 < args.count,
              ["actor-first", "main-first"].contains(args[i+1]) else { exit(2) }
        let unit = args[i+1]
        do {
            var observations: [Observation] = []
            if unit == "actor-first" { observations += try await Worker().check() }
            _ = NLLanguageRecognizer.dominantLanguage(for: "The fictional Cedar meeting is scheduled for Friday.")
            observations += [lookup("main-first"), lookup("main-second")]
            if unit == "main-first" { observations += try await Worker().check() }
            observations.append(lookup("main-explicit", explicit: true))
            struct Result: Encodable {
                let schemaVersion = 1; let syntheticOnly = true; let status = "ok"
                let unit: String; let result: [Observation]
            }
            let data = try JSONEncoder().encode(Result(unit: unit, result: observations))
            #if os(iOS)
            let url = URL.documentsDirectory.appendingPathComponent("unit-"+unit+".json")
            guard !FileManager.default.fileExists(atPath: url.path) else { exit(3) }
            try data.write(to: url, options: [.atomic])
            #endif
            print("IOS27_RESULT "+String(decoding: data,as:UTF8.self));fflush(stdout);exit(0)
        } catch { fputs("Context diagnostic failed: \(error)\n",stderr);exit(4) }
    }
}
#if os(iOS)
@main struct SentenceProbeApp: App {
    var body: some Scene { WindowGroup { Text("Sentence context diagnostic").task { await SentenceProbe.execute() } } }
}
#else
@main struct SentenceProbeCommand { static func main() async { await SentenceProbe.execute() } }
#endif
