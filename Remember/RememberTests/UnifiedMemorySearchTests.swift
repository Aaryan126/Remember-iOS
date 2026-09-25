import Foundation
import GRDB
import Testing
@testable import Remember

struct UnifiedMemorySearchTests {
    @Test func filterSummaryIsAbsentByDefaultAndAccurateWhenActive() {
        var options = UnifiedMemorySearchOptions()
        #expect(!options.hasActiveFilters && options.activeFilterSummary.isEmpty)
        options.includeHistory = true
        #expect(options.hasActiveFilters && options.activeFilterSummary == "Including history")
        options.sourceTextOnly = true
        #expect(options.activeFilterSummary == "Including history · Source text only")
        options.includeHistory = false
        #expect(options.activeFilterSummary == "Source text only")
        options = UnifiedMemorySearchOptions()
        #expect(!options.hasActiveFilters && options.scope == .current)
    }
    @Test func defaultScopeIsCurrentAndCardsDoNotDuplicatePassages() throws {
        let options = UnifiedMemorySearchOptions()
        let current = hit(), old = hit(current: false), archived = hit(archived: true)
        let page = page([current, old, archived])
        #expect(options.scope == .current)
        #expect(options.separateHits(in: page, cardMemoryIDs: [current.id.memoryID]).isEmpty)
    }

    @Test func historyAddsOlderAndArchivedWithoutDuplicatingCurrentCard() {
        let current = hit(), old = hit(current: false), archived = hit(archived: true)
        let options = UnifiedMemorySearchOptions(includeHistory: true)
        #expect(options.scope == .includeHistory)
        #expect(options.separateHits(in: page([current, old, archived]), cardMemoryIDs: [current.id.memoryID]).map(\.id) == [old.id, archived.id])
    }

    @Test func sourceOnlyShowsCurrentEvenWithCardAndHistoryIsOptIn() {
        let current = hit(), old = hit(current: false)
        var options = UnifiedMemorySearchOptions(sourceTextOnly: true)
        #expect(options.separateHits(in: page([current, old]), cardMemoryIDs: [current.id.memoryID]).map(\.id) == [current.id])
        options.includeHistory = true
        #expect(options.separateHits(in: page([current, old]), cardMemoryIDs: []).count == 2)
    }

    @Test func sourceWithoutIndexedCardIsNotLostAndArchivedOnlyLibraryStillSearches() {
        let current = hit(), archived = hit(archived: true)
        #expect(UnifiedMemorySearchOptions().separateHits(in: page([current]), cardMemoryIDs: []).count == 1)
        #expect(UnifiedMemorySearchOptions(includeHistory: true).separateHits(in: page([archived]), cardMemoryIDs: []).count == 1)
    }

