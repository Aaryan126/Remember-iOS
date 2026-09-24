import Foundation

/// Deterministic fictional text; records timing without flaky timing assertions.
@main
struct SearchTypoBenchmark {
    static func main() throws {
        let words = ["garden", "window", "yellow", "basket", "planet", "silver", "velvet",
                     "pencil", "bridge", "forest", "island", "meadow", "orange", "purple",
                     "marble", "cotton", "ticket", "meeting", "research", "holiday"]
        let documents = (0..<1_000).map { index in
            (0..<100).map { words[($0 + index) % words.count] }.joined(separator: " ")
                + (index.isMultiple(of: 10) ? " Conference receipt." : "")
        }
        for query in ["receipt", "reciept", "konferense reciept", "zzzzzzzz"] {
            var samples: [Double] = []
            var count = 0
            for _ in 0..<5 {
                var matcher = SearchTextMatcher(query: query)
                let start = ContinuousClock.now
                var hits = 0
                for text in documents {
                    if try matcher.match(in: text).coverage > 0 { hits += 1 }
                }
                let elapsed = start.duration(to: .now).components
                samples.append(Double(elapsed.seconds) * 1_000 + Double(elapsed.attoseconds) / 1e15)
                count = hits
            }
            print("query=\(query), documents=\(documents.count), hits=\(count), medianMS=\(samples.sorted()[2])")
        }
    }
}
