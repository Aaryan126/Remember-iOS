import SwiftUI
import Foundation
import Darwin

// Stage 4 deliberately reuses the frozen Stage 3 tokenizer and runtime unchanged.
private struct Fixture: Codable, Sendable { let id: String; let first: String; let second: String }
private struct Inputs: Decodable { let schemaVersion: Int; let fixtures: [Fixture] }
private struct Candidate: Decodable { let candidateID: String; let untrainedHead: Bool; let classOrder: [String] }
private struct MemorySample: Codable {
    let uptime: Double
    let footprintBytes: UInt64
    let residentBytes: UInt64
    let thermalState: Int
}

private final class MemorySampler: @unchecked Sendable {
    private let queue = DispatchQueue(label: "MatcherProbe.memory")
    private var timer: DispatchSourceTimer?
    private var samples: [MemorySample] = []
    private var failures = 0
    init() {
        queue.sync { sample() }
        let timer = DispatchSource.makeTimerSource(queue: queue)
        timer.schedule(deadline: .now(), repeating: .milliseconds(20), leeway: .milliseconds(2))
        timer.setEventHandler { [weak self] in self?.sample() }
        self.timer = timer
        timer.resume()
    }
    private func sample() {
        var info = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size / MemoryLayout<integer_t>.size)
        let result = withUnsafeMutablePointer(to: &info) { pointer in
            pointer.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        guard result == KERN_SUCCESS else { failures += 1; return }
        samples.append(MemorySample(uptime: ProcessInfo.processInfo.systemUptime,
            footprintBytes: info.phys_footprint, residentBytes: info.resident_size,
            thermalState: ProcessInfo.processInfo.thermalState.rawValue))
    }
    func peak() -> UInt64 { queue.sync { samples.map(\.footprintBytes).max() ?? 0 } }
    func stop() -> MemoryReport {
        timer?.cancel()
        return queue.sync {
            sample()
            return MemoryReport(requestedIntervalSeconds: 0.020, failedSamples: failures, samples: samples)
        }
    }
}
private struct MemoryReport: Codable {
    let requestedIntervalSeconds: Double
    let failedSamples: Int
    let samples: [MemorySample]
}
private struct Storage: Codable {
    let bundleLogicalBytes: Int64
    let compiledModelLogicalBytes: Int64
    let documentsLogicalBytes: Int64
    let libraryLogicalBytes: Int64
    let temporaryLogicalBytes: Int64
    static func bytes(_ root: URL) throws -> Int64 {
        guard let iterator = FileManager.default.enumerator(at: root,
            includingPropertiesForKeys: [.isRegularFileKey, .fileSizeKey],
            options: [], errorHandler: nil) else { throw MatcherError.missingResource(root.lastPathComponent) }
        var total: Int64 = 0
        for case let url as URL in iterator {
            let values = try url.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey])
            if values.isRegularFile == true { total += Int64(values.fileSize ?? 0) }
        }
        return total
    }
    static func current() throws -> Storage {
        Storage(bundleLogicalBytes: try bytes(Bundle.main.bundleURL),
            compiledModelLogicalBytes: try bytes(resource("MatcherReference", "mlmodelc")),
            documentsLogicalBytes: try bytes(.documentsDirectory),
            libraryLogicalBytes: try bytes(URL.libraryDirectory),
            temporaryLogicalBytes: try bytes(FileManager.default.temporaryDirectory))
    }
}
private struct LaunchRecord: Codable {
    let runID: String; let job: String; let launchID: String; let candidateID: String
    let mode: String; let length: Int; let count: Int
    let processID: Int32; let operatingSystem: String; let lowPowerMode: Bool
    let recordedAt: Date; let startedUptime: Double; let thermalState: Int
    let computeUnits: String; let storage: Storage
}
private struct LoadRecord: Codable {
    let launchID: String; let modelAndTokenizerLoadSeconds: Double; let loadWallSeconds: Double
    let launchTaskToLoadedSeconds: Double; let peakFootprintBytes: UInt64
}
private struct PairResult: Codable {
    let fixtureID: String; let averagedProbabilities: [Double]
}
private struct TimingRecord: Codable {
    let launchID: String; let index: Int; let length: Int; let passes: Int
    let fullShortlistSeconds: Double; let tokenizationSeconds: Double; let modelPredictionSeconds: Double
    let thermalBefore: Int; let thermalAfter: Int; let peakFootprintBytes: UInt64
    let pairs: [PairResult]
}
private struct ParityRecord: Codable {
    let launchID: String; let id: String; let fixtureID: String; let length: Int
    let orientation: String; let prediction: MatcherPrediction
}
private struct EndRecord: Codable {
    let launchID: String; let status: String; let message: String
    let recordedAt: Date; let memory: MemoryReport; let storage: Storage?
}
private func resource(_ name: String, _ ext: String) throws -> URL {
    guard let url = Bundle.main.url(forResource: name, withExtension: ext) else { throw MatcherError.missingResource(name) }
    return url
}
private func save<T: Encodable>(_ value: T, to url: URL) throws {
    guard !FileManager.default.fileExists(atPath: url.path) else { throw CocoaError(.fileWriteFileExists) }
    try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
    let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
    try encoder.encode(value).write(to: url, options: .atomic)
}
private struct Job: Sendable {
    let runID: String; let name: String; let launchID: String; let mode: String; let length: Int; let count: Int
    init() throws {
        let args = Array(ProcessInfo.processInfo.arguments.dropFirst())
        guard args.count == 7, args[0] == "stage4",
              [args[1], args[2], args[3]].allSatisfy({ !$0.isEmpty && $0.count <= 100 && $0.allSatisfy { $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "-") } }),
              ["cold", "warm", "parity", "interrupt"].contains(args[4]),
              let length = Int(args[5]), [256, 512].contains(length),
              let count = Int(args[6]), (1...100).contains(count) else { throw MatcherError.invalidFixture }
        runID = args[1]; name = args[2]; launchID = args[3]; mode = args[4]; self.length = length; self.count = count
    }
    var root: URL { URL.documentsDirectory.appendingPathComponent(runID).appendingPathComponent(name) }
    var launchRoot: URL { root.appendingPathComponent("launches").appendingPathComponent(launchID) }
    var pauseURL: URL { URL.documentsDirectory.appendingPathComponent(runID).appendingPathComponent("pause-\(launchID).json") }
    func boundary() throws {
        try Task.checkCancellation()
        if FileManager.default.fileExists(atPath: pauseURL.path) { throw CancellationError() }
        // High thermal pressure is a recorded stop, never a discarded slow sample.
        if ProcessInfo.processInfo.thermalState.rawValue >= 2 { throw ProbeFailure.thermalPressure }
    }
}
private enum ProbeFailure: Error { case thermalPressure }

