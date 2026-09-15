import SwiftUI
import QuickLook

struct ProjectStatusView: View {
    let model: ProjectViewModel
    var body: some View {
        if let error = model.errorMessage {
            HStack { Text(error).font(.footnote); Spacer(); Button("Dismiss") { model.errorMessage = nil } }.padding().background(.bar)
        } else if model.isOrganizing {
            HStack { ProgressView(); Text("Organizing your threads…").font(.caption) }.padding(8).background(.bar)
        }
    }
}

struct ProvenanceEventRow: View {
    let event: ProvenanceEvent
    var displayMemory: MemoryItem? = nil
    var showsIcon = true
    var showsRiverJunction = false
    var body: some View {
        let payload = try? event.payload()
        HStack(alignment: .top, spacing: 12) {
            if showsIcon {
                Image(systemName: event.kind == .merge ? "arrow.triangle.merge" : event.kind == .archive ? "archivebox" : "circle.fill")
                    .font(.system(size: event.kind == .capture ? 10 : 18)).foregroundStyle(.tint).frame(width: 24, height: 24)
            }
            VStack(alignment: .leading, spacing: 5) {
                Text(displayMemory?.displayTitle ?? payload?.memory?.displayTitle ?? payload?.title ?? event.kind.label).font(.headline).lineLimit(2)
                    .modifier(RiverTitleJunction(kind: event.kind, isVisible: showsRiverJunction))
                Text(event.kind.label + " · " + event.timestamp.formatted(date: .abbreviated, time: .shortened))
                    .font(.caption).foregroundStyle(RememberPalette.secondaryText)
                if let rationale = event.threadRationale, !rationale.isEmpty, rationale != event.kind.label {
                    Text(rationale).font(.subheadline).foregroundStyle(RememberPalette.secondaryText).lineLimit(2)
                }
            }
        }.padding(.vertical, 5)
    }
}

