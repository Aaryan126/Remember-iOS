import Foundation
import GRDB
import Testing
@testable import Remember

/// This is an integrity benchmark, not a semantic-quality benchmark. Expected state is
/// updated from test commands, never obtained by replaying production events.
@Suite(.serialized)
struct OrganizationHistoryBenchmarkTests {
    enum History: String, CaseIterable {
        case duplicateCapture, revisionChain, metadataThenRevision, memoryArchiveRestore
        case sharedThreadArchive, threadRestore, invalidRename, renameUndo
        case staleRenameUndo, placementUndo, stalePlacementUndo, mergeUndo
        case mergeUndoPreservesCorrection, splitProposal, splitDismiss, splitAccept
        case splitUndo, splitStaleArchive, splitStaleMembership, splitDoubleResolve
        case staleSequence, restart, unavailableEmbedding, cancellationAndPolicyRefresh
    }

    @Test(arguments: History.allCases)
    func explicitHistory(_ history: History) async throws {
        let harness = try HistoryHarness()
        do {
            for index in 1...4 { try await harness.capture(index) }
            try await harness.check()
            let a = historyID(1), b = historyID(2), c = historyID(3)
            switch history {
            case .duplicateCapture:
                let count = try await harness.store.provenanceEvents().count
                try await harness.capture(1)
                #expect(try await harness.store.provenanceEvents().count == count)
            case .revisionChain:
                for index in 1...4 {
                    try await harness.revise(a, text: "Revision \(index)")
                    try await harness.check()
                }
            case .metadataThenRevision:
                try await harness.store.updateEditableFields(id: a, title: "Edited", summary: "New metadata", tags: ["fictional"])
                harness.expected[a]?.title = "Edited"
                try await harness.check()
                try await harness.revise(a, text: "Revised source")
            case .memoryArchiveRestore:
                try await harness.archiveMemory(a, true)
                let count = try await harness.store.provenanceEvents().count
                try await harness.archiveMemory(a, true)
                #expect(try await harness.store.provenanceEvents().count == count)
                try await harness.archiveMemory(a, false)
            case .sharedThreadArchive, .threadRestore:
                try await harness.assign(a, to: [a, b])
                try await harness.archiveThread(a, true)
                #expect(try await harness.store.fetchAll().count == 4)
                if history == .threadRestore { try await harness.archiveThread(a, false) }
            case .invalidRename:
                await #expect(throws: ProvenanceError.self) { try await harness.store.renameProjectCluster(id: a, title: "   ") }
                try await harness.archiveThread(a, true)
                await #expect(throws: ProvenanceError.self) { try await harness.store.renameProjectCluster(id: a, title: "Hidden") }
            case .renameUndo:
                try await harness.rename(a, "Renamed")
                let event = try #require(await harness.store.provenanceEvents().last)
                try await harness.rename(c, "Unrelated correction")
                try await harness.store.undoProjectEvent(id: event.id)
                harness.titles[a] = "Memory 1"
            case .staleRenameUndo:
                try await harness.rename(a, "First name")
                let event = try #require(await harness.store.provenanceEvents().last)
                try await harness.rename(a, "Second name")
                await #expect(throws: ProvenanceError.self) { try await harness.store.undoProjectEvent(id: event.id) }
            case .placementUndo, .stalePlacementUndo:
                try await harness.assign(a, to: [b])
                let event = try #require(await harness.store.provenanceEvents().last)
                if history == .stalePlacementUndo {
                    try await harness.assign(a, to: [c])
                    await #expect(throws: ProvenanceError.self) { try await harness.store.undoProjectEvent(id: event.id) }
                } else {
                    try await harness.store.undoProjectEvent(id: event.id)
                    harness.expected[a]?.memberships = [a]
                }
            case .mergeUndo, .mergeUndoPreservesCorrection:
                let event = try await harness.merge(a, b)
                if history == .mergeUndoPreservesCorrection { try await harness.rename(c, "Unrelated correction") }
                try await harness.undoMerge(event, a, b)
                let snapshot = try ProvenanceSnapshot.replay(await harness.store.provenanceEvents())
                #expect(snapshot.blockedPairs.contains([a.uuidString, b.uuidString].sorted().joined(separator: ":")))
                await #expect(throws: ProvenanceError.self) { try await harness.store.undoProjectEvent(id: event.id) }
            case .splitProposal, .splitDismiss, .splitAccept, .splitUndo,
                 .splitStaleArchive, .splitStaleMembership, .splitDoubleResolve:
                try await harness.assign(b, to: [a])
                let proposal = try await harness.proposeSplit(b, from: a)
                // A suggestion itself must not alter memberships.
                try await harness.check()
                if history == .splitStaleArchive {
                    try await harness.archiveMemory(b, true)
                    await #expect(throws: ProvenanceError.self) { try await harness.store.resolveProjectSplit(id: proposal.id, accept: true) }
                } else if history == .splitStaleMembership {
                    try await harness.assign(b, to: [c])
                    await #expect(throws: ProvenanceError.self) { try await harness.store.resolveProjectSplit(id: proposal.id, accept: true) }
                } else if history != .splitProposal {
                    let accept = history != .splitDismiss
                    try await harness.store.resolveProjectSplit(id: proposal.id, accept: accept)
                    if accept {
                        harness.expected[b]?.memberships = [historyID(801)]
                        harness.titles[historyID(801)] = "Separate branch"
                    }
                    if history == .splitUndo {
                        let split = try #require(await harness.store.provenanceEvents().last)
                        try await harness.store.undoProjectEvent(id: split.id)
                        harness.expected[b]?.memberships = [a]
                    }
                    if history == .splitDoubleResolve {
                        await #expect(throws: ProvenanceError.self) { try await harness.store.resolveProjectSplit(id: proposal.id, accept: true) }
                    }
                }
            case .staleSequence:
                let sequence = try await harness.store.provenanceEvents().last?.sequence
                try await harness.rename(a, "User correction")
                var payload = ProvenancePayload()
                payload.clusterID = a; payload.title = "Stale automatic result"
                let event = try ProvenanceEvent(kind: .rename, payload: payload)
                await #expect(throws: ProvenanceError.self) { try await harness.store.appendProvenance(event, expectedSequence: sequence) }
            case .restart:
                try await harness.assign(a, to: [a, b])
                try await harness.revise(c, text: "A durable revision")
                try await harness.archiveThread(b, true)
                try await harness.reopen()
            case .unavailableEmbedding, .cancellationAndPolicyRefresh:
                try await harness.index(a)
                if history == .cancellationAndPolicyRefresh {
                    let count = try await harness.store.provenanceEvents().count
                    let engine = ProjectGraphService(store: harness.store, embeddings: HistoryEmbedding(cancelled: true), reasoner: HistoryNoReasoning())
                    await #expect(throws: CancellationError.self) { try await engine.synchronize() }
                    #expect(try await harness.store.provenanceEvents().count == count)
                    // A prior-policy placement must not suppress a current-policy refresh.
                    let events = try await harness.store.provenanceEvents()
                    var payload = ProvenancePayload()
                    payload.model = "historical-policy-fixture"
                    payload.sourceRevisionID = events.last?.id
                    payload.assignments = [a.uuidString: [a]]
                    try await harness.store.appendProvenance(ProvenanceEvent(kind: .placement, memoryID: a, payload: payload), expectedSequence: events.last?.sequence)
                }
                let engine = ProjectGraphService(store: harness.store, embeddings: HistoryEmbedding(cancelled: false), reasoner: HistoryNoReasoning())
                try await engine.synchronize()
                let first = try await harness.store.provenanceEvents()
                try await engine.synchronize()
                #expect(try await harness.store.provenanceEvents().count == first.count)
                #expect(try first.last(where: { $0.kind == .placement })?.payload().model == ProjectMath.policy)
            }
            try await harness.check()
            try await harness.verifyHistoricalCheckpoints()
        } catch {
            try await harness.closeAndRemove()
            throw error
        }
        try await harness.closeAndRemove()
    }