private func shortlist(runtime: MatcherRuntime, fixtures: [Fixture], index: Int,
                       job: Job, sampler: MemorySampler) async throws -> TimingRecord {
    let before = ProcessInfo.processInfo.thermalState.rawValue
    let start = ProcessInfo.processInfo.systemUptime
    var tokens = 0.0, predictionTime = 0.0
    var pairs: [PairResult] = []
    // Ten unique fictional pairs, rotating through all 104 fixtures (including edge cases).
    for offset in 0..<10 {
        try job.boundary()
        let fixture = fixtures[(index * 10 + offset) % fixtures.count]
        let forward = try await runtime.predict(first: fixture.first, second: fixture.second, length: job.length)
        try job.boundary()
        let reverse = try await runtime.predict(first: fixture.second, second: fixture.first, length: job.length)
        tokens += forward.tokenizationSeconds + reverse.tokenizationSeconds
        predictionTime += forward.predictionSeconds + reverse.predictionSeconds
        pairs.append(PairResult(fixtureID: fixture.id,
            averagedProbabilities: zip(forward.probabilities, reverse.probabilities).map { ($0 + $1) / 2 }))
    }
    let duration = ProcessInfo.processInfo.systemUptime - start
    return TimingRecord(launchID: job.launchID, index: index, length: job.length, passes: 20,
        fullShortlistSeconds: duration, tokenizationSeconds: tokens, modelPredictionSeconds: predictionTime,
        thermalBefore: before, thermalAfter: ProcessInfo.processInfo.thermalState.rawValue,
        peakFootprintBytes: sampler.peak(), pairs: pairs)
}

