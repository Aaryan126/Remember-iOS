import Foundation
import NaturalLanguage

/// Live organizer. Existing placements are never migrated by changing model versions.
/// The old ProjectGraphService remains a historical/test reference, not a fallback.
actor D3ProjectOrganizer {
    private let store: MemoryStore
    private let embeddings: any ProjectEmbeddingProviding
    private let matcher: any D3Matching
    private let supportsText: @Sendable (String) -> Bool
    private var cached: [UUID: (text: String, source: D3Source)] = [:]

    init(store: MemoryStore, embeddings: any ProjectEmbeddingProviding = AppleProjectEmbedding(),
         matcher: any D3Matching = D3PairMatcher(),
         supportsText: @escaping @Sendable (String) -> Bool = {
             !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && $0.unicodeScalars.count <= 16_000
                 && NLLanguageRecognizer.dominantLanguage(for: $0) == .english
         }) {
        self.store = store
        self.embeddings = embeddings
        self.matcher = matcher
        self.supportsText = supportsText
    }

    func synchronize(retryUnavailable: Bool = false) async throws {
        let events = try await store.provenanceEvents()
        let snapshot = try ProvenanceSnapshot.replay(events)
        cached = cached.filter { snapshot.memories[$0.key]?.isArchived == false }
        let ordered = snapshot.memories.values.filter { !$0.isArchived && $0.state == .indexed }.sorted {
            $0.createdAt == $1.createdAt ? $0.id.uuidString < $1.id.uuidString : $0.createdAt < $1.createdAt
        }
        for memory in ordered {
            try Task.checkCancellation()
            let latest = try await store.provenanceEvents()
            guard let source = latest.last(where: { $0.memoryID == memory.id && [.enrichment, .revision, .imported].contains($0.kind) }) else { continue }
            let prior = latest.last { $0.memoryID == memory.id && $0.kind == .placement }
            if let prior {
                let payload = try prior.payload()
                // Do not revisit older-policy placements or reassign an edited memory automatically.
                if payload.model != D3OrganizationPolicy.version || payload.sourceRevisionID != source.id || payload.scores["completed"] == 1 { continue }
                if !retryUnavailable && Date().timeIntervalSince(prior.timestamp) < 60 { continue }
            }
            try await place(memory: memory, source: source, events: latest)
        }
    }

    private func text(_ memory: MemoryItem) -> String {
        [memory.extractedText, memory.userCaption, memory.displayTitle].compactMap { $0 }
            .first { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty } ?? ""
    }

    private func encoded(_ memory: MemoryItem) async throws -> D3Source? {
        let value = text(memory)
        guard supportsText(value) else { return nil }
        if let entry = cached[memory.id], entry.text == value { return entry.source }
        guard let embedding = try await embeddings.embedding(for: value),
              embedding.space == D3OrganizationPolicy.embeddingSpace, let sentence = embedding.semanticVector,
              embedding.vector.count == 512, sentence.count == 512,
              ProjectMath.normalized(embedding.vector) != nil, ProjectMath.normalized(sentence) != nil else { return nil }
        let result = D3Source(text: value, contextual: embedding.vector, sentence: sentence, space: embedding.space)
        if cached.count >= 512 { cached.removeAll(keepingCapacity: true) }
        cached[memory.id] = (value, result)
        return result
    }

    private func place(memory: MemoryItem, source: ProvenanceEvent, events: [ProvenanceEvent]) async throws {
        let snapshot = try ProvenanceSnapshot.replay(events)
        guard let current = snapshot.memories[memory.id], !current.isArchived,
              current.originalFilename == memory.originalFilename else { return }
        let memory = current
        let old = snapshot.memberships[memory.id, default: [memory.id]].sorted { $0.uuidString < $1.uuidString }
        var payload = ProvenancePayload()
        payload.model = D3OrganizationPolicy.version
        payload.sourceRevisionID = source.id
        payload.sourceFilename = memory.originalFilename
        payload.previousAssignments = [memory.id.uuidString: old]
        payload.assignments = [memory.id.uuidString: old]
        payload.scores["completed"] = 1
        payload.rationale = "No unique corroborated D3 match; kept the existing thread."
        if snapshot.preservesOrganization(for: memory.id) {
            payload.rationale = "Preserved your explicit thread assignment."
        } else if !supportsText(text(memory)) {
            payload.rationale = "D3 currently supports English text up to 16,000 characters. Kept this capture separate; no cloud fallback was used."
        } else {
            let activity = try await store.startActivity(kind: .projectOrganization, memoryID: memory.id,
                sourceCount: 1, modelVersion: D3OrganizationPolicy.version)
            do {
                guard let query = try await encoded(memory) else { throw D3Error.invalidOutput }
                payload.vector = query.contextual
                payload.semanticVector = query.sentence
                payload.embeddingSpace = query.space
                let lexical = try await matcher.lexicalVector(query.text)
                var candidates: [D3OrganizationPolicy.Candidate] = []
                var sources: [UUID: D3Source] = [:]
                var memberCounts: [UUID: Int] = [:]
                let alreadyPlaced = Set(events.filter { $0.kind == .placement }.compactMap(\.memoryID))
                for member in snapshot.memories.values.sorted(by: { $0.id.uuidString < $1.id.uuidString }) where !member.isArchived && member.state == .indexed && member.id != memory.id {
                    try Task.checkCancellation()
                    // Batch imports follow the same ordered, observed-context rule as the replay.
                    guard alreadyPlaced.contains(member.id) || member.createdAt < memory.createdAt
                            || (member.createdAt == memory.createdAt && member.id.uuidString < memory.id.uuidString) else { continue }
                    let memberships = snapshot.memberships[member.id, default: [member.id]].filter { id in
                        !snapshot.archivedClusterIDs.contains(id) && snapshot.clusters[id]?.retired == false
                            && !old.contains { snapshot.blockedPairs.contains(ProvenanceSnapshot.pair($0, id)) }
                    }
                    guard !memberships.isEmpty else { continue }
                    for id in memberships { memberCounts[id, default: 0] += 1 }
                    guard let value = try await encoded(member), value.space == query.space else { continue }
                    sources[member.id] = value
                    candidates.append(.init(id: member.id, memberships: memberships,
                        contextual: try D3Features.cosine(query.contextual, value.contextual),
                        lexical: D3Features.lexicalCosine(lexical, try await matcher.lexicalVector(value.text))))
                }
                let retrieved = D3OrganizationPolicy.retrieve(candidates)
                var scores: [UUID: Double] = [:]
                for candidate in retrieved {
                    try Task.checkCancellation()
                    guard let value = sources[candidate.id] else { throw D3Error.invalidOutput }
                    scores[candidate.id] = try await matcher.score(query, value)
                }
                let decision = D3OrganizationPolicy.decide(retrieved: retrieved, memberCounts: memberCounts, scores: scores)
                payload.scores.merge(Dictionary(uniqueKeysWithValues: scores.map { ($0.key.uuidString, $0.value) })) { _, new in new }
                payload.scores["threshold"] = D3OrganizationPolicy.threshold
                if let selected = decision.selected {
                    payload.assignments[memory.id.uuidString] = [selected]
                    payload.rationale = "Local D3 matcher found one thread with corroborated support. No existing threads were merged."
                    let supporting = Set(decision.support[selected, default: []])
                    payload.citedEventIDs = supporting.compactMap { id in
                        events.last { $0.memoryID == id && [.enrichment, .revision, .imported].contains($0.kind) }?.id
                    }
                } else if decision.qualifying.count > 1 {
                    payload.rationale = "Several threads matched. Kept this capture separate for your review; no automatic merge."
                    payload.scores["qualifyingThreads"] = Double(decision.qualifying.count)
                }
                try await store.finishActivity(id: activity, status: .completed, sourceCount: retrieved.count + 1)
            } catch is CancellationError {
                try? await store.finishActivity(id: activity, status: .interrupted, failureCategory: "cancelled")
                throw CancellationError()
            } catch {
                try await store.finishActivity(id: activity, status: .failed, failureCategory: "local_matcher_unavailable")
                payload.scores["completed"] = 0
                payload.rationale = "Local D3 matching was unavailable. Retained the existing thread; no local-reasoner or cloud fallback was used."
            }
        }
        // Enrichment can improve a newly captured singleton's title, but must never rename
        // an existing multi-memory thread or overwrite an explicit user rename.
        if old == [memory.id], snapshot.members(of: memory.id).count == 1,
           !events.contains(where: { $0.kind == .rename && (try? $0.payload().clusterID) == memory.id }) {
            payload.clusterID = memory.id
            payload.title = memory.displayTitle
        }
        try Task.checkCancellation()
        try await store.appendProvenance(ProvenanceEvent(kind: .placement, memoryID: memory.id, payload: payload),
                                         expectedSequence: events.last?.sequence)
    }
}
