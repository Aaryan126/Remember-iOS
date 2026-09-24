import Foundation
import CoreML
import Darwin
#if os(iOS)
import SwiftUI
#endif

struct EmbeddingFixture: Decodable { let contextual: [Float]; let sentence: [Float] }
struct DirectionFixture: Decodable { let tokens: D3Tokens; let probability: Double }
struct PairFixture: Decodable {
    let id: String; let first: String; let second: String
    let embeddingA: EmbeddingFixture; let embeddingB: EmbeddingFixture
    let directions: [DirectionFixture]; let features: [Double]
    let expectedScore: Double; let coreMLScore: Double
}
struct Fixtures: Decodable { let fixtures: [PairFixture] }
enum ProbeError: Error { case arguments, unavailable, space, metadata, tokens }

@MainActor enum PrecisionProbe {
    static func memory() -> [String: UInt64] {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size / MemoryLayout<natural_t>.size)
        let status = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        return status == KERN_SUCCESS ? ["resident": UInt64(info.resident_size), "processPeakResident": UInt64(info.resident_size_max)] : [:]
    }

    static func perform(_ unit: String, root: URL) async throws -> [String: Any] {
        let parts = unit.split(separator: "-")
        let fixtures = try JSONDecoder().decode(Fixtures.self, from: Data(contentsOf: root.appendingPathComponent("parity-inputs.json")))
        guard parts.count == 2, ["fp16", "fp32"].contains(parts[0]), let index = Int(parts[1]), fixtures.fixtures.indices.contains(index) else { throw ProbeError.arguments }
        let fixture = fixtures.fixtures[index]
        let assets = FileManager.default.fileExists(atPath: root.appendingPathComponent("MatcherAssets").path) ? root.appendingPathComponent("MatcherAssets") : root
        let parameters = try JSONDecoder().decode(D3Parameters.self, from: Data(contentsOf: assets.appendingPathComponent("D3Parameters.json")))
        let features = try D3Features(parameters: parameters)
        let tokenizer = try D3Tokenizer(vocabularyURL: assets.appendingPathComponent("D3Vocabulary.txt"))
        let provider = AppleProjectEmbedding()
        let embeddingStart = ProcessInfo.processInfo.systemUptime
        guard let a = try await provider.embedding(for: fixture.first), let b = try await provider.embedding(for: fixture.second),
              let sa = a.semanticVector, let sb = b.semanticVector else { throw ProbeError.unavailable }
        guard a.space == D3OrganizationPolicy.embeddingSpace, b.space == a.space else { throw ProbeError.space }
        let embeddingSeconds = ProcessInfo.processInfo.systemUptime - embeddingStart
        let fresh = try features.values(first: fixture.first, second: fixture.second,
            contextualA: a.vector, contextualB: b.vector, sentenceA: sa, sentenceB: sb)
        let fixed = try features.values(first: fixture.first, second: fixture.second,
            contextualA: fixture.embeddingA.contextual, contextualB: fixture.embeddingB.contextual,
            sentenceA: fixture.embeddingA.sentence, sentenceB: fixture.embeddingB.sentence)
        let config = MLModelConfiguration(); config.computeUnits = .cpuOnly
        let name = parts[0] == "fp16" ? "D3Matcher" : "D3MatcherFP32"
        let loadStart = ProcessInfo.processInfo.systemUptime
        let model = try MLModel(contentsOf: assets.appendingPathComponent(name + ".mlmodelc"), configuration: config)
        let loadSeconds = ProcessInfo.processInfo.systemUptime - loadStart
        let metadata = model.modelDescription.metadata[.creatorDefinedKey] as? [String: String]
        guard metadata?["weights_sha256"] == parameters.weightsSHA256,
              metadata?["class_order"] == "[\"not_same\", \"same\"]" else { throw ProbeError.metadata }
        var probabilities: [Double] = [], timings: [Double] = []
        var firstTokens: D3Tokens?
        for (i, pair) in [(fixture.first, fixture.second), (fixture.second, fixture.first)].enumerated() {
            let tokens = try tokenizer.encode(first: pair.0, second: pair.1, length: 512)
            guard tokens == fixture.directions[i].tokens else { throw ProbeError.tokens }
            if i == 0 { firstTokens = tokens }
            let start = ProcessInfo.processInfo.systemUptime
            probabilities.append(try D3PairMatcher.probability(model: model, tokens: tokens))
            timings.append(ProcessInfo.processInfo.systemUptime - start)
        }
        guard let firstTokens else { throw ProbeError.tokens }
        let warmStart = ProcessInfo.processInfo.systemUptime
        let repeated = try D3PairMatcher.probability(model: model, tokens: firstTokens)
        let warmSeconds = ProcessInfo.processInfo.systemUptime - warmStart
        let mean = probabilities.reduce(0,+)/2
        let fixedScore = try features.score(features: fixed, neuralProbability: mean)
        let freshScore = try features.score(features: fresh, neuralProbability: mean)
        let originalDecision = fixture.expectedScore >= parameters.threshold
        let featureDelta = zip(fixed,fixture.features).map { abs($0-$1) }.max() ?? 0
        let probabilityDelta = zip(probabilities,fixture.directions).map { abs($0-$1.probability) }.max() ?? 0
        return ["fixture":fixture.id,"precision":String(parts[0]),"space":a.space,"tokenParity":true,
            "fixedFeatures":fixed,"freshFeatures":fresh,"probabilities":probabilities,
            "fixedScore":fixedScore,"freshScore":freshScore,
            "fixedDecisionUnchanged":(fixedScore >= parameters.threshold) == originalDecision,
            "freshDecisionUnchanged":(freshScore >= parameters.threshold) == originalDecision,
            "originalStrictGatePassed":featureDelta <= 1e-8 && abs(fixedScore-fixture.coreMLScore) <= 1e-7 && (fixedScore >= parameters.threshold) == originalDecision,
            "originalNeuralBoundMet":probabilityDelta <= 0.002,"maximumNeuralDelta":probabilityDelta,
            "embeddingSeconds":embeddingSeconds,"loadSeconds":loadSeconds,"inferenceSeconds":timings,
            "warmRepeatSeconds":warmSeconds,"warmRepeatDelta":abs(repeated-probabilities[0]),"computeUnits":"cpuOnly"]
    }

    static func execute() async {
        let args = CommandLine.arguments
        guard let i = args.firstIndex(of:"--unit"), i+1 < args.count else { exit(2) }
        let unit = args[i+1]
        let root: URL
        #if os(iOS)
        root = Bundle.main.resourceURL!
        #else
        guard let j = args.firstIndex(of:"--root"), j+1 < args.count else { exit(2) }
        root = URL(fileURLWithPath:args[j+1])
        #endif
        let start = ProcessInfo.processInfo.systemUptime
        var result: [String:Any] = ["unit":unit,"schemaVersion":1,"syntheticOnly":true,
            "os":ProcessInfo.processInfo.operatingSystemVersionString,"memoryBefore":memory()]
        do { result["result"] = try await perform(unit,root:root);result["status"]="ok" }
        catch { result["status"]="error";result["error"]=String(describing:error) }
        result["memoryAfter"]=memory();result["elapsedSeconds"]=ProcessInfo.processInfo.systemUptime-start
        do {
            let data = try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys])
            #if os(iOS)
            let path = URL.documentsDirectory.appendingPathComponent("unit-"+unit+".json")
            guard !FileManager.default.fileExists(atPath:path.path) else { exit(3) }
            try data.write(to:path,options:[.atomic])
            #endif
            print("IOS27_RESULT "+String(decoding:data,as:UTF8.self));fflush(stdout);exit(0)
        } catch { exit(4) }
    }
}
#if os(iOS)
@main struct PrecisionProbeApp: App {
    var body: some Scene { WindowGroup { Text("D3 precision comparison\nFictional inputs only").task { await PrecisionProbe.execute() } } }
}
#else
@main struct PrecisionProbeCommand { static func main() async { await PrecisionProbe.execute() } }
#endif