    @Test(arguments: Array(1...100))
    func seededStateMachine(seed: Int) async throws {
        let harness = try HistoryHarness()
        do {
            var random = HistoryRandom(state: UInt64(seed))
            for index in 1...8 { try await harness.capture(index) }
            try await harness.check()
            for step in 0..<50 {
                let index = Int(random.next() % 8) + 1
                let id = historyID(index)
                switch random.next() % 8 {
                case 0: try await harness.capture(index)
                case 1: try await harness.archiveMemory(id, true)
                case 2: try await harness.archiveMemory(id, false)
                case 3:
                    // Explicitly restore first so generated commands remain valid.
                    try await harness.archiveMemory(id, false)
                    let target = historyID(Int(random.next() % 8) + 1)
                    try await harness.archiveThread(target, false)
                    try await harness.assign(id, to: [target])
                case 4:
                    try await harness.archiveMemory(id, false)
                    try await harness.archiveThread(id, false)
                    let target = historyID(Int(random.next() % 8) + 1)
                    try await harness.archiveThread(target, false)
                    try await harness.assign(id, to: [id, target])
                case 5: try await harness.revise(id, text: "Seed \(seed) revision \(step)")
                case 6: try await harness.archiveThread(id, random.next() % 2 == 0)
                default:
                    try await harness.archiveThread(id, false)
                    try await harness.rename(id, "Seed \(seed) thread \(step)")
                    try await harness.reopen()
                }
                try await harness.check()
            }
            try await harness.verifyHistoricalCheckpoints()
        } catch {
            try await harness.closeAndRemove()
            throw error
        }
        try await harness.closeAndRemove()
    }
}

