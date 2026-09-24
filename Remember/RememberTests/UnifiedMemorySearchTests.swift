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
        #expect(options.snippet(for: current.id.memoryID, in: page)?.id == current.id)
        #expect(options.snippet(for: old.id.memoryID, in: page) == nil)
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
