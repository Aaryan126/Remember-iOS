import SwiftUI

// Diagnostic-only entrypoint; copied into the isolated build, never production.
@main
struct SourceBrowserMediaApp: App {
    var body: some Scene { WindowGroup { MediaFixtureRoot() } }
}

private struct MediaFixtureRoot: View {
    @State private var project: ProjectViewModel?
    @State private var error: String?

    var body: some View {
        Group {
            if let project {
                if ProcessInfo.processInfo.arguments.contains("--evidence-entry") {
                    ProjectView(model: project, onAsk: {})
                } else {
                    NavigationStack { SourceEvidenceSearchView(projectModel: project) }
                }
            } else if let error {
                Text(error).accessibilityIdentifier("fixture-error")
            } else { ProgressView("Preparing fictional sources…") }
        }
        .preferredColorScheme(ProcessInfo.processInfo.arguments.contains("--evidence-dark") ? .dark : .light)
        .task {
            guard project == nil, error == nil else { return }
            do {
                guard Bundle.main.bundleIdentifier == "SimpleStudio.Remember.SourceBrowserUI" else {
                    throw CocoaError(.fileReadNoPermission)
                }
                let store = try MemoryStore.live()
                let files = try LibraryFileStore(directoryURL: LibraryFileStore.defaultDirectory())
                let existing = Array(try ProvenanceSnapshot.replay(await store.provenanceEvents()).memories.values)
                if !existing.contains(where: { $0.originalFilename == "receipt-revised.txt" }) {
                    let date = Date(timeIntervalSince1970: 1_800_000_000)
                    let first = existing.first(where: { $0.originalFilename == "receipt-original.txt" }) ?? MemoryItem(id: UUID(uuidString: "00000000-0000-0000-0000-000000000201")!, kind: .text, createdAt: date, importedAt: date, updatedAt: date,
                        state: .captured, originalFilename: "receipt-original.txt", userCaption: "Receipt ORBIT-27. Delivery was planned for 12 June.",
                        title: "Fictional delivery record", summary: "Unicorn generated summary", extractedText: "Receipt ORBIT-27. Delivery was planned for 12 June.",
                        tagsJSON: "[]", processingError: nil, modelVersion: nil)
                    try files.replaceText(first.extractedText!, filename: first.originalFilename)
                    try await store.insertIfNeeded(first)
                    try files.replaceText("Receipt NOVA-42. Delivery moved to 19 June.", filename: "receipt-revised.txt")
                    try await store.updateNoteContent(id: first.id, document: NoteDocument(text: "Receipt NOVA-42. Delivery moved to 19 June."), filename: "receipt-revised.txt")
                }
                if !existing.contains(where: { $0.originalFilename == "missing-original.txt" }) {
                    let date = Date(timeIntervalSince1970: 1_800_000_000)
                    let archived = MemoryItem(id: UUID(uuidString: "00000000-0000-0000-0000-000000000202")!, kind: .text, createdAt: date, importedAt: date, updatedAt: date,
                        state: .captured, originalFilename: "missing-original.txt", userCaption: "Receipt ARCHIVE-8. Legacy instruction.",
                        title: "Fictional archived source", summary: nil, extractedText: "Receipt ARCHIVE-8. Legacy instruction.",
                        tagsJSON: "[]", processingError: nil, modelVersion: nil)
                    try await store.insertIfNeeded(archived)
                    try await store.setArchived(id: archived.id, archived: true)
                }
                // Stable IDs make repeated launches idempotent, including partial setup.
                let fixtures: [(String, MemoryKind, String, String)] = [
                    ("101", .image, "photo.png", "MEDIACHECK photo cobalt square"),
                    ("102", .audio, "silence.wav", "MEDIACHECK audio silent recording"),
                    ("103", .video, "motion.mp4", "MEDIACHECK video moving test pattern"),
                    ("104", .text, "document.txt", "MEDIACHECK document saved original"),
                    ("105", .video, "broken.mp4", "MEDIACHECK corrupt video retained evidence"),
                    ("106", .audio, "brief.wav", "MEDIACHECK brief silent recording")
                ]
                for (suffix, kind, filename, text) in fixtures {
                    guard let id = UUID(uuidString: "00000000-0000-0000-0000-000000000" + suffix) else {
                        throw CocoaError(.fileReadCorruptFile)
                    }
                    let target = files.url(for: "media-check-" + filename)
                    if !FileManager.default.fileExists(atPath: target.path) {
                        if filename == "document.txt" || filename == "broken.mp4" {
                            try Data(text.utf8).write(to: target, options: .atomic)
                        } else {
                            let name = (filename as NSString).deletingPathExtension
                            let ext = (filename as NSString).pathExtension
                            guard let source = Bundle.main.url(forResource: name, withExtension: ext) else {
                                throw CocoaError(.fileNoSuchFile)
                            }
                            try FileManager.default.copyItem(at: source, to: target)
                        }
                    }
                    if !existing.contains(where: { $0.id == id }) {
                        let date = Date(timeIntervalSince1970: 1_800_000_000)
                        let item = MemoryItem(id: id, kind: kind, createdAt: date, importedAt: date, updatedAt: date,
                            state: .captured, originalFilename: target.lastPathComponent, userCaption: nil,
                            title: "Fictional " + kind.rawValue + " source", summary: "Unicorn generated summary",
                            extractedText: text, tagsJSON: "[]", processingError: nil, modelVersion: nil)
                        try await store.insertIfNeeded(item)
                    }
                }
                // A replayed snapshot supplies real River content without observing
                // the organizer, invoking models, or accessing a different container.
                project = ProjectViewModel(initialSnapshot: try ProvenanceSnapshot.replay(await store.provenanceEvents()))
            } catch { self.error = "Fictional setup failed: \(error.localizedDescription)" }
        }
    }
}
