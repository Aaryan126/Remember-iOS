import Foundation
import CoreML

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

@main
struct D3ParityProbe {
    static func main() throws {
        guard CommandLine.arguments.count == 3 else { throw D3Error.invalidFixture }
        let root = URL(fileURLWithPath: CommandLine.arguments[1])
        let fixtures = try JSONDecoder().decode(Fixtures.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[2])))
        let parameters = try JSONDecoder().decode(D3Parameters.self, from: Data(contentsOf: root.appendingPathComponent("D3Parameters.json")))
        let features = try D3Features(parameters: parameters)
        let tokenizer = try D3Tokenizer(vocabularyURL: root.appendingPathComponent("D3Vocabulary.txt"))
        let url = try MLModel.compileModel(at: root.appendingPathComponent("D3Matcher.mlpackage"))
        let configuration = MLModelConfiguration(); configuration.computeUnits = .cpuOnly
        let model = try MLModel(contentsOf: url, configuration: configuration)
        var maximumFeatureDelta = 0.0, maximumScoreDelta = 0.0
        for fixture in fixtures.fixtures {
            let values = try features.values(first: fixture.first, second: fixture.second,
                contextualA: fixture.embeddingA.contextual, contextualB: fixture.embeddingB.contextual,
                sentenceA: fixture.embeddingA.sentence, sentenceB: fixture.embeddingB.sentence)
            maximumFeatureDelta = max(maximumFeatureDelta, zip(values, fixture.features).map { abs($0 - $1) }.max() ?? 0)
            var probabilities: [Double] = []
            for (index, texts) in [(fixture.first, fixture.second), (fixture.second, fixture.first)].enumerated() {
                let tokens = try tokenizer.encode(first: texts.0, second: texts.1, length: 512)
                guard tokens == fixture.directions[index].tokens else { throw D3Error.invalidFixture }
                probabilities.append(try D3PairMatcher.probability(model: model, tokens: tokens))
            }
            let score = try features.score(features: values, neuralProbability: probabilities.reduce(0, +) / 2)
            maximumScoreDelta = max(maximumScoreDelta, abs(score - fixture.coreMLScore))
            guard (score >= parameters.threshold) == (fixture.expectedScore >= parameters.threshold) else { throw D3Error.invalidOutput }
        }
        guard maximumFeatureDelta <= 1e-8, maximumScoreDelta <= 1e-7 else { throw D3Error.invalidOutput }
        let report: [String: Any] = ["passed": true, "pairs": fixtures.fixtures.count,
            "maximumFeatureDelta": maximumFeatureDelta, "maximumNativeScoreDelta": maximumScoreDelta,
            "tokenParity": true, "decisionParity": true, "compiledModel": url.path]
        print(String(decoding: try JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]), as: UTF8.self))
    }
}