struct ClusterRiverView: View {
    let clusterID: UUID
    let model: ProjectViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var isHistorical = false
    @State private var date = Date()
    @State private var title = ""
    @State private var showsRename = false
    @State private var showsDelete = false
    @State private var isDeleting = false
    @State private var selectedMemory: MemoryItem?
    @State private var selectedMemoryIsHistorical = false
    @State private var showsMemory = false
    @State private var showsActivity = false
    @State private var activitySuggestionsOnly = false
    @State private var limit = 50
    var body: some View {
        let snapshot = model.historical(at: isHistorical ? date : nil)
        let cluster = snapshot.clusters[clusterID]
        let history = ThreadHistory(snapshot: snapshot, clusterID: clusterID)
        let events = history.story
        let visibleEvents = Array(events.suffix(limit))
        let memoryCount = snapshot.members(of: clusterID).count
        List {
            Section {
                Text(cluster?.title ?? "This thread had not formed yet").font(.largeTitle.bold())
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityAddTraits(.isHeader)
                    .listRowInsets(EdgeInsets(top: 4, leading: 0, bottom: 0, trailing: 0))
                    .listRowBackground(Color.clear)
                    .listRowSeparator(.hidden)
                if isHistorical {
                    DatePicker("As of", selection: $date, in: ...Date())
                    Slider(value: Binding(get: { date.timeIntervalSince1970 }, set: { date = Date(timeIntervalSince1970: $0) }),
                        in: (model.snapshot.events.first?.timestamp.timeIntervalSince1970 ?? Date().timeIntervalSince1970 - 1)...Date().timeIntervalSince1970)
                        .accessibilityLabel("History date").accessibilityIdentifier("History date")
                    comparison(in: snapshot)
                }
            }
            if let cluster, !cluster.parents.isEmpty {
                Section("Merged threads") {
                    ForEach(cluster.parents, id: \.self) { id in
                        NavigationLink { ClusterRiverView(clusterID: id, model: model) } label: {
                            Label(snapshot.clusters[id]?.title ?? "Earlier thread", systemImage: "arrow.turn.down.right")
                        }
                    }
                    Label(cluster.title, systemImage: "arrow.triangle.merge").font(.headline)
                }
            }
            Section {
                VStack(alignment: .leading, spacing: 4) {
                    Text("History · \(memoryCount) \(memoryCount == 1 ? "memory" : "memories")")
                    if history.pendingSuggestionCount > 0 {
                        Button {
                            activitySuggestionsOnly = true
                            showsActivity = true
                        } label: {
                            Text("\(history.pendingSuggestionCount) \(history.pendingSuggestionCount == 1 ? "suggestion" : "suggestions") to review")
                                .font(.subheadline).foregroundStyle(RememberPalette.action)
                                .frame(minHeight: 44, alignment: .leading)
                        }
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("thread-review-suggestions")
                    }
                }
                .font(.headline).foregroundStyle(RememberPalette.secondaryText)
                .listRowInsets(EdgeInsets(top: 8, leading: 0, bottom: 16, trailing: 0))
                .listRowBackground(Color.clear)
                .listRowSeparator(.hidden)
                if events.isEmpty {
                    Text(isHistorical ? "No saved content at this point in the thread’s history." : "No saved content in this thread.")
                        .foregroundStyle(RememberPalette.secondaryText)
                }
                if events.count > limit {
                    Button("Unfold earlier history") { limit += 50 }
                        .listRowInsets(EdgeInsets(top: 20, leading: 42, bottom: 36, trailing: 16))
                        .listRowSeparator(.hidden)
                        .listRowBackground(RiverCardBackground())
                }
                ForEach(visibleEvents) { event in
                    Group {
                        if let original = event.riverSource {
                            let source = event.riverMemory(in: snapshot)
                            VStack(alignment: .leading, spacing: 20) {
                                Button { openMemory(source ?? original) } label: {
                                    HStack(alignment: .firstTextBaseline, spacing: 12) {
                                        VStack(alignment: .leading, spacing: 5) {
                                            Text((source ?? original).displayTitle).font(.headline).lineLimit(3)
                                                .modifier(RiverTitleJunction(kind: event.kind))
                                            Text((event.kind == .revision ? "Revised · " : "") +
                                                 (event.kind == .revision ? event.timestamp : original.createdAt)
                                                    .formatted(date: .abbreviated, time: .shortened))
                                                .font(.subheadline).foregroundStyle(RememberPalette.secondaryText)
                                        }
                                        Spacer(minLength: 0)
                                        Image(systemName: "chevron.right").font(.caption.weight(.semibold)).foregroundStyle(.tertiary)
                                    }
                                    .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
                                    .contentShape(Rectangle())
                                }
                                .buttonStyle(.plain)
                                .accessibilityHint("Opens this memory; Back returns to the thread")
                                .accessibilityIdentifier("project-source-\(original.id)")
                                RiverMediaView(memory: original, onOpenMemory: { openMemory(source ?? original) })
                                    .id(original.originalFilename)
                                if original.kind == .text, let text = original.userCaption {
                                    let document = NoteDocument(text: text)
                                    let body = document.title == (source ?? original).displayTitle ? document.body : text
                                    if !body.isEmpty { Text(body).font(.body).textSelection(.enabled) }
                                }
                            }
                        } else {
                            NavigationLink { ProvenanceEventView(event: event, model: model, historical: isHistorical) } label: {
                                VStack(alignment: .leading, spacing: 5) {
                                    Text(event.kind == .merge ? "Threads merged" : "Thread split")
                                        .font(.subheadline.weight(.semibold))
                                        .modifier(RiverTitleJunction(kind: event.kind))
                                    Text(event.timestamp.formatted(date: .abbreviated, time: .shortened))
                                        .font(.subheadline).foregroundStyle(RememberPalette.secondaryText)
                                }
                                .accessibilityHint("Inspect this change and its evidence")
                            }
                        }
                    }
                    .modifier(RiverRail(startsAtJunction: event.id == visibleEvents.first?.id))
                    .listRowInsets(EdgeInsets(top: 20, leading: 42, bottom: 36, trailing: 16))
                    .listRowSeparator(.hidden)
                    .listRowBackground(RiverCardBackground())
                }
            }
        }.rememberGroupedList().listRowSpacing(0)
            .listSectionSpacing(0)
            .contentMargins(.top, 20, for: .scrollContent)
            .contentMargins(.horizontal, 20, for: .scrollContent)
            .accessibilityIdentifier("thread-history")
            .navigationTitle(cluster?.title ?? "Thread history").navigationBarTitleDisplayMode(.inline)
            .navigationDestination(isPresented: $showsMemory) {
                if let selectedMemory {
                    ProjectSourceView(memory: selectedMemory, model: model, historical: selectedMemoryIsHistorical)
                }
            }
            .navigationDestination(isPresented: $showsActivity) {
                ThreadActivityView(model: model, clusterID: clusterID, asOf: isHistorical ? date : nil,
                                   onlySuggestions: activitySuggestionsOnly)
                    .id(activitySuggestionsOnly)
            }
            .toolbar {
                Menu {
                    Button("Activity & decisions", systemImage: "clock.arrow.circlepath") {
                        activitySuggestionsOnly = false
                        showsActivity = true
                    }
                        .accessibilityIdentifier("thread-activity-link")
                    if isHistorical {
                        Button("Back to present", systemImage: "clock") { isHistorical = false }
                    } else {
                        Button("View past state", systemImage: "clock.arrow.circlepath") {
                            date = Date()
                            isHistorical = true
                        }
                    }
                    if !isHistorical, cluster?.retired == false, !snapshot.archivedClusterIDs.contains(clusterID) {
                        Button("Rename thread", systemImage: "pencil") { title = cluster?.title ?? ""; showsRename = true }
                        Button("Archive thread…", systemImage: "archivebox", role: .destructive) { showsDelete = true }
                    }
                } label: {
                    Image(systemName: "ellipsis").rotationEffect(.degrees(90))
                        .foregroundStyle(.primary)
                        .frame(width: 28, height: 28)
                }
                .accessibilityLabel("Thread options")
                .disabled(isDeleting)
            }
            .alert("Rename thread", isPresented: $showsRename) {
                TextField("Thread name", text: $title)
                Button("Save") { Task { await model.rename(clusterID, title: title) } }
                    .disabled(title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                Button("Cancel", role: .cancel) {}
            }
            .confirmationDialog("Archive this thread?", isPresented: $showsDelete, titleVisibility: .visible) {
                Button("Archive thread", role: .destructive) {
                    Task {
                        isDeleting = true
                        let saved = await model.archiveThread(clusterID, archived: true)
                        isDeleting = false
                        if saved { dismiss() }
                    }
                }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("The thread moves to Archive. Its memories stay in Memories and any other threads. You can restore the thread from Settings → Archive.")
            }
            .task { await model.recap(clusterID) }
            .safeAreaInset(edge: .bottom) { ProjectStatusView(model: model) }
    }
    private func openMemory(_ memory: MemoryItem) {
        selectedMemory = memory
        selectedMemoryIsHistorical = isHistorical ||
            model.snapshot.memories[memory.id]?.originalFilename != memory.originalFilename
        showsMemory = true
    }
    private func comparison(in snapshot: ProvenanceSnapshot) -> some View {
        let before = Dictionary(uniqueKeysWithValues: snapshot.members(of: clusterID).map { ($0.id, $0) })
        let current = Dictionary(uniqueKeysWithValues: model.snapshot.members(of: clusterID).map { ($0.id, $0) })
        let added = Set(current.keys).subtracting(before.keys).count
        let removed = Set(before.keys).subtracting(current.keys).count
        let revised = before.values.filter { old in current[old.id].map { $0.originalFilename != old.originalFilename } ?? false }.count
        return VStack(alignment: .leading, spacing: 4) {
            Text("Since this moment: +\(added) sources, −\(removed) sources, \(revised) revised.")
            if snapshot.clusters[clusterID]?.title != model.snapshot.clusters[clusterID]?.title { Text("Now named \(model.snapshot.clusters[clusterID]?.title ?? "Unknown")") }
        }.font(.footnote).foregroundStyle(RememberPalette.secondaryText)
    }
}

struct ProvenanceEventView: View {
    let event: ProvenanceEvent
    let model: ProjectViewModel
    var historical = false
    var body: some View {
        let payload = try? event.payload()
        List {
            Section { ProvenanceEventRow(event: event) }
            Section("Why is this here?") {
                Text(event.threadRationale ?? "History unavailable")
                LabeledContent("Origin", value: event.origin.capitalized)
                LabeledContent("Method", value: payload?.model ?? "Unknown")
                if let device = payload?.deviceContext { LabeledContent("Capture context", value: device) }
                ForEach((payload?.scores ?? [:]).keys.sorted(), id: \.self) { key in
                    LabeledContent(UUID(uuidString: key).flatMap { model.snapshot.clusters[$0]?.title } ?? key,
                        value: String(format: "%.3f", payload?.scores[key] ?? 0))
                }
            }
            if let memory = payload?.memory {
                Section("Source revision") {
                    NavigationLink { ProjectSourceView(memory: memory, model: model, historical: true) } label: { Text(memory.displayTitle) }
                    if [.capture, .revision, .imported].contains(event.kind), memory.kind == .text {
                        Button("Restore this note revision") { Task { await model.restoreRevision(event) } }
                    }
                }
            }
            if let revisionID = payload?.sourceRevisionID, let source = model.snapshot.events.first(where: { $0.id == revisionID }) {
                Section("Evidence used for this decision") {
                    NavigationLink { ProvenanceEventView(event: source, model: model, historical: true) } label: { ProvenanceEventRow(event: source) }
                }
            }
            if let payload, !payload.assignments.isEmpty {
                Section(event.kind == .splitProposal ? "Proposed sources" : "Affected sources") {
                    ForEach(payload.assignments.keys.sorted(), id: \.self) { key in
                        if let id = UUID(uuidString: key), let memory = model.snapshot.memories[id] { Text(memory.displayTitle) }
                    }
                }
            }
            if let payload, !payload.citedEventIDs.isEmpty {
                Section(event.kind == .recap ? "Activity behind this recap" : "Evidence behind this change") {
                    ForEach(model.snapshot.events.filter { payload.citedEventIDs.contains($0.id) }) { source in
                        NavigationLink { ProvenanceEventView(event: source, model: model, historical: true) } label: { ProvenanceEventRow(event: source) }
                    }
                }
            }
            if !historical, !model.snapshot.resolved.contains(event.id) {
                if event.kind == .splitProposal {
                    Button("Accept split") { Task { await model.resolve(event, accept: true) } }
                    Button("Keep together") { Task { await model.resolve(event, accept: false) } }
                } else if [.merge, .placement, .split, .rename].contains(event.kind) {
                    Button("Undo this change") { Task { await model.undo(event) } }
                }
            }
        }.rememberGroupedList().navigationTitle(event.kind.label).safeAreaInset(edge: .bottom) { ProjectStatusView(model: model) }
    }
}

private struct RiverCardBackground: View {
    var body: some View {
        RoundedRectangle(cornerRadius: 20)
            .fill(Color(uiColor: .secondarySystemGroupedBackground))
            .padding(.leading, 26).padding(.bottom, 16)
            .accessibilityHidden(true).allowsHitTesting(false)
    }
}

private struct RiverJunctionAnchor: PreferenceKey {
    static var defaultValue: Anchor<CGRect>? { nil }
    static func reduce(value: inout Anchor<CGRect>?, nextValue: () -> Anchor<CGRect>?) {
        value = nextValue() ?? value
    }
}

private struct RiverRail: ViewModifier {
    let startsAtJunction: Bool
    @Environment(\.colorScheme) private var scheme

