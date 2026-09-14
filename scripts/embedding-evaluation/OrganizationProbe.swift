import CryptoKit
import Darwin
import Foundation
import FoundationModels
import SwiftUI

@main
struct OrganizationProbeApp: App {
    var body: some Scene {
        WindowGroup {
            Text("Remember organization benchmark\nIsolated fictional inputs; cloud disabled")
                .padding()
                .task {
                    UIApplication.shared.isIdleTimerDisabled = true
                    UserDefaults.standard.set(false, forKey: ProjectPreferences.cloudKey)
                    do {
                        try await OrganizationProbe().run()
                        print("ORGANIZATION_PROBE_FINISHED inspect scenario statuses; exit is not a quality score")
                        fflush(stdout)
                        exit(0)
                    } catch {
                        print("ORGANIZATION_PROBE_ERROR \(error)")
                        fflush(stdout)
                        exit(2)
                    }
                }
        }
    }
}

nonisolated struct OrganizationInput: Codable, Sendable {
    let id: String
    let text: String
    let kind: String
    let timestamp: Double
    let assetName: String?
    let caption: String?
}

nonisolated struct OrganizationLibrary: Codable, Sendable {
    let id: String
    let split: String
    let slice: String
    let items: [OrganizationInput]
    let orders: [String: [String]]?
}

nonisolated struct OrganizationConfig: Decodable, Sendable {
    let schemaVersion: Int
    let libraries: [OrganizationLibrary]
    let modes: [String]
    let orders: [String]
    let timeoutSeconds: Int
    let maximumRuns: Int
    let mediaMode: String
}

actor OrganizationRecordingEmbedding: ProjectEmbeddingProviding {
    let underlying = AppleProjectEmbedding()
    private(set) var milliseconds = 0.0

    func expectedSpace(for text: String) async -> String? { await underlying.expectedSpace(for: text) }
    func embedding(for text: String) async throws -> ProjectEmbedding? {
        let started = ContinuousClock.now
        defer { milliseconds += OrganizationProbe.milliseconds(since: started) }
        return try await underlying.embedding(for: text)
    }
}

actor OrganizationRecordingReasoner: ProjectReasoning {
    let enabled: Bool
    let underlying = ProjectReasoner()
    private(set) var calls = 0
    private(set) var decisions = 0
    private(set) var errors = 0
    private(set) var milliseconds = 0.0
    init(enabled: Bool) { self.enabled = enabled }

    func decide(source: String, candidates: [(id: UUID, title: String, summary: String)]) async throws -> ProjectReasoningResult? {
        guard enabled else { return nil }
        precondition(!ProjectPreferences.cloudEnabled)
        calls += 1
        let started = ContinuousClock.now
        defer { milliseconds += OrganizationProbe.milliseconds(since: started) }
        do {
            let result = try await underlying.decide(source: source, candidates: candidates)
            if let result, !result.candidateIDs.isEmpty { decisions += 1 }
            return result
        } catch { errors += 1; throw error }
    }
    // Production local suggestSplit returns nil. No alternative split model is introduced.
    func suggestSplit(candidates: [(id: UUID, title: String, summary: String)]) async throws -> ProjectReasoningResult? {
        guard enabled else { return nil }
        precondition(!ProjectPreferences.cloudEnabled)
        return try await underlying.suggestSplit(candidates: candidates)
    }
}

