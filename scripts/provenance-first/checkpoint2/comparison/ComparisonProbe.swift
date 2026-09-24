import Foundation

struct CandidateInput: Decodable {
    let id: UUID
    let memberships: [UUID]
    let contextual: Double?
    let lexical: Double
    let score: Double
}
struct DocumentInput: Decodable {
    let id: String
    let text: String
    let revision: Int
    let locator: String
    let created: Int
}
struct Request: Decodable {
    let kind: String
    let candidates: [CandidateInput]?
    let memberCounts: [String: Int]?
    let query: String?
    let documents: [DocumentInput]?
}
struct Hit {
    let document: DocumentInput
    let chunk: MemoryChunkDraft
    let score: Double
}
enum ProbeError: Error { case invalidRequest }

@main
struct ComparisonProbe {
    static func main() throws {
        while let line = readLine() {
            let input = try JSONDecoder().decode(Request.self, from: Data(line.utf8))
            var output: [String: Any] = ["locale": Locale.current.identifier]
            switch input.kind {
            case "metadata": break
            case "decide":
                guard let inputs = input.candidates, let counts = input.memberCounts else { throw ProbeError.invalidRequest }
                let candidates = inputs.map { D3OrganizationPolicy.Candidate(id: $0.id,
                    memberships: Set($0.memberships), contextual: $0.contextual, lexical: $0.lexical) }
                let retrieved = D3OrganizationPolicy.retrieve(candidates)
                let memberCounts = try Dictionary(uniqueKeysWithValues: counts.map { key, count in
                    guard let id = UUID(uuidString: key) else { throw ProbeError.invalidRequest }
                    return (id, count)
                })
                let scores = Dictionary(uniqueKeysWithValues: inputs.map { ($0.id, $0.score) })
                let decision = D3OrganizationPolicy.decide(retrieved: retrieved, memberCounts: memberCounts, scores: scores)
                output["retrieved"] = retrieved.map { $0.id.uuidString }
                output["qualifying"] = decision.qualifying.map(\.uuidString)
                output["selected"] = decision.selected.map { [$0.uuidString] } ?? []
                output["support"] = Dictionary(uniqueKeysWithValues: decision.support.map { ($0.key.uuidString, $0.value.map(\.uuidString)) })
            case "search":
                guard let query = input.query, let documents = input.documents else { throw ProbeError.invalidRequest }
                var hits: [Hit] = []
                for document in documents {
                    for chunk in MemoryTextChunker.chunks(from: document.text, locatorPrefix: document.locator, extractionMethod: .fixture) {
                        let score = LocalEvidence.lexicalCoverage(query: query, text: chunk.text)
                        if score > 0 { hits.append(Hit(document: document, chunk: chunk, score: score)) }
                    }
                }
                hits.sort { left, right in
                    if abs(left.score - right.score) > 0.000_1 { return left.score > right.score }
                    if left.document.created != right.document.created { return left.document.created > right.document.created }
                    if left.chunk.ordinal != right.chunk.ordinal { return left.chunk.ordinal < right.chunk.ordinal }
                    return left.document.id < right.document.id
                }
                var seen: Set<String> = []
                output["hits"] = hits.compactMap { hit -> [String: Any]? in
                    let identity = "\(hit.document.id):\(hit.document.revision)"
                    guard seen.insert(identity).inserted else { return nil }
                    return ["sourceId": hit.document.id, "revision": hit.document.revision,
                            "locator": hit.chunk.locator, "quote": hit.chunk.text, "ordinal": hit.chunk.ordinal, "score": hit.score]
                }
            default: throw ProbeError.invalidRequest
            }
            FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys]) + Data([10]))
        }
    }
}
