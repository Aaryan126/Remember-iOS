import Foundation
import FoundationModels
import CoreML
import SwiftUI
import UIKit
import Darwin

// Keep the C7 output schema unchanged: only the reviewer instructions differ.
@Generable enum ProjectVerdict: String, Codable { case same_project, separate_projects, abstain }
@Generable struct SourceQuotation: Codable {
    @Guide(description: "An exact source ID from the supplied packet") var sourceID: String
    @Guide(description: "A short verbatim substring of that source, not a paraphrase") var quote: String
}
@Generable struct ProjectVerification: Codable {
    @Guide(description: "Exact evidence, including both queried sources for a decisive verdict", .maximumCount(4))
    var evidence: [SourceQuotation]
    var verdict: ProjectVerdict
    @Guide(description: "One short sentence explaining the relationship or missing evidence") var rationale: String
}
struct Request: Decodable { let instructions: String; let packet: String; let context: String; let reviewer: String }
struct ControlPair: Decodable { let first: String; let second: String; let key: String }
struct Inputs: Decodable { let requests: [String: Request]; let controls: [String: ControlPair] }
enum QualityError: Error { case arguments, unavailable, metadata, foreground }

// Independent of the main actor/model executor, including terminal publication.
final class Recorder: @unchecked Sendable {
    let unit: String
    private let lock = NSLock()
    private let started = ProcessInfo.processInfo.systemUptime
    private var events: [[String: Any]] = []
    private var finished = false
    private var expired = false
    private var task: Task<Void, Never>?
    init(_ unit: String) { self.unit = unit }
    func attach(_ task: Task<Void, Never>) {
        lock.lock(); self.task = task; let expired = expired; lock.unlock()
        if expired { task.cancel() }
    }
    func mark(_ phase: String, _ fields: [String: Any] = [:]) {
        lock.lock(); defer { lock.unlock() }
        guard !finished else { return }
        events.append(fields.merging(["phase": phase, "elapsedSeconds": ProcessInfo.processInfo.systemUptime-started]) { _, v in v })
        do {
            let data = try JSONSerialization.data(withJSONObject: ["unit": unit, "events": events], options: .sortedKeys)
            try data.write(to: URL.documentsDirectory.appendingPathComponent("trace-"+unit+".json"), options: .atomic)
        } catch { exit(4) }
    }
    func arm() {
        DispatchQueue.global(qos: .userInitiated).asyncAfter(deadline: .now()+60) { [self] in
            lock.lock(); guard !finished else { lock.unlock(); return }
            expired = true; let current = task; lock.unlock()
            mark("deadline_cancel_requested"); current?.cancel()
            DispatchQueue.global(qos: .userInitiated).asyncAfter(deadline: .now()+2) { [self] in
                finish(nil, error: "app_deadline_cancellation_grace_expired")
            }
        }
    }
    func finish(_ output: [String: Any]?, error: String? = nil) -> Never {
        lock.lock()
        if finished { lock.unlock(); Thread.exit(); fatalError("unreachable") }
        finished = true
        let result: [String: Any] = ["schemaVersion": 1, "unit": unit, "syntheticOnly": true,
            "status": error == nil && !expired ? "ok" : "error",
            "os": ProcessInfo.processInfo.operatingSystemVersionString,
            "result": output ?? [:], "error": error as Any? ?? NSNull(), "deadlineFired": expired,
            "elapsedSeconds": ProcessInfo.processInfo.systemUptime-started, "events": events]
        do {
            let data = try JSONSerialization.data(withJSONObject: result, options: .sortedKeys)
            let path = URL.documentsDirectory.appendingPathComponent("unit-"+unit+".json")
            guard !FileManager.default.fileExists(atPath: path.path) else { exit(3) }
            try data.write(to: path, options: .atomic)
            print("IOS27_RESULT " + String(decoding: data, as: UTF8.self)); fflush(stdout); exit(0)
        } catch { exit(4) }
    }
}

@MainActor final class Controller {
    static let shared = Controller()
    private var started = false

