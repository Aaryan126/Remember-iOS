import Foundation

struct RuntimeRequest: Decodable { let id: String; let first: String; let second: String; let length: Int }
struct RuntimeResponse: Encodable { let id: String; let prediction: MatcherPrediction }

@main
struct Stage3RuntimeProbe {
    static func main() async throws {
        guard CommandLine.arguments.count == 3 else { throw MatcherError.missingResource("compiled model and vocabulary arguments") }
        let runtime = try MatcherRuntime(modelURL: URL(fileURLWithPath: CommandLine.arguments[1]),
                                        vocabularyURL: URL(fileURLWithPath: CommandLine.arguments[2]))
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        while let line = readLine() {
            let request = try JSONDecoder().decode(RuntimeRequest.self, from: Data(line.utf8))
            let prediction = try await runtime.predict(first: request.first, second: request.second, length: request.length)
            FileHandle.standardOutput.write(try encoder.encode(RuntimeResponse(id: request.id, prediction: prediction)) + Data([10]))
        }
    }
}
