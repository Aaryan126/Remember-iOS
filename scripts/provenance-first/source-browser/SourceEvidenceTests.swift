import Foundation

@main
struct SourceEvidenceTests {
    nonisolated struct Failure: Error { let message: String }

    nonisolated static func expect(_ value: Bool, _ message: String = "assertion failed") throws {
        if !value { throw Failure(message: message) }
    }

    nonisolated static func uuid(_ value: Int) -> UUID {
        UUID(uuidString: String(format: "00000000-0000-0000-0000-%012d", value))!
    }

    nonisolated static func memory(_ id: Int = 1, text: String? = "Receipt code ORBIT-27", caption: String? = nil,
                                  filename: String = "first.txt", archived: Bool = false, partial: Bool = false) -> MemoryItem {
        MemoryItem(id: uuid(id), kind: .text, createdAt: Date(timeIntervalSince1970: 1),
                   importedAt: Date(timeIntervalSince1970: 1), updatedAt: Date(timeIntervalSince1970: 1),
                   state: .indexed, originalFilename: filename, userCaption: caption,
                   title: "Generated unicorn title", summary: "Generated unicorn summary", extractedText: text,
                   tagsJSON: "[\"unicorn\"]", processingError: nil, modelVersion: nil,
                   analysisIsPartial: partial, isArchived: archived)
    }

    nonisolated static func event(_ sequence: Int, _ kind: ProvenanceKind, _ memory: MemoryItem? = nil,
                                 parent: Int? = nil, version: Int = 1, eventID: Int? = nil,
                                 restoredFrom: Int? = nil) throws -> ProvenanceEvent {
        var payload = ProvenancePayload()
        payload.version = version
        payload.memory = memory
        payload.sourceRevisionID = parent.map(uuid)
        payload.referencedEventID = restoredFrom.map(uuid)
        payload.rationale = "Generated unicorn rationale"
        var event = try ProvenanceEvent(kind: kind, memoryID: memory?.id,
                                        origin: restoredFrom == nil ? "system" : "user", payload: payload,
                                        timestamp: Date(timeIntervalSince1970: Double(sequence)), id: uuid(eventID ?? sequence + 100))
        event.sequence = Int64(sequence)
        return event
    }

    nonisolated static func search(_ events: [ProvenanceEvent], _ query: String = "receipt",
                                  scope: SourceEvidenceScope = .current, through: Int64? = nil,
                                  offset: Int = 0, limit: Int = 30,
                                  ids: Set<UUID>? = nil, excluded: Set<UUID> = []) throws -> SourceEvidencePage {
        let records = try SourceEvidenceStoreAdapter.records(events, through: through)
        return try SourceEvidenceSearch.search(records: records, request: SourceEvidenceRequest(
            query: query, scope: scope, throughSequence: through, memoryIDs: ids,
            excludedMemoryIDs: excluded, offset: offset, limit: limit
        ))
    }

    nonisolated static func rejects(_ expected: SourceEvidenceError, _ operation: () throws -> Void) throws {
        do { try operation() } catch let error as SourceEvidenceError {
            try expect(error == expected, "wrong rejection: \(error)")
            return
        }
        throw Failure(message: "expected rejection \(expected)")
    }

