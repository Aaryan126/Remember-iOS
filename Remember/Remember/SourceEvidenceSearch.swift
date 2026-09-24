import Foundation

/// Searchable source facts only. Generated titles, summaries and tags deliberately
/// have no representation here, so they cannot accidentally become evidence.
nonisolated struct SourceEvidenceSnapshot: Sendable {
    let memoryID: UUID
    let originalFilename: String
    let extractedText: String?
    let userCaption: String?
    let isArchived: Bool
    let analysisIsPartial: Bool
}

nonisolated enum SourceEvidenceEventKind: Sendable {
    case capture, imported, revision, enrichment, metadata, processing, archive, restore, organization
}

nonisolated struct SourceEvidenceRecord: Sendable {
    let sequence: Int64
    let id: UUID
    let timestamp: Date
    let kind: SourceEvidenceEventKind
    let memoryID: UUID?
    let sourceRevisionID: UUID?
    let restoredFromRevisionID: UUID?
    let snapshot: SourceEvidenceSnapshot?
}

nonisolated enum SourceEvidenceScope: String, Sendable {
    case current, includeHistory
}

nonisolated struct SourceEvidenceRequest: Sendable {
    let query: String
    var scope: SourceEvidenceScope = .current
    var throughSequence: Int64? = nil
    var memoryIDs: Set<UUID>? = nil
    // An explicit caller exclusion, not a claim that an erasure registry exists.
    var excludedMemoryIDs: Set<UUID> = []
    var offset = 0
    var limit = 30

    func validate() throws {
        guard query.count <= 512, offset >= 0, (1...100).contains(limit), (throughSequence ?? 0) >= 0 else {
            throw SourceEvidenceError.invalidRequest
        }
    }
}

nonisolated enum SourceEvidenceField: String, Sendable {
    case extractedText, userCaption
}

nonisolated struct SourceEvidenceHit: Identifiable, Sendable {
    nonisolated struct ID: Hashable, Sendable {
        let memoryID: UUID
        let revisionID: UUID
        let snapshotID: UUID
        let field: SourceEvidenceField
        let ordinal: Int
    }

    let id: ID
    let revision: Int
    let sourceSequence: Int64
    let snapshotSequence: Int64
    let sourceDate: Date
    let snapshotDate: Date
    let quote: String
    /// A retained-text location only; not an original page, media timestamp or region.
    let locator: String
    let isCurrentVersion: Bool
    let isArchived: Bool
    let importedHistoryGap: Bool
    let analysisIsPartial: Bool
    /// A sorting weight, never a probability of correctness or answer confidence.
    let lexicalScore: Double

    // Searching ledger text does not check the vault or original media files.
    var originalAssetAvailability: String { "notChecked" }
    var mediaLocatorAvailability: String { "notRetainedInLedger" }
}

nonisolated struct SourceEvidencePage: Sendable {
    let throughSequence: Int64
    let scope: SourceEvidenceScope
    let totalMatchingPassages: Int
    let hits: [SourceEvidenceHit]
}

nonisolated enum SourceEvidenceError: Error, Equatable {
    case invalidRequest
    case invalidLedger
    case safetyLimitExceeded
}

