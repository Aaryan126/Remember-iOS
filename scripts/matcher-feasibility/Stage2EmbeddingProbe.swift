import Foundation
import NaturalLanguage

// The build copies the production embedding provider verbatim into a generated
// companion file. Only its notification dependency is supplied by this probe.
enum ProjectPreferences {
    static let embeddingsAvailable = Notification.Name("matcher.probe.assetsAvailable")
}

struct ProbeRequest: Decodable { let id: String; let text: String }
struct ProbeResponse: Encodable {
    let id: String
    let status: String
    let language: String?
    let space: String?
    let expectedSpace: String?
    let contextual: [Float]?
    let sentence: [Float]?
    let seconds: Double
    let error: String?
}

@main
struct Stage2EmbeddingProbe {
    static func main() async throws {
        let provider = AppleProjectEmbedding()
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        while let line = readLine() {
            let request = try JSONDecoder().decode(ProbeRequest.self, from: Data(line.utf8))
            let start = ContinuousClock.now
            let language = NLLanguageRecognizer.dominantLanguage(for: request.text)?.rawValue
            var value: ProjectEmbedding?
            var failure: String?
            do { value = try await provider.embedding(for: request.text) }
            catch { failure = String(describing: error) }
            let elapsed = start.duration(to: .now).components
            let expected = await provider.expectedSpace(for: request.text)
            let result = ProbeResponse(id: request.id,
                status: failure != nil ? "error" : value == nil ? "unavailable" : "ok",
                language: language, space: value?.space, expectedSpace: expected,
                contextual: value?.vector, sentence: value?.semanticVector,
                seconds: Double(elapsed.seconds) + Double(elapsed.attoseconds) / 1e18,
                error: failure)
            let data = try encoder.encode(result)
            FileHandle.standardOutput.write(data + Data([10]))
        }
    }
}
