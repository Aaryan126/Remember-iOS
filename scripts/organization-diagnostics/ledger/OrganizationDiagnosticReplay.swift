import CryptoKit
import Foundation
import GRDB

// Compiled alongside unchanged production sources in an isolated simulator app.
// The oracle is supplied by policy commands, never inferred from replay output.
struct DiagnosticBatch: Codable {
    let schemaVersion: Int
    let runs: [DiagnosticRun]
}

struct DiagnosticRun: Codable {
    let id: String
    let events: [DiagnosticCommand]
}

struct DiagnosticSource: Codable {
    let id: String
    let text: String
    let modality: String
}

struct DiagnosticExpected: Codable, Equatable {
    var memberships: [String]
    var archived: Bool
    var textSHA256: String
    var revision: Int
}

struct DiagnosticCommand: Codable {
    let id: String
    let kind: String
    let source: DiagnosticSource?
    let target: String?
    let text: String?
    let assignments: [String]?
    let expectedState: [String: DiagnosticExpected]
}

struct DiagnosticFailure: Error, CustomStringConvertible {
    let description: String
}

func diagnosticRequire(_ condition: @autoclosure () -> Bool, _ message: String) throws {
    if !condition() { throw DiagnosticFailure(description: message) }
}

func diagnosticHash(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

func diagnosticID(_ name: String) -> UUID {
    // Production capture creates a singleton cluster whose UUID equals the memory UUID.
    let canonical = name.hasPrefix("t:c") ? "local" + name.dropFirst(2) : name
    let bytes = Array(SHA256.hash(data: Data(("organization-diagnostics-v1:" + canonical).utf8)).prefix(16))
    return UUID(uuid: (bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5], bytes[6], bytes[7],
                       bytes[8], bytes[9], bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15]))
}

func diagnosticJSON<T: Encodable>(_ value: T) throws -> Data {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys, .prettyPrinted]
    return try encoder.encode(value)
}

struct DiagnosticPrefixReceipt: Codable {
    let id: String
    let ledgerCount: Int
    let stateSHA256: String
}

struct DiagnosticRunReceipt: Codable {
    let schemaVersion: Int
    let id: String
    let inputSHA256: String
    let batchSHA256: String
    let bindingsSHA256: String
    let attempt: String
    let ledgerSHA256: String
    let prefixCount: Int
    let ledgerCount: Int
    let elapsedSeconds: Double
    let restartVerified: Bool
    let historicalPrefixesVerified: Int
    let prefixes: [DiagnosticPrefixReceipt]
}

final class DiagnosticHarness {
    let root: URL
    var store: MemoryStore
    var priorEvents: [ProvenanceEvent] = []
    var pinned: Set<UUID> = []
    var archivedThreads: Set<UUID> = []
    var revisionCounts: [String: Int] = [:]

    init(root: URL) throws {
        self.root = root
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        store = try MemoryStore(databaseURL: root.appendingPathComponent("db.sqlite"))
    }

    func close() async throws { try store.databasePool.close() }

    func reopen() async throws {
        try await close()
        store = try MemoryStore(databaseURL: root.appendingPathComponent("db.sqlite"))
    }

