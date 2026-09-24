import Foundation
import Testing
@testable import Remember

struct D3OrganizationTests {
    @Test func corroborationRejectsSingleSupportInAnEstablishedThread() {
        let thread = UUID(), a = UUID(), b = UUID(), c = UUID()
        let candidates = [a, b, c].map { D3OrganizationPolicy.Candidate(id: $0, memberships: [thread], contextual: 1, lexical: 1) }
        #expect(D3OrganizationPolicy.decide(retrieved: candidates, memberCounts: [thread: 3], scores: [a: 0.99]).selected == nil)
        #expect(D3OrganizationPolicy.decide(retrieved: candidates, memberCounts: [thread: 3], scores: [a: 0.99, b: 0.99]).selected == thread)
        #expect(D3OrganizationPolicy.decide(retrieved: candidates, memberCounts: [thread: 3], scores: [a: .nan, b: .infinity, c: 2]).selected == nil)
        #expect(D3OrganizationPolicy.decide(retrieved: Array(candidates.prefix(1)), memberCounts: [thread: 1], scores: [a: D3OrganizationPolicy.threshold]).selected == thread)
    }

    @Test func multipleQualifyingThreadsRemainSeparate() {
        let a = UUID(), b = UUID()
        let candidates = [a, b].map { D3OrganizationPolicy.Candidate(id: $0, memberships: [$0], contextual: 1, lexical: 1) }
        let decision = D3OrganizationPolicy.decide(retrieved: candidates, memberCounts: [a: 1, b: 1], scores: [a: 0.99, b: 0.99])
        #expect(decision.selected == nil)
        #expect(decision.qualifying.count == 2)
    }

    @Test func retrievalIsBoundedAndDeterministic() {
        let candidates = (0..<12).map { n in
            D3OrganizationPolicy.Candidate(id: UUID(uuidString: String(format: "00000000-0000-0000-0000-%012d", n))!,
                memberships: [], contextual: Double(n), lexical: Double(12 - n))
        }
        let first = D3OrganizationPolicy.retrieve(candidates).map(\.id)
        #expect(first.count == 10)
        #expect(first == D3OrganizationPolicy.retrieve(candidates.reversed()).map(\.id))
        let invalid = D3OrganizationPolicy.Candidate(id: UUID(), memberships: [], contextual: .nan, lexical: .nan)
        #expect(D3OrganizationPolicy.retrieve([invalid]).isEmpty)
    }

    @Test func batchImportAttachesForwardWithoutMergingOrReprocessing() async throws {
        let (root, store) = try temporaryStore()
        defer { try? FileManager.default.removeItem(at: root) }
        let items = (0..<3).map { item("A project capture \($0)", offset: $0) }
        for item in items { try await index(item, store: store) }
        let organizer = D3ProjectOrganizer(store: store, embeddings: D3TestEmbeddings(), matcher: D3TestMatcher(), supportsText: { _ in true })
        try await organizer.synchronize()
        let events = try await store.provenanceEvents()
        let snapshot = try ProvenanceSnapshot.replay(events)
        #expect(items.allSatisfy { snapshot.memberships[$0.id] == [items[0].id] })
        #expect(events.filter { $0.kind == .placement }.count == 3)
        #expect(events.allSatisfy { $0.kind != .merge && $0.kind != .split })
        #expect(snapshot.clusters[items[0].id]?.title == items[0].displayTitle)
        try await organizer.synchronize()
        #expect(try await store.provenanceEvents().count == events.count)
    }

    @Test func legacyAssignmentsAndUserRenamesAreNotMigrated() async throws {
        let (root, store) = try temporaryStore()
        defer { try? FileManager.default.removeItem(at: root) }
        let a = item("Original capture", offset: 0)
        try await index(a, store: store)
        var payload = ProvenancePayload()
        payload.model = "legacy-policy"
        payload.assignments = [a.id.uuidString: [a.id]]
        try await store.appendProvenance(ProvenanceEvent(kind: .placement, memoryID: a.id, payload: payload), expectedSequence: await store.provenanceEvents().last?.sequence)
        try await store.renameProjectCluster(id: a.id, title: "My chosen name")
        let before = try await store.provenanceEvents()
        try await D3ProjectOrganizer(store: store, embeddings: D3TestEmbeddings(), matcher: D3TestMatcher(), supportsText: { _ in true }).synchronize()
        #expect(try await store.provenanceEvents().map(\.payloadJSON) == before.map(\.payloadJSON))
    }

