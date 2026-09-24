import Foundation
import GRDB
import Testing
@testable import Remember

struct SourceEvidenceBrowserTests {
    @MainActor @Test func replayedProjectCanDisplayRiverWithoutStartingOrganization() throws {
        let item = memory("Fictional River context")
        let event = try ProvenanceEvent(kind: .capture, memoryID: item.id, payload: ProvenancePayload(memory: item))
        let snapshot = try ProvenanceSnapshot.replay([event])
        let model = ProjectViewModel(initialSnapshot: snapshot)
        #expect(!model.isLoading && !model.isOrganizing && model.errorMessage == nil)
        #expect(model.snapshot.members(of: item.id).map(\.id) == [item.id])
        #expect(model.historical(at: nil).events.map(\.id) == [event.id])
        #expect(ProjectViewModel().isLoading)
    }

    private func fixture() throws -> (URL, MemoryStore, SourceEvidenceBrowserRepository) {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("SourceBrowser-\(UUID())", isDirectory: true)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        let store = try MemoryStore(databaseURL: root.appendingPathComponent("fixture.sqlite"))
        return (root, store, SourceEvidenceBrowserRepository(store: store, originalsDirectory: root))
    }

    private func memory(_ text: String, filename: String = "original.txt") -> MemoryItem {
        MemoryItem(id: UUID(), kind: .text, createdAt: Date(timeIntervalSince1970: 100),
            importedAt: Date(timeIntervalSince1970: 100), updatedAt: Date(timeIntervalSince1970: 100),
            state: .captured, originalFilename: filename, userCaption: text, title: "Fixture only",
            summary: "Generated unicorn", extractedText: text, tagsJSON: "[]", processingError: nil, modelVersion: nil)
    }

    @Test func realStoreSearchAndResolutionAreReadOnly() async throws {
        let (root, store, repository) = try fixture()
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        let item = memory("Receipt code ORBIT-27")
        try Data("Receipt code ORBIT-27".utf8).write(to: root.appendingPathComponent(item.originalFilename))
        try await store.insertIfNeeded(item)
        let before = try await store.provenanceEvents()
        let page = try await repository.search(.init(query: "receipt"))
        let hit = try #require(page.hits.first)
        let resolved = try await repository.resolve(hit, through: page.throughSequence)
        #expect(resolved.memory.id == item.id)
        #expect(resolved.fieldText == "Receipt code ORBIT-27")
        #expect(resolved.original == .available(root.appendingPathComponent(item.originalFilename).resolvingSymlinksInPath()))
        #expect(!resolved.libraryHasChanged)
        #expect(try await store.provenanceEvents().map(\.id) == before.map(\.id))
        #expect(try await store.fetchAll() == [item])
        #expect(try await repository.search(.init(query: "unicorn")).hits.isEmpty)
    }

