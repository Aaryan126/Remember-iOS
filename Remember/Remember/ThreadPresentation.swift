import Foundation

/// A source event, rather than a filename, identifies a revision in the River.
nonisolated struct ThreadHistoryTarget: Hashable {
    let memoryID: UUID
    let eventID: UUID
    let isSavedRevision: Bool
    var snapshotID: UUID? = nil

    func index(in events: [ProvenanceEvent]) -> Int? {
        events.firstIndex { $0.id == eventID && $0.riverSource?.id == memoryID }
    }

    func memory(in snapshot: ProvenanceSnapshot) -> MemoryItem? {
        guard let index = index(in: snapshot.events) else { return nil }
        let event = snapshot.events[index]
        if isSavedRevision, let snapshotID, snapshotID != eventID {
            guard let extraction = snapshot.events.first(where: { $0.id == snapshotID }),
                  extraction.kind == .enrichment, extraction.memoryID == memoryID,
                  let payload = try? extraction.payload(), payload.sourceRevisionID == eventID,
                  let memory = payload.memory, memory.id == memoryID,
                  memory.originalFilename == event.riverSource?.originalFilename else { return nil }
            return memory
        }
        return isSavedRevision ? event.riverSource : event.riverMemory(in: snapshot)
    }

    func original(in snapshot: ProvenanceSnapshot) -> SourceEvidenceOriginalState {
        guard let memory = memory(in: snapshot) else { return .unavailable }
        // An old filename may now hold different bytes. Keep the saved text accessible.
        for event in snapshot.events where event.id != eventID && [.capture, .imported, .revision].contains(event.kind) {
            guard let payload = try? event.payload() else { return .versionUnverified }
            if payload.memory?.originalFilename == memory.originalFilename { return .versionUnverified }
        }
        guard let directory = try? LibraryFileStore.defaultDirectory(),
              let url = SourceEvidenceBrowserRepository.readableOriginal(
                filename: memory.originalFilename, directory: directory) else { return .unavailable }
        return .available(url)
    }

    func visibleLimit(in events: [ProvenanceEvent], minimum: Int) -> Int {
        guard let index = index(in: events) else { return minimum }
        // Include the preceding entry as well as the selected entry and newer context.
        return max(minimum, events.count - max(0, index - 1))
    }
}

nonisolated struct MemoryThreadDestination: Identifiable, Hashable {
    let id: UUID
    let title: String
    let isArchived: Bool
    let target: ThreadHistoryTarget

    var label: String { title + (isArchived ? " · Archived" : "") }

    static func resolve(memoryID: UUID, revisionID: UUID? = nil, snapshotID: UUID? = nil,
                        snapshot: ProvenanceSnapshot) -> [Self] {
        let source: ProvenanceEvent?
        if let revisionID {
            source = snapshot.events.first { $0.id == revisionID && $0.riverSource?.id == memoryID }
        } else {
            source = snapshot.events.last { $0.riverSource?.id == memoryID }
        }
        guard let source else { return [] }
        let target = ThreadHistoryTarget(memoryID: memoryID, eventID: source.id,
                                         isSavedRevision: revisionID != nil, snapshotID: snapshotID)
        guard target.memory(in: snapshot) != nil else { return [] }
        let memberships = snapshot.memberships[memoryID, default: []]
        return snapshot.clusters.values.compactMap { cluster in
            let archived = snapshot.archivedClusterIDs.contains(cluster.id)
            guard memberships.contains(cluster.id), !cluster.retired,
                  revisionID != nil || (!archived && snapshot.memories[memoryID]?.isArchived == false),
                  target.index(in: ThreadHistory(snapshot: snapshot, clusterID: cluster.id).story) != nil
            else { return nil }
            return Self(id: cluster.id, title: cluster.title, isArchived: archived, target: target)
        }.sorted { $0.title == $1.title ? $0.id.uuidString < $1.id.uuidString : $0.title < $1.title }
    }
}

/// The finder is independent of the map's bounded rendering window.
nonisolated struct ThreadDirectory {
    struct Entry: Identifiable {
        let id: UUID
        let title: String
        let memoryCount: Int
    }

    let entries: [Entry]

    init(snapshot: ProvenanceSnapshot) {
        var counts: [UUID: Int] = [:]
        for memory in snapshot.memories.values where !memory.isArchived {
            for id in snapshot.memberships[memory.id, default: []] { counts[id, default: 0] += 1 }
        }
        entries = snapshot.clusters.values.compactMap { cluster in
            guard !cluster.retired, !snapshot.archivedClusterIDs.contains(cluster.id),
                  let count = counts[cluster.id], count > 0 else { return nil }
            return Entry(id: cluster.id, title: cluster.title, memoryCount: count)
        }.sorted { $0.title == $1.title ? $0.id.uuidString < $1.id.uuidString : $0.title < $1.title }
    }

    func matching(_ query: String) -> [Entry] {
        let terms = query.split(whereSeparator: \.isWhitespace).map(String.init)
        return entries.filter { entry in terms.allSatisfy { entry.title.localizedStandardContains($0) } }
    }
}

/// Read-only projections: suppress routine activity in the story, never in storage.
nonisolated struct ThreadHistory {
    let activity: [ProvenanceEvent]
    let story: [ProvenanceEvent]
    let pendingSuggestionCount: Int

    init(snapshot: ProvenanceSnapshot, clusterID: UUID? = nil) {
        if let clusterID {
            // Use only the supplied snapshot, including its lineage when viewing the past.
            let lineage = snapshot.ancestors(of: clusterID)
            activity = snapshot.events.filter { event in
                guard let payload = try? event.payload() else { return false }
                if let id = payload.clusterID, lineage.contains(id) { return true }
                if !lineage.isDisjoint(with: payload.parents) { return true }
                if payload.assignments.values.contains(where: { !lineage.isDisjoint(with: $0) }) { return true }
                if payload.previousAssignments.values.contains(where: { !lineage.isDisjoint(with: $0) }) { return true }
                if let id = event.memoryID {
                    return snapshot.memberships[id, default: []].contains(clusterID) || lineage.contains(id)
                }
                return false
            }
        } else {
            activity = snapshot.events
        }
        story = activity.filter { $0.riverSource != nil || [.merge, .split].contains($0.kind) }
        pendingSuggestionCount = activity.filter { $0.kind == .splitProposal && !snapshot.resolved.contains($0.id) }.count
    }
}

extension ProvenanceEvent {
    /// Translate only known stock UI copy. Source/model text and immutable payloads stay verbatim.
    nonisolated var threadRationale: String? {
        guard let rationale = try? payload().rationale else { return nil }
        guard origin == "user" else { return rationale }
        switch (kind, rationale) {
        case (.rename, "You renamed this topic."): return "You renamed this thread."
        case (.placement, "You chose these topics. Automatic organization will preserve this assignment."):
            return "You chose these threads. Automatic organization will preserve this assignment."
        case (.revert, "You restored the previous topic name."): return "You restored the previous thread name."
        default: return rationale
        }
    }
}
