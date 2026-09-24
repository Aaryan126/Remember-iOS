import SwiftUI

struct ThreadActivityView: View {
    let model: ProjectViewModel
    var clusterID: UUID? = nil
    var asOf: Date? = nil
    @State private var kind: MemoryKind?
    @State private var range = MemoryDateRange.anytime
    @State private var selectedThread: UUID?
    @State private var onlySuggestions = false
    @State private var limit = 60

    init(model: ProjectViewModel, clusterID: UUID? = nil, asOf: Date? = nil, onlySuggestions: Bool = false) {
        self.model = model
        self.clusterID = clusterID
        self.asOf = asOf
        _onlySuggestions = State(initialValue: onlySuggestions)
    }

    var body: some View {
        let snapshot = model.historical(at: asOf)
        let history = ThreadHistory(snapshot: snapshot, clusterID: clusterID ?? selectedThread)
        let events = history.activity.reversed().filter { event in
            if onlySuggestions && (event.kind != .splitProposal || snapshot.resolved.contains(event.id)) { return false }
            if !range.includes(event.timestamp, now: asOf ?? Date()) { return false }
            if let kind, event.memoryID.flatMap({ snapshot.memories[$0]?.kind }) != kind { return false }
            return true
        }
        List {
            Section {
                if let asOf {
                    Label("As of \(asOf.formatted(date: .abbreviated, time: .shortened))", systemImage: "clock")
                }
                Text("Captures, revisions and organization decisions are kept here. Open an event to inspect its evidence and available corrections.")
                    .font(.subheadline).foregroundStyle(RememberPalette.secondaryText)
            }
            Section("Filters") {
                Picker("Source", selection: $kind) {
                    Text("All sources").tag(nil as MemoryKind?)
                    ForEach([MemoryKind.text, .image, .video, .audio, .pdf, .link], id: \.self) {
                        Text($0.rawValue.capitalized).tag(Optional($0))
                    }
                }
                Picker("Date", selection: $range) {
                    ForEach(MemoryDateRange.allCases) { Text($0.label).tag($0) }
                }
                if clusterID == nil {
                    Picker("Thread", selection: $selectedThread) {
                        Text("All threads").tag(nil as UUID?)
                        ForEach(ThreadDirectory(snapshot: snapshot).entries) { thread in
                            Text(thread.title).tag(Optional(thread.id))
                        }
                    }
                }
                Toggle("Suggestions to review", isOn: $onlySuggestions)
            }
            Section("Activity") {
                ForEach(Array(events.prefix(limit))) { event in
                    NavigationLink {
                        ProvenanceEventView(event: event, model: model, historical: asOf != nil)
                    } label: {
                        ProvenanceEventRow(event: event, displayMemory: event.memoryID.flatMap { snapshot.memories[$0] })
                    }.accessibilityIdentifier("thread-event-\(event.id)")
                }
                if events.isEmpty { Text("No activity matches these filters.").foregroundStyle(RememberPalette.secondaryText) }
                if events.count > limit { Button("Show earlier activity") { limit += 60 } }
            }
        }
        .rememberGroupedList()
        .accessibilityIdentifier("thread-activity")
        .navigationTitle("Activity & decisions")
        .navigationBarTitleDisplayMode(.inline)
        .safeAreaInset(edge: .bottom) { ProjectStatusView(model: model) }
        .onChange(of: kind) { _, _ in limit = 60 }
        .onChange(of: range) { _, _ in limit = 60 }
        .onChange(of: selectedThread) { _, _ in limit = 60 }
        .onChange(of: onlySuggestions) { _, _ in limit = 60 }
        .onChange(of: ThreadDirectory(snapshot: snapshot).entries.map(\.id)) { _, ids in
            if let selectedThread, !ids.contains(selectedThread) { self.selectedThread = nil }
        }
    }
}
