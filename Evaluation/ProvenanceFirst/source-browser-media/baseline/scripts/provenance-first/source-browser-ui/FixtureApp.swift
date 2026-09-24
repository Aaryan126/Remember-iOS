import SwiftUI

// This replaces ONLY the launcher in the separately bundled diagnostic build.
// Production RememberApp and the user's app/container are never modified by it.
@main
struct SourceBrowserFixtureApp: App {
    var body: some Scene { WindowGroup { SourceBrowserFixtureRoot() } }
}

private struct SourceBrowserFixtureRoot: View {
    @State private var ready = false
    @State private var error: String?
    @State private var project = ProjectViewModel()

    var body: some View {
        Group {
            if ready {
                if ProcessInfo.processInfo.arguments.contains("--evidence-entry") {
                    ProjectView(model: project, onAsk: {})
                } else {
                    NavigationStack { SourceEvidenceSearchView() }
                }
            } else if let error {
                Text(error).accessibilityIdentifier("fixture-error")
            } else { ProgressView("Preparing fictional sources…") }
        }
        // Explicit fixture-only appearance: launch-default overrides are not
        // reliably applied to SwiftUI's window appearance on the tested runtime.
        .preferredColorScheme(ProcessInfo.processInfo.arguments.contains("--evidence-dark") ? .dark : .light)
        .task {
            guard !ready else { return }
            do {
                guard Bundle.main.bundleIdentifier == "SimpleStudio.Remember.SourceBrowserUI" else {
                    throw CocoaError(.fileReadNoPermission)
                }
                let store = try MemoryStore.live()
                // Existing fixture data is reused, never deleted or rewritten.
                if try await store.provenanceEvents().isEmpty {
                    let originals = try LibraryFileStore(directoryURL: LibraryFileStore.defaultDirectory())
                    let first = memory("Receipt ORBIT-27. Delivery was planned for 12 June.", filename: "receipt-original.txt")
                    try originals.replaceText(first.extractedText!, filename: first.originalFilename)
                    try await store.insertIfNeeded(first)
                    let revised = "Receipt NOVA-42. Delivery moved to 19 June."
                    try originals.replaceText(revised, filename: "receipt-revised.txt")
                    try await store.updateNoteContent(id: first.id, document: NoteDocument(text: revised), filename: "receipt-revised.txt")
                    let archived = memory("Receipt ARCHIVE-8. Legacy instruction.", filename: "missing-original.txt")
                    try await store.insertIfNeeded(archived)
                    try await store.setArchived(id: archived.id, archived: true)
                }
                ready = true
            } catch { self.error = "Fictional fixture could not be prepared: \(error.localizedDescription)" }
        }
    }

    private func memory(_ text: String, filename: String) -> MemoryItem {
        MemoryItem(id: UUID(), kind: .text, createdAt: Date(timeIntervalSince1970: 1_800_000_000),
            importedAt: Date(timeIntervalSince1970: 1_800_000_000), updatedAt: Date(timeIntervalSince1970: 1_800_000_000),
            state: .captured, originalFilename: filename, userCaption: text, title: "Fictional delivery record",
            summary: "Unicorn generated summary", extractedText: text, tagsJSON: "[]", processingError: nil, modelVersion: nil)
    }
}