actor OrganizationProbe {
    enum ProbeError: Error { case invalidConfiguration, timeLimit }
    private var report: [String: Any] = [:]
    private var resultURL: URL?
    private var activeResultURL: URL?

    nonisolated static func milliseconds(since start: ContinuousClock.Instant) -> Double {
        let value = start.duration(to: .now).components
        return Double(value.seconds) * 1_000 + Double(value.attoseconds) / 1e15
    }

    func run() async throws {
        let config = try JSONDecoder().decode(OrganizationConfig.self, from: OrganizationConfiguration.data)
        guard config.schemaVersion == 1,
              let raw = try JSONSerialization.jsonObject(with: OrganizationConfiguration.data) as? [String: Any],
              var manifest = raw["manifest"] as? [String: Any],
              let configurationHash = manifest["configurationSHA256"] as? String else { throw ProbeError.invalidConfiguration }
        let url = URL.documentsDirectory.appendingPathComponent("organization-\(configurationHash).json")
        resultURL = url
        activeResultURL = URL.documentsDirectory.appendingPathComponent("organization-\(configurationHash)-active.json")
        if FileManager.default.fileExists(atPath: url.path) {
            report = try JSONSerialization.jsonObject(with: Data(contentsOf: url)) as? [String: Any] ?? [:]
            guard (report["manifest"] as? [String: Any])?["configurationSHA256"] as? String == configurationHash else { throw ProbeError.invalidConfiguration }
        } else {
            manifest["deviceOS"] = ProcessInfo.processInfo.operatingSystemVersionString
            manifest["deviceModel"] = await UIDevice.current.model
            var hardware = utsname()
            uname(&hardware)
            let machineCapacity = MemoryLayout.size(ofValue: hardware.machine)
            manifest["hardwareIdentifier"] = withUnsafePointer(to: &hardware.machine) {
                $0.withMemoryRebound(to: CChar.self, capacity: machineCapacity) { String(cString: $0) }
            }
            manifest["policy"] = ProjectMath.policy
            manifest["foundationModels"] = String(describing: SystemLanguageModel.default.availability)
            manifest["startedAt"] = ISO8601DateFormatter().string(from: Date())
            manifest["timeoutSemantics"] = "cooperative per scenario; host process timeout required for unresponsive OS calls"
            manifest["localSplitReasoning"] = "unsupported by current production local reasoner"
            manifest["relationshipScope"] = "ProjectGraphMap visible first 40 active clusters; core text metadata is deterministic without tags; media libraries use local production enrichment"
            report = ["schemaVersion": 1, "manifest": manifest, "runs": [[String: Any]]()]
        }
        try save()
        var executed = 0
        for library in config.libraries {
            for mode in config.modes {
                for order in config.orders {
                    let repeats = mode == "local" && order == "chronological" ? 0..<3 : 0..<1
                    for repeatIndex in repeats {
                        let runID = "\(library.id)-\(mode)-\(order)-\(repeatIndex)"
                        let previous = (report["runs"] as? [[String: Any]] ?? []).first { $0["runID"] as? String == runID }
                        if ["completed", "blocked", "timeout", "error"].contains(previous?["status"] as? String ?? "") { continue }
                        if config.maximumRuns > 0 && executed >= config.maximumRuns { return }
                        executed += 1
                        // Cancellation covers extraction/enrichment as well as graph work.
                        // The host still bounds OS calls that do not cooperate with cancellation.
                        let scenarioWork = Task {
                            try await self.scenario(library: library, mode: mode, order: order, repeatIndex: repeatIndex,
                                                    runID: runID, timeoutSeconds: config.timeoutSeconds, mediaMode: config.mediaMode)
                        }
                        let scenarioDeadline = Task {
                            try await Task.sleep(for: .seconds(config.timeoutSeconds))
                            scenarioWork.cancel()
                        }
                        do {
                            try await scenarioWork.value
                            scenarioDeadline.cancel()
                        } catch {
                            scenarioDeadline.cancel()
                            throw error
                        }
                    }
                }
            }
        }
    }

    private func scenario(library: OrganizationLibrary, mode: String, order: String, repeatIndex: Int,
                          runID: String, timeoutSeconds: Int, mediaMode: String) async throws {
        let items = Self.ordered(library, order: order)
        var result: [String: Any] = ["runID": runID, "libraryID": library.id, "mode": mode, "order": order,
            "attemptID": UUID().uuidString,
            "repeat": repeatIndex, "status": "running", "inputIDs": items.map(\.id), "memberships": [String: [String]](),
            "snapshots": [[String: Any]](), "events": [[String: Any]](), "slice": library.slice, "split": library.split,
            "mediaMode": mediaMode]
        update(result)
        try save()
        if mode == "local", SystemLanguageModel.default.availability != .available {
            result["status"] = "blocked"
            result["error"] = "Local Foundation Models unavailable; embedding-only coverage is reported separately"
            result["availability"] = ["foundationModels": String(describing: SystemLanguageModel.default.availability)]
            update(result); try save(); return
        }
        let root = URL.temporaryDirectory.appendingPathComponent("OrganizationScenario-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let embeddings = OrganizationRecordingEmbedding()
        let reasoner = OrganizationRecordingReasoner(enabled: mode == "local")
        let started = ContinuousClock.now
        var samples: [UUID: String] = [:]
        var snapshots: [[String: Any]] = []
        var stageTimes: [[String: Any]] = []
        var peakResidentBytes: UInt64 = 0
        var extractionRecords: [[String: Any]] = []
        var sourceTexts: [String: String] = [:]
        var recordedVectors: [UUID: ProjectEmbedding] = [:]
        var reportingMilliseconds = 0.0
        var openedStore: MemoryStore?
        do {
            let store = try MemoryStore(databaseURL: root.appendingPathComponent("benchmark.sqlite"))
            openedStore = store
            let graph = ProjectGraphService(store: store, embeddings: embeddings, reasoner: reasoner)
            for (index, input) in items.enumerated() {
                try deadline(started, seconds: timeoutSeconds)
                let id = Self.stableUUID(library.id + "/" + input.id)
                samples[id] = input.id
                let date = Date(timeIntervalSince1970: input.timestamp)
                // Titles use source content, never opaque IDs or gold topics. Captures are fed through the real store.
                var text = input.text
                var content: ExtractedMemoryContent?
                let kind = MemoryKind(rawValue: input.kind) ?? .text
                var item = MemoryItem(id: id, kind: kind, createdAt: date, importedAt: date, updatedAt: date,
                    state: .captured, originalFilename: input.assetName ?? id.uuidString + ".txt", userCaption: input.caption,
                    title: nil, summary: nil, extractedText: nil, tagsJSON: "[]", processingError: nil, modelVersion: nil)
                if kind != .text, mediaMode == "extracted" {
                    let extractionStart = ContinuousClock.now
                    do {
                        guard let name = input.assetName, let url = Bundle.main.url(forResource: name, withExtension: nil) else {
                            throw ProbeError.invalidConfiguration
                        }
                        let supportingText = kind == .audio ? try await OnDeviceSpeechTranscriber().transcribe(audioURL: url) : nil
                        let extracted = try await MemoryContentExtractor().extract(memory: item, originalURL: url, supportingText: supportingText)
                        content = extracted
                        text = extracted.text
                        let hasEvidence = !extracted.chunks.isEmpty || !extracted.visualLabels.isEmpty
                        extractionRecords.append(["itemID": input.id, "status": hasEvidence ? "completed" : "no_source_evidence", "text": text,
                            "chunkCount": extracted.chunks.count, "visualLabelCount": extracted.visualLabels.count,
                            "expectedNoEvidence": kind == .video && (input.caption ?? "").isEmpty,
                            "isPartial": extracted.isPartial, "milliseconds": Self.milliseconds(since: extractionStart)])
                    } catch is CancellationError {
                        throw CancellationError()
                    } catch {
                        // Missing extraction remains observable and keeps its own unsupported singleton.
                        text = ""
                        extractionRecords.append(["itemID": input.id, "status": "blocked", "text": "",
                            "error": String(describing: error), "milliseconds": Self.milliseconds(since: extractionStart)])
                    }
                }
                try deadline(started, seconds: timeoutSeconds)
                sourceTexts[input.id] = text
                let title = text.isEmpty ? "Untitled" : String(text.prefix(80))
                item.title = title
                let stageStart = ContinuousClock.now
                try await store.insertIfNeeded(item)
                let analysis: MemoryAnalysisResult
                if library.slice == "media" {
                    let extracted = content ?? ExtractedMemoryContent(text: text,
                        chunks: MemoryTextChunker.chunks(from: text, locatorPrefix: "Benchmark source", extractionMethod: .plainText),
                        isPartial: kind == .video, visualLabels: [])
                    analysis = try await LocalCaptureAnalyzer(cloudEnabled: { false }, usesFoundationModels: mode == "local")
                        .analyzeExtracted(memory: item, originalURL: root.appendingPathComponent(item.originalFilename),
                            supportingText: kind == .audio ? text : nil, extracted: extracted)
                } else {
                    analysis = MemoryAnalysisResult(title: title, summary: text,
                        tags: [], extractedText: text, modelVersion: "benchmark-source-text-v1")
                }
                try deadline(started, seconds: timeoutSeconds)
                try await store.markIndexed(id: id, analysis: analysis)
                let work = Task {
                    try await graph.synchronize()
                    let immediateEvents = try await store.provenanceEvents()
                    let immediate = try ProvenanceSnapshot.replay(immediateEvents)
                    var lastCount = immediateEvents.count
                    // A production observation resumes after each merge. Reproduce that bounded settling here.
                    for _ in 0..<(items.count * 2 + 4) {
                        try Task.checkCancellation()
                        try await graph.synchronize()
                        let count = try await store.provenanceEvents().count
                        if count == lastCount { return immediate }
                        lastCount = count
                    }
                    throw ProbeError.timeLimit
                }
                let remaining = max(0.001, Double(timeoutSeconds) - Self.milliseconds(since: started) / 1000)
                let cancellation = Task {
                    try await Task.sleep(for: .seconds(remaining))
                    work.cancel()
                }
                defer { cancellation.cancel() }
                let immediate = try await work.value
                try deadline(started, seconds: timeoutSeconds)
                let events = try await store.provenanceEvents()
                let state = try ProvenanceSnapshot.replay(events)
                recordedVectors = try ProjectGraphService.vectors(events, snapshot: state)
                let memberships = Self.memberships(state, samples: samples)
                let checkpointStride = library.slice == "scale" ? max(1, items.count / 20) : 1
                let checkpoint = (index + 1) % checkpointStride == 0 || index + 1 == items.count
                if checkpoint {
                    snapshots.append(["step": index + 1, "itemID": input.id, "memberships": memberships,
                                      "immediateMemberships": Self.memberships(immediate, samples: samples),
                                      "eventCount": events.count, "phase": "afterObservationSettlingIncludingDueBatch"])
                }
                stageTimes.append(["itemID": input.id, "synchronizeMilliseconds": Self.milliseconds(since: stageStart)])
                peakResidentBytes = max(peakResidentBytes, Self.residentBytes())
                result["memberships"] = memberships
                result["snapshots"] = snapshots
                result["events"] = try Self.eventFacts(events, samples: samples)
                let map = ProjectGraphMap(snapshot: state)
                result["edges"] = map.edges.map { ["first": map.nodes[$0.first].id.uuidString, "second": map.nodes[$0.second].id.uuidString] }
                result["visibleClusterIDs"] = map.nodes.map { $0.id.uuidString }
                result["totalClusterCount"] = map.totalCount
                result["completedInputCount"] = index + 1
                result["extractions"] = extractionRecords
                if checkpoint {
                    let reportingStart = ContinuousClock.now
                    try saveActive(result)
                    reportingMilliseconds += Self.milliseconds(since: reportingStart)
                }
                print("ORGANIZATION_PROGRESS run=\(runID) step=\(index + 1)/\(items.count)")
                fflush(stdout)
            }
            result["status"] = "completed"
        } catch {
            result["status"] = Self.milliseconds(since: started) >= Double(timeoutSeconds) * 1000 ? "timeout" : "error"
            result["error"] = String(describing: error)
        }
        if let openedStore {
            do { try await openedStore.databasePool.close() }
            catch {
                result["status"] = "error"
                result["cleanupError"] = String(describing: error)
            }
        }
        result["embeddings"] = Dictionary(uniqueKeysWithValues: items.compactMap { item -> (String, [String: Any])? in
            guard let value = recordedVectors[Self.stableUUID(library.id + "/" + item.id)] else { return nil }
            return (item.id, ["space": value.space, "vector": value.vector, "semanticVector": value.semanticVector ?? []])
        })
        result["availability"] = ["foundationModels": String(describing: SystemLanguageModel.default.availability),
            "unavailableEmbeddingIDs": items.filter { sourceTexts[$0.id] != nil && recordedVectors[Self.stableUUID(library.id + "/" + $0.id)] == nil }.map(\.id),
            "blockedExtractionIDs": extractionRecords.filter { $0["status"] as? String == "blocked" }.compactMap { $0["itemID"] as? String },
            "reasoningCalls": await reasoner.calls, "reasoningDecisions": await reasoner.decisions,
            "reasoningErrors": await reasoner.errors]
        result["timings"] = ["totalMilliseconds": Self.milliseconds(since: started), "embeddingMilliseconds": await embeddings.milliseconds,
            "reasoningMilliseconds": await reasoner.milliseconds, "reportingMilliseconds": reportingMilliseconds,
            "peakSampledResidentBytes": peakResidentBytes, "steps": stageTimes]
        update(result); try save()
    }

    private func deadline(_ start: ContinuousClock.Instant, seconds: Int) throws {
        if Self.milliseconds(since: start) >= Double(seconds) * 1000 { throw ProbeError.timeLimit }
        try Task.checkCancellation()
    }
    private func update(_ result: [String: Any]) {
        var runs = report["runs"] as? [[String: Any]] ?? []
        runs.removeAll { $0["runID"] as? String == result["runID"] as? String }
        runs.append(result)
        report["runs"] = runs
    }
    private func save() throws {
        guard let resultURL else { throw ProbeError.invalidConfiguration }
        try JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]).write(to: resultURL, options: .atomic)
    }
    private func saveActive(_ result: [String: Any]) throws {
        guard let activeResultURL,
              let configurationHash = (report["manifest"] as? [String: Any])?["configurationSHA256"] as? String else {
            throw ProbeError.invalidConfiguration
        }
        // Capture checkpoints must not repeatedly serialize vectors/history from every finished run.
        let checkpoint: [String: Any] = ["schemaVersion": 1, "configurationSHA256": configurationHash, "run": result]
        try JSONSerialization.data(withJSONObject: checkpoint, options: [.sortedKeys]).write(to: activeResultURL, options: .atomic)
    }
    private static func memberships(_ state: ProvenanceSnapshot, samples: [UUID: String]) -> [String: [String]] {
        Dictionary(uniqueKeysWithValues: samples.map { id, source in (source, state.memberships[id, default: []].map(\.uuidString).sorted()) })
    }
    private static func eventFacts(_ events: [ProvenanceEvent], samples: [UUID: String]) throws -> [[String: Any]] {
        try events.map { event in
            let payload = try event.payload()
            let assignments = Dictionary(uniqueKeysWithValues: payload.assignments.compactMap { key, values -> (String, [String])? in
                guard let id = UUID(uuidString: key), let source = samples[id] else { return nil }
                return (source, values.map(\.uuidString).sorted())
            })
            return ["id": event.id.uuidString, "kind": event.kind.rawValue, "sequence": event.sequence ?? 0,
                "itemID": event.memoryID.flatMap { samples[$0] } as Any? ?? NSNull(),
                "clusterID": payload.clusterID?.uuidString as Any? ?? NSNull(), "parents": payload.parents.map(\.uuidString),
                "assignments": assignments, "sourceRevisionID": payload.sourceRevisionID?.uuidString as Any? ?? NSNull(),
                "citedEventIDs": payload.citedEventIDs.map(\.uuidString), "origin": event.origin, "model": payload.model,
                "rationale": payload.rationale, "scores": payload.scores, "timestamp": event.timestamp.timeIntervalSince1970]
        }
    }
    private static func stableUUID(_ text: String) -> UUID {
        let bytes = Array(SHA256.hash(data: Data(text.utf8)).prefix(16))
        return UUID(uuid: (bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5], bytes[6], bytes[7],
                           bytes[8], bytes[9], bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15]))
    }
    private static func ordered(_ library: OrganizationLibrary, order: String) -> [OrganizationInput] {
        let items = library.items.sorted { $0.timestamp == $1.timestamp ? $0.id < $1.id : $0.timestamp < $1.timestamp }
        if order == "reverse" { return Array(items.reversed()) }
        if order == "interleaved" {
            if let ids = library.orders?[order] {
                let lookup = Dictionary(uniqueKeysWithValues: items.map { ($0.id, $0) })
                return ids.compactMap { lookup[$0] }
            }
            let chunk = max(1, Int(ceil(Double(items.count) / 6)))
            return (0..<chunk).flatMap { offset in stride(from: offset, to: items.count, by: chunk).map { items[$0] } }
        }
        if order.hasPrefix("seed") {
            var state: UInt64 = order == "seed17" ? 17 : 29
            var shuffled = items
            for i in stride(from: shuffled.count - 1, through: 1, by: -1) {
                state = state &* 6364136223846793005 &+ 1442695040888963407
                shuffled.swapAt(i, Int(state % UInt64(i + 1)))
            }
            return shuffled
        }
        return items
    }
    private static func residentBytes() -> UInt64 {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size / MemoryLayout<natural_t>.size)
        let status = withUnsafeMutablePointer(to: &info) { pointer in
            pointer.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        return status == KERN_SUCCESS ? UInt64(info.resident_size) : 0
    }
}