    @Test func archivedThreadCannotAbsorbANewCapture() async throws {
        let (root, store) = try temporaryStore()
        defer { try? FileManager.default.removeItem(at: root) }
        let a = item("Hidden project", offset: 0), b = item("New capture", offset: 1)
        let organizer = D3ProjectOrganizer(store: store, embeddings: D3TestEmbeddings(), matcher: D3TestMatcher(), supportsText: { _ in true })
        try await index(a, store: store)
        try await organizer.synchronize()
        try await store.setProjectThreadArchived(id: a.id, archived: true)
        try await index(b, store: store)
        try await organizer.synchronize()
        let snapshot = try ProvenanceSnapshot.replay(await store.provenanceEvents())
        #expect(snapshot.memberships[b.id] == [b.id])
    }

    @Test func unavailableMatcherRetainsCapturesAndSupportsExplicitRetry() async throws {
        let (root, store) = try temporaryStore()
        defer { try? FileManager.default.removeItem(at: root) }
        let a = item("First project note", offset: 0), b = item("Second project note", offset: 1)
        for item in [a, b] { try await index(item, store: store) }
        let failed = D3ProjectOrganizer(store: store, embeddings: D3TestEmbeddings(), matcher: D3TestMatcher(fails: true), supportsText: { _ in true })
        try await failed.synchronize()
        let events = try await store.provenanceEvents()
        #expect(try ProvenanceSnapshot.replay(events).memberships[b.id] == [b.id])
        #expect(try events.last?.payload().scores["completed"] == 0)
        try await failed.synchronize()
        #expect(try await store.provenanceEvents().count == events.count)
        try await D3ProjectOrganizer(store: store, embeddings: D3TestEmbeddings(), matcher: D3TestMatcher(), supportsText: { _ in true }).synchronize(retryUnavailable: true)
        #expect(try await store.provenanceEvents().last?.payload().scores["completed"] == 1)
    }

    @Test func explicitAssignmentIsPreservedWithoutCallingMatcher() async throws {
        let (root, store) = try temporaryStore()
        defer { try? FileManager.default.removeItem(at: root) }
        let a = item("One project", offset: 0), b = item("Another capture", offset: 1)
        for item in [a, b] { try await index(item, store: store) }
        try await store.assignProjectMemory(id: b.id, clusters: [a.id])
        try await D3ProjectOrganizer(store: store, embeddings: D3TestEmbeddings(), matcher: D3TestMatcher(fails: true), supportsText: { _ in true }).synchronize()
        let snapshot = try ProvenanceSnapshot.replay(await store.provenanceEvents())
        #expect(snapshot.memberships[b.id] == [a.id])
        #expect(snapshot.pinned.contains(b.id))
    }

    @Test func cancellationCannotCommitAnAutomaticPlacement() async throws {
        let (root, store) = try temporaryStore()
        defer { try? FileManager.default.removeItem(at: root) }
        try await index(item("A project note", offset: 0), store: store)
        do {
            try await D3ProjectOrganizer(store: store, embeddings: D3TestEmbeddings(), matcher: D3CancelledMatcher(), supportsText: { _ in true }).synchronize()
            Issue.record("Expected cancellation")
        } catch is CancellationError { }
        #expect(try await store.provenanceEvents().allSatisfy { $0.kind != .placement })
    }

    @Test func bundledModelLoadsAndScoresSymmetrically() async throws {
        let matcher = D3PairMatcher()
        let vector: [Float] = [1] + Array(repeating: 0, count: 511)
        let a = D3Source(text: "Design notes for the orbit project.", contextual: vector, sentence: vector, space: D3OrganizationPolicy.embeddingSpace)
        let b = D3Source(text: "The orbit project design notes.", contextual: vector, sentence: vector, space: D3OrganizationPolicy.embeddingSpace)
        let score = try await matcher.score(a, b)
        #expect(score.isFinite && (0...1).contains(score))
        #expect(abs(score - (try await matcher.score(b, a))) < 1e-10)
        #expect(!(try await matcher.lexicalVector("project design")).isEmpty)
    }

