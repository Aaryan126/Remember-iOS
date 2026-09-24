import Foundation

// Experiment-only projection. The immutable production ledger remains the authority.
enum HistoryScope: String, Codable { case current, includeHistory }

struct HistoryRequest {
    var scope: HistoryScope = .current
    var throughSequence: Int64
    var sourceIDs: Set<UUID>? = nil
    var limit: Int = 10_000
    // An external erasure registry must supply these IDs: production delete is archive.
    var tombstonedSourceIDs: Set<UUID> = []
}

struct HistoryCandidate: Codable, Equatable {
    let id: String
    let sourceID: UUID
    let versionID: UUID
    let revision: Int
    let snapshotID: UUID
    let sourceSequence: Int64
    let snapshotSequence: Int64
    let ordinal: Int
    let quote: String
    let evidenceField: String
    let locator: String
    let locatorAvailability: String
    let originalAssetAvailability: String
    let mediaLocatorAvailability: String
    let isArchived: Bool
    let isCurrentVersion: Bool
    let importedHistoryGap: Bool
}

enum HistoryIndex {
    private struct Version {
        let event: ProvenanceEvent
        let revision: Int
        var snapshot: ProvenanceEvent
        var memory: MemoryItem
    }

    static func candidates(events: [ProvenanceEvent], request: HistoryRequest) throws -> [HistoryCandidate] {
        try diagnosticRequire(request.throughSequence >= 0 && request.limit >= 0 && request.limit <= 100_000,
                              "invalid history boundary or result limit")
        var previous: Int64 = 0
        var seen: Set<UUID> = []
        var versions: [UUID: Version] = [:]
        var latest: [UUID: UUID] = [:]
        var counts: [UUID: Int] = [:]
        var archive: [UUID: Bool] = [:]
        for event in events {
            guard let sequence = event.sequence else { throw DiagnosticFailure(description: "missing ledger sequence") }
            try diagnosticRequire(sequence > previous && seen.insert(event.id).inserted, "duplicate or unordered history ledger")
            previous = sequence
            // Never decode or associate future enrichment with this prefix.
            guard sequence <= request.throughSequence else { continue }
            let payload = try event.payload()
            guard let memory = payload.memory else {
                try diagnosticRequire(![.capture, .imported, .revision, .enrichment, .metadata, .processing].contains(event.kind)
                    && !([.archive, .restore].contains(event.kind) && event.memoryID != nil),
                    "source event is missing its memory snapshot")
                continue
            }
            try diagnosticRequire(event.memoryID == memory.id, "history payload/source identity mismatch")
            if [.capture, .imported, .revision].contains(event.kind) {
                if event.kind == .revision {
                    try diagnosticRequire(latest[memory.id] != nil && payload.sourceRevisionID == latest[memory.id],
                                          "revision has no current predecessor")
                } else {
                    try diagnosticRequire(latest[memory.id] == nil && payload.sourceRevisionID == nil,
                                          "duplicate capture/import or invalid initial predecessor")
                }
                let revision = counts[memory.id, default: -1] + 1
                counts[memory.id] = revision
                versions[event.id] = Version(event: event, revision: revision, snapshot: event, memory: memory)
                latest[memory.id] = event.id
                archive[memory.id] = memory.isArchived
            } else if let versionID = payload.sourceRevisionID, var version = versions[versionID] {
                try diagnosticRequire(version.memory.id == memory.id && version.memory.originalFilename == memory.originalFilename,
                                      "enrichment references a different source revision")
                if [.archive, .restore].contains(event.kind) {
                    try diagnosticRequire(latest[memory.id] == versionID && memory.isArchived == (event.kind == .archive),
                                          "archive/restore references stale revision or inconsistent state")
                    archive[memory.id] = memory.isArchived
                } else if latest[memory.id] == versionID {
                    try diagnosticRequire(memory.isArchived == archive[memory.id],
                                          "non-archive event unexpectedly changes archive state")
                }
                // Metadata/processing snapshots do not mint source evidence. Enrichment must
                // explicitly name a retained revision, including late work on an older one.
                if event.kind == .enrichment && (version.memory.extractedText != memory.extractedText
                    || version.memory.userCaption != memory.userCaption) {
                    version.snapshot = event
                    version.memory = memory
                    versions[versionID] = version
                }
            } else {
                throw DiagnosticFailure(description: "memory snapshot has no retained source revision")
            }
        }
        var result: [HistoryCandidate] = []
        let ordered = versions.values.sorted { $0.event.sequence! < $1.event.sequence! }
        for version in ordered {
            let memory = version.memory
            let isCurrent = latest[memory.id] == version.event.id
            let isArchived = archive[memory.id, default: false]
            guard !request.tombstonedSourceIDs.contains(memory.id),
                  request.sourceIDs.map({ $0.contains(memory.id) }) ?? true,
                  request.scope == .includeHistory || (isCurrent && !isArchived) else { continue }
            // Keep distinct caption evidence, but do not duplicate identical extracted text.
            var fields: [(String, String)] = []
            if let text = memory.extractedText, !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                fields.append(("extractedText", text))
            }
            if let caption = memory.userCaption, !caption.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
               !fields.contains(where: { $0.1 == caption }) { fields.append(("userCaption", caption)) }
            for (field, text) in fields {
                let drafts = MemoryTextChunker.chunks(from: text, locatorPrefix: "Retained \(field)", extractionMethod: .plainText)
                for draft in drafts {
                    let identity = [memory.id.uuidString, version.event.id.uuidString, version.snapshot.id.uuidString,
                                    field, String(draft.ordinal)].joined(separator: ":")
                    result.append(HistoryCandidate(id: diagnosticHash(Data(identity.utf8)), sourceID: memory.id,
                        versionID: version.event.id, revision: version.revision, snapshotID: version.snapshot.id,
                        sourceSequence: version.event.sequence!, snapshotSequence: version.snapshot.sequence!,
                        ordinal: draft.ordinal, quote: draft.text, evidenceField: field, locator: draft.locator,
                        locatorAvailability: "retained-ledger-text", originalAssetAvailability: "unavailable",
                        mediaLocatorAvailability: "unavailable", isArchived: isArchived, isCurrentVersion: isCurrent,
                        importedHistoryGap: version.event.kind == .imported))
                }
            }
        }
        // Sequence/field/ordinal order is stable enumeration, not relevance ranking.
        return Array(result.prefix(request.limit))
    }
}