    func apply(_ command: DiagnosticCommand) async throws {
        switch command.kind {
        case "capture":
            guard let source = command.source else { throw DiagnosticFailure(description: "capture missing source") }
            try diagnosticRequire(revisionCounts[source.id] == nil, "duplicate input source: \(source.id)")
            let modality = ["note": "text", "voice": "audio", "file": "pdf"][source.modality] ?? source.modality
            guard let kind = MemoryKind(rawValue: modality) else {
                throw DiagnosticFailure(description: "unknown modality: \(source.modality)")
            }
            let id = diagnosticID(source.id)
            let time = Date(timeIntervalSince1970: 1_800_000_000 + Double(revisionCounts.count))
            let memory = MemoryItem(id: id, kind: kind, createdAt: time, importedAt: time, updatedAt: time,
                state: .captured, originalFilename: "\(id.uuidString)-r0.txt", userCaption: source.text,
                title: String(source.text.prefix(80)), summary: nil, extractedText: source.text,
                tagsJSON: "[]", processingError: nil, modelVersion: "fictional-diagnostic-source-v1")
            try await store.insertIfNeeded(memory)
            revisionCounts[source.id] = 0
            if let assignments = command.assignments {
                try diagnosticRequire(!assignments.isEmpty, "empty automatic assignments")
                let events = try await store.provenanceEvents()
                let snapshot = try ProvenanceSnapshot.replay(events)
                let clusters = assignments.map(diagnosticID)
                try diagnosticRequire(clusters.allSatisfy { snapshot.clusters[$0] != nil }, "unknown placement cluster")
                var payload = ProvenancePayload()
                payload.assignments = [id.uuidString: clusters]
                payload.previousAssignments = [id.uuidString: [id]]
                payload.sourceRevisionID = events.last { $0.memoryID == id && $0.kind == .capture }?.id
                payload.model = "frozen-diagnostic-policy-actions-v1"
                try await store.appendProvenance(ProvenanceEvent(kind: .placement, memoryID: id, payload: payload),
                                                  expectedSequence: events.last?.sequence)
            }
        case "revise":
            guard let target = command.target, let text = command.text, let revision = revisionCounts[target] else {
                throw DiagnosticFailure(description: "revision missing known target or text")
            }
            let document = NoteDocument(text: text)
            try diagnosticRequire(document.text == text, "revision NoteDocument normalization changes raw UTF8: \(command.id)")
            let id = diagnosticID(target)
            try await store.updateNoteContent(id: id, document: document, filename: "\(id.uuidString)-r\(revision + 1).txt")
            revisionCounts[target] = revision + 1
        case "correct":
            guard let target = command.target, revisionCounts[target] != nil, let assignments = command.assignments,
                  !assignments.isEmpty else { throw DiagnosticFailure(description: "correction missing target/assignments") }
            let id = diagnosticID(target)
            try await store.assignProjectMemory(id: id, clusters: Set(assignments.map(diagnosticID)))
            pinned.insert(id)
        case "archive", "restore":
            guard let target = command.target, revisionCounts[target] != nil else {
                throw DiagnosticFailure(description: "archive/restore missing known target")
            }
            try await store.setArchived(id: diagnosticID(target), archived: command.kind == "archive")
        default: throw DiagnosticFailure(description: "unsupported command kind: \(command.kind)")
        }
    }

    func verifyLedger(_ events: [ProvenanceEvent]) throws {
        try diagnosticRequire(events.count >= priorEvents.count, "ledger shrank")
        for (old, current) in zip(priorEvents, events) {
            try diagnosticRequire(old.id == current.id && old.sequence == current.sequence && old.timestamp == current.timestamp
                && old.kind == current.kind && old.memoryID == current.memoryID && old.origin == current.origin
                && old.payloadJSON == current.payloadJSON, "historical ledger event changed")
        }
        var seen: Set<UUID> = []
        var previous: Int64 = 0
        var latestSources: [UUID: UUID] = [:]
        for event in events {
            guard let sequence = event.sequence else { throw DiagnosticFailure(description: "missing ledger sequence") }
            try diagnosticRequire(sequence > previous && seen.insert(event.id).inserted, "duplicate ID or unordered sequence")
            let payload = try event.payload()
            for reference in [payload.sourceRevisionID, payload.referencedEventID].compactMap({ $0 }) + payload.citedEventIDs {
                try diagnosticRequire(reference != event.id && seen.contains(reference), "dangling/future event reference")
            }
            if let id = event.memoryID, [.capture, .revision].contains(event.kind) {
                try diagnosticRequire(payload.sourceRevisionID == latestSources[id], "broken source revision chain")
                latestSources[id] = event.id
            }
            previous = sequence
        }
        priorEvents = events
    }

