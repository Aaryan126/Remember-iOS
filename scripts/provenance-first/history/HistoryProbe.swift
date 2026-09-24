import Foundation
import GRDB

// Input extends DiagnosticBatch.runs with optional queries and tombstonedSourceIDs.
// A query contains id, afterEvent (diagnostic command ID), optional scope (current),
// optional sourceIDs (fixture names such as localc01), and optional limit (10000).
// No query labels, expected evidence, or answerability enter the history index.
struct HistoryBatch: Decodable { let schemaVersion: Int; let runs: [HistoryRun] }
struct HistoryRun: Decodable {
    let id: String
    let queries: [HistoryQuery]?
    let tombstonedSourceIDs: [String]?
}
struct HistoryQuery: Decodable {
    let id: String
    let afterEvent: String
    let scope: HistoryScope?
    let sourceIDs: [String]?
    let limit: Int?
}
struct HistoryPrefix: Codable, Equatable {
    let id: String
    let sequence: Int64
    let current: [HistoryCandidate]
    let includeHistory: [HistoryCandidate]
}
struct HistoryQueryResult: Codable {
    let id: String
    let afterEvent: String
    let scope: HistoryScope
    let sequence: Int64
    let candidates: [HistoryCandidate]
}
struct HistoryProjection: Codable {
    let schemaVersion: Int
    let id: String
    let batchSHA256: String
    let bindingsSHA256: String
    let ledgerSHA256: String
    let restartVerified: Bool
    let prefixes: [HistoryPrefix]
    let queries: [HistoryQueryResult]
}
struct HistoryReceipt: Codable {
    let schemaVersion: Int
    let id: String
    let batchSHA256: String
    let bindingsSHA256: String
    let ledgerSHA256: String
    let projectionSHA256: String
    let projection: String
    let prefixCount: Int
    let queryCount: Int
    let restartVerified: Bool
}

enum HistoryProbe {
    // This executes before the unchanged replay harness can inspect its receipts.
    static func validateOutput(_ output: URL) throws {
        let canonical = output.standardizedFileURL
        try diagnosticRequire(canonical.resolvingSymlinksInPath().path == canonical.path,
                              "history output may not contain symlink ancestors")
        if let iterator = FileManager.default.enumerator(at: canonical,
                includingPropertiesForKeys: [.isSymbolicLinkKey], options: []) {
            for case let child as URL in iterator {
                let values = try child.resourceValues(forKeys: [.isSymbolicLinkKey])
                try diagnosticRequire(values.isSymbolicLink != true
                    && child.standardizedFileURL.resolvingSymlinksInPath().path.hasPrefix(canonical.path + "/"),
                    "history output contains a symlink or escaped descendant")
            }
        }
    }

    static func checkedAttempt(_ name: String, key: String, output: URL) throws -> URL {
        let prefix = key + "-"
        try diagnosticRequire(name.hasPrefix(prefix) && UUID(uuidString: String(name.dropFirst(prefix.count))) != nil,
                              "invalid native receipt attempt path")
        let root = output.appendingPathComponent(name).standardizedFileURL
        try diagnosticRequire(root.resolvingSymlinksInPath().path == root.path
            && root.path.hasPrefix(output.standardizedFileURL.path + "/"), "escaped native attempt path")
        return root
    }

