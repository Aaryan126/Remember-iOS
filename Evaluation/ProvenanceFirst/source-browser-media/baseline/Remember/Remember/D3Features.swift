import Foundation

/// Portable P2 transforms. Feature order and normalization must match the frozen export.
nonisolated struct D3Parameters: Decodable, Sendable {
    struct Combiner: Decodable, Sendable {
        let mean: [Double]
        let scale: [Double]
        let coefficient: [Double]
        let intercept: Double
        let kind: String
    }
    struct TFIDF: Decodable, Sendable {
        let vocabulary: [String: Int]
        let idf: [Double]
        let ngramRange: [Int]
        let lowercase: Bool
        let tokenPattern: String
        let norm: String
    }
    let version: String
    let threshold: Double
    let weightsSHA256: String
    let combiner: Combiner
    let tfidf: TFIDF

    func validate() throws {
        guard version == "d3-p2-seed29-corroborated-v1", threshold.isFinite, (0...1).contains(threshold),
              combiner.kind == "logistic", combiner.mean.count == 11, combiner.scale.count == 11,
              combiner.coefficient.count == 11, combiner.intercept.isFinite,
              combiner.mean.allSatisfy(\.isFinite), combiner.coefficient.allSatisfy(\.isFinite),
              combiner.scale.allSatisfy({ $0.isFinite && $0 > 0 }),
              tfidf.ngramRange == [1, 2], tfidf.lowercase, tfidf.norm == "l2",
              tfidf.tokenPattern == "(?u)\\b\\w\\w+\\b", !tfidf.idf.isEmpty,
              tfidf.idf.allSatisfy({ $0.isFinite && $0 > 0 }),
              Set(tfidf.vocabulary.values) == Set(tfidf.idf.indices),
              tfidf.vocabulary.count == tfidf.idf.count else { throw D3Error.invalidOutput }
    }
}

nonisolated struct D3Features: Sendable {
    let parameters: D3Parameters

    init(parameters: D3Parameters) throws {
        try parameters.validate()
        self.parameters = parameters
    }

    static func matches(_ pattern: String, _ text: String) -> [String] {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return [] }
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        return regex.matches(in: text, range: range).compactMap { match in
            Range(match.range, in: text).map { String(text[$0]) }
        }
    }

    func lexicalVector(_ text: String) -> [Int: Double] {
        // Python's Unicode \w is letters/numbers/underscore, not ICU's marks/joiners.
        let words = Self.matches("[\\p{L}\\p{N}_]{2,}", text.lowercased())
        var terms = words
        if words.count > 1 { terms += zip(words, words.dropFirst()).map { $0 + " " + $1 } }
        var values: [Int: Double] = [:]
        for term in terms {
            if let index = parameters.tfidf.vocabulary[term] { values[index, default: 0] += 1 }
        }
        for index in values.keys { values[index]! *= parameters.tfidf.idf[index] }
        let norm = sqrt(values.values.reduce(0) { $0 + $1 * $1 })
        return norm > 0 ? values.mapValues { $0 / norm } : [:]
    }

    static func lexicalCosine(_ a: [Int: Double], _ b: [Int: Double]) -> Double {
        a.reduce(0) { $0 + $1.value * b[$1.key, default: 0] }
    }

    static func cosine(_ a: [Float], _ b: [Float]) throws -> Double {
        guard !a.isEmpty, a.count == b.count, a.allSatisfy(\.isFinite), b.allSatisfy(\.isFinite) else { throw D3Error.invalidOutput }
        let norm = sqrt(a.reduce(0.0) { $0 + Double($1) * Double($1) } * b.reduce(0.0) { $0 + Double($1) * Double($1) })
        guard norm > 0 else { throw D3Error.invalidOutput }
        return max(-1, min(1, zip(a, b).reduce(0) { $0 + Double($1.0) * Double($1.1) } / norm))
    }

    static func jaccard(_ a: Set<String>, _ b: Set<String>) -> Double {
        let union = a.union(b).count
        return union == 0 ? 0 : Double(a.intersection(b).count) / Double(union)
    }

    static func trigrams(_ text: String) -> Set<String> {
        let scalars = text.lowercased().unicodeScalars
        let words = scalars.split { $0.properties.isWhitespace || (0x1c...0x1f).contains($0.value) }
        let normalized = words.map { String(String.UnicodeScalarView($0)) }.joined(separator: " ")
        let characters = Array(normalized.unicodeScalars)
        guard characters.count >= 3 else { return [] }
        return Set((0..<(characters.count - 2)).map { String(String.UnicodeScalarView(characters[$0..<($0 + 3)])) })
    }

    static func identifiers(_ text: String) -> Set<String> {
        Set(matches("(?<![A-Za-z0-9])[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*(?![A-Za-z0-9])", text).filter {
            !matches("[A-Za-z]", $0).isEmpty && (!$0.allSatisfy { !$0.isNumber } || $0.contains("-"))
        })
    }

    func values(first: String, second: String, contextualA: [Float], contextualB: [Float], sentenceA: [Float], sentenceB: [Float]) throws -> [Double] {
        let a = Self.identifiers(first), b = Self.identifiers(second)
        let x = first.unicodeScalars.count, y = second.unicodeScalars.count
        return [try Self.cosine(contextualA, contextualB), try Self.cosine(sentenceA, sentenceB),
                Self.lexicalCosine(lexicalVector(first), lexicalVector(second)),
                Self.jaccard(Self.trigrams(first), Self.trigrams(second)),
                Self.jaccard(Set(Self.matches("\\d+(?:[.,]\\d+)*", first)), Set(Self.matches("\\d+(?:[.,]\\d+)*", second))),
                max(x, y) == 0 ? 0 : Double(min(x, y)) / Double(max(x, y)),
                Self.jaccard(a, b), !a.isEmpty && !b.isEmpty && a.isDisjoint(with: b) ? 1 : 0,
                a.isEmpty || b.isEmpty ? 1 : 0, a.isEmpty && b.isEmpty ? 1 : 0]
    }

    func score(features: [Double], neuralProbability: Double) throws -> Double {
        guard features.count == 10, features.allSatisfy(\.isFinite), neuralProbability.isFinite,
              (0...1).contains(neuralProbability) else { throw D3Error.invalidOutput }
        let p = max(1e-6, min(1 - 1e-6, neuralProbability))
        let values = features + [log(p / (1 - p))]
        let model = parameters.combiner
        let logit = zip(values.indices, values).reduce(model.intercept) { value, item in
            value + (item.1 - model.mean[item.0]) / model.scale[item.0] * model.coefficient[item.0]
        }
        return logit >= 0 ? 1 / (1 + exp(-logit)) : exp(logit) / (1 + exp(logit))
    }
}
