import Foundation
import FoundationModels
import Darwin

@Generable enum SupportVerdict: String, Codable {
    case supported, explicit_missing, conflicting, not_established
}
@Generable struct EvidenceReference: Codable {
    @Guide(description: "Exact candidate ID from the input, never invent an ID")
    var candidateID: String
    @Guide(description: "Verbatim supporting passage, 4 to 480 characters; preserve negation and qualifiers")
    var quote: String
}
@Generable struct SupportOutput: Codable {
    var verdict: SupportVerdict
    @Guide(description: "Minimal verbatim answer span up to 160 characters when supported, otherwise the empty string")
    var answer: String
    @Guide(description: "Up to three exact evidence passages; conflict requires two distinct passages", .maximumCount(3))
    var evidence: [EvidenceReference]
}
struct SupportRequest: Decodable {
    let schemaVersion: Int
    let unit: String
    let instructions: String
    let packet: String
    let expectedRuntime: RuntimeIdentity
}
struct RuntimeIdentity: Codable, Equatable {
    let os: String
    let availability: String
    let contextSize: Int
    static func current() -> RuntimeIdentity {
        let model = SystemLanguageModel.default
        return RuntimeIdentity(os: ProcessInfo.processInfo.operatingSystemVersionString,
            availability: String(describing: model.availability), contextSize: model.contextSize)
    }
}
enum SupportError: Error { case arguments, unavailable, runtimeChanged, invalidRequest }

// Independent of the model executor: a stalled cancellation still gets a terminal
// receipt and exits within the native grace period. Host watchdog is separate.
final class TerminalRecorder: @unchecked Sendable {
    private let lock = NSLock()
    private let started = ProcessInfo.processInfo.systemUptime
    private var finished = false
    private var cancellationReason: String?
    private var task: Task<Void, Never>?
    let unit: String
    let runtime: RuntimeIdentity
    init(unit: String, runtime: RuntimeIdentity) { self.unit = unit; self.runtime = runtime }
    func attach(_ task: Task<Void, Never>) {
        lock.lock(); self.task = task; let cancelled = cancellationReason != nil; lock.unlock()
        if cancelled { task.cancel() }
    }
    func cancel(_ reason: String) {
        lock.lock()
        guard !finished, cancellationReason == nil else { lock.unlock(); return }
        cancellationReason = reason
        let current = task
        lock.unlock()
        current?.cancel()
        DispatchQueue.global(qos: .userInitiated).asyncAfter(deadline: .now()+2) { [self] in
            finish(nil, error: reason + "_cancellation_grace_expired")
        }
    }
    func arm() {
        DispatchQueue.global(qos: .userInitiated).asyncAfter(deadline: .now()+60) { [self] in
            cancel("native_deadline")
        }
    }
    func finish(_ output: SupportOutput?, error: String? = nil) -> Never {
        lock.lock()
        if finished { lock.unlock(); Thread.exit(); fatalError("unreachable") }
        finished = true
        let reason = cancellationReason ?? error
        var usage = rusage()
        getrusage(RUSAGE_SELF, &usage)
        do {
            let runtimeObject = try JSONSerialization.jsonObject(with: JSONEncoder().encode(runtime))
            let outputObject: Any = try output.map { try JSONSerialization.jsonObject(with: JSONEncoder().encode($0)) } ?? NSNull()
            let receipt: [String: Any] = ["schemaVersion": 1, "unit": unit,
                "status": reason == nil && output != nil ? "ok" : "error",
                "output": outputObject, "error": reason as Any? ?? NSNull(),
                "runtime": runtimeObject, "elapsedSeconds": ProcessInfo.processInfo.systemUptime-started,
                "peakResidentBytes": usage.ru_maxrss, "syntheticOnly": true,
                "nativeDeadlineSeconds": 60, "cancellationGraceSeconds": 2]
            let data = try JSONSerialization.data(withJSONObject: receipt, options: .sortedKeys)
            print("ANSWER_SUPPORT_RESULT " + String(decoding: data, as: UTF8.self))
            fflush(stdout)
            exit(0)
        } catch { fputs("Terminal serialization failed\n", stderr); fflush(stderr); exit(4) }
    }
}

@main struct AnswerSupportProbe {
    static func main() async {
        let arguments = CommandLine.arguments
        guard arguments.count == 3, arguments[1] == "--input" else { exit(2) }
        do {
            let input = try Data(contentsOf: URL(fileURLWithPath: arguments[2]))
            guard input.count <= 32768 else { throw SupportError.invalidRequest }
            let request = try JSONDecoder().decode(SupportRequest.self, from: input)
            guard request.schemaVersion == 1, !request.unit.isEmpty,
                  !request.instructions.isEmpty, !request.packet.isEmpty else { throw SupportError.invalidRequest }
            let runtime = RuntimeIdentity.current()
            let recorder = TerminalRecorder(unit: request.unit, runtime: runtime)
            signal(SIGTERM, SIG_IGN)
            let termination = DispatchSource.makeSignalSource(signal: SIGTERM, queue: .global(qos: .userInitiated))
            termination.setEventHandler { recorder.cancel("host_cancel_requested") }
            termination.resume()
            recorder.arm()
            let task = Task { @MainActor in
                do {
                    guard runtime == request.expectedRuntime else { throw SupportError.runtimeChanged }
                    guard SystemLanguageModel.default.availability == .available else { throw SupportError.unavailable }
                    let session = LanguageModelSession(model: SystemLanguageModel.default, instructions: request.instructions)
                    try Task.checkCancellation()
                    let response = try await session.respond(to: request.packet, generating: SupportOutput.self,
                        options: GenerationOptions(sampling: .greedy, maximumResponseTokens: 768))
                    try Task.checkCancellation()
                    recorder.finish(response.content)
                } catch { recorder.finish(nil, error: String(describing: error)) }
            }
            recorder.attach(task)
            await task.value
            withExtendedLifetime(termination) {}
        } catch { fputs("Invalid probe request: \(error)\n", stderr); fflush(stderr); exit(2) }
    }
}