    static func run(input: URL, output: URL, bindings: URL, maximumRuns: Int?) async throws {
        let inputData = try Data(contentsOf: input)
        let batch = try JSONDecoder().decode(HistoryBatch.self, from: inputData)
        try diagnosticRequire(batch.schemaVersion == 1, "invalid history batch schema")
        try validateOutput(output)
        for run in batch.runs {
            let key = diagnosticHash(Data(run.id.utf8))
            let path = output.appendingPathComponent("\(key).receipt.json")
            if FileManager.default.fileExists(atPath: path.path) {
                let receipt = try JSONDecoder().decode(DiagnosticRunReceipt.self, from: Data(contentsOf: path))
                _ = try checkedAttempt(receipt.attempt, key: key, output: output)
            }
        }
        // The unchanged harness proves append-only persistence, expected organization,
        // every command prefix and reopening. It also owns per-library pause boundaries.
        try await DiagnosticReplay.run(input: input, output: output, bindings: bindings, maximumRuns: maximumRuns)
        let batchHash = diagnosticHash(inputData)
        let bindingsHash = diagnosticHash(try Data(contentsOf: bindings))
        for run in batch.runs {
            let key = diagnosticHash(Data(run.id.utf8))
            let receiptURL = output.appendingPathComponent("\(key).receipt.json")
            guard FileManager.default.fileExists(atPath: receiptURL.path) else { continue }
            let receipt = try JSONDecoder().decode(DiagnosticRunReceipt.self, from: Data(contentsOf: receiptURL))
            let root = try checkedAttempt(receipt.attempt, key: key, output: output)
            let ledgerData = try Data(contentsOf: root.appendingPathComponent("ledger.json"))
            let events = try JSONDecoder().decode([ProvenanceEvent].self, from: ledgerData)
            let historyReceiptURL = output.appendingPathComponent("\(key).history.receipt.json")
            let projectionName = "\(key).projection.json"
            let projectionURL = output.appendingPathComponent(projectionName)
            if FileManager.default.fileExists(atPath: historyReceiptURL.path) {
                let saved = try JSONDecoder().decode(HistoryReceipt.self, from: Data(contentsOf: historyReceiptURL))
                let savedProjectionHash = diagnosticHash(try Data(contentsOf: projectionURL))
                try diagnosticRequire(saved.id == run.id && saved.batchSHA256 == batchHash
                    && saved.bindingsSHA256 == bindingsHash && saved.ledgerSHA256 == diagnosticHash(ledgerData)
                    && saved.projection == projectionName
                    && saved.projectionSHA256 == savedProjectionHash,
                    "history resume receipt mismatch")
                continue
            }
            let tombstones = Set((run.tombstonedSourceIDs ?? []).map(diagnosticID))
            func project(_ ledger: [ProvenanceEvent]) throws -> [HistoryPrefix] {
                try receipt.prefixes.map { prefix in
                    try diagnosticRequire(prefix.ledgerCount > 0 && prefix.ledgerCount <= ledger.count,
                                          "invalid ledger prefix count")
                    let sequence = ledger[prefix.ledgerCount - 1].sequence!
                    return HistoryPrefix(id: prefix.id, sequence: sequence,
                        current: try HistoryIndex.candidates(events: ledger, request: HistoryRequest(
                            throughSequence: sequence, tombstonedSourceIDs: tombstones)),
                        includeHistory: try HistoryIndex.candidates(events: ledger, request: HistoryRequest(
                            scope: .includeHistory, throughSequence: sequence, tombstonedSourceIDs: tombstones)))
                }
            }
            let prefixes = try project(events)
            let reopened = try MemoryStore(databaseURL: root.appendingPathComponent("db.sqlite"))
            do {
                let reloaded = try await reopened.provenanceEvents()
                let rebuilt = try project(reloaded)
                try diagnosticRequire(rebuilt == prefixes, "history projection changed after reopen")
                try reopened.databasePool.close()
            } catch { try? reopened.databasePool.close(); throw error }
            let queries = run.queries ?? []
            try diagnosticRequire(Set(queries.map(\.id)).count == queries.count, "duplicate history query IDs")
            let results = try queries.map { query -> HistoryQueryResult in
                guard let prefix = prefixes.first(where: { $0.id == query.afterEvent }) else {
                    throw DiagnosticFailure(description: "unknown query prefix: \(query.afterEvent)")
                }
                let scope = query.scope ?? .current
                let candidates = try HistoryIndex.candidates(events: events, request: HistoryRequest(
                    scope: scope, throughSequence: prefix.sequence,
                    sourceIDs: query.sourceIDs.map { Set($0.map(diagnosticID)) }, limit: query.limit ?? 10_000,
                    tombstonedSourceIDs: tombstones))
                return HistoryQueryResult(id: query.id, afterEvent: query.afterEvent, scope: scope,
                                          sequence: prefix.sequence, candidates: candidates)
            }
            let projection = HistoryProjection(schemaVersion: 1, id: run.id, batchSHA256: batchHash,
                bindingsSHA256: bindingsHash, ledgerSHA256: diagnosticHash(ledgerData), restartVerified: true,
                prefixes: prefixes, queries: results)
            let data = try diagnosticJSON(projection)
            try data.write(to: projectionURL, options: .atomic)
            let historyReceipt = HistoryReceipt(schemaVersion: 1, id: run.id, batchSHA256: batchHash,
                bindingsSHA256: bindingsHash, ledgerSHA256: diagnosticHash(ledgerData), projectionSHA256: diagnosticHash(data),
                projection: projectionName, prefixCount: prefixes.count, queryCount: results.count, restartVerified: true)
            try diagnosticJSON(historyReceipt).write(to: historyReceiptURL, options: .atomic)
        }
    }
}
