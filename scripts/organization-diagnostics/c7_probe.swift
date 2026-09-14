import Foundation
import FoundationModels

@Generable
enum ProjectVerdict: String, Codable {
    case same_project
    case separate_projects
    case abstain
}

@Generable
struct SourceQuotation: Codable {
    @Guide(description: "An exact source ID from the supplied packet")
    var sourceID: String
    @Guide(description: "A short verbatim substring of that source, not a paraphrase")
    var quote: String
}

@Generable
struct ProjectVerification: Codable {
    @Guide(description: "Exact evidence, including both queried sources for a decisive verdict", .maximumCount(4))
    var evidence: [SourceQuotation]
    var verdict: ProjectVerdict
    @Guide(description: "One short sentence explaining the relationship or missing evidence")
    var rationale: String
}

struct ProbeRequest: Decodable {
    let instructions: String
    let packet: String
}

struct ProbeResponse: Encodable {
    let status: String
    let availability: String
    let output: ProjectVerification?
    let error: String?
}

@main
struct SemanticProbe {
    static func main() async {
        let model = SystemLanguageModel.default
        let availability = String(describing: model.availability)
        let result: ProbeResponse
        if CommandLine.arguments == [CommandLine.arguments[0], "--availability"] {
            result = ProbeResponse(status: "availability", availability: availability, output: nil, error: nil)
        } else if model.availability != .available {
            result = ProbeResponse(status: "unavailable", availability: availability, output: nil, error: nil)
        } else {
            do {
                let data = FileHandle.standardInput.readDataToEndOfFile()
                guard data.count <= 32_768 else { throw CocoaError(.fileReadTooLarge) }
                let request = try JSONDecoder().decode(ProbeRequest.self, from: data)
                let session = LanguageModelSession(model: model, instructions: request.instructions)
                let response = try await session.respond(
                    to: request.packet, generating: ProjectVerification.self,
                    options: GenerationOptions(sampling: .greedy, maximumResponseTokens: 600)
                )
                result = ProbeResponse(status: "ok", availability: availability,
                                       output: response.content, error: nil)
            } catch {
                result = ProbeResponse(status: "error", availability: availability,
                                       output: nil, error: String(describing: error))
            }
        }
        do {
            let data = try JSONEncoder().encode(result)
            FileHandle.standardOutput.write(data)
            FileHandle.standardOutput.write(Data([10]))
        } catch {
            FileHandle.standardError.write(Data("Could not encode probe response\n".utf8))
            Foundation.exit(2)
        }
    }
}
