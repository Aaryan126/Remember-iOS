import Foundation
import FoundationModels
import CoreML
import NaturalLanguage
import Darwin
#if os(iOS)
import SwiftUI
#endif

struct EmbeddingFixture: Decodable { let contextual: [Float]; let sentence: [Float] }
struct DirectionFixture: Decodable { let tokens: D3Tokens; let probability: Double }
struct PairFixture: Decodable {
    let id: String
    let first: String
    let second: String
    let embeddingA: EmbeddingFixture
    let embeddingB: EmbeddingFixture
    let directions: [DirectionFixture]
    let features: [Double]
    let expectedScore: Double
    let coreMLScore: Double
}
struct Fixtures: Decodable { let fixtures: [PairFixture] }

enum ProbeFailure: Error { case invalidArguments, unavailable, invalidVector, compatibility, invalidFixture }
@Generable struct CompatibilityCode { var code: String }

// One process owns one unit. The host publishes the result before starting another.
@MainActor
enum CompatibilityProbe {
    static func memoryBytes() -> UInt64? {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size / MemoryLayout<natural_t>.size)
        let result = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        return result == KERN_SUCCESS ? UInt64(info.resident_size) : nil
    }

    static func execute() async {
        let arguments = CommandLine.arguments
        guard let index = arguments.firstIndex(of: "--unit"), index + 1 < arguments.count else { exit(2) }
        let unit = arguments[index + 1]
        let root: URL
        #if os(iOS)
        root = Bundle.main.resourceURL!
        #else
        guard let i = arguments.firstIndex(of: "--root"), i + 1 < arguments.count else { exit(2) }
        root = URL(fileURLWithPath: arguments[i + 1])
        #endif
        let started = ProcessInfo.processInfo.systemUptime
        var result: [String: Any] = ["unit": unit, "schemaVersion": 1,
            "os": ProcessInfo.processInfo.operatingSystemVersionString,
            "policy": D3OrganizationPolicy.version, "syntheticOnly": true,
            "residentBeforeBytes": memoryBytes() as Any? ?? NSNull()]
        do {
            result["result"] = try await perform(unit, root: root)
            result["status"] = "ok"
        } catch {
            result["status"] = "error"
            result["error"] = String(describing: error)
        }
        result["elapsedSeconds"] = ProcessInfo.processInfo.systemUptime - started
        result["residentAfterBytes"] = memoryBytes() as Any? ?? NSNull()
        do {
            let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
            #if os(iOS)
            let destination = URL.documentsDirectory.appendingPathComponent("unit-" + unit + ".json")
            guard !FileManager.default.fileExists(atPath: destination.path) else { exit(3) }
            try data.write(to: destination, options: [.atomic])
            #endif
            print("IOS27_RESULT " + String(decoding: data, as: UTF8.self))
            fflush(stdout)
            exit(0)
        } catch { exit(4) }
    }

    static func perform(_ unit: String, root: URL) async throws -> [String: Any] {
        if unit == "environment" {
            let model = SystemLanguageModel.default
            let contextual = NLContextualEmbedding(language: .english)
            let sentence = NLEmbedding.sentenceEmbedding(for: .english)
            return ["foundationModels": String(describing: model.availability),
                "foundationModelsAvailable": model.availability == .available,
                "contextSize": model.contextSize,
                "contextualAssetsAvailable": contextual?.hasAvailableAssets ?? false,
                "contextualIdentifier": contextual?.modelIdentifier as Any? ?? NSNull(),
                "contextualRevision": contextual?.revision as Any? ?? NSNull(),
                "contextualDimension": contextual?.dimension as Any? ?? NSNull(),
                "sentenceRevision": sentence?.revision as Any? ?? NSNull(),
                "sentenceDimension": sentence?.dimension as Any? ?? NSNull(),
                "expectedEmbeddingSpace": D3OrganizationPolicy.embeddingSpace,
                "pcc": "not-requested; entitlement-and-account-eligibility-unverified"]
        }
        if unit == "generation" {
            guard SystemLanguageModel.default.availability == .available else { throw ProbeFailure.unavailable }
            let session = LanguageModelSession(model: SystemLanguageModel.default,
                instructions: "Extract only the explicitly stated code from this fictional receipt.")
            let start = ProcessInfo.processInfo.systemUptime
            let response = try await session.respond(to: "Fictional receipt code: ORBIT-27.",
                generating: CompatibilityCode.self,
                options: GenerationOptions(sampling: .greedy, maximumResponseTokens: 100))
            return ["code": response.content.code, "passed": response.content.code == "ORBIT-27",
                    "generationSeconds": ProcessInfo.processInfo.systemUptime - start,
                    "note": "Technical smoke check, not a grouping quality evaluation"]
        }
        let fixtures = try JSONDecoder().decode(Fixtures.self,
            from: Data(contentsOf: root.appendingPathComponent("parity-inputs.json")))
        let parts = unit.split(separator: "-")
        guard parts.count == 2, let number = Int(parts[1]), fixtures.fixtures.indices.contains(number) else {
            throw ProbeFailure.invalidArguments
        }
        let fixture = fixtures.fixtures[number]
        let asset = FileManager.default.fileExists(atPath: root.appendingPathComponent("MatcherAssets").path)
            ? root.appendingPathComponent("MatcherAssets") : root
        let parameters = try JSONDecoder().decode(D3Parameters.self,
            from: Data(contentsOf: asset.appendingPathComponent("D3Parameters.json")))
        let features = try D3Features(parameters: parameters)
        let tokenizer = try D3Tokenizer(vocabularyURL: asset.appendingPathComponent("D3Vocabulary.txt"))
        if parts[0] == "embedding" {
            // Query the production provider; do not force English or substitute reference vectors.
            let provider = AppleProjectEmbedding()
            guard let a = try await provider.embedding(for: fixture.first),
                  let b = try await provider.embedding(for: fixture.second),
                  let sa = a.semanticVector, let sb = b.semanticVector else { throw ProbeFailure.unavailable }
            guard a.space == D3OrganizationPolicy.embeddingSpace, b.space == a.space else {
                return ["fixture": fixture.id, "compatible": false, "spaceA": a.space, "spaceB": b.space]
            }
            let values = try features.values(first: fixture.first, second: fixture.second,
                contextualA: a.vector, contextualB: b.vector, sentenceA: sa, sentenceB: sb)
            let neural = fixture.directions.map(\.probability).reduce(0, +) / 2
            let score = try features.score(features: values, neuralProbability: neural)
            return ["fixture": fixture.id, "compatible": true, "space": a.space,
                "contextualA": a.vector, "contextualB": b.vector, "sentenceA": sa, "sentenceB": sb,
                "cosineToReference": [try D3Features.cosine(a.vector, fixture.embeddingA.contextual),
                    try D3Features.cosine(b.vector, fixture.embeddingB.contextual),
                    try D3Features.cosine(sa, fixture.embeddingA.sentence),
                    try D3Features.cosine(sb, fixture.embeddingB.sentence)],
                "featureMaxDelta": zip(values, fixture.features).map { abs($0 - $1) }.max() ?? 0,
                "scoreWithReferenceNeural": score,
                "decisionUnchanged": (score >= parameters.threshold) == (fixture.expectedScore >= parameters.threshold)]
        }
        guard parts[0] == "parity" else { throw ProbeFailure.invalidArguments }
        let values = try features.values(first: fixture.first, second: fixture.second,
            contextualA: fixture.embeddingA.contextual, contextualB: fixture.embeddingB.contextual,
            sentenceA: fixture.embeddingA.sentence, sentenceB: fixture.embeddingB.sentence)
        let configuration = MLModelConfiguration(); configuration.computeUnits = .cpuOnly
        var compiled = asset.appendingPathComponent("D3Matcher.mlmodelc")
        if !FileManager.default.fileExists(atPath: compiled.path) {
            compiled = try await MLModel.compileModel(at: asset.appendingPathComponent("D3Matcher.mlpackage"))
        }
        let loadStart = ProcessInfo.processInfo.systemUptime
        let model = try MLModel(contentsOf: compiled, configuration: configuration)
        let loadSeconds = ProcessInfo.processInfo.systemUptime - loadStart
        var probabilities: [Double] = [], timings: [Double] = []
        for (index, texts) in [(fixture.first, fixture.second), (fixture.second, fixture.first)].enumerated() {
            let tokens = try tokenizer.encode(first: texts.0, second: texts.1, length: 512)
            guard tokens == fixture.directions[index].tokens else { throw ProbeFailure.invalidFixture }
            let start = ProcessInfo.processInfo.systemUptime
            probabilities.append(try D3PairMatcher.probability(model: model, tokens: tokens))
            timings.append(ProcessInfo.processInfo.systemUptime - start)
        }
        let score = try features.score(features: values, neuralProbability: probabilities.reduce(0, +) / 2)
        let featureDelta = zip(values, fixture.features).map { abs($0 - $1) }.max() ?? 0
        let scoreDelta = abs(score - fixture.coreMLScore)
        let decisionsAgree = (score >= parameters.threshold) == (fixture.expectedScore >= parameters.threshold)
        return ["fixture": fixture.id, "tokenParity": true, "decisionParity": decisionsAgree,
            "maximumFeatureDelta": featureDelta, "maximumNativeScoreDelta": scoreDelta,
            "passed": featureDelta <= 1e-8 && scoreDelta <= 1e-7 && decisionsAgree,
            "probabilities": probabilities, "score": score, "loadSeconds": loadSeconds,
            "inferenceSeconds": timings, "computeUnits": "cpuOnly"]
    }
}

#if os(iOS)
@main struct CompatibilityProbeApp: App {
    var body: some Scene {
        WindowGroup { Text("Remember compatibility check\nFictional data only").padding().task { await CompatibilityProbe.execute() } }
    }
}
#else
@main struct CompatibilityProbeCommand {
    static func main() async { await CompatibilityProbe.execute() }
}
#endif