    func verifyState(_ expected: [String: DiagnosticExpected], events: [ProvenanceEvent], checkStore: Bool) async throws {
        let snapshot = try ProvenanceSnapshot.replay(events)
        let expectedIDs = Set(expected.keys.map(diagnosticID))
        try diagnosticRequire(Set(snapshot.memories.keys) == expectedIDs, "memory ID set differs")
        try diagnosticRequire(Set(snapshot.memberships.keys) == expectedIDs, "membership key set differs")
        for (source, value) in expected {
            let id = diagnosticID(source)
            guard let memory = snapshot.memories[id] else { throw DiagnosticFailure(description: "missing memory") }
            try diagnosticRequire(!value.memberships.isEmpty, "oracle has empty membership")
            try diagnosticRequire(snapshot.memberships[id] == Set(value.memberships.map(diagnosticID)), "membership mismatch: \(source)")
            try diagnosticRequire(memory.isArchived == value.archived, "archive mismatch: \(source)")
            try diagnosticRequire(diagnosticHash(Data((memory.extractedText ?? "").utf8)) == value.textSHA256, "text hash mismatch: \(source)")
            try diagnosticRequire(memory.originalFilename == "\(id.uuidString)-r\(value.revision).txt", "revision filename mismatch: \(source)")
            let revisions = events.filter { $0.memoryID == id && $0.kind == .revision }.count
            try diagnosticRequire(revisions == value.revision, "revision count mismatch: \(source)")
        }
        let active = Set(expected.values.filter { !$0.archived }.flatMap { $0.memberships.map(diagnosticID) }).subtracting(archivedThreads)
        try diagnosticRequire(Set(snapshot.activeClusters.map(\.id)) == active, "active cluster projection mismatch")
        try diagnosticRequire(snapshot.archivedClusterIDs == archivedThreads, "thread archive state differs")
        if checkStore {
            try diagnosticRequire(snapshot.pinned == pinned, "explicit corrections not preserved as pinned")
            let materialized = try await store.databasePool.read { try MemoryItem.fetchAll($0) }
            try diagnosticRequire(Set(materialized.map(\.id)) == expectedIDs, "SQLite memory ID set differs")
            for var row in materialized {
                guard let historical = snapshot.memories[row.id] else { throw DiagnosticFailure(description: "missing SQLite memory in replay") }
                // GRDB's SQLite date serialization has millisecond precision; JSON preserves submilliseconds.
                try diagnosticRequire(abs(row.updatedAt.timeIntervalSince(historical.updatedAt)) < 0.002,
                                      "SQLite updated timestamp differs from replay")
                row.updatedAt = historical.updatedAt
                try diagnosticRequire(row == historical, "SQLite memory fields differ from provenance reconstruction")
            }
            let visible = try await store.fetchAll()
            try diagnosticRequire(Set(visible.map(\.id)) == Set(expected.filter { !$0.value.archived }.keys.map(diagnosticID)),
                                  "visible store memory set differs")
        }
    }
}

