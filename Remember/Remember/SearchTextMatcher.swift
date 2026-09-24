import Foundation

/// Request-local word matching. Quotes and stored text are never corrected.
nonisolated struct SearchTextMatcher {
    struct Match {
        var coverage = 0.0
        var containsPhrase = false
        var permitsMatch = true

        var passageScore: Double { coverage * 0.75 + (containsPhrase ? 0.25 : 0) }
    }

    private struct Word {
        let text: String
        let characters: [Character]
    }

    private struct Text {
        let normalized: String
        var words: Set<String> = []
        var fuzzyWords: Set<String> = []
        var literals: Set<String> = []
        var requiredLiterals: Set<String> = []

        init(_ value: String) {
            normalized = value.folding(options: [.caseInsensitive, .diacriticInsensitive],
                locale: Locale(identifier: "en_US_POSIX")).lowercased()
                .trimmingCharacters(in: .whitespacesAndNewlines)
            // Keep connected numeric references together, e.g. AS1-02-07.
            // Individual components remain searchable, but cannot be typo-expanded.
            for run in normalized.split(whereSeparator: {
                !$0.isLetter && !$0.isNumber && !"-_/.".contains($0)
            }) {
                let parts = run.split(whereSeparator: { !$0.isLetter && !$0.isNumber }).map(String.init)
                words.formUnion(parts)
                literals.formUnion(parts)
                if run.contains(where: \.isNumber) {
                    let literal = String(run).trimmingCharacters(in: CharacterSet(charactersIn: "-_/."))
                    literals.insert(literal)
                    requiredLiterals.insert(literal)
                } else {
                    fuzzyWords.formUnion(parts)
                }
            }
        }
    }

    private struct Pair: Hashable {
        let query: String
        let candidate: String
    }

    private let query: Text
    private let queryWords: [Word]
    private var distances: [Pair: Int] = [:]

    init(query: String) {
        let text = Text(query)
        self.query = text
        queryWords = text.words.sorted().map { Word(text: $0, characters: Array($0)) }
    }

    mutating func match(in value: String,
                        checkCancellation: () throws -> Void = { try Task.checkCancellation() }) throws -> Match {
        try checkCancellation()
        let document = Text(value)
        guard query.requiredLiterals.isSubset(of: document.literals) else {
            return Match(permitsMatch: false)
        }
        guard !queryWords.isEmpty else { return Match(permitsMatch: false) }
        var weight = Double(query.words.intersection(document.words).count)
        let missing = queryWords.filter { !document.words.contains($0.text) }
        // Exact matching remains available for arbitrarily long words/queries.
        // Bound fuzzy work to ordinary search phrases and human-sized words.
        if queryWords.count <= 16, !missing.isEmpty {
            let candidates = Dictionary(grouping: document.fuzzyWords.compactMap { text -> Word? in
                let characters = Array(text)
                return (3...64).contains(characters.count) ? Word(text: text, characters: characters) : nil
            }, by: { $0.characters.count })
            var comparisons = 0
            for word in missing where query.fuzzyWords.contains(word.text) {
                let length = word.characters.count
                guard (4...64).contains(length) else { continue }
                let limit = length < 8 ? 1 : 2
                var best = limit + 1
                for size in max(3, length - limit)...min(64, length + limit) {
                    for candidate in candidates[size] ?? [] {
                        comparisons += 1
                        if comparisons.isMultiple(of: 128) { try checkCancellation() }
                        let pair = Pair(query: word.text, candidate: candidate.text)
                        let distance: Int
                        if let cached = distances[pair] {
                            distance = cached
                        } else {
                            distance = Self.distance(word.characters, candidate.characters, limit: limit)
                            // Cache limits affect speed only; candidates are never silently dropped.
                            if distances.count < 8_192 { distances[pair] = distance }
                        }
                        best = min(best, distance)
                        if best == 1 { break }
                    }
                    if best == 1 { break }
                }
                if best == 1 { weight += 0.7 }
                else if best == 2 && limit == 2 { weight += 0.4 }
            }
        }
        return Match(coverage: weight / Double(queryWords.count),
                     containsPhrase: document.normalized.contains(query.normalized))
    }

    /// Banded optimal-string-alignment distance (restricted Damerau–Levenshtein).
    /// Adjacent swaps count as one edit; no matrix grows with document length.
    private static func distance(_ left: [Character], _ right: [Character], limit: Int) -> Int {
        let outside = limit + 1
        guard abs(left.count - right.count) <= limit else { return outside }
        var previous = Array(0...right.count)
        var beforePrevious = previous
        for row in 1...left.count {
            var current = Array(repeating: outside, count: right.count + 1)
            current[0] = min(row, outside)
            let start = max(1, row - limit), end = min(right.count, row + limit)
            guard start <= end else { return outside }
            for column in start...end {
                let substitution = previous[column - 1] + (left[row - 1] == right[column - 1] ? 0 : 1)
                current[column] = min(substitution, previous[column] + 1, current[column - 1] + 1)
                if row > 1, column > 1,
                   left[row - 1] == right[column - 2], left[row - 2] == right[column - 1] {
                    current[column] = min(current[column], beforePrevious[column - 2] + 1)
                }
            }
            if current.min()! > limit { return outside }
            beforePrevious = previous
            previous = current
        }
        return min(outside, previous[right.count])
    }
}
