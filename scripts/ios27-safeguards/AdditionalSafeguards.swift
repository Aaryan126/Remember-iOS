import Foundation
import GRDB
import Testing
@testable import Remember

struct AdditionalSafeguards {
    @Test func ledgerRejectsUpdateAndDelete() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("AppendOnly-" + UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let store = try MemoryStore(databaseURL: root.appendingPathComponent("test.sqlite"))
        let date = Date(timeIntervalSince1970: 1_800_000_000)
        let item = MemoryItem(id: UUID(), kind: .text, createdAt: date, importedAt: date, updatedAt: date,
            state: .captured, originalFilename: "fictional.txt", userCaption: "Fictional source", title: "Fictional source",
            summary: nil, extractedText: nil, tagsJSON: "[]", processingError: nil, modelVersion: nil)
        try await store.insertIfNeeded(item)
        let before = try await store.provenanceEvents()
        let pool = await store.databasePool
        for sql in ["UPDATE provenanceEvent SET origin = 'modified'", "DELETE FROM provenanceEvent"] {
            do {
                try await pool.write { database in try database.execute(sql: sql) }
                Issue.record("Immutable ledger accepted mutation")
            } catch is DatabaseError { }
        }
        #expect(try await store.provenanceEvents().map(\.payloadJSON) == before.map(\.payloadJSON))
        try await store.insertIfNeeded(item)
        #expect(try await store.provenanceEvents().count == before.count)
    }

    @Test func thresholdAdjacentScoresHaveExactInclusiveSemantics() {
        let id = UUID()
        let candidate = D3OrganizationPolicy.Candidate(id: id, memberships: [id], contextual: 1, lexical: 1)
        let threshold = D3OrganizationPolicy.threshold
        for (score, accepted) in [(threshold.nextDown, false), (threshold, true), (threshold.nextUp, true)] {
            let result = D3OrganizationPolicy.decide(retrieved: [candidate], memberCounts: [id: 1], scores: [id: score])
            #expect((result.selected == id) == accepted)
        }
    }

    @Test func thirdSupportCannotRescueTwoFailuresAmongFirstThree() {
        let thread = UUID()
        let members = (0..<4).map { _ in UUID() }
        let candidates = members.map { D3OrganizationPolicy.Candidate(id: $0, memberships: [thread], contextual: 1, lexical: 1) }
        let scores = [members[0]: 0.1, members[1]: 0.1, members[2]: 1.0, members[3]: 1.0]
        #expect(D3OrganizationPolicy.decide(retrieved: candidates, memberCounts: [thread: 4], scores: scores).selected == nil)
    }
}
