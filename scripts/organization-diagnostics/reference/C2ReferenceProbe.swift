// Native Mac adaptation of ProjectGraphService.place's embedding-only branch.
// ProjectEmbedding, ProjectMath and ProjectTopicEvidence are inserted verbatim by
// c2_reference.py. This is not a full graph replay: there is no reasoning,
// preserved manual assignment, old singleton candidate, or periodic merge/split.
// Inputs are already active clusters; lexical thread/source IDs replace UUID order.
import Foundation
import NaturalLanguage

private struct InputEmbedding: Decodable {
    let contextual: [Float]
    let sentence: [Float]?
    let space: String

    var value: ProjectEmbedding {
        ProjectEmbedding(vector: contextual, space: space, semanticVector: sentence)
    }
}

private struct Source: Decodable {
    let id: String
    let text: String
    let embedding: InputEmbedding?
}

private struct Request: Decodable {
    let source: Source
    let clusters: [String: [Source]]
}

private struct Candidate: Encodable {
    let threadID: String
    let contextualScore: Double
    let semanticScore: Double
    let grounded: Bool
}

private struct Grounding: Encodable {
    let threadID: String
    let sourceTerms: [String]
    let members: [MemberGrounding]
    let allMembersSupported: Bool
}

private struct MemberGrounding: Encodable {
    let sourceID: String
    let terms: [String]
    let sharedTerms: [String]
    let supported: Bool
}

private struct Response: Encodable {
    let selected: [String]
    let candidates: [Candidate]
    let grounding: [Grounding]
    let scores: [String: Double]
    let reference = "production embedding-only placement, no reasoning or batch maintenance"
    let policy = ProjectMath.policy
    let adaptations = [
        "Native Mac NLTagger with supplied embeddings; no embedding model requests or downloads.",
        "Active clusters only, source-ID evidence order, lexical thread-ID ties in place of UUID ties.",
        "New capture only; no preserved assignments, old singleton candidates, or graph persistence."
    ]
}

private func place(_ request: Request) -> Response {
    let evidence = ProjectTopicEvidence(request.source.text)
    let orderedClusters = request.clusters.keys.sorted()
    let grounding = orderedClusters.map { threadID -> Grounding in
        let members = request.clusters[threadID, default: []].sorted { $0.id < $1.id }
        let details = members.map { member -> MemberGrounding in
            let other = ProjectTopicEvidence(member.text)
            return MemberGrounding(sourceID: member.id, terms: other.terms.sorted(),
                sharedTerms: evidence.terms.intersection(other.terms).sorted(),
                supported: evidence.supports(other))
        }
        return Grounding(threadID: threadID, sourceTerms: evidence.terms.sorted(),
            members: details, allMembersSupported: details.allSatisfy(\.supported))
    }
    let groundedClusters = Set(grounding.filter(\.allMembersSupported).map(\.threadID))
    guard let embedding = request.source.embedding?.value else {
        return Response(selected: [], candidates: [], grounding: grounding, scores: [:])
    }
    let candidates = orderedClusters.compactMap { threadID -> Candidate? in
        let members = request.clusters[threadID, default: []].sorted { $0.id < $1.id }
        let compatible = members.compactMap { $0.embedding?.value }.filter { $0.space == embedding.space }
        guard compatible.count == members.count,
              ProjectMath.coherent(compatible),
              ProjectMath.supports(embedding, members: compatible),
              let centroid = ProjectMath.centroid(compatible.map(\.vector)) else { return nil }
        return Candidate(threadID: threadID,
            contextualScore: ProjectMath.cosine(embedding.vector, centroid),
            semanticScore: ProjectMath.semanticScore(embedding, members: compatible),
            grounded: groundedClusters.contains(threadID))
    }.sorted {
        $0.contextualScore == $1.contextualScore
            ? $0.threadID < $1.threadID : $0.contextualScore > $1.contextualScore
    }
    var scores = Dictionary(uniqueKeysWithValues: candidates.prefix(2).map { ($0.threadID, $0.contextualScore) })
    let grounded = candidates.filter(\.grounded)
    var selected: [String] = []
    if ProjectMath.clearWinner(grounded.map(\.contextualScore)), let winner = grounded.first,
       winner.semanticScore >= ProjectMath.semanticThreshold {
        selected = [winner.threadID]
        scores["sentenceSimilarity"] = winner.semanticScore
    }
    return Response(selected: selected, candidates: candidates, grounding: grounding, scores: scores)
}

@main
private enum C2ReferenceProbe {
    static func main() {
        let decoder = JSONDecoder()
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        while let line = readLine() {
            do {
                let request = try decoder.decode(Request.self, from: Data(line.utf8))
                let response = place(request)
                let data = try encoder.encode(response)
                FileHandle.standardOutput.write(data + Data([10]))
            } catch {
                // Do not print source text or decoder context to stderr.
                FileHandle.standardOutput.write(Data("{\"error\":\"invalid_reference_request\"}\n".utf8))
            }
        }
    }
}
