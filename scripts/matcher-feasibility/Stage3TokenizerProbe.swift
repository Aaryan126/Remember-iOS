import Foundation

struct TokenRequest: Decodable {
    let id: String
    let first: String
    let second: String
    let length: Int
}
struct TokenResponse: Encodable {
    let id: String
    let inputs: MatcherTokens
}

@main
struct Stage3TokenizerProbe {
    static func main() throws {
        guard CommandLine.arguments.count == 2 else { throw MatcherError.missingResource("vocab.txt argument") }
        let tokenizer = try MatcherTokenizer(vocabularyURL: URL(fileURLWithPath: CommandLine.arguments[1]))
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        while let line = readLine() {
            let request = try JSONDecoder().decode(TokenRequest.self, from: Data(line.utf8))
            let inputs = try tokenizer.encode(first: request.first, second: request.second, length: request.length)
            let response = TokenResponse(id: request.id, inputs: inputs)
            FileHandle.standardOutput.write(try encoder.encode(response) + Data([10]))
        }
    }
}
