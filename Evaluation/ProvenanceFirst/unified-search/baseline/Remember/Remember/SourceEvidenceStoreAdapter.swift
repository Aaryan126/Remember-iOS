import Foundation

/// Additive foundation only: no UI calls this service yet. In contrast to ordinary
/// search it never synchronizes indexes or starts an embedding/model request.
actor SourceEvidenceSearchService {
    private let store: MemoryStore

    init(store: MemoryStore) {
        self.store = store
    }

    func search(_ request: SourceEvidenceRequest) async throws -> SourceEvidencePage {
        try Task.checkCancellation()
        try request.validate()
        let events = try await store.provenanceEvents()
        let records = try SourceEvidenceStoreAdapter.records(events, through: request.throughSequence)
        return try SourceEvidenceSearch.search(records: records, request: request)
    }
}

nonisolated enum SourceEvidenceStoreAdapter {
    static func records(_ events: [ProvenanceEvent], through boundary: Int64?) throws -> [SourceEvidenceRecord] {
        guard events.count <= SourceEvidenceSearch.maximumEvents else {
            throw SourceEvidenceError.safetyLimitExceeded
        }
        return try events.map { event in
            try Task.checkCancellation()
            guard let sequence = event.sequence else { throw SourceEvidenceError.invalidLedger }
            // Leave future payloads undecoded, while still allowing the projection
            // to validate ordering/unique event IDs across the supplied ledger.
            let payload = sequence <= (boundary ?? Int64.max) ? try event.payload() : nil
            return SourceEvidenceRecord(
                sequence: sequence, id: event.id, timestamp: event.timestamp,
                kind: kind(event.kind), memoryID: event.memoryID,
                sourceRevisionID: payload?.sourceRevisionID,
                restoredFromRevisionID: event.kind == .revision && event.origin == "user" && payload?.memory?.kind == .text
                    ? payload?.referencedEventID : nil,
                snapshot: payload?.memory.map { memory in
                    SourceEvidenceSnapshot(
                        memoryID: memory.id, originalFilename: memory.originalFilename,
                        extractedText: memory.extractedText, userCaption: memory.userCaption,
                        isArchived: memory.isArchived, analysisIsPartial: memory.analysisIsPartial
                    )
                }
            )
        }
    }

    private static func kind(_ kind: ProvenanceKind) -> SourceEvidenceEventKind {
        switch kind {
        case .capture: .capture
        case .imported: .imported
        case .revision: .revision
        case .enrichment: .enrichment
        case .metadata: .metadata
        case .processing: .processing
        case .archive: .archive
        case .restore: .restore
        case .placement, .rename, .merge, .splitProposal, .split, .dismiss, .revert, .recap, .checkpoint:
            .organization
        }
    }
}
