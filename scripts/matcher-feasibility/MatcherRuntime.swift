import Foundation
import CoreML

struct MatcherPrediction: Codable, Sendable {
    let inputs: MatcherTokens
    let logits: [Double]
    let probabilities: [Double]
    let tokenizationSeconds: Double
    let predictionSeconds: Double
}

actor MatcherRuntime {
    private let model: MLModel
    private let tokenizer: MatcherTokenizer
    let modelLoadSeconds: Double

    init(modelURL: URL, vocabularyURL: URL, computeUnits: MLComputeUnits = .all) throws {
        let start = ProcessInfo.processInfo.systemUptime
        let configuration = MLModelConfiguration()
        configuration.computeUnits = computeUnits
        model = try MLModel(contentsOf: modelURL, configuration: configuration)
        tokenizer = try MatcherTokenizer(vocabularyURL: vocabularyURL)
        modelLoadSeconds = ProcessInfo.processInfo.systemUptime - start
        guard Set(model.modelDescription.inputDescriptionsByName.keys) == ["input_ids", "attention_mask", "token_type_ids"],
              Set(model.modelDescription.outputDescriptionsByName.keys) == ["logits", "probabilities"],
              let metadata = model.modelDescription.metadata[.creatorDefinedKey] as? [String: String],
              let order = metadata["class_order"],
              let data = order.data(using: .utf8),
              try JSONDecoder().decode([String].self, from: data) == ["same", "related", "unrelated"]
        else { throw MatcherError.invalidOutput }
    }

    func predict(first: String, second: String, length: Int) throws -> MatcherPrediction {
        try Task.checkCancellation()
        let start = ProcessInfo.processInfo.systemUptime
        let tokens = try tokenizer.encode(first: first, second: second, length: length)
        let tokenSeconds = ProcessInfo.processInfo.systemUptime - start
        let values = ["input_ids": tokens.input_ids, "attention_mask": tokens.attention_mask, "token_type_ids": tokens.token_type_ids]
        var features: [String: MLFeatureValue] = [:]
        for (key, rows) in values {
            guard rows.count == 1, rows[0].count == length else { throw MatcherError.invalidFixture }
            let array = try MLMultiArray(shape: [1, NSNumber(value: length)], dataType: .int32)
            for index in 0..<length { array[index] = NSNumber(value: rows[0][index]) }
            features[key] = MLFeatureValue(multiArray: array)
        }
        let provider = try MLDictionaryFeatureProvider(dictionary: features)
        let predictionStart = ProcessInfo.processInfo.systemUptime
        let output = try model.prediction(from: provider)
        let seconds = ProcessInfo.processInfo.systemUptime - predictionStart
        guard let rawLogits = output.featureValue(for: "logits")?.multiArrayValue,
              let rawProbabilities = output.featureValue(for: "probabilities")?.multiArrayValue,
              rawLogits.count == 3, rawProbabilities.count == 3 else { throw MatcherError.invalidOutput }
        let logits = (0..<3).map { rawLogits[$0].doubleValue }
        let probabilities = (0..<3).map { rawProbabilities[$0].doubleValue }
        guard logits.allSatisfy(\.isFinite), probabilities.allSatisfy({ $0.isFinite && $0 >= 0 && $0 <= 1 }),
              abs(probabilities.reduce(0, +) - 1) < 0.002 else { throw MatcherError.invalidOutput }
        return MatcherPrediction(inputs: tokens, logits: logits, probabilities: probabilities,
                                 tokenizationSeconds: tokenSeconds, predictionSeconds: seconds)
    }
}
