import SwiftUI
import UIKit

// Simulator-only fictional library. No production startup, capture or cloud calls.
@main
struct SearchTransitionFixtureApp: App {
    var body: some Scene { WindowGroup { SearchTransitionFixtureRoot() } }
}

private struct SearchTransitionFixtureRoot: View {
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
        .background(SearchMotionTrace())
        .preferredColorScheme(ProcessInfo.processInfo.arguments.contains("--unified-dark") ? .dark : .light)
        .task {
            guard !ready else { return }
            do {
                guard Bundle.main.bundleIdentifier == "SimpleStudio.Remember.SourceBrowserUI" else {
                    throw CocoaError(.fileReadNoPermission)
                }
                let store = try MemoryStore.live()
                let events = try await store.provenanceEvents()
                let filenames = Set(events.compactMap { try? $0.payload().memory?.originalFilename })
                if !filenames.contains("unified-v1.txt") {
                    let first = memory("Parcel ORBIT-27. Delivery planned for 12 June.", filename: "unified-v1.txt")
                    try await store.insertIfNeeded(first)
                    try await store.updateNoteContent(id: first.id, document: .init(text: "Parcel NOVA-42. Delivery moved to 19 June."))
                    try await store.updateEditableFields(id: first.id, title: "Delivery note", summary: "Unicorn generated summary", tags: [])
                    let archived = memory("Parcel ARCHIVE-8. Earlier instruction.", filename: "unified-archive.txt")
                    try await store.insertIfNeeded(archived)
                    try await store.setArchived(id: archived.id, archived: true)
                }
                if ProcessInfo.processInfo.arguments.contains("--transition-long-library") {
                    for index in 0..<24 {
                        let filename = "transition-scroll-\(index).txt"
                        if !filenames.contains(filename) {
                            try await store.insertIfNeeded(memory("Fictional travel journal entry \(index). A quiet afternoon in the garden.", filename: filename))
                        }
                    }
                }
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

 
// Read-only instrumentation in the fictional simulator app, never in Remember.
private struct SearchMotionTrace: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> Recorder { Recorder() }
    func updateUIViewController(_ controller: Recorder, context: Context) {}
    @MainActor final class Recorder: UIViewController {
        private var link: CADisplayLink?
        private var stream: FileHandle?
        private var began = CACurrentMediaTime()
        private var previous = ""
        override func viewDidAppear(_ animated: Bool) {
            super.viewDidAppear(animated)
            guard link == nil else { return }
            let url = URL.documentsDirectory.appendingPathComponent("search-motion-trace.jsonl")
            FileManager.default.createFile(atPath: url.path, contents: nil)
            stream = try? FileHandle(forWritingTo: url)
            let display = CADisplayLink(target: self, selector: #selector(sample))
            display.add(to: .main, forMode: .common)
            link = display
        }
        @objc private func sample() {
            guard let window = view.window, CACurrentMediaTime() - began < 240 else { return }
            var rows: [[String: Any]] = []
            func visit(_ view: UIView) {
                if let scroll = view as? UIScrollView, !(scroll is UITextView) {
                    let f = scroll.convert(scroll.bounds, to: window)
                    let p = scroll.layer.presentation()?.bounds.origin.y ?? scroll.bounds.origin.y
                    rows.append(["id": String(describing: ObjectIdentifier(scroll)),
                                 "class": String(describing: type(of: scroll)),
                                 "offset": scroll.contentOffset.y, "presentation": p,
                                 "inset": scroll.adjustedContentInset.top,
                                 "bottom": scroll.adjustedContentInset.bottom,
                                 "frameY": f.minY, "height": f.height,
                                 "hidden": scroll.isHidden, "alpha": scroll.alpha,
                                 "contentHeight": scroll.contentSize.height])
                }
                if let field = view as? UISearchTextField {
                    rows.append(["queryLength": field.text?.count ?? 0,
                                 "editing": field.isFirstResponder])
                }
                for child in view.subviews { visit(child) }
            }
            visit(window)
            guard let body = try? JSONSerialization.data(withJSONObject: rows, options: [.sortedKeys]),
                  let key = String(data: body, encoding: .utf8), key != previous else { return }
            previous = key
            let line = "{\"time\":\(CACurrentMediaTime() - began),\"views\":\(key)}\n"
            if let data = line.data(using: .utf8) { try? stream?.write(contentsOf: data) }
        }
        deinit { link?.invalidate(); try? stream?.close() }
    }
}

