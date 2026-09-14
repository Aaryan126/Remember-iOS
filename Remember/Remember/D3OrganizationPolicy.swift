import Foundation

/// Native port of the frozen C3 top-five dual retrieval / two-of-three support policy.
nonisolated enum D3OrganizationPolicy {
    static let version = "d3-p2-seed29-corroborated-v1"
    static let threshold = 0.9804276486193665
    // P2's measured Apple representation. A future asset revision needs parity/evaluation,
    // not silent reuse of a classifier calibrated against different feature values.
    static let embeddingSpace = "apple-dual:en:5C45D94E-BAB4-4927-94B6-8B5745C46289:1:512:1:512:token64-sentence256-v3"

    struct Candidate: Sendable {
        let id: UUID
        let memberships: Set<UUID>
        let contextual: Double?
        let lexical: Double
    }

    struct Decision: Sendable {
        let selected: UUID?
        let qualifying: [UUID]
        let support: [UUID: [UUID]]
    }

    static func retrieve(_ candidates: [Candidate]) -> [Candidate] {
        var ranks: [UUID: Double] = [:]
        let channels = [candidates.filter { $0.contextual?.isFinite == true }.sorted {
            $0.contextual == $1.contextual ? $0.id.uuidString < $1.id.uuidString : $0.contextual! > $1.contextual!
        }, candidates.filter { $0.lexical.isFinite }.sorted {
            $0.lexical == $1.lexical ? $0.id.uuidString < $1.id.uuidString : $0.lexical > $1.lexical
        }]
        for channel in channels {
            for (rank, candidate) in channel.prefix(5).enumerated() { ranks[candidate.id, default: 0] += 1 / Double(61 + rank) }
        }
        return candidates.filter { ranks[$0.id] != nil }.sorted {
            ranks[$0.id] == ranks[$1.id] ? $0.id.uuidString < $1.id.uuidString : ranks[$0.id]! > ranks[$1.id]!
        }
    }

    static func decide(retrieved: [Candidate], memberCounts: [UUID: Int], scores: [UUID: Double]) -> Decision {
        let threads = Set(retrieved.flatMap(\.memberships)).sorted { $0.uuidString < $1.uuidString }
        var support: [UUID: [UUID]] = [:]
        var qualifying: [UUID] = []
        for thread in threads {
            guard let count = memberCounts[thread], count > 0 else { continue }
            let tested = retrieved.filter { $0.memberships.contains(thread) }.prefix(3)
            let matches = tested.compactMap { candidate -> UUID? in
                guard let score = scores[candidate.id], score.isFinite, (threshold...1).contains(score) else { return nil }
                return candidate.id
            }
            support[thread] = matches
            if matches.count >= min(2, count) { qualifying.append(thread) }
        }
        return Decision(selected: qualifying.count == 1 ? qualifying[0] : nil, qualifying: qualifying, support: support)
    }
}
