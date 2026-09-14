import Foundation

struct MatcherTokens: Codable, Sendable, Equatable {
    let input_ids: [[Int32]]
    let attention_mask: [[Int32]]
    let token_type_ids: [[Int32]]
}

enum MatcherError: Error { case invalidVocabulary, unsupportedLength, missingResource(String), invalidOutput, invalidFixture }

/// Narrow, offline implementation of the pinned uncased BERT tokenizer.
/// Its contract is verified against tokenizers 0.21.4, including longest-first
/// pair tie behavior; it is not a general replacement for Hugging Face tokenizers.
struct MatcherTokenizer: Sendable {
    private let vocabulary: [String: Int32]
    private let specials = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]

    init(vocabularyURL: URL) throws {
        let text = try String(contentsOf: vocabularyURL, encoding: .utf8)
        var words = text.components(separatedBy: "\n")
        if words.last == "" { words.removeLast() }
        guard words.count == 30_522, Set(words).count == words.count else { throw MatcherError.invalidVocabulary }
        vocabulary = Dictionary(uniqueKeysWithValues: words.enumerated().map { ($0.element, Int32($0.offset)) })
        guard vocabulary["[PAD]"] == 0, vocabulary["[UNK]"] == 100,
              vocabulary["[CLS]"] == 101, vocabulary["[SEP]"] == 102,
              vocabulary["[MASK]"] == 103 else { throw MatcherError.invalidVocabulary }
    }

    func encode(first: String, second: String, length: Int) throws -> MatcherTokens {
        guard [256, 512].contains(length) else { throw MatcherError.unsupportedLength }
        var a = tokenize(first), b = tokenize(second)
        // The pinned Transformers Python adapter omits a literally empty
        // second string (but not whitespace-only text), encoding a single input.
        if second.isEmpty {
            a = Array(a.prefix(length - 2))
            let used = a.count + 2
            return MatcherTokens(input_ids: [[101] + a + [102] + Array(repeating: 0, count: length - used)],
                attention_mask: [Array(repeating: 1, count: used) + Array(repeating: 0, count: length - used)],
                token_type_ids: [Array(repeating: 0, count: length)])
        }
        let capacity = length - 3
        if a.count + b.count > capacity {
            // Preserve the original shorter/longer ordering when assigning an
            // odd spare token, matching the pinned Rust fast tokenizer.
            if a.count > b.count {
                let keepB = min(b.count, capacity / 2)
                a = Array(a.prefix(capacity - keepB)); b = Array(b.prefix(keepB))
            } else {
                let keepA = min(a.count, capacity / 2)
                b = Array(b.prefix(capacity - keepA)); a = Array(a.prefix(keepA))
            }
        }
        let used = a.count + b.count + 3
        let ids: [Int32] = [101] + a + [102] + b + [102] + Array(repeating: 0, count: length - used)
        let mask: [Int32] = Array(repeating: 1, count: used) + Array(repeating: 0, count: length - used)
        let types: [Int32] = Array(repeating: 0, count: a.count + 2) + Array(repeating: 1, count: b.count + 1)
            + Array(repeating: 0, count: length - used)
        return MatcherTokens(input_ids: [ids], attention_mask: [mask], token_type_ids: [types])
    }

    private func tokenize(_ text: String) -> [Int32] {
        var result: [Int32] = []
        var cursor = text.startIndex
        while cursor < text.endIndex {
            let remaining = cursor..<text.endIndex
            let match = specials.compactMap { token -> (String, Range<String.Index>)? in
                guard let range = text.range(of: token, options: .literal, range: remaining) else { return nil }
                return (token, range)
            }.min { $0.1.lowerBound < $1.1.lowerBound }
            if let (token, range) = match {
                result += basic(String(text[cursor..<range.lowerBound])).flatMap(wordPieces)
                if let identifier = vocabulary[token] { result.append(identifier) }
                cursor = range.upperBound
            } else {
                result += basic(String(text[cursor...])).flatMap(wordPieces)
                break
            }
        }
        return result
    }

    private func basic(_ text: String) -> [String] {
        var clean = ""
        for scalar in text.unicodeScalars {
            let value = scalar.value
            if value == 0 || value == 0xFFFD { continue }
            if scalar.properties.isWhitespace { clean.append(" "); continue }
            switch scalar.properties.generalCategory {
            case .control, .format, .surrogate, .privateUse, .unassigned: continue
            default: break
            }
            if isChinese(value) { clean.append(" "); clean.unicodeScalars.append(scalar); clean.append(" ") }
            else { clean.unicodeScalars.append(scalar) }
        }
        let decomposed = clean.decomposedStringWithCanonicalMapping.unicodeScalars
        var normalized = ""
        for scalar in decomposed where scalar.properties.generalCategory != .nonspacingMark {
            normalized.append(String(scalar).lowercased())
        }
        var tokens: [String] = [], current = ""
        func flush() { if !current.isEmpty { tokens.append(current); current = "" } }
        for scalar in normalized.unicodeScalars {
            if scalar.properties.isWhitespace { flush() }
            else if isPunctuation(scalar) { flush(); tokens.append(String(scalar)) }
            else { current.unicodeScalars.append(scalar) }
        }
        flush()
        return tokens
    }

    private func wordPieces(_ token: String) -> [Int32] {
        let scalars = Array(token.unicodeScalars)
        guard scalars.count <= 100 else { return [100] }
        var start = 0, result: [Int32] = []
        while start < scalars.count {
            var end = scalars.count
            var found: Int32?
            while end > start {
                let piece = (start > 0 ? "##" : "") + String(String.UnicodeScalarView(scalars[start..<end]))
                if let identifier = vocabulary[piece] { found = identifier; break }
                end -= 1
            }
            guard let found else { return [100] }
            result.append(found); start = end
        }
        return result
    }

    private func isChinese(_ v: UInt32) -> Bool {
        [0x4E00...0x9FFF, 0x3400...0x4DBF, 0x20000...0x2A6DF, 0x2A700...0x2B73F,
         0x2B740...0x2B81F, 0x2B920...0x2CEAF, 0xF900...0xFAFF, 0x2F800...0x2FA1F]
            .contains { $0.contains(v) }
    }

    private func isPunctuation(_ scalar: Unicode.Scalar) -> Bool {
        let v = scalar.value
        if (33...47).contains(v) || (58...64).contains(v) || (91...96).contains(v) || (123...126).contains(v) { return true }
        switch scalar.properties.generalCategory {
        case .connectorPunctuation, .dashPunctuation, .openPunctuation, .closePunctuation,
             .initialPunctuation, .finalPunctuation, .otherPunctuation: return true
        default: return false
        }
    }
}