    static func main() async throws {
        var passed: [String] = []
        var failed: [String] = []
        func test(_ name: String, _ body: () throws -> Void) {
            do { try body(); passed.append(name) }
            catch { failed.append("\(name): \(error)") }
        }
        let first = try event(1, .capture, memory())
        let revised = try event(2, .revision, memory(text: "Receipt code NOVA-42", filename: "second.txt"), parent: 101)
        let ledger = [first, revised]
        test("current revision replaces old evidence") {
            let result = try search(ledger)
            try expect(result.hits.count == 1 && result.hits[0].quote.contains("NOVA-42"))
            try expect(result.hits[0].revision == 1 && result.hits[0].id.revisionID == uuid(102))
            try expect(try search(ledger, "ORBIT").hits.isEmpty)
        }
        test("history retains exact revision identities") {
            let result = try search(ledger, scope: .includeHistory)
            try expect(result.hits.count == 2 && Set(result.hits.map(\.id.revisionID)) == [uuid(101), uuid(102)])
            try expect(result.hits.filter(\.isCurrentVersion).count == 1)
        }
        test("historical prefix excludes newer revisions") {
            let result = try search(ledger, through: 1)
            try expect(result.throughSequence == 1 && result.hits[0].quote.contains("ORBIT"))
            try expect(result.hits[0].isCurrentVersion)
        }
        test("boundary zero returns empty history") {
            try expect(try search(ledger, scope: .includeHistory, through: 0).hits.isEmpty)
        }
        test("future boundary reports actual available boundary") {
            try expect(try search(ledger, through: 100).throughSequence == 2)
        }
        test("late enrichment stays attached to old version") {
            let enriched = try event(3, .enrichment, memory(text: "Receipt code ORBIT-27 late detail"), parent: 101)
            try expect(try search(ledger + [enriched], "late").hits.isEmpty)
            let result = try search(ledger + [enriched], "late", scope: .includeHistory)
            try expect(result.hits.count == 1 && result.hits[0].id.revisionID == uuid(101))
            try expect(result.hits[0].id.snapshotID == uuid(103) && result.hits[0].snapshotSequence == 3)
            try expect(!result.hits[0].isCurrentVersion && result.hits[0].sourceSequence == 1)
        }
        test("future enrichment cannot leak into earlier prefix") {
            let enriched = try event(3, .enrichment, memory(text: "Receipt late detail"), parent: 101)
            try expect(try search(ledger + [enriched], "late", scope: .includeHistory, through: 2).hits.isEmpty)
        }
        test("future unsupported payload is not decoded") {
            let future = try event(3, .enrichment, memory(), parent: 101, version: 999)
            try expect(try search(ledger + [future], through: 2).hits.count == 1)
            do { _ = try search(ledger + [future]) }
            catch ProvenanceError.unsupportedVersion { return }
            throw Failure(message: "unsupported visible payload accepted")
        }
        test("archive is excluded by default and explicitly included in history") {
            let archive = try event(2, .archive, memory(archived: true), parent: 101)
            try expect(try search([first, archive]).hits.isEmpty)
            let result = try search([first, archive], scope: .includeHistory)
            try expect(result.hits.count == 1 && result.hits[0].isArchived)
            try expect(try search([first, archive], through: 1).hits.count == 1)
        }
        test("restore makes current evidence visible without new revision") {
            let archive = try event(2, .archive, memory(archived: true), parent: 101)
            let restore = try event(3, .restore, memory(), parent: 101)
            let result = try search([first, archive, restore])
            try expect(result.hits.count == 1 && !result.hits[0].isArchived && result.hits[0].revision == 0)
        }
        test("organization events cannot mint evidence") {
            let recap = try event(2, .recap)
            try expect(try search([first, recap], "unicorn").hits.isEmpty)
            try expect(try search([first, recap]).hits.count == 1)
        }
        test("generated titles summaries and tags cannot match") {
            try expect(try search([first], "unicorn").hits.isEmpty)
        }
        test("metadata and processing do not replace source text") {
            let metadata = try event(2, .metadata, memory(text: "unicorn"), parent: 101)
            let processing = try event(3, .processing, memory(text: "unicorn"), parent: 101)
            try expect(try search([first, metadata, processing], "unicorn").hits.isEmpty)
            try expect(try search([first, metadata, processing]).hits[0].id.snapshotID == uuid(101))
        }
        test("empty source never falls back to generated summary") {
            try expect(try search([event(1, .capture, memory(text: nil))], "unicorn").hits.isEmpty)
        }
        test("distinct captions are retained and identical ones deduplicated") {
            let same = try event(1, .capture, memory(text: "receipt", caption: "receipt"))
            try expect(try search([same]).hits.count == 1)
            let distinct = try event(1, .capture, memory(text: "receipt one", caption: "receipt two"))
            let result = try search([distinct])
            try expect(result.hits.count == 2 && Set(result.hits.map(\.id.field)) == [.extractedText, .userCaption])
        }
        test("import history gap persists across revisions") {
            let imported = try event(1, .imported, memory())
            let result = try search([imported, revised], scope: .includeHistory)
            try expect(result.hits.count == 2 && result.hits.allSatisfy(\.importedHistoryGap))
        }
        test("partial extraction and unverified asset state stay explicit") {
            let partial = try event(2, .enrichment, memory(partial: true), parent: 101)
            let hit = try search([first, partial]).hits[0]
            try expect(hit.analysisIsPartial && hit.id.snapshotID == uuid(102))
            try expect(hit.originalAssetAvailability == "notChecked" && hit.mediaLocatorAvailability == "notRetainedInLedger")
        }
        test("source filters and exclusions apply to every revision") {
            let other = try event(3, .capture, memory(2))
            try expect(try search(ledger + [other], scope: .includeHistory, ids: [uuid(2)]).hits.count == 1)
            let result = try search(ledger + [other], scope: .includeHistory, excluded: [uuid(1)])
            try expect(result.hits.count == 1 && result.hits[0].id.memoryID == uuid(2))
            try expect(try search(ledger, ids: []).hits.isEmpty)
        }
        test("ranking happens before pagination") {
            let weak = try event(1, .capture, memory(text: "alpha"))
            let strong = try event(2, .capture, memory(2, text: "alpha beta"))
            let result = try search([weak, strong], "alpha beta", limit: 1)
            try expect(result.totalMatchingPassages == 2 && result.hits[0].id.memoryID == uuid(2))
            try expect(try search([weak, strong], "alpha beta", offset: 1, limit: 1).hits[0].id.memoryID == uuid(1))
            try expect(try search([weak, strong], "alpha beta", offset: Int.max).hits.isEmpty)
        }
        test("deterministic ties prefer newer source sequence") {
            let other = try event(2, .capture, memory(2))
            let a = try search([first, other])
            let b = try search([first, other])
            try expect(a.hits.map(\.id) == b.hits.map(\.id) && a.hits[0].id.memoryID == uuid(2))
        }
        test("case diacritics and punctuation tokenize predictably") {
            let source = try event(1, .capture, memory(text: "CAFÉ receipt 27"))
            try expect(try search([source], "cafe").hits.count == 1)
            try expect(try search([source], "!!!").hits.isEmpty)
            try expect(try search([source], "  ").hits.isEmpty)
        }
        test("substrings alone are not word matches") {
            try expect(try search([first], "rece").hits.isEmpty)
        }
        test("long source uses original chunker and stable distinct identities") {
            let text = String(repeating: "receipt evidence. ", count: 180)
            let source = try event(1, .capture, memory(text: text))
            let result = try search([source])
            let chunks = MemoryTextChunker.chunks(from: text, locatorPrefix: "Retained extractedText", extractionMethod: .plainText)
            try expect(result.hits.map(\.quote) == chunks.map(\.text))
            try expect(Set(result.hits.map(\.id)).count == chunks.count && chunks.count > 1)
            try expect(result.hits.allSatisfy { $0.quote.count <= MemoryTextChunker.targetLength })
        }
        test("duplicate and unordered sequences reject") {
            try rejects(.invalidLedger) { _ = try search([first, first]) }
            try rejects(.invalidLedger) { _ = try search([revised, first]) }
        }
        test("duplicate event identity rejects even across distinct sequences") {
            let duplicate = try event(2, .capture, memory(2), eventID: 101)
            try rejects(.invalidLedger) { _ = try search([first, duplicate]) }
        }
        test("missing sequence rejects") {
            var missing = first
            missing.sequence = nil
            try rejects(.invalidLedger) { _ = try search([missing]) }
        }
        test("zero sequence rejects") {
            try rejects(.invalidLedger) { _ = try search([event(0, .capture, memory())]) }
        }
        test("missing source snapshot rejects") {
            try rejects(.invalidLedger) { _ = try search([event(1, .capture)]) }
        }
        test("source identity mismatch rejects") {
            let records = try SourceEvidenceStoreAdapter.records([first], through: nil)
            let source = records[0]
            let broken = SourceEvidenceRecord(sequence: 1, id: source.id, timestamp: source.timestamp,
                kind: .capture, memoryID: uuid(2), sourceRevisionID: nil, restoredFromRevisionID: nil, snapshot: source.snapshot)
            try rejects(.invalidLedger) { _ = try SourceEvidenceSearch.search(records: [broken], request: .init(query: "receipt")) }
        }
        test("duplicate capture and orphan revision reject") {
            try rejects(.invalidLedger) { _ = try search([first, event(2, .capture, memory())]) }
            try rejects(.invalidLedger) { _ = try search([revised]) }
        }
        test("stale revision predecessor rejects") {
            let stale = try event(3, .revision, memory(), parent: 101)
            try rejects(.invalidLedger) { _ = try search(ledger + [stale]) }
        }
        test("legacy note restoration is a new current revision with exact old source text") {
            let restore = try event(3, .revision, memory(), restoredFrom: 101)
            let result = try search(ledger + [restore])
            try expect(result.hits.count == 1 && result.hits[0].quote.contains("ORBIT-27"))
            try expect(result.hits[0].revision == 2 && result.hits[0].id.revisionID == uuid(103))
            try expect(try search(ledger + [restore], scope: .includeHistory).hits.count == 3)
        }
        test("legacy restoration validates against original snapshot rather than enrichment") {
            let enriched = try event(2, .enrichment, memory(text: "Receipt enriched later"), parent: 101)
            let revision = try event(3, .revision, memory(text: "Receipt replacement", filename: "second.txt"), parent: 101)
            let restore = try event(4, .revision, memory(), restoredFrom: 101)
            try expect(try search([first, enriched, revision, restore]).hits[0].quote.contains("ORBIT-27"))
        }
        test("legacy restoration rejects nonexistent cross-source or mismatched targets") {
            try rejects(.invalidLedger) { _ = try search(ledger + [event(3, .revision, memory(), restoredFrom: 999)]) }
            try rejects(.invalidLedger) { _ = try search(ledger + [event(3, .revision, memory(text: "forged"), restoredFrom: 101)]) }
            let other = try event(3, .capture, memory(2))
            try rejects(.invalidLedger) { _ = try search(ledger + [other, event(4, .revision, memory(), restoredFrom: 103)]) }
        }
        test("legacy note restore compatibility does not admit media revisions") {
            let original = MemoryItem(id: uuid(1), kind: .image, createdAt: Date(timeIntervalSince1970: 1),
                importedAt: Date(timeIntervalSince1970: 1), updatedAt: Date(timeIntervalSince1970: 1),
                state: .indexed, originalFilename: "image.jpg", userCaption: nil, title: nil, summary: nil,
                extractedText: "receipt", tagsJSON: "[]", processingError: nil, modelVersion: nil)
            try rejects(.invalidLedger) {
                _ = try search([event(1, .capture, original), event(2, .revision, original, restoredFrom: 101)])
            }
        }
        test("enrichment with different original rejects") {
            let bad = try event(2, .enrichment, memory(filename: "wrong.txt"), parent: 101)
            try rejects(.invalidLedger) { _ = try search([first, bad]) }
        }
        test("unknown or missing enrichment parent rejects") {
            try rejects(.invalidLedger) { _ = try search([first, event(2, .enrichment, memory(), parent: 999)]) }
            try rejects(.invalidLedger) { _ = try search([first, event(2, .enrichment, memory())]) }
        }
        test("stale archive and inconsistent archive state reject") {
            try rejects(.invalidLedger) { _ = try search(ledger + [event(3, .archive, memory(archived: true), parent: 101)]) }
            try rejects(.invalidLedger) { _ = try search([first, event(2, .archive, memory(), parent: 101)]) }
        }
        test("metadata cannot silently archive source") {
            try rejects(.invalidLedger) { _ = try search([first, event(2, .metadata, memory(archived: true), parent: 101)]) }
        }
        test("revision cannot silently change archive state") {
            try rejects(.invalidLedger) { _ = try search([first, event(2, .revision, memory(archived: true), parent: 101)]) }
        }
        test("organization event carrying memory snapshot rejects") {
            try rejects(.invalidLedger) { _ = try search([first, event(2, .recap, memory(), parent: 101)]) }
        }
        test("thread archive without source snapshot is harmless") {
            try expect(try search([first, event(2, .archive)]).hits.count == 1)
        }
        test("invalid requests reject rather than truncate") {
            try rejects(.invalidRequest) { _ = try search([first], limit: 0) }
            try rejects(.invalidRequest) { _ = try search([first], limit: 101) }
            try rejects(.invalidRequest) { _ = try search([first], offset: -1) }
            try rejects(.invalidRequest) { _ = try search([first], through: -1) }
            try rejects(.invalidRequest) { _ = try search([first], String(repeating: "a", count: 513)) }
        }
        test("empty ledger is an honest empty page") {
            let page = try search([])
            try expect(page.throughSequence == 0 && page.hits.isEmpty && page.totalMatchingPassages == 0)
        }
        test("oversized field rejects rather than silently truncates") {
            let large = try event(1, .capture, memory(text: String(repeating: "a", count: SourceEvidenceSearch.maximumFieldBytes + 1)))
            try rejects(.safetyLimitExceeded) { _ = try search([large], "a") }
        }
        test("oversized ledger rejects") {
            let records = try SourceEvidenceStoreAdapter.records([first], through: nil)
            try rejects(.safetyLimitExceeded) {
                _ = try SourceEvidenceSearch.search(records: Array(repeating: records[0], count: SourceEvidenceSearch.maximumEvents + 1), request: .init(query: "receipt"))
            }
        }
        test("aggregate text budget rejects rather than returning a partial page") {
            let text = String(repeating: "x", count: SourceEvidenceSearch.maximumFieldBytes)
            let events = try (1...9).map { try event($0, .capture, memory($0, text: text)) }
            try rejects(.safetyLimitExceeded) { _ = try search(events, "receipt") }
        }
        test("cancellation propagates without partial success") {
            let records = try SourceEvidenceStoreAdapter.records(ledger, through: nil)
            var checks = 0
            do {
                _ = try SourceEvidenceSearch.search(records: records, request: .init(query: "receipt"), checkCancellation: {
                    checks += 1
                    if checks == 3 { throw CancellationError() }
                })
            } catch is CancellationError { return }
            throw Failure(message: "cancellation swallowed")
        }
        // Only the storage transport is a fixture. The real adapter/service and
        // production model Codable implementations run above and below.
        let store = MemoryStore(events: ledger)
        do {
            let page = try await SourceEvidenceSearchService(store: store).search(.init(query: "receipt"))
            let reads = await store.readCount
            try expect(page.hits.count == 1 && reads == 1)
            passed.append("service performs one read and returns source projection")
        } catch { failed.append("service: \(error)") }
        do {
            let service = SourceEvidenceSearchService(store: store)
            do { _ = try await service.search(.init(query: "receipt", limit: 0)) }
            catch SourceEvidenceError.invalidRequest {
                let reads = await store.readCount
                try expect(reads == 1)
                passed.append("invalid service request performs no ledger read")
            }
            try expect(passed.last == "invalid service request performs no ledger read")
        } catch { failed.append("service invalid request: \(error)") }
        do {
            let service = SourceEvidenceSearchService(store: store)
            let operation = Task { try await service.search(.init(query: "receipt")) }
            operation.cancel()
            do { _ = try await operation.value }
            catch is CancellationError {
                let reads = await store.readCount
                try expect(reads == 1)
                passed.append("cancelled service request performs no ledger read")
            }
            try expect(passed.last == "cancelled service request performs no ledger read")
        } catch { failed.append("service cancellation: \(error)") }
        do {
            let failing = SourceEvidenceSearchService(store: MemoryStore(events: ledger, fails: true))
            do { _ = try await failing.search(.init(query: "receipt")) }
            catch FixtureStoreError.offline { passed.append("storage failure propagates without empty success") }
            try expect(passed.last == "storage failure propagates without empty success")
        } catch { failed.append("service storage failure: \(error)") }
        let report: [String: Any] = ["passed": passed.count, "failed": failed.count, "tests": passed, "failures": failed]
        print(String(decoding: try JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]), as: UTF8.self))
        if !failed.isEmpty { throw Failure(message: "native tests failed") }
    }
}
