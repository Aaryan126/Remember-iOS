import Foundation
import FoundationModels
import SwiftUI
import UIKit
import Darwin

@Generable struct CompatibilityCode { var code: String }

// This lock-backed recorder does not depend on the main actor or model executor.
// Its deadline can publish a terminal failure even if model cancellation stalls.
final class TraceRecorder: @unchecked Sendable {
    let unit: String
    private let lock = NSLock()
    private let started = ProcessInfo.processInfo.systemUptime
    private var events: [[String: Any]] = []
    private var finished = false
    private var expired = false
    private var deadlinePhase: String?
    private var task: Task<Void, Never>?
    private var parked: CheckedContinuation<Void, Never>?
    private var phase = "created"

    init(unit: String) { self.unit = unit }

    func attach(_ task: Task<Void, Never>) {
        lock.lock(); self.task = task; let cancelled = expired; lock.unlock()
        if cancelled { task.cancel() }
    }

    func park(_ continuation: CheckedContinuation<Void, Never>) {
        lock.lock(); parked = continuation; lock.unlock()
    }

    func mark(_ name: String, _ fields: [String: Any] = [:]) {
        lock.lock(); defer { lock.unlock() }
        guard !finished else { return }
        phase = name
        let entry = fields.merging(["phase": name, "elapsedSeconds": ProcessInfo.processInfo.systemUptime-started]) { _, new in new }
        events.append(entry)
        do {
            let data = try JSONSerialization.data(withJSONObject: ["unit": unit, "events": events], options: [.sortedKeys])
            try data.write(to: URL.documentsDirectory.appendingPathComponent("trace-"+unit+".json"), options: .atomic)
            let line = try JSONSerialization.data(withJSONObject: entry, options: [.sortedKeys])
            print("IOS27_PROGRESS " + String(decoding: line, as: UTF8.self)); fflush(stdout)
        } catch {
            fputs("Trace checkpoint write failed\n", stderr); fflush(stderr); exit(4)
        }
    }

    func arm(seconds: Double) {
        DispatchQueue.global(qos: .userInitiated).asyncAfter(deadline: .now()+seconds) { [self] in
            lock.lock()
            guard !finished else { lock.unlock(); return }
            expired = true; deadlinePhase = phase
            let current = task
            lock.unlock()
            mark("deadline_cancel_requested", ["deadlineSeconds": seconds])
            current?.cancel()
            // Do not await an uncooperative structured-concurrency child indefinitely.
            DispatchQueue.global(qos: .userInitiated).asyncAfter(deadline: .now()+2) { [self] in
                finish(code: nil, error: "app_deadline_cancellation_grace_expired")
            }
        }
    }

    func finish(code: String?, error: String?) -> Never {
        lock.lock()
        if finished { lock.unlock(); Thread.exit(); fatalError("unreachable") }
        finished = true
        let control = unit == "watchdog-control"
        let passed = control ? expired : (code == "ORBIT-27" && error == nil && !expired)
        let result: [String: Any] = ["schemaVersion": 1, "unit": unit, "syntheticOnly": true,
            "status": passed ? "ok" : "error", "os": ProcessInfo.processInfo.operatingSystemVersionString,
            "result": ["passed": passed, "watchdogControl": control, "deadlineFired": expired,
                "phaseAtDeadline": deadlinePhase as Any? ?? NSNull(), "lastPhase": phase,
                "code": code as Any? ?? NSNull(), "error": error as Any? ?? NSNull(),
                "elapsedSeconds": ProcessInfo.processInfo.systemUptime-started, "events": events]]
        do {
            let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
            let path = URL.documentsDirectory.appendingPathComponent("unit-"+unit+".json")
            guard !FileManager.default.fileExists(atPath: path.path) else { exit(3) }
            try data.write(to: path, options: .atomic)
            print("IOS27_RESULT " + String(decoding: data, as: UTF8.self)); fflush(stdout)
            exit(0)
        } catch { fputs("Final checkpoint write failed\n", stderr); fflush(stderr); exit(4) }
    }
}

@MainActor final class ProbeController {
    static let shared = ProbeController()
    private var started = false

    func execute() async {
        guard !started else { return }; started = true
        let args = CommandLine.arguments
        guard let i = args.firstIndex(of: "--unit"), i+1 < args.count,
              ["watchdog-control", "generation"].contains(args[i+1]) else { exit(2) }
        let unit = args[i+1]
        let recorder = TraceRecorder(unit: unit)
        recorder.mark("app_task_entered", ["applicationState": UIApplication.shared.applicationState.rawValue,
            "protectedDataAvailable": UIApplication.shared.isProtectedDataAvailable])
        recorder.arm(seconds: unit == "watchdog-control" ? 2 : 60)
        let task = Task { @MainActor in
            do {
                if unit == "watchdog-control" {
                    recorder.mark("synthetic_uncooperative_wait", ["modelRequests": 0])
                    // A retained continuation deliberately ignores cooperative cancellation.
                    // The independent watchdog must write the terminal record and exit.
                    await withCheckedContinuation { recorder.park($0) }
                    recorder.finish(code: nil, error: "unexpected_control_return")
                }
                for _ in 0..<50 {
                    if UIApplication.shared.applicationState == .active { break }
                    try await Task.sleep(for: .milliseconds(100))
                }
                guard UIApplication.shared.applicationState == .active,
                      UIApplication.shared.isProtectedDataAvailable else {
                    recorder.finish(code: nil, error: "app_not_active_or_protected_data_unavailable")
                }
                UIApplication.shared.isIdleTimerDisabled = true // This isolated app only; ends on exit.
                recorder.mark("foreground_verified", ["applicationState": UIApplication.shared.applicationState.rawValue,
                    "protectedDataAvailable": UIApplication.shared.isProtectedDataAvailable])
                recorder.mark("model_lookup_started")
                let model = SystemLanguageModel.default
                recorder.mark("model_lookup_finished")
                recorder.mark("availability_check_started")
                let availability = model.availability
                recorder.mark("availability_check_finished", ["availability": String(describing: availability), "contextSize": model.contextSize])
                guard availability == .available else { recorder.finish(code: nil, error: "model_unavailable") }
                recorder.mark("session_init_started")
                let session = LanguageModelSession(model: model,
                    instructions: "Extract only the explicitly stated code from this fictional receipt.")
                recorder.mark("session_init_finished")
                recorder.mark("response_started", ["prewarmUsed": false, "maximumResponseTokens": 100,
                    "applicationState": UIApplication.shared.applicationState.rawValue])
                let response = try await session.respond(to: "Fictional receipt code: ORBIT-27.",
                    generating: CompatibilityCode.self,
                    options: GenerationOptions(sampling: .greedy, maximumResponseTokens: 100))
                recorder.mark("response_finished", ["applicationState": UIApplication.shared.applicationState.rawValue])
                recorder.finish(code: response.content.code, error: nil)
            } catch {
                recorder.mark("caught_error", ["errorType": String(reflecting: type(of: error)), "message": String(describing: error)])
                recorder.finish(code: nil, error: String(describing: error))
            }
        }
        recorder.attach(task)
        await task.value
    }
}

@main struct GenerationProbeApp: App {
    var body: some Scene {
        WindowGroup {
            Text("Remember: local model diagnostic\nFictional prompt only\nPlease keep this app open.")
                .padding().task { await ProbeController.shared.execute() }
        }
    }
}
