import XCTest
@testable import Remember

final class FeedbackDemoSeedTests: XCTestCase {
    func testSeedFictionalFeedbackLibrary() async throws {
        #if !targetEnvironment(simulator)
        throw XCTSkip("Fictional feedback fixture is simulator-only")
        #else
        let store = try MemoryStore.live()
        guard try await store.fetchAll().isEmpty else { XCTFail("Requires a fresh disposable simulator"); return }
        UserDefaults.standard.set(false, forKey: "remember.project.cloudAssistance")
        let root = try LibraryFileStore.defaultDirectory()
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        let notes: [(String, String, String)] = [
            ("Garden studio", "A room for making", "Turn the unused garden room into a quiet studio. Keep the morning light, add a long workbench, and leave one wall clear for sketches."),
            ("Kyoto autumn trip", "A slower Kyoto itinerary", "Leave the first morning open. Walk beside the river, visit a small ceramics studio, and save time for places we discover along the way."),
            ("Reading notebook", "An idea worth keeping", "Good tools help us return to unfinished thoughts. A useful note should keep enough context that it still makes sense a month later."),
            ("Weekend recipes", "Lemon pasta for friends", "Save a cup of pasta water. Finish with lemon zest, olive oil, and parmesan. Add the herbs just before serving."),
            ("Community garden", "Saturday planting plan", "Meet at the east gate at nine. Bring gloves, label the herb beds, and leave the central path wide enough for everyone."),
            ("Photo essay", "Look for small details", "A photo series about ordinary morning rituals: an open window, a bicycle at the bakery, and shadows crossing the kitchen table."),
            ("Learning Spanish", "Practice in small moments", "Try ten minutes of listening on the walk home. Keep a short list of phrases to use in an actual conversation."),
            ("Garden studio", "Workbench measurements", "The garden studio workbench can be 180 cm wide. Keep the drawers shallow and leave space beneath for a stool. Measure the doorway before ordering."),
            ("Garden studio", "Choose warm lighting", "For the garden studio, test warm task lighting over the workbench. Keep the reading corner softer. Compare the samples after sunset.")
        ]
        var threads: [String: UUID] = [:]
        var ids: [UUID] = []
        for (index, note) in notes.enumerated() {
            let id = UUID(); ids.append(id)
            let text = note.1 + "\n\n" + note.2
            let filename = id.uuidString + ".txt"
            try Data(text.utf8).write(to: root.appendingPathComponent(filename), options: .atomic)
            let date = Date().addingTimeInterval(Double(index - notes.count) * 86_400)
            let item = MemoryItem(id: id, kind: .text, createdAt: date, importedAt: date, updatedAt: date,
                state: .indexed, originalFilename: filename, userCaption: text, title: note.1,
                summary: note.2, extractedText: text, tagsJSON: MemoryItem.encodeTags(note.0 == "Garden studio" || note.0 == "Community garden" ? ["home", "garden"] : [note.0]), processingError: nil, modelVersion: "fictional-feedback-fixture")
            try await store.insertIfNeeded(item)
            if let thread = threads[note.0] {
                try await store.assignProjectMemory(id: id, clusters: [thread])
                try await store.setProjectThreadArchived(id: id, archived: true)
            } else {
                threads[note.0] = id
                try await store.renameProjectCluster(id: id, title: note.0)
                try await store.assignProjectMemory(id: id, clusters: [id])
            }
        }
        let total = try await store.fetchAll().count
        XCTAssertEqual(total, 9)
        #endif
    }
}
