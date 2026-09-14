import CryptoKit
import Darwin
import Foundation
import FoundationModels
import SwiftUI

@main
struct OrganizationDecisionProbeApp: App {
    var body: some Scene {
        WindowGroup {
            Text("Controlled organization decisions\nFictional seeded states • No cloud")
                .padding()
                .task {
                    UIApplication.shared.isIdleTimerDisabled = true
                    UserDefaults.standard.set(false, forKey: ProjectPreferences.cloudKey)
                    do {
                        try await OrganizationDecisionProbe().run()
                        print("DECISION_PROBE_FINISHED inspect coverage and host scores")
                        fflush(stdout); exit(0)
                    } catch {
                        print("DECISION_PROBE_ERROR \(error)")
                        fflush(stdout); exit(2)
                    }
                }
        }
    }
}

nonisolated struct DecisionInput: Decodable, Sendable {
    let id: String
    let text: String
    let timestamp: Double
}
nonisolated struct DecisionCase: Decodable, Sendable {
    let id: String
    let libraryID: String
    let split: String
    let items: [DecisionInput]
    let initialMemberships: [String: [String]]
}
nonisolated struct DecisionConfig: Decodable, Sendable {
    let cases: [DecisionCase]
    let modes: [String]
    let timeoutSeconds: Int
}
actor DecisionReasoner: ProjectReasoning {
    let local: Bool
    let underlying = ProjectReasoner()
    private(set) var calls = 0
    init(local: Bool) { self.local = local }
    func decide(source: String, candidates: [(id: UUID, title: String, summary: String)]) async throws -> ProjectReasoningResult? {
        guard local else { return nil }
        precondition(!ProjectPreferences.cloudEnabled)
        calls += 1
        return try await underlying.decide(source: source, candidates: candidates)
    }
    func suggestSplit(candidates: [(id: UUID, title: String, summary: String)]) async throws -> ProjectReasoningResult? {
        guard local else { return nil }
        precondition(!ProjectPreferences.cloudEnabled)
        calls += 1
        return try await underlying.suggestSplit(candidates: candidates)
    }
}