enum DiagnosticReplay {
    static func run(input: URL, output: URL, bindings: URL, maximumRuns: Int?) async throws {
        let inputData = try Data(contentsOf: input)
        let batchHash = diagnosticHash(inputData)
        let bindingsHash = diagnosticHash(try Data(contentsOf: bindings))
        let batch = try JSONDecoder().decode(DiagnosticBatch.self, from: inputData)
        try diagnosticRequire(batch.schemaVersion == 1 && !batch.runs.isEmpty, "invalid/empty batch")
        try diagnosticRequire(Set(batch.runs.map(\.id)).count == batch.runs.count, "duplicate run IDs")
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        var completed = 0
        var executed = 0
        for run in batch.runs {
            let key = diagnosticHash(Data(run.id.utf8))
            let receiptURL = output.appendingPathComponent("\(key).receipt.json")
            let runHash = diagnosticHash(try diagnosticJSON(run))
            if FileManager.default.fileExists(atPath: receiptURL.path) {
                let receipt = try JSONDecoder().decode(DiagnosticRunReceipt.self, from: Data(contentsOf: receiptURL))
                try diagnosticRequire(receipt.id == run.id && receipt.inputSHA256 == runHash && receipt.batchSHA256 == batchHash
                    && receipt.bindingsSHA256 == bindingsHash && receipt.prefixCount == run.events.count,
                    "resume receipt identity mismatch")
                let ledger = output.appendingPathComponent(receipt.attempt).appendingPathComponent("ledger.json")
                let ledgerHash = diagnosticHash(try Data(contentsOf: ledger))
                try diagnosticRequire(ledgerHash == receipt.ledgerSHA256, "resume ledger hash mismatch")
                completed += 1
                continue
            }
            if FileManager.default.fileExists(atPath: output.appendingPathComponent("pause.request").path)
                || maximumRuns.map({ executed >= $0 }) == true {
                try diagnosticJSON(["status": "paused", "completed": String(completed), "batchSHA256": batchHash])
                    .write(to: output.appendingPathComponent("status.json"), options: .atomic)
                return
            }
            try diagnosticRequire(!run.events.isEmpty && Set(run.events.map(\.id)).count == run.events.count, "empty run/duplicate command IDs")
            let started = Date()
            let attempt = "\(key)-\(UUID().uuidString)"
            let root = output.appendingPathComponent(attempt)
            let harness = try DiagnosticHarness(root: root)
            do {
                var prefixes: [DiagnosticPrefixReceipt] = []
                for command in run.events {
                    do {
                        try await harness.apply(command)
                        let events = try await harness.store.provenanceEvents()
                        try harness.verifyLedger(events)
                        try diagnosticRequire(!events.contains { $0.kind == .merge || $0.kind == .split }, "policy unexpectedly merged/split")
                        try await harness.verifyState(command.expectedState, events: events, checkStore: true)
                        prefixes.append(DiagnosticPrefixReceipt(id: command.id, ledgerCount: events.count,
                            stateSHA256: diagnosticHash(try diagnosticJSON(command.expectedState))))
                    } catch {
                        throw DiagnosticFailure(description: "run \(run.id), command \(command.id): \(error)")
                    }
                }
                try await harness.reopen()
                let events = try await harness.store.provenanceEvents()
                try harness.verifyLedger(events)
                try await harness.verifyState(run.events.last!.expectedState, events: events, checkStore: true)
                for (command, prefix) in zip(run.events, prefixes) {
                    try await harness.verifyState(command.expectedState, events: Array(events.prefix(prefix.ledgerCount)), checkStore: false)
                }
                let ledger = try diagnosticJSON(events)
                try ledger.write(to: root.appendingPathComponent("ledger.json"), options: .atomic)
                try await harness.close()
                let receipt = DiagnosticRunReceipt(schemaVersion: 1, id: run.id, inputSHA256: runHash, batchSHA256: batchHash,
                    bindingsSHA256: bindingsHash, attempt: attempt, ledgerSHA256: diagnosticHash(ledger), prefixCount: prefixes.count,
                    ledgerCount: events.count, elapsedSeconds: Date().timeIntervalSince(started), restartVerified: true,
                    historicalPrefixesVerified: prefixes.count, prefixes: prefixes)
                // Publish completion only after durable evidence and a closed SQLite store.
                try diagnosticJSON(receipt).write(to: receiptURL, options: .atomic)
                executed += 1
                completed += 1
                print("ledger replay completed \(completed)/\(batch.runs.count): \(run.id)")
            } catch {
                try? await harness.close()
                try diagnosticJSON(["status": "failed", "run": run.id, "attempt": attempt, "error": String(describing: error)])
                    .write(to: output.appendingPathComponent("status.json"), options: .atomic)
                throw error
            }
        }
        try diagnosticJSON(["status": "complete", "completed": String(completed), "batchSHA256": batchHash,
                            "bindingsSHA256": bindingsHash])
            .write(to: output.appendingPathComponent("status.json"), options: .atomic)
    }
}
