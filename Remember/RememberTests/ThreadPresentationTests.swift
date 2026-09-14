import Foundation
import Testing
@testable import Remember

struct ThreadPresentationTests {
    @Test func finderReachesEveryThreadBeyondMapWindowAndPreservesSharedCounts() throws {
        var snapshot = ProvenanceSnapshot()
        for index in 0..<500 {
            let item = memory(index)
            snapshot.memories[item.id] = item
            snapshot.clusters[item.id] = ProvenanceCluster(id: item.id, title: String(format: "Thread %03d", index))
            snapshot.memberships[item.id] = [item.id]
        }
        let first = memory(0).id, last = memory(499).id
        snapshot.memberships[first] = [first, last]
        let directory = ThreadDirectory(snapshot: snapshot)
        #expect(directory.entries.count == 500)
        #expect(directory.matching("499").map(\.id) == [last])
        #expect(directory.matching("499").first?.memoryCount == 2)
        #expect(ProjectGraphMap(snapshot: snapshot).nodes.count == 40)
        #expect(!ProjectGraphMap(snapshot: snapshot).nodes.contains { $0.id == last })
        #expect(directory.matching("   ").count == 500)
        #expect(directory.matching("no-such-thread").isEmpty)
    }

    @Test func finderMatchesFullNamesAndExcludesArchivedRetiredAndEmptyThreads() {
        var snapshot = ProvenanceSnapshot()
        for index in 0..<5 {
            let item = memory(index)
            snapshot.memories[item.id] = item
            snapshot.clusters[item.id] = ProvenanceCluster(id: item.id, title: "Café studio plans")
            snapshot.memberships[item.id] = [item.id]
        }
        snapshot.archivedClusterIDs.insert(memory(1).id)
        snapshot.clusters[memory(2).id]?.retired = true
        snapshot.memories[memory(3).id]?.isArchived = true
        snapshot.memberships[memory(4).id] = []
        let directory = ThreadDirectory(snapshot: snapshot)
        #expect(directory.entries.map(\.id) == [memory(0).id])
        #expect(directory.matching("  PLANS cafe  ").count == 1)
        #expect(ThreadDirectory(snapshot: ProvenanceSnapshot()).entries.isEmpty)
    }