    @Test func oldResultOpensOldTextAfterNewRevision() async throws {
        let (root, store, repository) = try fixture()
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        let item = memory("Receipt ORBIT-27")
        try await store.insertIfNeeded(item)
        let old = try await repository.search(.init(query: "receipt"))
        try await store.updateNoteContent(id: item.id, document: NoteDocument(title: "Receipt NOVA-42", body: ""), filename: "revised.txt")
        let resolved = try await repository.resolve(#require(old.hits.first), through: old.throughSequence)
        #expect(resolved.fieldText == "Receipt ORBIT-27")
        #expect(resolved.memory.originalFilename == "original.txt")
        #expect(resolved.libraryHasChanged)
        #expect(try await repository.search(.init(query: "ORBIT")).hits.isEmpty)
        #expect(try await repository.search(.init(query: "ORBIT", scope: .includeHistory)).hits.count == 1)
    }

    @Test func archivesRequireExplicitHistoryAndMissingOriginalRetainsText() async throws {
        let (root, store, repository) = try fixture()
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        let item = memory("Receipt ORBIT-27")
        try await store.insertIfNeeded(item)
        try await store.setArchived(id: item.id, archived: true)
        #expect(try await repository.search(.init(query: "receipt")).hits.isEmpty)
        let page = try await repository.search(.init(query: "receipt", scope: .includeHistory))
        let hit = try #require(page.hits.first)
        #expect(hit.isArchived)
        let resolved = try await repository.resolve(hit, through: page.throughSequence)
        #expect(resolved.original == .unavailable)
        #expect(resolved.fieldText == "Receipt ORBIT-27")
    }

    @Test func reusedFilenameDoesNotOpenNewFileForHistoricalResult() async throws {
        let (root, store, repository) = try fixture()
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        let item = memory("Receipt ORBIT-27")
        try await store.insertIfNeeded(item)
        let old = try await repository.search(.init(query: "receipt"))
        try await store.updateNoteContent(id: item.id, document: .init(title: "Receipt NEW", body: ""))
        try Data("Receipt NEW".utf8).write(to: root.appendingPathComponent(item.originalFilename))
        let resolved = try await repository.resolve(#require(old.hits.first), through: old.throughSequence)
        #expect(resolved.original == .versionUnverified)
        #expect(resolved.fieldText == "Receipt ORBIT-27")
    }

    @Test func resultCannotBeResolvedBeforeItsSnapshot() async throws {
        let (root, store, repository) = try fixture()
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        try await store.insertIfNeeded(memory("Receipt ORBIT-27"))
        let page = try await repository.search(.init(query: "receipt"))
        let hit = try #require(page.hits.first)
        await #expect(throws: SourceEvidenceError.self) { try await repository.resolve(hit, through: 0) }
    }

    @Test func originalPathRejectsTraversalDirectoriesAndEscapingSymlinks() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("SourceBrowserPaths-\(UUID())", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let originals = root.appendingPathComponent("Originals", isDirectory: true)
        try FileManager.default.createDirectory(at: originals, withIntermediateDirectories: true)
        let outside = root.appendingPathComponent("outside.txt")
        try Data("fixture".utf8).write(to: outside)
        try FileManager.default.createSymbolicLink(at: originals.appendingPathComponent("escape.txt"), withDestinationURL: outside)
        for filename in ["", ".", "..", "../outside.txt", "/outside.txt", "nested/file.txt", "escape.txt", "missing.txt"] {
            #expect(SourceEvidenceBrowserRepository.readableOriginal(filename: filename, directory: originals) == nil)
        }
        try FileManager.default.createDirectory(at: originals.appendingPathComponent("directory"), withIntermediateDirectories: false)
        #expect(SourceEvidenceBrowserRepository.readableOriginal(filename: "directory", directory: originals) == nil)
    }

    @MainActor @Test func screenRestoresResultsWithoutNewSearchOnBack() async throws {
        let (root, store, repository) = try fixture()
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        try await store.insertIfNeeded(memory("Receipt ORBIT-27"))
        let model = SourceEvidenceBrowserModel(repository: repository)
        model.query = "receipt"
        await model.search()
        let page = try #require(model.page)
        _ = try await model.resolve(#require(page.hits.first), through: page.throughSequence)
        await model.search()
        #expect(model.query == "receipt" && model.scope == .current)
        #expect(model.page?.hits.map(\.id) == page.hits.map(\.id))
        #expect(model.errorMessage == nil && !model.isLoading)
    }

    @MainActor @Test func emptyQueryClearsResultsWithoutFalseEmptyClaim() async throws {
        let (root, store, repository) = try fixture()
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        try await store.insertIfNeeded(memory("Receipt ORBIT-27"))
        let model = SourceEvidenceBrowserModel(repository: repository)
        model.query = "receipt"; await model.search()
        model.query = "  "; await model.search()
        #expect(model.page == nil && !model.didSearch && !model.isLoading && model.errorMessage == nil)
    }

    @MainActor @Test func paginationPinsBoundaryAndRefreshSeesNewRecords() async throws {
        let (root, store, repository) = try fixture()
        let pool = await store.databasePool
        defer { try? pool.close(); try? FileManager.default.removeItem(at: root) }
        for index in 0..<35 { try await store.insertIfNeeded(memory("Receipt \(index)", filename: "\(index).txt")) }
        let model = SourceEvidenceBrowserModel(repository: repository)
        model.query = "receipt"; await model.search()
        let boundary = try #require(model.page?.throughSequence)
        #expect(model.page?.hits.count == 30 && model.canLoadMore)
        try await store.insertIfNeeded(memory("Receipt newer", filename: "new.txt"))
        await model.loadMore()
        #expect(model.page?.hits.count == 35 && model.page?.throughSequence == boundary && !model.canLoadMore)
        #expect(Set(model.page?.hits.map(\.id) ?? []).count == 35)
        await model.search(force: true)
        #expect(model.page?.totalMatchingPassages == 36)
        #expect(model.page?.throughSequence != boundary)
    }

    @MainActor @Test func staleResponsesCannotReplaceNewScope() async throws {
        let repository = ControlledEvidenceRepository()
        let model = SourceEvidenceBrowserModel(repository: repository)
        model.query = "receipt"
        let old = Task { await model.search() }
        await repository.waitForFirstRequest()
        model.scope = .includeHistory
        await model.search()
        await repository.releaseFirst()
        await old.value
        #expect(model.page?.scope == .includeHistory && model.page?.throughSequence == 2)
        #expect(!model.isLoading && model.errorMessage == nil)
    }

    @MainActor @Test func cancelledResponseCannotPublishResults() async throws {
        let repository = ControlledEvidenceRepository()
        let model = SourceEvidenceBrowserModel(repository: repository)
        model.query = "receipt"
        let operation = Task { await model.search() }
        await repository.waitForFirstRequest()
        operation.cancel()
        await repository.releaseFirst()
        await operation.value
        #expect(model.page == nil && model.errorMessage == nil && !model.isLoading && !model.didSearch)
    }
}

private actor ControlledEvidenceRepository: SourceEvidenceBrowsing {
    private var first: CheckedContinuation<SourceEvidencePage, Never>?
    private var ready: CheckedContinuation<Void, Never>?
    private var calls = 0

    func search(_ request: SourceEvidenceRequest) async throws -> SourceEvidencePage {
        calls += 1
        if calls == 1 {
            return await withCheckedContinuation { continuation in
                first = continuation
                ready?.resume(); ready = nil
            }
        }
        return SourceEvidencePage(throughSequence: 2, scope: request.scope, totalMatchingPassages: 0, hits: [])
    }

    func waitForFirstRequest() async {
        if first != nil { return }
        await withCheckedContinuation { ready = $0 }
    }

    func releaseFirst() {
        first?.resume(returning: SourceEvidencePage(throughSequence: 1, scope: .current, totalMatchingPassages: 0, hits: []))
        first = nil
    }

    func resolve(_ hit: SourceEvidenceHit, through sequence: Int64) async throws -> ResolvedSourceEvidence {
        throw SourceEvidenceError.invalidLedger
    }
}