    func control(_ pair: ControlPair, root: URL) async throws -> [String: Any] {
        let assets = FileManager.default.fileExists(atPath: root.appendingPathComponent("MatcherAssets").path)
            ? root.appendingPathComponent("MatcherAssets") : root
        let parameters = try JSONDecoder().decode(D3Parameters.self, from: Data(contentsOf: assets.appendingPathComponent("D3Parameters.json")))
        guard parameters.threshold == D3OrganizationPolicy.threshold else { throw QualityError.metadata }
        let features = try D3Features(parameters: parameters)
        let tokenizer = try D3Tokenizer(vocabularyURL: assets.appendingPathComponent("D3Vocabulary.txt"))
        let provider = AppleProjectEmbedding()
        guard let a = try await provider.embedding(for: pair.first), let b = try await provider.embedding(for: pair.second),
              let sa = a.semanticVector, let sb = b.semanticVector,
              a.space == D3OrganizationPolicy.embeddingSpace, a.space == b.space else { throw QualityError.unavailable }
        let values = try features.values(first: pair.first, second: pair.second,
            contextualA: a.vector, contextualB: b.vector, sentenceA: sa, sentenceB: sb)
        let tokens = try [(pair.first, pair.second), (pair.second, pair.first)].map { try tokenizer.encode(first: $0.0, second: $0.1, length: 512) }
        var results: [String: Any] = [:]
        for precision in ["fp16", "fp32"] {
            try Task.checkCancellation()
            let configuration = MLModelConfiguration(); configuration.computeUnits = .cpuOnly
            let name = precision == "fp16" ? "D3Matcher" : "D3MatcherFP32"
            let model = try MLModel(contentsOf: assets.appendingPathComponent(name+".mlmodelc"), configuration: configuration)
            let metadata = model.modelDescription.metadata[.creatorDefinedKey] as? [String: String]
            guard metadata?["weights_sha256"] == parameters.weightsSHA256,
                  metadata?["class_order"] == "[\"not_same\", \"same\"]" else { throw QualityError.metadata }
            let probabilities = try tokens.map { try D3PairMatcher.probability(model: model, tokens: $0) }
            let score = try features.score(features: values, neuralProbability: probabilities.reduce(0,+)/2)
            results[precision] = ["score": score, "probabilities": probabilities, "accepted": score >= parameters.threshold]
        }
        return ["key": pair.key, "features": values, "space": a.space, "threshold": parameters.threshold, "scores": results]
    }

    func execute() async {
        guard !started else { return }; started = true
        let args = CommandLine.arguments
        guard let i = args.firstIndex(of: "--unit"), i+1 < args.count else { exit(2) }
        let unit = args[i+1], recorder = Recorder(args[i+1])
        recorder.mark("app_task_entered"); recorder.arm()
        let task = Task { @MainActor in
            do {
                for _ in 0..<50 {
                    if UIApplication.shared.applicationState == .active { break }
                    try await Task.sleep(for: .milliseconds(100))
                }
                guard UIApplication.shared.applicationState == .active, UIApplication.shared.isProtectedDataAvailable else { throw QualityError.foreground }
                UIApplication.shared.isIdleTimerDisabled = true
                recorder.mark("foreground_verified", ["applicationState": UIApplication.shared.applicationState.rawValue])
                let root = Bundle.main.resourceURL!
                let inputs = try JSONDecoder().decode(Inputs.self, from: Data(contentsOf: root.appendingPathComponent("inputs.json")))
                if let pair = inputs.controls[unit] { recorder.finish(try await control(pair, root: root)) }
                guard let request = inputs.requests[unit] else { throw QualityError.arguments }
                let model = SystemLanguageModel.default
                recorder.mark("availability", ["availability": String(describing: model.availability), "contextSize": model.contextSize])
                guard model.availability == .available else { throw QualityError.unavailable }
                let session = LanguageModelSession(model: model, instructions: request.instructions)
                recorder.mark("response_started")
                let start = ProcessInfo.processInfo.systemUptime
                let response = try await session.respond(to: request.packet, generating: ProjectVerification.self,
                    options: GenerationOptions(sampling: .greedy, maximumResponseTokens: 600))
                let seconds = ProcessInfo.processInfo.systemUptime-start
                recorder.mark("response_finished")
                let output = try JSONSerialization.jsonObject(with: JSONEncoder().encode(response.content))
                recorder.finish(["output": output, "context": request.context, "reviewer": request.reviewer,
                    "generationSeconds": seconds, "contextSize": model.contextSize])
            } catch { recorder.finish(nil, error: String(describing: error)) }
        }
        recorder.attach(task); await task.value
    }
}

@main struct QualityProbeApp: App {
    var body: some Scene { WindowGroup {
        Text("Remember: grouping evaluation\nFictional inputs only\nPlease keep this app open.")
            .padding().task { await Controller.shared.execute() }
    } }
}