    func body(content: Content) -> some View {
        content.backgroundPreferenceValue(RiverJunctionAnchor.self) { anchor in
            GeometryReader { geometry in
                if let anchor {
                    Canvas { context, size in
                        // Resolve the actual title junction, including Dynamic Type and wrapping.
                        let start = startsAtJunction ? geometry[anchor].minY + 18 + 20 : 0
                        var trunk = Path()
                        trunk.move(to: CGPoint(x: 8, y: start))
                        trunk.addLine(to: CGPoint(x: 8, y: size.height))
                        context.stroke(trunk, with: .color(scheme == .dark ? .accentColor.opacity(0.45) : RememberPalette.rule), lineWidth: 2)
                    }
                    // Include the row insets so adjacent rails meet through the card gaps.
                    .frame(width: geometry.size.width + 58, height: geometry.size.height + 56)
                    .offset(x: -42, y: -20)
                }
            }
            .accessibilityHidden(true).allowsHitTesting(false)
        }
    }
}

private struct RiverTitleJunction: ViewModifier {
    let kind: ProvenanceKind
    var isVisible = true
    @ScaledMetric(relativeTo: .headline) private var capHeight = UIFont.preferredFont(
        forTextStyle: .headline,
        compatibleWith: UITraitCollection(preferredContentSizeCategory: .large)
    ).capHeight

