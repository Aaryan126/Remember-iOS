import SwiftUI

// Isolated simulator-only launcher. Never installed over the personal Remember app.
@main
struct UnifiedSearchFixtureApp: App {
    var body: some Scene { WindowGroup { UnifiedSearchFixtureRoot() } }
}

private struct UnifiedSearchFixtureRoot: View {
    @State private var ready = false
    @State private var error: String?
    @State private var library = LibraryViewModel()
    @State private var project = ProjectViewModel()

    var body: some View {
        Group {
            if ready {
                if ProcessInfo.processInfo.arguments.contains("--unified-threads") {
                    ProjectView(model: project, onAsk: {})
                } else {
                    MemoryLibraryView(viewModel: library, onAsk: {}, projectModel: project)
                }
            } else if let error {
                Text(error).accessibilityIdentifier("fixture-error")
            } else { ProgressView("Preparing fictional sources…") }
        }
        .preferredColorScheme(ProcessInfo.processInfo.arguments.contains("--unified-dark") ? .dark : .light)
        .task {
            guard !ready else { return }
            do {
                guard Bundle.main.bundleIdentifier == "SimpleStudio.Remember.SourceBrowserUI" else {
                    throw CocoaError(.fileReadNoPermission)
                }
                let store = try MemoryStore.live()
                let events = try await store.provenanceEvents()
                // Add a uniquely named fixture if a previous diagnostic used this
                // isolated bundle. Never delete existing diagnostic or personal data.
                if !events.contains(where: { (try? $0.payload().memory?.originalFilename) == "unified-v1.txt" }) {
                    let first = memory("Parcel ORBIT-27. Delivery planned for 12 June.", filename: "unified-v1.txt")
                    try await store.insertIfNeeded(first)
                    try await store.updateNoteContent(id: first.id, document: .init(text: "Parcel NOVA-42. Delivery moved to 19 June."))
                    try await store.updateEditableFields(id: first.id, title: "Delivery note", summary: "Unicorn generated summary", tags: [])
                    let archived = memory("Parcel ARCHIVE-8. Earlier instruction.", filename: "unified-archive.txt")
                    try await store.insertIfNeeded(archived)
                    try await store.setArchived(id: archived.id, archived: true)
                }
                // Loads/searches only; never bootstrap pending imports or ask AI.
                if !ProcessInfo.processInfo.arguments.contains("--unified-empty-library") {
                    await library.reloadLibraryProjection()
                }
                project = ProjectViewModel(initialSnapshot: try ProvenanceSnapshot.replay(await store.provenanceEvents()))
                ready = true
            } catch { self.error = "Fictional fixture failed: \(error.localizedDescription)" }
        }
    }

    private func memory(_ text: String, filename: String) -> MemoryItem {
        .init(id: UUID(), kind: .text, createdAt: Date(timeIntervalSince1970: 1_800_000_000),
            importedAt: Date(timeIntervalSince1970: 1_800_000_000), updatedAt: Date(timeIntervalSince1970: 1_800_000_000),
            state: .indexed, originalFilename: filename, userCaption: text, title: "Delivery note",
            summary: "Unicorn generated summary", extractedText: text, tagsJSON: "[]", processingError: nil, modelVersion: nil)
    }
}
