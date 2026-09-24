import Foundation

/// Presentation policy only. Retrieval still uses the existing local library and
/// version-bound source engines; neither scope grants permission for AI calls.
nonisolated struct UnifiedMemorySearchOptions: Equatable, Hashable {
    var includeHistory = false
    var sourceTextOnly = false

    var scope: SourceEvidenceScope { includeHistory ? .includeHistory : .current }
    var hasActiveFilters: Bool { includeHistory || sourceTextOnly }
    var activeFilterSummary: String {
        [includeHistory ? "Including history" : nil, sourceTextOnly ? "Source text only" : nil]
            .compactMap { $0 }.joined(separator: " · ")
    }

    func separateHits(in page: SourceEvidencePage, cardMemoryIDs: Set<UUID>) -> [SourceEvidenceHit] {
        page.hits.filter { hit in
            guard includeHistory || (hit.isCurrentVersion && !hit.isArchived) else { return false }
            // Current matches accompany their cards. A source without a current
            // indexed card (e.g. pending analysis) must remain discoverable.
            return sourceTextOnly || !hit.isCurrentVersion || hit.isArchived || !cardMemoryIDs.contains(hit.id.memoryID)
        }
    }

    func snippet(for memoryID: UUID, in page: SourceEvidencePage) -> SourceEvidenceHit? {
        page.hits.first { $0.id.memoryID == memoryID && $0.isCurrentVersion && !$0.isArchived }
    }
}
