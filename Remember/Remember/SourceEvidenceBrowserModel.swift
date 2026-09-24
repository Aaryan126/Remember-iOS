import Foundation
import Observation

@MainActor @Observable
final class SourceEvidenceBrowserModel {
    var query = ""
    var scope: SourceEvidenceScope = .current
    private(set) var page: SourceEvidencePage?
    private(set) var isLoading = false
    private(set) var errorMessage: String?
    private(set) var didSearch = false
    @ObservationIgnored private var repository: (any SourceEvidenceBrowsing)?
    @ObservationIgnored private var generation = 0
    @ObservationIgnored private var pageQuery = ""

    init(repository: (any SourceEvidenceBrowsing)? = nil) {
        self.repository = repository
    }

    var canLoadMore: Bool {
        guard let page else { return false }
        return page.hits.count < page.totalMatchingPassages && !isLoading
    }

    func search(force: Bool = false, debounce: Bool = false) async {
        if !force, let page, page.scope == scope,
           pageQuery == query.trimmingCharacters(in: .whitespacesAndNewlines), errorMessage == nil { return }
        generation += 1
        let token = generation
        let query = query.trimmingCharacters(in: .whitespacesAndNewlines)
        let scope = scope
        page = nil
        errorMessage = nil
        didSearch = false
        isLoading = false
        guard !query.isEmpty else { return }
        isLoading = true
        defer { if generation == token { isLoading = false } }
        do {
            // SwiftUI cancels the task when its request identity changes.
            if debounce { try await Task.sleep(for: .milliseconds(200)) }
            try Task.checkCancellation()
            let repository = try makeRepository()
            let result = try await repository.search(SourceEvidenceRequest(query: query, scope: scope))
            try Task.checkCancellation()
            guard generation == token, self.query.trimmingCharacters(in: .whitespacesAndNewlines) == query,
                  self.scope == scope else { return }
            pageQuery = query
            page = result
            didSearch = true
        } catch is CancellationError {
            // Cancellation is not an empty-result claim or a user-facing failure.
        } catch {
            guard generation == token, self.query.trimmingCharacters(in: .whitespacesAndNewlines) == query,
                  self.scope == scope else { return }
            errorMessage = Self.message(for: error)
        }
    }

    func loadMore() async {
        guard canLoadMore, let previous = page, query.trimmingCharacters(in: .whitespacesAndNewlines) == pageQuery,
              scope == previous.scope else { return }
        let token = generation
        isLoading = true
        errorMessage = nil
        defer { if generation == token { isLoading = false } }
        do {
            let repository = try makeRepository()
            let result = try await repository.search(SourceEvidenceRequest(
                query: pageQuery, scope: previous.scope, throughSequence: previous.throughSequence,
                offset: previous.hits.count
            ))
            try Task.checkCancellation()
            guard generation == token, query.trimmingCharacters(in: .whitespacesAndNewlines) == pageQuery,
                  scope == previous.scope else { return }
            page = SourceEvidencePage(throughSequence: result.throughSequence, scope: result.scope,
                totalMatchingPassages: result.totalMatchingPassages, hits: previous.hits + result.hits)
        } catch is CancellationError {
        } catch {
            guard generation == token, query.trimmingCharacters(in: .whitespacesAndNewlines) == pageQuery,
                  scope == previous.scope else { return }
            errorMessage = Self.message(for: error)
        }
    }

    func resolve(_ hit: SourceEvidenceHit, through sequence: Int64) async throws -> ResolvedSourceEvidence {
        let repository = try makeRepository()
        return try await repository.resolve(hit, through: sequence)
    }

    private func makeRepository() throws -> any SourceEvidenceBrowsing {
        if let repository { return repository }
        let created = try SourceEvidenceBrowserRepository(store: MemoryStore.live(), originalsDirectory: LibraryFileStore.defaultDirectory())
        repository = created
        return created
    }

    static func message(for error: Error) -> String {
        switch error {
        case SourceEvidenceError.invalidRequest:
            "Use a shorter search, up to 512 characters."
        case SourceEvidenceError.safetyLimitExceeded:
            "This search exceeds the current local browsing limit. No partial results are shown."
        case SourceEvidenceError.invalidLedger:
            "The saved history could not be verified. Your memories have not been changed."
        default:
            "Saved evidence could not be opened. Please try again. Your memories have not been changed."
        }
    }
}