    @Test func storyKeepsOriginalsRevisionsAndMilestonesWhileActivityRetainsEveryRecord() throws {
        let item = memory(0)
        let kinds: [ProvenanceKind] = [.capture, .metadata, .enrichment, .processing, .rename, .placement,
                                      .revision, .merge, .splitProposal, .split, .checkpoint, .recap, .archive, .restore]
        var snapshot = ProvenanceSnapshot()
        snapshot.memories[item.id] = item
        snapshot.memberships[item.id] = [item.id]
        snapshot.clusters[item.id] = ProvenanceCluster(id: item.id, title: "Studio")
        for (index, kind) in kinds.enumerated() {
            var source = item
            if kind == .revision { source.originalFilename = "revision.txt"; source.userCaption = "Revised evidence" }
            snapshot.events.append(try ProvenanceEvent(kind: kind, memoryID: item.id,
                payload: ProvenancePayload(memory: source, clusterID: item.id),
                timestamp: Date(timeIntervalSince1970: Double(index))))
        }
        let before = snapshot.events.map(\.payloadJSON)
        let history = ThreadHistory(snapshot: snapshot, clusterID: item.id)
        #expect(history.story.map(\.kind) == [.capture, .revision, .merge, .split])
        #expect(history.story.first?.riverSource?.originalFilename == item.originalFilename)
        #expect(history.story[1].riverSource?.originalFilename == "revision.txt")
        #expect(history.activity.map(\.kind) == kinds)
        #expect(history.pendingSuggestionCount == 1)
        snapshot.resolved.insert(try #require(snapshot.events.first { $0.kind == .splitProposal }).id)
        #expect(ThreadHistory(snapshot: snapshot, clusterID: item.id).pendingSuggestionCount == 0)
        #expect(snapshot.events.map(\.payloadJSON) == before)
    }

    @Test func scopedActivityIncludesRemovalDecisionsButNotUnrelatedWork() throws {
        let source = memory(0), target = memory(1), other = memory(2)
        var state = ProvenanceSnapshot()
        state.memories[source.id] = source
        state.memberships[source.id] = [other.id]
        state.clusters[target.id] = ProvenanceCluster(id: target.id, title: "Target")
        var moved = ProvenancePayload()
        moved.assignments = [source.id.uuidString: [other.id]]
        moved.previousAssignments = [source.id.uuidString: [target.id]]
        let event = try ProvenanceEvent(kind: .placement, memoryID: source.id, origin: "user", payload: moved)
        let unrelated = try ProvenanceEvent(kind: .processing, memoryID: other.id, payload: ProvenancePayload())
        state.events = [event, unrelated]
        #expect(ThreadHistory(snapshot: state, clusterID: target.id).activity.map(\.id) == [event.id])
        #expect(ThreadHistory(snapshot: state, clusterID: target.id).story.isEmpty)
        #expect(ThreadHistory(snapshot: state).activity.count == 2)
    }

    @Test func historicalViewNeverUsesFutureMergeLineageOrDecisions() throws {
        let a = memory(0), b = memory(1), merged = memory(2).id
        let events = try [
            ProvenanceEvent(kind: .capture, memoryID: a.id, payload: ProvenancePayload(memory: a), timestamp: Date(timeIntervalSince1970: 10)),
            ProvenanceEvent(kind: .capture, memoryID: b.id, payload: ProvenancePayload(memory: b), timestamp: Date(timeIntervalSince1970: 20)),
            ProvenanceEvent(kind: .merge, payload: ProvenancePayload(clusterID: merged, title: "Merged", parents: [a.id, b.id],
                assignments: [a.id.uuidString: [merged], b.id.uuidString: [merged]]), timestamp: Date(timeIntervalSince1970: 30))
        ]
        let past = try ProvenanceSnapshot.replay(events, through: Date(timeIntervalSince1970: 25))
        #expect(ThreadHistory(snapshot: past, clusterID: merged).activity.isEmpty)
        #expect(ThreadHistory(snapshot: past, clusterID: a.id).story.map(\.memoryID) == [a.id])
        let current = try ProvenanceSnapshot.replay(events)
        #expect(ThreadHistory(snapshot: current, clusterID: merged).story.map(\.kind) == [.capture, .capture, .merge])
    }

    @Test func stockCopyAdaptsWithoutChangingStoredOrGeneratedEvidence() throws {
        let payload = ProvenancePayload(rationale: "You renamed this topic.")
        let user = try ProvenanceEvent(kind: .rename, origin: "user", payload: payload)
        let generated = try ProvenanceEvent(kind: .rename, origin: "model", payload: payload)
        let custom = try ProvenanceEvent(kind: .rename, origin: "user", payload: ProvenancePayload(rationale: "Topic is the source title."))
        #expect(user.threadRationale == "You renamed this thread.")
        #expect(try user.payload().rationale == "You renamed this topic.")
        #expect(generated.threadRationale == "You renamed this topic.")
        #expect(custom.threadRationale == "Topic is the source title.")
    }

    private func memory(_ index: Int) -> MemoryItem {
        let id = UUID(uuidString: String(format: "00000000-0000-0000-0000-%012d", index + 1))!
        let date = Date(timeIntervalSince1970: 0)
        return MemoryItem(id: id, kind: .text, createdAt: date, importedAt: date, updatedAt: date,
            state: .indexed, originalFilename: "\(index).txt", userCaption: "Source \(index)", title: "Source \(index)",
            summary: nil, extractedText: nil, tagsJSON: "[]", processingError: nil, modelVersion: nil)
    }
}
