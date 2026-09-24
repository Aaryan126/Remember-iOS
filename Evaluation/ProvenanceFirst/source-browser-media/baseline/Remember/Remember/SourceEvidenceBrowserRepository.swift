import Foundation

nonisolated enum SourceEvidenceOriginalState: Equatable, Sendable {
    case available(URL)
    case unavailable
    case versionUnverified
}

nonisolated struct ResolvedSourceEvidence: Sendable {
    let hit: SourceEvidenceHit
    let memory: MemoryItem
    let fieldText: String
    let original: SourceEvidenceOriginalState
    let libraryHasChanged: Bool
}

nonisolated protocol SourceEvidenceBrowsing: Sendable {
    func search(_ request: SourceEvidenceRequest) async throws -> SourceEvidencePage
    func resolve(_ hit: SourceEvidenceHit, through sequence: Int64) async throws -> ResolvedSourceEvidence
}

/// Reading a search result must never resolve it through the mutable current-memory
/// table. The source event and attributed extraction snapshot are the authority.
actor SourceEvidenceBrowserRepository: SourceEvidenceBrowsing {
    private let store: MemoryStore
    private let searchService: SourceEvidenceSearchService
    private let originalsDirectory: URL

    init(store: MemoryStore, originalsDirectory: URL) {
        self.store = store
        self.searchService = SourceEvidenceSearchService(store: store)
        self.originalsDirectory = originalsDirectory
    }

    func search(_ request: SourceEvidenceRequest) async throws -> SourceEvidencePage {
        try await searchService.search(request)
    }

    func resolve(_ hit: SourceEvidenceHit, through sequence: Int64) async throws -> ResolvedSourceEvidence {
        try Task.checkCancellation()
        let events = try await store.provenanceEvents()
        let records = try SourceEvidenceStoreAdapter.records(events, through: sequence)
        // Validate the retained prefix without performing another text search.
        _ = try SourceEvidenceSearch.search(records: records,
            request: SourceEvidenceRequest(query: "", scope: .includeHistory, throughSequence: sequence))
        guard let source = events.first(where: { $0.id == hit.id.revisionID }),
              let snapshot = events.first(where: { $0.id == hit.id.snapshotID }),
              source.sequence == hit.sourceSequence, snapshot.sequence == hit.snapshotSequence,
              hit.sourceSequence <= hit.snapshotSequence, hit.snapshotSequence <= sequence,
              [.capture, .imported, .revision].contains(source.kind),
              source.memoryID == hit.id.memoryID, snapshot.memoryID == hit.id.memoryID,
              let originalMemory = try source.payload().memory else {
            throw SourceEvidenceError.invalidLedger
        }
        let payload = try snapshot.payload()
        guard let memory = payload.memory, memory.id == hit.id.memoryID,
              memory.originalFilename == originalMemory.originalFilename,
              snapshot.id == source.id || (snapshot.kind == .enrichment && payload.sourceRevisionID == source.id),
              let text = hit.id.field == .extractedText ? memory.extractedText : memory.userCaption,
              text.utf8.count <= SourceEvidenceSearch.maximumFieldBytes else {
            throw SourceEvidenceError.invalidLedger
        }
        let chunks = MemoryTextChunker.chunks(from: text, locatorPrefix: "Retained \(hit.id.field.rawValue)", extractionMethod: .plainText)
        guard let chunk = chunks.first(where: { $0.ordinal == hit.id.ordinal }),
              chunk.text == hit.quote, chunk.locator == hit.locator else {
            throw SourceEvidenceError.invalidLedger
        }
        try Task.checkCancellation()
        // Look beyond the search prefix only for file safety, never to replace the
        // displayed evidence. A reused filename cannot prove which revision is on disk.
        var reusedFilename = false
        for event in events where event.id != source.id && [.capture, .imported, .revision].contains(event.kind) {
            try Task.checkCancellation()
            do {
                if try event.payload().memory?.originalFilename == memory.originalFilename {
                    reusedFilename = true
                    break
                }
            } catch {
                // An unreadable future source cannot rewrite earlier evidence, but
                // prevents us from establishing that its original was not reused.
                reusedFilename = true
                break
            }
        }
        let original: SourceEvidenceOriginalState
        if reusedFilename {
            original = .versionUnverified
        } else if let url = Self.readableOriginal(filename: memory.originalFilename, directory: originalsDirectory) {
            original = .available(url)
        } else {
            original = .unavailable
        }
        return ResolvedSourceEvidence(hit: hit, memory: memory, fieldText: text, original: original,
                                      libraryHasChanged: (events.last?.sequence ?? sequence) > sequence)
    }

    nonisolated static func readableOriginal(filename: String, directory: URL) -> URL? {
        let root = directory.standardizedFileURL.resolvingSymlinksInPath()
        guard !filename.isEmpty, filename != ".", filename != "..", !filename.contains("/") else { return nil }
        let url = root.appendingPathComponent(filename).standardizedFileURL.resolvingSymlinksInPath()
        guard url.deletingLastPathComponent() == root,
              (try? url.resourceValues(forKeys: [.isRegularFileKey]).isRegularFile) == true,
              FileManager.default.isReadableFile(atPath: url.path) else { return nil }
        return url
    }
}