    @Test func revisedPlacedMemoryIsNotSilentlyReassigned() async throws {
        let (root, store) = try temporaryStore()
        defer { try? FileManager.default.removeItem(at: root) }
        let a = item("Project alpha", offset: 0)
        try await index(a, store: store)
        let organizer = D3ProjectOrganizer(store: store, embeddings: D3TestEmbeddings(), matcher: D3TestMatcher(), supportsText: { _ in true })
        try await organizer.synchronize()
        try await store.markIndexed(id: a.id, analysis: MemoryAnalysisResult(title: "Changed source", summary: "", tags: [],
            extractedText: "Changed source", modelVersion: "fixture-revision"))
        let before = try await store.provenanceEvents()
        try await organizer.synchronize(retryUnavailable: true)
        #expect(try await store.provenanceEvents().count == before.count)
        #expect(try ProvenanceSnapshot.replay(before).memberships[a.id] == [a.id])
    }

    @Test func unsupportedTextRemainsSeparateWithoutUsingMatcher() async throws {
        let (root, store) = try temporaryStore()
        defer { try? FileManager.default.removeItem(at: root) }
        let a = item("Unsupported language fixture", offset: 0)
        try await index(a, store: store)
        try await D3ProjectOrganizer(store: store, embeddings: D3TestEmbeddings(), matcher: D3TestMatcher(fails: true), supportsText: { _ in false }).synchronize()
        let events = try await store.provenanceEvents()
        #expect(try events.last?.payload().scores["completed"] == 1)
        #expect(try ProvenanceSnapshot.replay(events).memberships[a.id] == [a.id])
    }

    @Test func concurrentEditInvalidatesPlacement() async throws {
        let (root, store) = try temporaryStore()
        defer { try? FileManager.default.removeItem(at: root) }
        let a = item("Concurrent project note", offset: 0)
        try await index(a, store: store)
        let matcher = D3EditingMatcher(store: store, id: a.id)
        do {
            try await D3ProjectOrganizer(store: store, embeddings: D3TestEmbeddings(), matcher: matcher, supportsText: { _ in true }).synchronize()
            Issue.record("Expected a stale decision")
        } catch ProvenanceError.staleDecision { }
        let events = try await store.provenanceEvents()
        #expect(events.allSatisfy { $0.kind != .placement })
        #expect(try ProvenanceSnapshot.replay(events).clusters[a.id]?.title == "User edit during inference")
    }

    private func temporaryStore() throws -> (URL, MemoryStore) {
        let root = URL.temporaryDirectory.appendingPathComponent("D3Tests-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        return (root, try MemoryStore(databaseURL: root.appendingPathComponent("test.sqlite")))
    }

    private func item(_ title: String, offset: Int) -> MemoryItem {
        let date = Date(timeIntervalSince1970: 1_800_000_000 + Double(offset))
        return MemoryItem(id: UUID(), kind: .text, createdAt: date, importedAt: date, updatedAt: date,
            state: .captured, originalFilename: UUID().uuidString + ".txt", userCaption: title, title: title,
            summary: nil, extractedText: nil, tagsJSON: "[]", processingError: nil, modelVersion: nil)
    }

    private func index(_ memory: MemoryItem, store: MemoryStore) async throws {
        try await store.insertIfNeeded(memory)
        try await store.markIndexed(id: memory.id, analysis: MemoryAnalysisResult(title: memory.displayTitle,
            summary: "", tags: [], extractedText: memory.displayTitle, modelVersion: "fixture"))
    }
}

private struct D3TestEmbeddings: ProjectEmbeddingProviding {
    func embedding(for text: String) async throws -> ProjectEmbedding? {
        let vector: [Float] = [1] + Array(repeating: 0, count: 511)
        return ProjectEmbedding(vector: vector, space: D3OrganizationPolicy.embeddingSpace, semanticVector: vector)
    }
}

private struct D3TestMatcher: D3Matching {
    var fails = false
    func lexicalVector(_ text: String) async throws -> [Int: Double] {
        if fails { throw D3Error.invalidOutput }
        return [0: 1]
    }
    func score(_ first: D3Source, _ second: D3Source) async throws -> Double {
        if fails { throw D3Error.invalidOutput }
        return 0.99
    }
}

private struct D3CancelledMatcher: D3Matching {
    func lexicalVector(_ text: String) async throws -> [Int: Double] { throw CancellationError() }
    func score(_ first: D3Source, _ second: D3Source) async throws -> Double { throw CancellationError() }
}

private struct D3EditingMatcher: D3Matching {
    let store: MemoryStore
    let id: UUID
    func lexicalVector(_ text: String) async throws -> [Int: Double] {
        try await store.renameProjectCluster(id: id, title: "User edit during inference")
        return [0: 1]
    }
    func score(_ first: D3Source, _ second: D3Source) async throws -> Double { 0.99 }
}