private struct HistoryExpectedMemory {
    var filename: String
    var title: String
    var archived = false
    var memberships: Set<UUID>
}

private final class HistoryHarness {
    let root: URL
    var store: MemoryStore
    var expected: [UUID: HistoryExpectedMemory] = [:]
    var titles: [UUID: String] = [:]
    var pinned: Set<UUID> = []
    var archivedThreads: Set<UUID> = []
    var retired: Set<UUID> = []
    private var priorEvents: [ProvenanceEvent] = []
    private var checkpoints: [(count: Int, memories: [UUID: HistoryExpectedMemory], titles: [UUID: String], pinned: Set<UUID>, archived: Set<UUID>)] = []
    private var revision = 0

    init() throws {
        root = FileManager.default.temporaryDirectory.appendingPathComponent("OrganizationHistory-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        store = try MemoryStore(databaseURL: root.appendingPathComponent("db.sqlite"))
    }

    func closeAndRemove() async throws {
        try await store.databasePool.close()
        try FileManager.default.removeItem(at: root)
    }

    func reopen() async throws {
        try await store.databasePool.close()
        store = try MemoryStore(databaseURL: root.appendingPathComponent("db.sqlite"))
    }

    func capture(_ index: Int) async throws {
        let id = historyID(index)
        let title = "Memory \(index)", filename = "original-\(index).txt"
        let time = Date(timeIntervalSince1970: 1_800_000_000 + Double(index))
        let item = MemoryItem(id: id, kind: .text, createdAt: time, importedAt: time, updatedAt: time,
            state: .captured, originalFilename: filename, userCaption: title, title: title,
            summary: nil, extractedText: nil, tagsJSON: "[]", processingError: nil, modelVersion: nil)
        try await store.insertIfNeeded(item)
        if expected[id] == nil {
            expected[id] = HistoryExpectedMemory(filename: filename, title: title, memberships: [id])
            titles[id] = title
        }
    }

    func revise(_ id: UUID, text: String) async throws {
        revision += 1
        let filename = "revision-\(revision).txt"
        let before = try await store.provenanceEvents()
        let previousSource = before.last { $0.memoryID == id && [.capture, .revision, .imported].contains($0.kind) }
        try await store.updateNoteContent(id: id, document: NoteDocument(text: text), filename: filename)
        expected[id]?.filename = filename
        expected[id]?.title = text
        let last = try #require(await store.provenanceEvents().last)
        #expect(try last.payload().sourceRevisionID == previousSource?.id)
        #expect(try last.payload().sourceFilename == filename)
    }

    func index(_ id: UUID) async throws {
        let title = try #require(expected[id]?.title)
        try await store.markIndexed(id: id, analysis: MemoryAnalysisResult(title: title,
            summary: "", tags: [], extractedText: title, modelVersion: "history-fixture"))
    }

    func archiveMemory(_ id: UUID, _ archived: Bool) async throws {
        try await store.setArchived(id: id, archived: archived)
        expected[id]?.archived = archived
    }

    func archiveThread(_ id: UUID, _ archived: Bool) async throws {
        try await store.setProjectThreadArchived(id: id, archived: archived)
        if archived { archivedThreads.insert(id) } else { archivedThreads.remove(id) }
    }

    func assign(_ id: UUID, to memberships: Set<UUID>) async throws {
        try await store.assignProjectMemory(id: id, clusters: memberships)
        expected[id]?.memberships = memberships
        pinned.insert(id)
    }

    func rename(_ id: UUID, _ title: String) async throws {
        try await store.renameProjectCluster(id: id, title: title)
        titles[id] = title
    }

    func merge(_ a: UUID, _ b: UUID) async throws -> ProvenanceEvent {
        let merged = historyID(800)
        var payload = ProvenancePayload()
        payload.clusterID = merged; payload.title = "Merged branch"; payload.parents = [a, b]
        payload.assignments = [a.uuidString: [merged], b.uuidString: [merged]]
        payload.previousAssignments = [a.uuidString: [a], b.uuidString: [b]]
        let event = try ProvenanceEvent(kind: .merge, payload: payload, id: historyID(900))
        try await store.appendProvenance(event, expectedSequence: await store.provenanceEvents().last?.sequence)
        expected[a]?.memberships = [merged]; expected[b]?.memberships = [merged]
        titles[merged] = "Merged branch"; retired.formUnion([a, b])
        try await check()
        let snapshot = try ProvenanceSnapshot.replay(await store.provenanceEvents())
        #expect(snapshot.clusters[merged]?.parents == [a, b])
        #expect(snapshot.ancestors(of: merged) == [merged, a, b])
        return event
    }

    func undoMerge(_ event: ProvenanceEvent, _ a: UUID, _ b: UUID) async throws {
        try await store.undoProjectEvent(id: event.id)
        expected[a]?.memberships = [a]; expected[b]?.memberships = [b]
        retired.subtract([a, b]); pinned.formUnion([a, b])
    }

    func proposeSplit(_ member: UUID, from parent: UUID) async throws -> ProvenanceEvent {
        var payload = ProvenancePayload()
        payload.clusterID = parent; payload.parents = [historyID(801)]; payload.title = "Separate branch"
        payload.previousAssignments = [member.uuidString: [parent]]
        payload.assignments = [member.uuidString: [historyID(801)]]
        let event = try ProvenanceEvent(kind: .splitProposal, payload: payload, id: historyID(901))
        try await store.appendProvenance(event, expectedSequence: await store.provenanceEvents().last?.sequence)
        return event
    }

    func check() async throws {
        let events = try await store.provenanceEvents()
        // Historical payloads/IDs/sequences remain byte-for-byte stable after every command.
        #expect(events.count >= priorEvents.count)
        for (old, current) in zip(priorEvents, events) {
            #expect(old.id == current.id && old.sequence == current.sequence)
            #expect(old.payloadJSON == current.payloadJSON && old.timestamp == current.timestamp)
            #expect(old.kind == current.kind && old.origin == current.origin && old.memoryID == current.memoryID)
        }
        let knownIDs = Set(events.map(\.id))
        #expect(knownIDs.count == events.count)
        var seen: Set<UUID> = []
        for event in events {
            let payload = try event.payload()
            if let source = payload.sourceRevisionID { #expect(seen.contains(source)) }
            if let reference = payload.referencedEventID { #expect(seen.contains(reference)) }
            #expect(payload.citedEventIDs.allSatisfy(seen.contains))
            seen.insert(event.id)
        }
        let actual = try ProvenanceSnapshot.replay(events)
        #expect(Set(actual.memories.keys) == Set(expected.keys))
        #expect(actual.pinned == pinned)
        #expect(actual.archivedClusterIDs == archivedThreads)
        #expect(actual.memberships == expected.mapValues(\.memberships))
        let expectedActive = Set(titles.keys.filter { thread in
            !archivedThreads.contains(thread) && !retired.contains(thread)
                && expected.values.contains { !$0.archived && $0.memberships.contains(thread) }
        })
        #expect(Set(actual.activeClusters.map(\.id)) == expectedActive)
        #expect(Set(try await store.fetchAll().map(\.id)) == Set(expected.filter { !$0.value.archived }.keys))
        for (id, value) in expected {
            #expect(actual.memories[id]?.originalFilename == value.filename)
            #expect(actual.memories[id]?.displayTitle == value.title)
            #expect(actual.memories[id]?.isArchived == value.archived)
        }
        for (id, title) in titles { #expect(actual.clusters[id]?.title == title) }
        priorEvents = events
        checkpoints.append((events.count, expected, titles, pinned, archivedThreads))
    }

    func verifyHistoricalCheckpoints() async throws {
        let events = try await store.provenanceEvents()
        // Sequence prefixes avoid assumptions about timestamp resolution or elapsed time.
        // The expected snapshots are copied from commands before future operations occur.
        for index in Set([0, checkpoints.count / 2, checkpoints.count - 1]) {
            let checkpoint = checkpoints[index]
            let actual = try ProvenanceSnapshot.replay(Array(events.prefix(checkpoint.count)))
            #expect(actual.memberships == checkpoint.memories.mapValues(\.memberships))
            #expect(actual.pinned == checkpoint.pinned)
            #expect(actual.archivedClusterIDs == checkpoint.archived)
            for (id, value) in checkpoint.memories {
                #expect(actual.memories[id]?.originalFilename == value.filename)
                #expect(actual.memories[id]?.displayTitle == value.title)
                #expect(actual.memories[id]?.isArchived == value.archived)
            }
            for (id, title) in checkpoint.titles { #expect(actual.clusters[id]?.title == title) }
        }
    }
}

private func historyID(_ index: Int) -> UUID {
    UUID(uuidString: String(format: "00000000-0000-0000-0000-%012d", index))!
}

private struct HistoryRandom {
    var state: UInt64
    mutating func next() -> UInt64 {
        state = state &* 6_364_136_223_846_793_005 &+ 1_442_695_040_888_963_407
        // High bits avoid the short low-bit cycles of an LCG in modulo selection.
        return state >> 32
    }
}

private struct HistoryEmbedding: ProjectEmbeddingProviding {
    let cancelled: Bool
    func embedding(for text: String) async throws -> ProjectEmbedding? {
        if cancelled { throw CancellationError() }
        return nil
    }
}

private struct HistoryNoReasoning: ProjectReasoning {
    func decide(source: String, candidates: [(id: UUID, title: String, summary: String)]) async throws -> ProjectReasoningResult? { nil }
}