actor OrganizationDecisionProbe {
    enum Failure: Error { case invalidConfiguration, timeout, unsettled }
    private var report: [String: Any] = [:]
    private var url: URL?

    func run() async throws {
        let config = try JSONDecoder().decode(DecisionConfig.self, from: DecisionConfiguration.data)
        guard let raw = try JSONSerialization.jsonObject(with: DecisionConfiguration.data) as? [String: Any],
              var manifest = raw["manifest"] as? [String: Any],
              let hash = manifest["configurationSHA256"] as? String else { throw Failure.invalidConfiguration }
        let target = URL.documentsDirectory.appendingPathComponent("decisions-\(hash).json")
        url = target
        if FileManager.default.fileExists(atPath: target.path) {
            guard let previous = try JSONSerialization.jsonObject(with: Data(contentsOf: target)) as? [String: Any],
                  (previous["manifest"] as? [String: Any])?["configurationSHA256"] as? String == hash else { throw Failure.invalidConfiguration }
            report = previous
        } else {
            manifest["policy"] = ProjectMath.policy
            manifest["deviceOS"] = ProcessInfo.processInfo.operatingSystemVersionString
            manifest["foundationModels"] = String(describing: SystemLanguageModel.default.availability)
            manifest["startedAt"] = ISO8601DateFormatter().string(from: Date())
            manifest["reasoningScope"] = "Cached placements normally bypass reasoning; batch merges and local split proposals are production heuristics. Modes are not independent reasoning comparisons."
            report = ["schemaVersion": 1, "manifest": manifest, "runs": [[String: Any]]()]
        }
        try save()
        for item in config.cases {
            for mode in config.modes {
                let runID = item.id + "-" + mode
                let prior = (report["runs"] as? [[String: Any]] ?? []).first { $0["runID"] as? String == runID }
                if ["completed", "error", "timeout"].contains(prior?["status"] as? String ?? "") { continue }
                try await scenario(item, mode: mode, runID: runID, timeout: config.timeoutSeconds)
            }
        }
    }

    private func scenario(_ input: DecisionCase, mode: String, runID: String, timeout: Int) async throws {
        let started = ContinuousClock.now
        var result: [String: Any] = ["runID": runID, "caseID": input.id, "libraryID": input.libraryID,
            "mode": mode, "status": "running", "inputIDs": input.items.map(\.id)]
        update(result); try save()
        let root = URL.temporaryDirectory.appendingPathComponent("OrganizationDecision-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let embeddings = AppleProjectEmbedding()
        let reasoner = DecisionReasoner(local: mode == "local")
        var store: MemoryStore?
        var unavailable: [String] = []
        var recorded: [String: [String: Any]] = [:]
        var batchStarted: ContinuousClock.Instant?
        let ids = Dictionary(uniqueKeysWithValues: input.items.map { ($0.id, Self.stableUUID(input.id + "/" + $0.id)) })
        do {
            let database = try MemoryStore(databaseURL: root.appendingPathComponent("diagnostic.sqlite"))
            store = database
            // Generic seed IDs map to source-owned initial clusters. No semantic gold labels enter this process.
            var clusters: [String: UUID] = [:]
            for item in input.items {
                guard let group = input.initialMemberships[item.id]?.first, let id = ids[item.id] else { throw Failure.invalidConfiguration }
                if clusters[group] == nil { clusters[group] = id }
                let date = Date(timeIntervalSince1970: item.timestamp)
                let memory = MemoryItem(id: id, kind: .text, createdAt: date, importedAt: date, updatedAt: date,
                    state: .captured, originalFilename: id.uuidString + ".txt", userCaption: nil,
                    title: String(item.text.prefix(80)), summary: nil, extractedText: nil, tagsJSON: "[]", processingError: nil, modelVersion: nil)
                try await database.insertIfNeeded(memory)
                try await database.markIndexed(id: id, analysis: MemoryAnalysisResult(title: String(item.text.prefix(80)),
                    summary: item.text, tags: [], extractedText: item.text, modelVersion: "controlled-source-text-v1"))
            }
            for item in input.items {
                try deadline(started, seconds: timeout)
                guard let id = ids[item.id], let group = input.initialMemberships[item.id]?.first, let cluster = clusters[group] else { throw Failure.invalidConfiguration }
                let events = try await database.provenanceEvents()
                guard let source = events.last(where: { $0.memoryID == id && [.enrichment, .revision, .imported].contains($0.kind) }) else { throw Failure.invalidConfiguration }
                let value = try await embeddings.embedding(for: item.text)
                if let value {
                    recorded[item.id] = ["space": value.space, "vector": value.vector, "semanticVector": value.semanticVector ?? []]
                } else { unavailable.append(item.id) }
                var payload = ProvenancePayload()
                payload.sourceRevisionID = source.id
                payload.sourceFilename = id.uuidString + ".txt"
                payload.vector = value?.vector
                payload.semanticVector = value?.semanticVector
                payload.embeddingSpace = value?.space
                payload.model = ProjectMath.policy
                payload.assignments = [id.uuidString: [cluster]]
                payload.previousAssignments = [id.uuidString: [id]]
                payload.rationale = "Controlled benchmark initial state, not a scored automatic decision."
                try await database.appendProvenance(ProvenanceEvent(kind: .placement, memoryID: id,
                    origin: "benchmark-seed", payload: payload), expectedSequence: events.last?.sequence)
            }
            let initialEvents = try await database.provenanceEvents()
            let initial = try ProvenanceSnapshot.replay(initialEvents)
            result["initialMemberships"] = Self.memberships(initial, ids: ids)
            result["seededEventCount"] = initialEvents.count
            result["initialPinnedCount"] = initial.pinned.count
            let sourceNames = Dictionary(uniqueKeysWithValues: ids.map { ($0.value, $0.key) })
            result["seedEvidence"] = try initialEvents.map { event -> [String: Any] in
                let payload = try event.payload()
                return ["id": event.id.uuidString, "kind": event.kind.rawValue,
                    "itemID": event.memoryID.flatMap { sourceNames[$0] } as Any? ?? NSNull(),
                    "sourceRevisionID": payload.sourceRevisionID?.uuidString as Any? ?? NSNull(),
                    "origin": event.origin]
            }
            batchStarted = .now
            let graph = ProjectGraphService(store: database, embeddings: embeddings, reasoner: reasoner)
            let work = Task {
                var previous = initialEvents.count
                for _ in 0..<16 {
                    try Task.checkCancellation()
                    try await graph.synchronize()
                    let count = try await database.provenanceEvents().count
                    if count == previous { return }
                    previous = count
                }
                throw Failure.unsettled
            }
            let remaining = max(0.001, Double(timeout) - Self.milliseconds(started) / 1_000)
            let timer = Task { try await Task.sleep(for: .seconds(remaining)); work.cancel() }
            defer { timer.cancel() }
            try await work.value
            try deadline(started, seconds: timeout)
            let finalEvents = try await database.provenanceEvents()
            let final = try ProvenanceSnapshot.replay(finalEvents)
            result["memberships"] = Self.memberships(final, ids: ids)
            let names = Dictionary(uniqueKeysWithValues: ids.map { ($0.value.uuidString, $0.key) })
            result["events"] = try finalEvents.dropFirst(initialEvents.count).map { event -> [String: Any] in
                let payload = try event.payload()
                let assignments = Dictionary(uniqueKeysWithValues: payload.assignments.compactMap { key, values -> (String, [String])? in
                    guard let name = names[key] else { return nil }
                    return (name, values.map(\.uuidString).sorted())
                })
                return ["id": event.id.uuidString, "kind": event.kind.rawValue, "origin": event.origin,
                    "clusterID": payload.clusterID?.uuidString as Any? ?? NSNull(), "parents": payload.parents.map(\.uuidString),
                    "assignments": assignments, "citedEventIDs": payload.citedEventIDs.map(\.uuidString),
                    "model": payload.model, "rationale": payload.rationale, "scores": payload.scores]
            }
            result["status"] = "completed"
            result["batchCheckpointObserved"] = finalEvents.dropFirst(initialEvents.count).contains { $0.kind == .checkpoint }
            var knownEventIDs = Set(initialEvents.map(\.id))
            result["citationsValid"] = try finalEvents.dropFirst(initialEvents.count).allSatisfy { event in
                defer { knownEventIDs.insert(event.id) }
                return try event.payload().citedEventIDs.allSatisfy(knownEventIDs.contains)
            }
        } catch {
            result["status"] = Self.milliseconds(started) >= Double(timeout) * 1_000 ? "timeout" : "error"
            result["error"] = String(describing: error)
        }
        if let store {
            do { try await store.databasePool.close() }
            catch { result["status"] = "error"; result["cleanupError"] = String(describing: error) }
        }
        result["availability"] = ["unavailableEmbeddingIDs": unavailable,
            "foundationModels": String(describing: SystemLanguageModel.default.availability), "reasoningCalls": await reasoner.calls]
        result["embeddings"] = recorded
        result["timings"] = ["totalMilliseconds": Self.milliseconds(started),
            "batchMilliseconds": batchStarted.map(Self.milliseconds) ?? 0]
        update(result); try save()
        print("DECISION_PROGRESS run=\(runID) status=\(result["status"] ?? "unknown")")
        fflush(stdout)
    }

    private func update(_ result: [String: Any]) {
        var runs = report["runs"] as? [[String: Any]] ?? []
        runs.removeAll { $0["runID"] as? String == result["runID"] as? String }
        runs.append(result); report["runs"] = runs
    }
    private func save() throws {
        guard let url else { throw Failure.invalidConfiguration }
        try JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]).write(to: url, options: .atomic)
    }
    private func deadline(_ start: ContinuousClock.Instant, seconds: Int) throws {
        if Self.milliseconds(start) >= Double(seconds) * 1_000 { throw Failure.timeout }
        try Task.checkCancellation()
    }
    private static func milliseconds(_ start: ContinuousClock.Instant) -> Double {
        let delta = start.duration(to: .now).components
        return Double(delta.seconds) * 1_000 + Double(delta.attoseconds) / 1e15
    }
    private static func memberships(_ state: ProvenanceSnapshot, ids: [String: UUID]) -> [String: [String]] {
        Dictionary(uniqueKeysWithValues: ids.map { ($0.key, state.memberships[$0.value, default: []].map(\.uuidString).sorted()) })
    }
    private static func stableUUID(_ string: String) -> UUID {
        let bytes = Array(SHA256.hash(data: Data(string.utf8)).prefix(16))
        return UUID(uuid: (bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5], bytes[6], bytes[7],
                           bytes[8], bytes[9], bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15]))
    }
}
