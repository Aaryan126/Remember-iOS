import Foundation
import SwiftUI

@main
struct DiagnosticReplayApp: App {
    var body: some Scene {
        WindowGroup {
            Text("Fictional organization ledger diagnostics")
                .task { await execute() }
        }
    }

    private func execute() async {
        let arguments = ProcessInfo.processInfo.arguments
        func option(_ key: String) -> String? {
            guard let index = arguments.firstIndex(of: key), index + 1 < arguments.count else { return nil }
            return arguments[index + 1]
        }
        do {
            guard let inputPath = option("--input"), let outputPath = option("--output"),
                  let bindings = Bundle.main.url(forResource: "bindings", withExtension: "json") else {
                throw DiagnosticFailure(description: "--input and --output are required; bindings.json must be bundled")
            }
            let input = URL(fileURLWithPath: inputPath).resolvingSymlinksInPath()
            let output = URL(fileURLWithPath: outputPath).resolvingSymlinksInPath()
            let privateInputs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                .appendingPathComponent("OrganizationDiagnostics").resolvingSymlinksInPath()
            // Host-authored Desktop files may trigger macOS TCC. The coordinator can copy
            // the fictional JSON into this app's private input directory before launch.
            try diagnosticRequire(input.path.hasPrefix(privateInputs.path + "/")
                || input.path.contains("/Evaluation/OrganizationDiagnostics/runs/"), "input must be in diagnostic workspace or this app's private inputs")
            try diagnosticRequire(output.path.contains("/Evaluation/OrganizationDiagnostics/runs/"), "output must be inside diagnostic runs workspace")
            let maxRuns = option("--max-runs").flatMap(Int.init)
            if let maxRuns { try diagnosticRequire(maxRuns > 0, "--max-runs must be positive") }
            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
            if arguments.contains("--invariants") { try await DiagnosticInvariants.run(output: output) }
            try await DiagnosticReplay.run(input: input, output: output, bindings: bindings, maximumRuns: maxRuns)
            print("LEDGER_REPLAY_FINISHED")
            exit(0)
        } catch {
            print("LEDGER_REPLAY_FAILED: \(error)")
            exit(1)
        }
    }
}