/// A pure, cancellable projection: no writes, embeddings, model calls or inferred
/// relationships. It is intentionally separate from the app's ordinary search.
nonisolated enum SourceEvidenceSearch {
    static let maximumEvents = 100_000
    static let maximumFieldBytes = 4 * 1_024 * 1_024
    static let maximumSearchBytes = 32 * 1_024 * 1_024

    private struct Version {
        let source: SourceEvidenceRecord
        let revision: Int
        let importedHistoryGap: Bool
        var evidence: SourceEvidenceRecord
        var memory: SourceEvidenceSnapshot
    }

    static func search(
        records: [SourceEvidenceRecord],
        request: SourceEvidenceRequest,
        checkCancellation: () throws -> Void = { try Task.checkCancellation() }
    ) throws -> SourceEvidencePage {
        try checkCancellation()
        try request.validate()
        guard records.count <= maximumEvents else { throw SourceEvidenceError.safetyLimitExceeded }
        let boundary = min(request.throughSequence ?? Int64.max, records.last?.sequence ?? 0)
        var previous: Int64 = 0
        var seen = Set<UUID>()
        var versions: [UUID: Version] = [:]
        var latest: [UUID: UUID] = [:]
        var archived: [UUID: Bool] = [:]

        for record in records {
            try checkCancellation()
            guard record.sequence > previous, seen.insert(record.id).inserted else {
                throw SourceEvidenceError.invalidLedger
            }
            previous = record.sequence
            guard record.sequence <= boundary else { continue }
            guard let memory = record.snapshot else {
                guard record.kind == .organization ||
                        ([.archive, .restore].contains(record.kind) && record.memoryID == nil) else {
                    throw SourceEvidenceError.invalidLedger
                }
                continue
            }
            guard record.memoryID == memory.memoryID, record.kind != .organization else {
                throw SourceEvidenceError.invalidLedger
            }
            if [.capture, .imported, .revision].contains(record.kind) {
                let predecessor = latest[memory.memoryID].flatMap { versions[$0] }
                if record.kind == .revision {
                    guard let predecessor, memory.isArchived == archived[memory.memoryID] else {
                        throw SourceEvidenceError.invalidLedger
                    }
                    if record.sourceRevisionID != predecessor.source.id {
                        // Older restoreRevision writes referencedEventID but omits
                        // sourceRevisionID. Accept only that explicit, verifiable
                        // restore shape, not arbitrary orphan revisions. Restoration
                        // copies the source event snapshot, not later enrichment.
                        guard record.sourceRevisionID == nil,
                              let restoredID = record.restoredFromRevisionID,
                              let original = versions[restoredID]?.source.snapshot,
                              original.memoryID == memory.memoryID,
                              original.originalFilename == memory.originalFilename,
                              original.extractedText == memory.extractedText,
                              original.userCaption == memory.userCaption,
                              !memory.isArchived else {
                            throw SourceEvidenceError.invalidLedger
                        }
                    }
                } else {
                    guard predecessor == nil, record.sourceRevisionID == nil else {
                        throw SourceEvidenceError.invalidLedger
                    }
                }
                versions[record.id] = Version(
                    source: record, revision: (predecessor?.revision ?? -1) + 1,
                    importedHistoryGap: predecessor?.importedHistoryGap ?? (record.kind == .imported),
                    evidence: record, memory: memory
                )
                latest[memory.memoryID] = record.id
                archived[memory.memoryID] = memory.isArchived
            } else {
                guard let revisionID = record.sourceRevisionID, var version = versions[revisionID],
                      version.memory.memoryID == memory.memoryID,
                      version.memory.originalFilename == memory.originalFilename else {
                    throw SourceEvidenceError.invalidLedger
                }
                if [.archive, .restore].contains(record.kind) {
                    guard latest[memory.memoryID] == revisionID,
                          memory.isArchived == (record.kind == .archive) else {
                        throw SourceEvidenceError.invalidLedger
                    }
                    archived[memory.memoryID] = memory.isArchived
                } else if latest[memory.memoryID] == revisionID {
                    guard memory.isArchived == archived[memory.memoryID] else {
                        throw SourceEvidenceError.invalidLedger
                    }
                }
                // Processing/metadata may repeat or change generated fields. Only
                // explicitly attributed enrichment can replace retained evidence.
                if record.kind == .enrichment && (
                    version.memory.extractedText != memory.extractedText ||
                    version.memory.userCaption != memory.userCaption ||
                    version.memory.analysisIsPartial != memory.analysisIsPartial
                ) {
                    version.evidence = record
                    version.memory = memory
                    versions[revisionID] = version
                }
            }
        }

        let query = normalized(request.query)
        let queryTokens = tokens(query)
        var matcher = SearchTextMatcher(query: request.query)
        var hits: [SourceEvidenceHit] = []
        var searchedBytes = 0
        for version in versions.values.sorted(by: { $0.source.sequence < $1.source.sequence }) {
            try checkCancellation()
            let memory = version.memory
            let current = latest[memory.memoryID] == version.source.id
            let isArchived = archived[memory.memoryID] ?? false
            guard !queryTokens.isEmpty, !request.excludedMemoryIDs.contains(memory.memoryID),
                  request.memoryIDs.map({ $0.contains(memory.memoryID) }) ?? true,
                  request.scope == .includeHistory || (current && !isArchived) else { continue }
            var fields: [(SourceEvidenceField, String)] = []
            if let text = memory.extractedText, !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                fields.append((.extractedText, text))
            }
            if let caption = memory.userCaption, !caption.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
               !fields.contains(where: { $0.1 == caption }) {
                fields.append((.userCaption, caption))
            }
            for (field, text) in fields {
                let bytes = text.utf8.count
                guard bytes <= maximumFieldBytes, bytes <= maximumSearchBytes - searchedBytes else {
                    throw SourceEvidenceError.safetyLimitExceeded
                }
                searchedBytes += bytes
                let chunks = MemoryTextChunker.chunks(
                    from: text, locatorPrefix: "Retained \(field.rawValue)", extractionMethod: .plainText
                )
                for chunk in chunks {
                    try checkCancellation()
                    let match = try matcher.match(in: chunk.text, checkCancellation: checkCancellation)
                    guard match.coverage > 0 else { continue }
                    let score = match.passageScore
                    hits.append(SourceEvidenceHit(
                        id: .init(memoryID: memory.memoryID, revisionID: version.source.id,
                                  snapshotID: version.evidence.id, field: field, ordinal: chunk.ordinal),
                        revision: version.revision, sourceSequence: version.source.sequence,
                        snapshotSequence: version.evidence.sequence, sourceDate: version.source.timestamp,
                        snapshotDate: version.evidence.timestamp, quote: chunk.text, locator: chunk.locator,
                        isCurrentVersion: current, isArchived: isArchived,
                        importedHistoryGap: version.importedHistoryGap,
                        analysisIsPartial: memory.analysisIsPartial, lexicalScore: score
                    ))
                }
            }
        }
        try checkCancellation()
        hits.sort {
            if $0.lexicalScore != $1.lexicalScore { return $0.lexicalScore > $1.lexicalScore }
            if $0.sourceSequence != $1.sourceSequence { return $0.sourceSequence > $1.sourceSequence }
            if $0.id.field != $1.id.field { return $0.id.field.rawValue < $1.id.field.rawValue }
            return $0.id.ordinal < $1.id.ordinal
        }
        return SourceEvidencePage(throughSequence: boundary, scope: request.scope,
                                  totalMatchingPassages: hits.count,
                                  hits: Array(hits.dropFirst(request.offset).prefix(request.limit)))
    }

    private static func normalized(_ text: String) -> String {
        text.folding(options: [.caseInsensitive, .diacriticInsensitive], locale: Locale(identifier: "en_US_POSIX"))
            .lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private static func tokens(_ text: String) -> Set<String> {
        Set(text.split(whereSeparator: { !$0.isLetter && !$0.isNumber }).map(String.init))
    }
}
