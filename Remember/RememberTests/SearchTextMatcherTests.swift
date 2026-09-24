import Foundation
import Testing
@testable import Remember

struct SearchTextMatcherTests {
    @Test(arguments: ["reciept", "receit", "receiptt", "receopt"])
    func commonTyposFindOriginalWord(query: String) throws {
        var matcher = SearchTextMatcher(query: query)
        let match = try matcher.match(in: "Your receipt is saved here.")
        #expect(match.coverage > 0 && match.coverage < 1)
        #expect(!match.containsPhrase)
    }

    @Test func twoEditsRequireLongWordAndExactRanksAboveFuzzy() throws {
        var matcher = SearchTextMatcher(query: "conference")
        let exact = try matcher.match(in: "Conference")
        let one = try matcher.match(in: "conferense")
        let two = try matcher.match(in: "konferense")
        #expect(exact.passageScore > one.passageScore && one.passageScore > two.passageScore)
        #expect(two.coverage > 0)
        var short = SearchTextMatcher(query: "receipt")
        #expect(try short.match(in: "rexeopt").coverage == 0)
        var three = SearchTextMatcher(query: "cat")
        #expect(try three.match(in: "car cart").coverage == 0)
    }

    @Test func firstLetterAndExtraLetterInFourCharacterWordAreSupported() throws {
        var first = SearchTextMatcher(query: "xeceipt")
        #expect(try first.match(in: "receipt").coverage > 0)
        var extra = SearchTextMatcher(query: "caat")
        #expect(try extra.match(in: "cat").coverage > 0)
    }

    @Test func namesCaseAccentsAndCanonicalUnicodeWorkWithoutDictionary() throws {
        var matcher = SearchTextMatcher(query: "Aaryna CAFÉ")
        #expect(try matcher.match(in: "Aaryan cafe\u{301}").coverage > 0.8)
        var nonLatin = SearchTextMatcher(query: "Москва")
        #expect(try nonLatin.match(in: "Моксва").coverage > 0)
        var punctuation = SearchTextMatcher(query: "!!!")
        #expect(try punctuation.match(in: "Some text!").passageScore == 0)
        #expect(try !punctuation.match(in: "!!!").permitsMatch)
    }

    @Test(arguments: ["2027", "ORBIT-28", "ORBIt-28", "ORBIt-027", "ORIBT-27", "AS1-02-08"])
    func numbersAndReferencesDoNotExpand(query: String) throws {
        var matcher = SearchTextMatcher(query: query)
        #expect(try matcher.match(in: "2026 ORBIT-27 AS1-02-07").passageScore == 0)
    }

    @Test func referencesMustMatchEvenWhenOtherQueryWordsMatch() throws {
        var wrong = SearchTextMatcher(query: "receipt ORBIT-28")
        #expect(try wrong.match(in: "Receipt ORBIT-27.").passageScore == 0)
        var correct = SearchTextMatcher(query: "reciept orbit-27")
        #expect(try correct.match(in: "Receipt ORBIT-27.").coverage > 0.8)
        var component = SearchTextMatcher(query: "27")
        #expect(try component.match(in: "ORBIT-27").coverage == 1)
        var fuzzyCode = SearchTextMatcher(query: "oribt")
        #expect(try fuzzyCode.match(in: "ORBIT-27").coverage == 0)
    }

    @Test func longInputsKeepExactMatchingAndBoundFuzzyWork() throws {
        let long = String(repeating: "a", count: 65)
        var matcher = SearchTextMatcher(query: long)
        #expect(try matcher.match(in: long).coverage == 1)
        #expect(try matcher.match(in: String(repeating: "a", count: 64) + "b").coverage == 0)
        let words = "receipt garden window yellow basket planet silver velvet pencil bridge forest island meadow orange purple marble cotton"
        var many = SearchTextMatcher(query: words)
        #expect(try many.match(in: words).coverage == 1)
        #expect(try many.match(in: "reciept").coverage == 0)
        var empty = SearchTextMatcher(query: "  ")
        #expect(try empty.match(in: "receipt").passageScore == 0)
    }

    @Test func cancellationPropagatesInsteadOfReturningPartialMatches() throws {
        var matcher = SearchTextMatcher(query: "receipt")
        #expect(throws: CancellationError.self) {
            try matcher.match(in: "receipt", checkCancellation: { throw CancellationError() })
        }
    }

    @Test func candidateOrderAndRepeatedCallsDoNotChangeScores() throws {
        var matcher = SearchTextMatcher(query: "conference")
        let first = try matcher.match(in: "konferense conferense unrelated")
        let second = try matcher.match(in: "unrelated conferense konferense")
        #expect(first.coverage == second.coverage && first.coverage == 0.7)
    }

    @Test func fullCacheNeverDropsLaterMatches() throws {
        var matcher = SearchTextMatcher(query: "reciept")
        let unrelated = (0..<8_300).map(unrelatedWord).joined(separator: " ")
        #expect(try matcher.match(in: unrelated).coverage == 0)
        #expect(try matcher.match(in: "receipt").coverage == 0.7)
    }

    @Test func cancellationIsCheckedDuringCandidateComparisons() throws {
        var matcher = SearchTextMatcher(query: "receipt")
        let unrelated = (0..<256).map(unrelatedWord).joined(separator: " ")
        var checks = 0
        #expect(throws: CancellationError.self) {
            try matcher.match(in: unrelated) {
                checks += 1
                if checks == 2 { throw CancellationError() }
            }
        }
        #expect(checks == 2)
    }

    private func unrelatedWord(_ index: Int) -> String {
        var value = index
        var word = "zz"
        for _ in 0..<6 {
            word.append(Character(UnicodeScalar(97 + value % 26)!))
            value /= 26
        }
        return word
    }
}