private func execute(_ job: Job) async -> String {
    let start = ProcessInfo.processInfo.systemUptime
    let sampler = MemorySampler()
    var status = "failed", message = ""
    do {
        let candidate = try JSONDecoder().decode(Candidate.self, from: Data(contentsOf: resource("candidate", "json")))
        let inputs = try JSONDecoder().decode(Inputs.self, from: Data(contentsOf: resource("fixtures", "json")))
        guard candidate.untrainedHead, candidate.classOrder == ["same", "related", "unrelated"],
              candidate.candidateID.count == 64, candidate.candidateID.allSatisfy({ "0123456789abcdef".contains($0) }),
              inputs.schemaVersion == 1, inputs.fixtures.count == 104,
              Set(inputs.fixtures.map(\.id)).count == 104,
              inputs.fixtures.allSatisfy({ !$0.id.isEmpty && $0.id.allSatisfy { $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "-") } })
        else { throw MatcherError.invalidFixture }
        try save(LaunchRecord(runID: job.runID, job: job.name, launchID: job.launchID, candidateID: candidate.candidateID,
            mode: job.mode, length: job.length, count: job.count, processID: getpid(),
            operatingSystem: ProcessInfo.processInfo.operatingSystemVersionString,
            lowPowerMode: ProcessInfo.processInfo.isLowPowerModeEnabled, recordedAt: Date(), startedUptime: start,
            thermalState: ProcessInfo.processInfo.thermalState.rawValue, computeUnits: "all", storage: try Storage.current()),
            to: job.launchRoot.appendingPathComponent("start.json"))
        try job.boundary()
        let loadStart = ProcessInfo.processInfo.systemUptime
        let runtime = try MatcherRuntime(modelURL: resource("MatcherReference", "mlmodelc"), vocabularyURL: resource("vocab", "txt"))
        let loaded = ProcessInfo.processInfo.systemUptime
        try save(LoadRecord(launchID: job.launchID, modelAndTokenizerLoadSeconds: runtime.modelLoadSeconds,
            loadWallSeconds: loaded - loadStart, launchTaskToLoadedSeconds: loaded - start,
            peakFootprintBytes: sampler.peak()), to: job.launchRoot.appendingPathComponent("load.json"))
        if job.mode == "parity" {
            for fixture in inputs.fixtures {
                for length in [256, 512] {
                    for orientation in ["forward", "reverse"] {
                        try job.boundary()
                        let id = "\(fixture.id)-\(length)-\(orientation)"
                        let url = job.root.appendingPathComponent("records/\(id).json")
                        if FileManager.default.fileExists(atPath: url.path) {
                            let prior = try JSONDecoder().decode(ParityRecord.self, from: Data(contentsOf: url))
                            guard prior.id == id, prior.length == length, prior.fixtureID == fixture.id,
                                  prior.orientation == orientation else { throw MatcherError.invalidFixture }
                            continue
                        }
                        let value = try await runtime.predict(first: orientation == "forward" ? fixture.first : fixture.second,
                            second: orientation == "forward" ? fixture.second : fixture.first, length: length)
                        try save(ParityRecord(launchID: job.launchID, id: id, fixtureID: fixture.id,
                            length: length, orientation: orientation, prediction: value), to: url)
                    }
                }
            }
        } else {
            // A cold launch includes the first real twenty-pass decision path, separately timed.
            let warmups = job.mode == "cold" ? 0 : 3
            for index in 0..<warmups {
                let value = try await shortlist(runtime: runtime, fixtures: inputs.fixtures, index: index, job: job, sampler: sampler)
                try save(value, to: job.launchRoot.appendingPathComponent("warmup-\(index).json"))
            }
            for index in 0..<job.count {
                try job.boundary()
                let url = job.root.appendingPathComponent("records/\(index).json")
                if FileManager.default.fileExists(atPath: url.path) {
                    let prior = try JSONDecoder().decode(TimingRecord.self, from: Data(contentsOf: url))
                    guard prior.index == index, prior.length == job.length, prior.passes == 20,
                          prior.pairs.count == 10 else { throw MatcherError.invalidFixture }
                    continue
                }
                let value = try await shortlist(runtime: runtime, fixtures: inputs.fixtures, index: index, job: job, sampler: sampler)
                // Persist a finished shortlist even if a pause arrived during its last prediction.
                try save(value, to: url)
                print("STAGE4 saved \(job.name) \(index + 1)/\(job.count) seconds=\(value.fullShortlistSeconds)")
                fflush(stdout)
            }
        }
        status = "complete"
    } catch is CancellationError { status = "paused"; message = "Unfinished shortlist will be repeated; completed records retained." }
    catch { message = String(describing: error) }
    let memory = sampler.stop()
    do {
        try save(EndRecord(launchID: job.launchID, status: status, message: message, recordedAt: Date(),
            memory: memory, storage: try Storage.current()), to: job.launchRoot.appendingPathComponent("end.json"))
    } catch { status = "failed"; message += " End receipt failed: \(error)" }
    print("STAGE4 \(status) \(job.name) \(message)"); fflush(stdout)
    return status
}

@MainActor private final class Stage4Controller: ObservableObject {
    @Published var status = "Preparing isolated device measurements…"
    private var task: Task<Void, Never>?
    private var started = false
    func start() {
        guard !started else { return }; started = true
        do {
            let job = try Job()
            UIApplication.shared.isIdleTimerDisabled = true
            status = "Running \(job.name). Fictional inputs only."
            task = Task {
                let worker = Task.detached { await execute(job) }
                let result = await withTaskCancellationHandler(operation: { await worker.value }, onCancel: { worker.cancel() })
                status = result
                UIApplication.shared.isIdleTimerDisabled = false
                // Controlled exit is only for this command-line-driven development probe.
                exit(result == "failed" ? 1 : 0)
            }
        } catch { status = "Launch from the Stage 4 Mac controller. \(error)" }
    }
    func pause() { status = "Pausing and saving…"; task?.cancel() }
}

@main struct Stage4ProbeApp: App {
    @StateObject private var controller = Stage4Controller()
    @Environment(\.scenePhase) private var phase
    var body: some Scene {
        WindowGroup {
            NavigationStack {
                Form {
                    Section("On-device feasibility") {
                        Text(controller.status)
                        Text("Untrained reference head: these runs measure speed, memory and output consistency—not grouping quality.")
                        Text("No Remember data, shared storage or network requests.")
                        Button("Pause measurements", role: .cancel) { controller.pause() }
                    }
                }.navigationTitle("Matcher Probe")
            }.task { controller.start() }
            .onChange(of: phase) { _, newPhase in if newPhase != .active { controller.pause() } }
        }
    }
}