    @Test func generatedMetadataIsDiscoverableNormallyButNotAsSourceEvidence() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("UnifiedSearch-\(UUID())")
        let store = try MemoryStore(databaseURL: root.appendingPathComponent("fixture.sqlite"))
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        let item = MemoryItem(id: UUID(), kind: .text, createdAt: .distantPast,
            importedAt: .distantPast, updatedAt: .distantPast, state: .indexed,
            originalFilename: "fictional.txt", userCaption: "Receipt ORBIT-27",
            title: "Fictional delivery", summary: "Unicorn generated summary",
            extractedText: "Receipt ORBIT-27", tagsJSON: "[]", processingError: nil, modelVersion: nil)
        try await store.insertIfNeeded(item)
        let library = MemorySearchService(memoryStore: store)
        let sources = SourceEvidenceBrowserRepository(store: store, originalsDirectory: root)
        #expect(try await library.search(.init(query: "unicorn")).map(\.id) == [item.id])
        #expect(try await sources.search(.init(query: "unicorn")).hits.isEmpty)
        #expect(try await sources.search(.init(query: "receipt")).hits.count == 1)
        try await store.updateNoteContent(id: item.id, document: .init(text: "Receipt NOVA-42"))
        #expect(try await library.search(.init(query: "ORBIT")).isEmpty)
        #expect(try await sources.search(.init(query: "ORBIT")).hits.isEmpty)
        let history = try await sources.search(.init(query: "ORBIT", scope: .includeHistory))
        let old = try #require(history.hits.first)
        #expect(!old.isCurrentVersion)
        #expect(try await sources.resolve(old, through: history.throughSequence).fieldText == "Receipt ORBIT-27")
    }

    @Test func typoSearchRanksExactFirstAndKeepsMetadataOutOfPassages() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("TypoSearch-\(UUID())")
        let store = try MemoryStore(databaseURL: root.appendingPathComponent("fixture.sqlite"))
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        let exact = searchMemory("Receipt", date: .distantPast)
        let approximate = searchMemory("Reciept", date: .distantFuture)
        try await store.insertIfNeeded(exact)
        try await store.insertIfNeeded(approximate)
        let library = MemorySearchService(memoryStore: store)
        let sources = SourceEvidenceBrowserRepository(store: store, originalsDirectory: root)
        let cards = try await library.search(.init(query: "receipt"), tolerateTypos: true)
        #expect(cards.map(\.id) == [exact.id, approximate.id])
        #expect(cards[0].score > cards[1].score)
        let passages = try await sources.search(.init(query: "receipt"))
        #expect(passages.hits.map(\.id.memoryID) == [exact.id, approximate.id])
        #expect(passages.hits.last?.quote == "Reciept")
        #expect(try await library.search(.init(query: "unicron"), tolerateTypos: true).count == 2)
        #expect(try await sources.search(.init(query: "unicron")).hits.isEmpty)
        // The explicit cloud/answer retrieval paths retain their existing exact policy.
        #expect(try await library.search(.init(query: "unicron")).isEmpty)
        #expect(try await library.searchEvidence(.init(query: "reciept")).map(\.memory.id) == [approximate.id])
    }

    @Test func typoHistoryAndArchiveResolveUnchangedExactRevision() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("TypoHistory-\(UUID())")
        let store = try MemoryStore(databaseURL: root.appendingPathComponent("fixture.sqlite"))
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        let item = searchMemory("Receipt ORBIT-27")
        try await store.insertIfNeeded(item)
        try await store.updateNoteContent(id: item.id, document: .init(text: "Receipt NOVA-42"))
        let sources = SourceEvidenceBrowserRepository(store: store, originalsDirectory: root)
        #expect(try await sources.search(.init(query: "reciept ORBIT-27")).hits.isEmpty)
        let before = try await store.provenanceEvents().map(\.id)
        let page = try await sources.search(.init(query: "reciept ORBIT-27", scope: .includeHistory))
        let hit = try #require(page.hits.first)
        #expect(!hit.isCurrentVersion && hit.quote == "Receipt ORBIT-27")
        #expect(try await sources.resolve(hit, through: page.throughSequence).fieldText == "Receipt ORBIT-27")
        #expect(try await store.provenanceEvents().map(\.id) == before)
        try await store.setArchived(id: item.id, archived: true)
        #expect(try await sources.search(.init(query: "reciept")).hits.isEmpty)
        let archived = try await sources.search(.init(query: "reciept", scope: .includeHistory))
        #expect(archived.hits.count == 2 && archived.hits.allSatisfy(\.isArchived))
        #expect(try await sources.search(.init(query: "reciept ORBIT-28", scope: .includeHistory)).hits.isEmpty)
    }

    @Test func typoSearchFindsTextBeyondMetadataIndexAndHonorsFilters() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("TypoChunks-\(UUID())")
        let store = try MemoryStore(databaseURL: root.appendingPathComponent("fixture.sqlite"))
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        var item = searchMemory("Short caption")
        item.extractedText = String(repeating: "Ordinary background notes. ", count: 200) + "Conference receipt ORBIT-27."
        try await store.insertIfNeeded(item)
        let library = MemorySearchService(memoryStore: store)
        #expect(try await library.search(.init(query: "conferense"), tolerateTypos: true).map(\.id) == [item.id])
        #expect(try await library.search(.init(query: "conferense", kind: .image), tolerateTypos: true).isEmpty)
        #expect(try await library.search(.init(query: "reciept ORBIT-28"), tolerateTypos: true).isEmpty)
    }

    @Test func fuzzyPassagePaginationUsesStableOrderAndLedgerBoundary() throws {
        let records = (1...35).map { index in
            let memoryID = UUID()
            return SourceEvidenceRecord(sequence: Int64(index), id: UUID(), timestamp: .distantPast,
                kind: .capture, memoryID: memoryID, sourceRevisionID: nil, restoredFromRevisionID: nil,
                snapshot: SourceEvidenceSnapshot(memoryID: memoryID, originalFilename: "fictional.txt",
                    extractedText: "Receipt", userCaption: nil, isArchived: false, analysisIsPartial: false))
        }
        let first = try SourceEvidenceSearch.search(records: records, request: .init(query: "reciept"))
        let next = try SourceEvidenceSearch.search(records: records,
            request: .init(query: "reciept", throughSequence: first.throughSequence, offset: first.hits.count))
        #expect(first.hits.count == 30 && next.hits.count == 5)
        #expect(Set((first.hits + next.hits).map(\.id)).count == 35)
        #expect(first.hits.map(\.sourceSequence) == Array((6...35).reversed()).map(Int64.init))
    }

    private func searchMemory(_ text: String, date: Date = .distantPast) -> MemoryItem {
        .init(id: UUID(), kind: .text, createdAt: date, importedAt: date, updatedAt: date,
              state: .indexed, originalFilename: "fictional.txt", userCaption: text,
              title: text, summary: "Unicorn generated summary", extractedText: text,
              tagsJSON: "[]", processingError: nil, modelVersion: nil)
    }

    private func page(_ hits: [SourceEvidenceHit]) -> SourceEvidencePage {
        .init(throughSequence: 10, scope: .includeHistory, totalMatchingPassages: hits.count, hits: hits)
    }

    private func hit(current: Bool = true, archived: Bool = false) -> SourceEvidenceHit {
        .init(id: .init(memoryID: UUID(), revisionID: UUID(), snapshotID: UUID(), field: .extractedText, ordinal: 0),
            revision: 0, sourceSequence: 1, snapshotSequence: 1, sourceDate: .distantPast,
            snapshotDate: .distantPast, quote: "Fictional receipt", locator: "Retained text",
            isCurrentVersion: current, isArchived: archived, importedHistoryGap: false,
            analysisIsPartial: false, lexicalScore: 1)
    }
}
