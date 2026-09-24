import Foundation
import CoreML

nonisolated struct D3Source: Sendable {
    let text: String
    let contextual: [Float]
    let sentence: [Float]
    let space: String
}

nonisolated protocol D3Matching: Sendable {
    func lexicalVector(_ text: String) async throws -> [Int: Double]
    func score(_ first: D3Source, _ second: D3Source) async throws -> Double
}

actor D3PairMatcher: D3Matching {
    private let bundle: Bundle
    private var features: D3Features?
    private var tokenizer: D3Tokenizer?
    private var model: MLModel?

    init(bundle: Bundle = .main) { self.bundle = bundle }

    private func resource(_ name: String, _ ext: String) throws -> URL {
        guard let url = bundle.url(forResource: name, withExtension: ext, subdirectory: "MatcherAssets")
                ?? bundle.url(forResource: name, withExtension: ext) else { throw D3Error.missingResource(name) }
        return url
    }

    private func loadFeatures() throws -> D3Features {
        if let features { return features }
        let parameters = try JSONDecoder().decode(D3Parameters.self, from: Data(contentsOf: resource("D3Parameters", "json")))
        guard parameters.threshold == D3OrganizationPolicy.threshold else { throw D3Error.invalidOutput }
        let result = try D3Features(parameters: parameters)
        features = result
        return result
    }

    func lexicalVector(_ text: String) throws -> [Int: Double] {
        try Task.checkCancellation()
        return try loadFeatures().lexicalVector(text)
    }

    func score(_ first: D3Source, _ second: D3Source) throws -> Double {
        try Task.checkCancellation()
        guard first.space == second.space, first.space == D3OrganizationPolicy.embeddingSpace,
              first.contextual.count == 512, second.contextual.count == 512,
              first.sentence.count == 512, second.sentence.count == 512 else { throw D3Error.invalidOutput }
        let features = try loadFeatures()
        if model == nil {
            let configuration = MLModelConfiguration()
            // Start with the compute path checked by conversion parity; measure other units separately.
            configuration.computeUnits = .cpuOnly
            let loaded = try MLModel(contentsOf: resource("D3Matcher", "mlmodelc"), configuration: configuration)
            let metadata = loaded.modelDescription.metadata[.creatorDefinedKey] as? [String: String]
            guard metadata?["weights_sha256"] == features.parameters.weightsSHA256,
                  metadata?["class_order"] == "[\"not_same\", \"same\"]" else { throw D3Error.invalidOutput }
            tokenizer = try D3Tokenizer(vocabularyURL: resource("D3Vocabulary", "txt"))
            model = loaded
        }
        guard let model, let tokenizer else { throw D3Error.invalidOutput }
        let a = try Self.probability(model: model, tokens: tokenizer.encode(first: first.text, second: second.text, length: 512))
        try Task.checkCancellation()
        let b = try Self.probability(model: model, tokens: tokenizer.encode(first: second.text, second: first.text, length: 512))
        let values = try features.values(first: first.text, second: second.text,
            contextualA: first.contextual, contextualB: second.contextual, sentenceA: first.sentence, sentenceB: second.sentence)
        return try features.score(features: values, neuralProbability: (a + b) / 2)
    }

    nonisolated static func probability(model: MLModel, tokens: D3Tokens) throws -> Double {
        var inputs: [String: MLFeatureValue] = [:]
        for (key, values) in [("input_ids", tokens.input_ids), ("attention_mask", tokens.attention_mask), ("token_type_ids", tokens.token_type_ids)] {
            guard values.count == 1, values[0].count == 512 else { throw D3Error.invalidFixture }
            let array = try MLMultiArray(shape: [1, 512], dataType: .int32)
            for i in 0..<512 { array[i] = NSNumber(value: values[0][i]) }
            inputs[key] = MLFeatureValue(multiArray: array)
        }
        let result = try model.prediction(from: MLDictionaryFeatureProvider(dictionary: inputs))
        guard let probabilities = result.featureValue(for: "probabilities")?.multiArrayValue,
              probabilities.count == 2 else { throw D3Error.invalidOutput }
        let a = probabilities[0].doubleValue, b = probabilities[1].doubleValue
        guard a.isFinite, b.isFinite, (0...1).contains(a), (0...1).contains(b), abs(a + b - 1) < 0.002 else { throw D3Error.invalidOutput }
        return b
    }
}
