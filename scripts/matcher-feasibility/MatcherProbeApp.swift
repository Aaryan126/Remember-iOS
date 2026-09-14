import SwiftUI
import Foundation

struct ProbeFixture: Decodable, Sendable { let id: String; let first: String; let second: String }
struct ProbeInputs: Decodable { let schemaVersion: Int; let fixtures: [ProbeFixture] }
struct ProbeCandidate: Decodable { let candidateID: String; let untrainedHead: Bool; let classOrder: [String] }
struct ProbeRecord: Codable {
    let candidateID: String
    let fixtureID: String
    let length: Int
    let orientation: String
    let recordedAt: Date
    let prediction: MatcherPrediction
}

@MainActor
final class ProbeController: ObservableObject {
    @Published var status = "Ready. Fictional inputs only."
    @Published var completed = 0
    @Published var total = 0
    @Published var running = false
    private var task: Task<Void, Never>?

    func pause() {
        guard running else { return }
        status = "Pausing after the current prediction is saved…"
        task?.cancel()
    }

    func run() {
        guard !running else { return }
        running = true
        task = Task {
            do {
                let bundle = Bundle.main
                func resource(_ name: String, _ ext: String) throws -> URL {
                    guard let url = bundle.url(forResource: name, withExtension: ext) else { throw MatcherError.missingResource(name) }
                    return url
                }
                let candidate = try JSONDecoder().decode(ProbeCandidate.self, from: Data(contentsOf: resource("candidate", "json")))
                guard candidate.untrainedHead, candidate.classOrder == ["same", "related", "unrelated"],
                      candidate.candidateID.count == 64,
                      candidate.candidateID.allSatisfy({ "0123456789abcdef".contains($0) }) else { throw MatcherError.invalidFixture }
                let inputs = try JSONDecoder().decode(ProbeInputs.self, from: Data(contentsOf: resource("fixtures", "json")))
                guard inputs.schemaVersion == 1, inputs.fixtures.count == 104,
                      Set(inputs.fixtures.map(\.id)).count == inputs.fixtures.count,
                      inputs.fixtures.allSatisfy({ !$0.id.isEmpty && $0.id.allSatisfy { $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "-") } })
                else { throw MatcherError.invalidFixture }
                total = inputs.fixtures.count * 4
                completed = 0
                status = "Loading the isolated reference model…"
                let runtime = try MatcherRuntime(modelURL: resource("MatcherReference", "mlmodelc"), vocabularyURL: resource("vocab", "txt"))
                let root = URL.documentsDirectory.appendingPathComponent("MatcherProbe-" + candidate.candidateID, isDirectory: true)
                try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
                let encoder = JSONEncoder()
                encoder.outputFormatting = [.sortedKeys]
                for fixture in inputs.fixtures {
                    for length in [256, 512] {
                        for orientation in ["forward", "reverse"] {
                            try Task.checkCancellation()
                            let url = root.appendingPathComponent("\(fixture.id)-\(length)-\(orientation).json")
                            if FileManager.default.fileExists(atPath: url.path) {
                                let saved = try JSONDecoder().decode(ProbeRecord.self, from: Data(contentsOf: url))
                                guard saved.candidateID == candidate.candidateID, saved.fixtureID == fixture.id,
                                      saved.length == length, saved.orientation == orientation else { throw MatcherError.invalidFixture }
                            } else {
                                let prediction = try await runtime.predict(first: orientation == "forward" ? fixture.first : fixture.second,
                                    second: orientation == "forward" ? fixture.second : fixture.first, length: length)
                                // Save the completed result even if pause arrived during
                                // inference. Cancellation is checked before the next case.
                                let record = ProbeRecord(candidateID: candidate.candidateID, fixtureID: fixture.id,
                                    length: length, orientation: orientation, recordedAt: Date(), prediction: prediction)
                                try encoder.encode(record).write(to: url, options: .atomic)
                            }
                            completed += 1
                            status = "Saved \(completed) of \(total) reference predictions."
                        }
                    }
                }
                status = "Complete. Results saved in this probe’s Documents folder."
            } catch is CancellationError {
                status = "Paused. Completed predictions are saved; tap Resume to continue."
            } catch {
                status = "Stopped: \(error.localizedDescription). Completed results are retained."
            }
            running = false
            task = nil
        }
    }
}

@main
struct MatcherProbeApp: App {
    @StateObject private var controller = ProbeController()
    @Environment(\.scenePhase) private var scenePhase
    var body: some Scene {
        WindowGroup {
            NavigationStack {
                Form {
                    Section("Isolated feasibility probe") {
                        Text("MiniLM reference · FP16")
                        Text("The classification head is untrained. Outputs test conversion consistency, not memory-grouping quality.")
                            .font(.footnote).foregroundStyle(.secondary)
                        Text("No Remember vault access, cloud requests or shared app storage.")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                    Section("Progress") {
                        Text(controller.status).accessibilityIdentifier("probeStatus")
                        if controller.total > 0 { ProgressView(value: Double(controller.completed), total: Double(controller.total)) }
                        Button(controller.completed > 0 ? "Resume checks" : "Run checks") { controller.run() }
                            .disabled(controller.running)
                        Button("Pause", role: .cancel) { controller.pause() }.disabled(!controller.running)
                    }
                    Section {
                        Text("Each completed prediction is saved separately. Results are exported and assessed on the Mac; this app contains no benchmark labels.")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }.navigationTitle("Matcher Probe")
            }.onChange(of: scenePhase) { _, phase in if phase != .active { controller.pause() } }
        }
    }
}