    func body(content: Content) -> some View {
        content.overlay(alignment: Alignment(horizontal: .leading, vertical: .firstTextBaseline)) {
            if isVisible {
                Canvas { context, _ in
                    let x: CGFloat = 6
                    let junction: CGFloat = 18
                    if kind == .merge {
                        var tributary = Path()
                        tributary.move(to: CGPoint(x: 22, y: 0))
                        tributary.addCurve(to: CGPoint(x: x, y: junction),
                            control1: CGPoint(x: 22, y: 10), control2: CGPoint(x: x, y: 10))
                        context.stroke(tributary, with: .color(RememberPalette.action), lineWidth: 2)
                    }
                    let diameter: CGFloat = kind == .merge ? 12 : 8
                    context.fill(Path(ellipseIn: CGRect(x: x - diameter / 2, y: junction - diameter / 2,
                                                       width: diameter, height: diameter)), with: .color(RememberPalette.action))
                }
                .frame(width: 24, height: 24)
                .anchorPreference(key: RiverJunctionAnchor.self, value: .bounds) { $0 }
                // The first baseline is measured from the actual title, even
                // when it wraps. Half the scaled cap height gives its optical center.
                .alignmentGuide(.firstTextBaseline) { _ in 18 + capHeight / 2 }
                .offset(x: -40)
                .accessibilityHidden(true).allowsHitTesting(false)
            }
        }
    }
}

struct ProjectSourceView: View {
    let memory: MemoryItem
    let model: ProjectViewModel
    var historical = false
    @State private var selected: Set<UUID> = []
    @State private var preview: URL?
    var body: some View {
        List {
            Section {
                Text(memory.displayTitle).font(.title2.bold())
                RiverMediaView(memory: memory).id(memory.originalFilename)
                LabeledContent("Captured", value: memory.createdAt.formatted(date: .abbreviated, time: .shortened))
                Text(memory.extractedText ?? memory.userCaption ?? memory.displaySummary ?? "Extraction is pending. The original is saved.").textSelection(.enabled)
                Button("Open saved original") {
                    do { preview = try LibraryFileStore(directoryURL: LibraryFileStore.defaultDirectory()).url(for: memory.originalFilename) }
                    catch { model.errorMessage = error.localizedDescription }
                }
            }
            if memory.kind == .video, let note = memory.analysisNote {
                Section("Video search") {
                    Text(note).font(.footnote).foregroundStyle(RememberPalette.secondaryText)
                }
            }
            Section("Activity & decisions") {
                ForEach(model.snapshot.events.filter { $0.memoryID == memory.id && $0.kind != .processing }.reversed()) { event in
                    NavigationLink { ProvenanceEventView(event: event, model: model, historical: historical) } label: { ProvenanceEventRow(event: event) }
                }
            }
            if !historical, model.snapshot.memories[memory.id]?.isArchived == false {
                Section("Threads") {
                    ForEach(model.snapshot.activeClusters) { cluster in
                        Toggle(cluster.title, isOn: Binding(get: { selected.contains(cluster.id) }, set: {
                            if $0 { selected.insert(cluster.id) } else { selected.remove(cluster.id) }
                        }))
                    }
                    Button("Save thread assignments") { Task { await model.assign(memory.id, clusters: selected) } }
                    Text("Choose several threads, or clear all to start a separate thread. Your choice is preserved during automatic organization.")
                        .font(.caption).foregroundStyle(RememberPalette.secondaryText)
                }
                Button("Archive memory") { Task { await model.archive(memory.id, archived: true) } }
            }
        }.rememberGroupedList().navigationTitle(historical ? "Saved revision" : "Memory").quickLookPreview($preview)
            .onAppear { selected = model.snapshot.memberships[memory.id, default: []].subtracting(model.snapshot.archivedClusterIDs) }
            .safeAreaInset(edge: .bottom) { ProjectStatusView(model: model) }
    }
}

struct ProjectArchiveView: View {
    let model: ProjectViewModel
    var body: some View {
        List {
            Section { Text("Restore archived threads or memories here. Their originals and history stay on this device.").font(.subheadline).foregroundStyle(RememberPalette.secondaryText) }
            if !model.snapshot.archivedClusters.isEmpty {
                Section("Threads") {
                    ForEach(model.snapshot.archivedClusters) { cluster in
                        HStack {
                            Text(cluster.title)
                            Spacer()
                            Button("Restore") { Task { _ = await model.archiveThread(cluster.id, archived: false) } }
                                .buttonStyle(.borderless)
                                .accessibilityLabel("Restore thread \(cluster.title)")
                        }
                    }
                }
            }
            ForEach(model.snapshot.memories.values.filter(\.isArchived).sorted { $0.updatedAt > $1.updatedAt }) { memory in
                VStack(alignment: .leading, spacing: 8) {
                    NavigationLink { ProjectSourceView(memory: memory, model: model, historical: true) } label: { Text(memory.displayTitle) }
                    Button("Restore") { Task { await model.archive(memory.id, archived: false) } }
                        .accessibilityLabel("Restore \(memory.displayTitle)")
                }
            }
        }.rememberGroupedList().navigationTitle("Archive").safeAreaInset(edge: .bottom) { ProjectStatusView(model: model) }
    }
}
