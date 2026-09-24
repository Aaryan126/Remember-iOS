import Foundation

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
