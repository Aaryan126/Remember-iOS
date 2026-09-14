import Foundation
import NaturalLanguage

enum ProjectPreferences {
    static let embeddingsAvailable = Notification.Name("matcher.validation.assetsAvailable")
}

struct Request: Decodable { let id: String; let text: String }
struct Response: Encodable {
    let id: String
    let status: String
    let space: String?
    let expectedSpace: String?
    let contextual: [Float]?
    let sentence: [Float]?
}

@main
struct ValidationEmbeddingProbe {
    static func main() async throws {
        let provider = AppleProjectEmbedding()
        let encoder = JSONEncoder()
        while let line = readLine() {
            let request = try JSONDecoder().decode(Request.self, from: Data(line.utf8))
            // expectedSpace checks installed assets. Never enter the production
            // provider's missing-assets request path during this offline experiment.
            let expected = await provider.expectedSpace(for: request.text)
            let value = expected == nil ? nil : try await provider.embedding(for: request.text)
            let result = Response(id: request.id, status: value == nil ? "unavailable" : "ok",
                                  space: value?.space, expectedSpace: expected,
                                  contextual: value?.vector, sentence: value?.semanticVector)
            FileHandle.standardOutput.write(try encoder.encode(result) + Data([10]))
        }
    }
}
