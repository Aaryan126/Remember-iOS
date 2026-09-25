import SwiftUI
import QuickLook

struct SourceEvidenceSearchView: View {
    var projectModel: ProjectViewModel? = nil
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize
    @State private var model: SourceEvidenceBrowserModel
    @State private var selection: Selection?
    @State private var showsSource = false
    @State private var actionTask: Task<Void, Never>?

    private struct Selection {
        let hit: SourceEvidenceHit
        let sequence: Int64
    }

    init(projectModel: ProjectViewModel? = nil, repository: (any SourceEvidenceBrowsing)? = nil) {
        self.projectModel = projectModel
        _model = State(initialValue: SourceEvidenceBrowserModel(repository: repository))
    }

    var body: some View {
        List {
            Section {
                if dynamicTypeSize.isAccessibilitySize {
                    accessibleScopeMenu
                } else {
                    scopePicker.pickerStyle(.segmented)
                }
                Text(model.scope == .current
                     ? "Current, unarchived sources."
                     : "Includes archived sources and earlier revisions.")
                    .font(.footnote).foregroundStyle(RememberPalette.secondaryText)
                DisclosureGroup("Search limitations") {
                    Text("Results are saved passages, not verified answers. Older revisions may be out of date. Only retained extracted text and your captions are searched—not AI summaries. No match does not prove that a fact was never recorded.")
                        .font(.footnote).foregroundStyle(RememberPalette.secondaryText)
                }
            }
            if let error = model.errorMessage {
                Section {
                    Label(error, systemImage: "exclamationmark.triangle")
                    Button("Try again") {
                        actionTask?.cancel()
                        actionTask = Task { await model.search(force: true) }
                    }
                }.accessibilityIdentifier("evidence-error")
            }
            if let page = model.page, !page.hits.isEmpty {
                Section {
                    ForEach(page.hits) { hit in
                        Button {
                            selection = Selection(hit: hit, sequence: page.throughSequence)
                            showsSource = true
                        } label: {
                            SourceEvidenceResultRow(hit: hit)
                        }
                        .buttonStyle(.plain)
                        .accessibilityHint("Opens this saved version. Back returns to search results.")
                        .accessibilityIdentifier("evidence-result-\(hit.sourceSequence)-\(hit.id.field.rawValue)-\(hit.id.ordinal)")
                    }
                    if model.canLoadMore {
                        Button("Show more passages") {
                            actionTask?.cancel()
                            actionTask = Task { await model.loadMore() }
                        }
                            .accessibilityIdentifier("evidence-load-more")
                    }
                } header: {
                    Text("\(page.totalMatchingPassages) matching \(page.totalMatchingPassages == 1 ? "passage" : "passages")")
                } footer: {
                    Text("Only retained extracted text and your captions are searched. AI summaries are not used as evidence.")
                }
            } else if !model.isLoading && model.errorMessage == nil {
                Section {
                    ContentUnavailableView(
                        model.didSearch ? "No matching saved text" : "Find your saved evidence",
                        systemImage: model.didSearch ? "doc.text.magnifyingglass" : "text.magnifyingglass",
                        description: Text(model.didSearch
                            ? "Try another word or Include history. Some media may not have searchable text."
                            : "Search a name, phrase or reference code. Open a passage to see its saved source and revision.")
                    )
                }.listRowBackground(Color.clear)
            }
            if model.isLoading {
                Section { ProgressView("Searching saved text…") }
            }
        }
        .rememberGroupedList()
        .navigationTitle("Saved evidence")
        .navigationBarTitleDisplayMode(.inline)
        .searchable(text: $model.query, placement: .navigationBarDrawer(displayMode: .always), prompt: "Search saved text")
        .scrollDismissesKeyboard(.interactively)
        .accessibilityIdentifier("evidence-search")
        .task(id: "\(model.scope.rawValue):\(model.query)") { await model.search(debounce: true) }
        .onChange(of: model.query) { actionTask?.cancel() }
        .onChange(of: model.scope) { actionTask?.cancel() }
        .onDisappear { actionTask?.cancel() }
        .refreshable { await model.search(force: true) }
        .navigationDestination(isPresented: $showsSource) {
            if let selection {
                SourceEvidenceDetailView(hit: selection.hit, sequence: selection.sequence, model: model, projectModel: projectModel)
                    .id(selection.hit.id)
            }
        }
    }

    private var scopePicker: some View {
        Picker("Evidence scope", selection: $model.scope) {
            Text("Current").tag(SourceEvidenceScope.current)
            Text("Include history").tag(SourceEvidenceScope.includeHistory)
        }
        .accessibilityIdentifier("evidence-scope")
        .accessibilityLabel("Evidence scope")
    }

    private var accessibleScopeMenu: some View {
        Menu {
            Picker("Evidence scope", selection: $model.scope) {
                Text("Current").tag(SourceEvidenceScope.current)
                Text("Include history").tag(SourceEvidenceScope.includeHistory)
            }
        } label: {
            HStack {
                Text(model.scope == .current ? "Current" : "Include history")
                    .fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 8)
                Image(systemName: "chevron.up.chevron.down").font(.caption)
            }
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
        }
        .accessibilityIdentifier("evidence-scope")
        .accessibilityLabel("Evidence scope")
        .accessibilityValue(model.scope == .current ? "Current" : "Include history")
    }
}

struct SourceEvidenceResultRow: View {
    let hit: SourceEvidenceHit

    var body: some View {
        VStack(alignment: .leading, spacing: 9) {
            HStack(alignment: .firstTextBaseline) {
                Text(hit.isCurrentVersion ? "Current revision" : "Earlier revision")
                    .font(.subheadline.weight(.semibold))
                Spacer(minLength: 8)
                Image(systemName: "chevron.right").font(.caption.weight(.semibold))
                    .foregroundStyle(RememberPalette.secondaryText)
            }
            Text(hit.quote).font(.body).lineLimit(5)
                .foregroundStyle(.primary)
            Text(hit.sourceDate.formatted(date: .abbreviated, time: .shortened) +
                 " · Revision \(hit.revision + 1)" + (hit.isArchived ? " · Archived" : ""))
                .font(.caption).foregroundStyle(RememberPalette.secondaryText)
            if hit.analysisIsPartial {
                Label("Partial extraction", systemImage: "doc.text")
                    .font(.caption).foregroundStyle(RememberPalette.secondaryText)
            }
        }
        .padding(.vertical, 8)
        .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
    }
}

struct SourceEvidenceDetailView: View {
    let hit: SourceEvidenceHit
    let sequence: Int64
    let model: SourceEvidenceBrowserModel
    let projectModel: ProjectViewModel?
    @State private var threadDestination: MemoryThreadDestination?
    @State private var resolved: ResolvedSourceEvidence?
    @State private var errorMessage: String?
    @State private var preview: URL?
    @State private var retry = 0
    @State private var contextLimit = 8_000

    var body: some View {
        List {
            if let resolved {
                Section {
                    Text(resolved.memory.displayTitle).font(.title2.bold())
                        .fixedSize(horizontal: false, vertical: true)
                    Text("Revision \(hit.revision + 1) · " + hit.sourceDate.formatted(date: .abbreviated, time: .shortened))
                        .foregroundStyle(RememberPalette.secondaryText)
                    Text(status).font(.subheadline)
                        .accessibilityIdentifier("evidence-version-status")
                    if resolved.libraryHasChanged {
                        Text("Your library has changed since this search. This view still shows the saved search version; refresh search to see newer activity.")
                            .font(.footnote).foregroundStyle(RememberPalette.secondaryText)
                    }
                }
                Section("Matched passage") {
                    Text(hit.quote).textSelection(.enabled)
                        .accessibilityIdentifier("evidence-exact-quote")
                    Text(hit.id.field == .userCaption ? "From your saved caption" : "From retained extracted text")
                        .font(.caption).foregroundStyle(RememberPalette.secondaryText)
                }
                if resolved.fieldText.trimmingCharacters(in: .whitespacesAndNewlines) != hit.quote {
                    Section("Saved text context") {
                        Text(String(resolved.fieldText.prefix(contextLimit))).textSelection(.enabled)
                        if resolved.fieldText.count > contextLimit {
                            Text("Showing the first \(contextLimit) characters. The matched passage above is shown in full.")
                                .font(.footnote).foregroundStyle(RememberPalette.secondaryText)
                            Button("Show more saved text") { contextLimit += 8_000 }
                        }
                    }
                }
                Section("Saved original") {
                    switch resolved.original {
                    case .available(let url):
                        if resolved.memory.kind == .image {
                            LocalImageView(url: url, maximumPixelSize: 2_400, contentMode: .fit)
                                .frame(maxWidth: .infinity).frame(minHeight: 120)
                                .accessibilityLabel("Saved photo")
                        } else if resolved.memory.kind == .video {
                            LocalVideoPlayerView(url: url)
                        } else if resolved.memory.kind == .audio {
                            AudioMemoryPlayerView(url: url)
                                .buttonStyle(.borderless)
                        }
                        Button("Open saved original", systemImage: "doc") { preview = url }
                            .buttonStyle(.borderless)
                            .accessibilityIdentifier("evidence-open-original")
                    case .unavailable:
                        Label("The original file is unavailable on this device. The retained text above is still available.", systemImage: "doc.badge.ellipsis")
                    case .versionUnverified:
                        Label("This filename was used by more than one revision. We can show the retained text, but cannot verify that the file matches this version.", systemImage: "doc.badge.ellipsis")
                    }
                }
                Section("About this evidence") {
                    Text("This is a saved source, not an AI-verified answer. Extracted text may contain recognition errors. Original page numbers and media timestamps are not retained in this history view.")
                    if hit.analysisIsPartial { Text("Only part of this source was extracted.") }
                    if hit.importedHistoryGap { Text("This memory was imported when history recording began. Earlier revisions may never have been recorded.") }
                    if hit.snapshotSequence != hit.sourceSequence {
                        LabeledContent("Extraction snapshot", value: hit.snapshotDate.formatted(date: .abbreviated, time: .shortened))
                    }
                }.font(.footnote).foregroundStyle(RememberPalette.secondaryText)
                if let projectModel {
                    let destinations = MemoryThreadDestination.resolve(memoryID: hit.id.memoryID,
                        revisionID: hit.id.revisionID, snapshotID: hit.id.snapshotID, snapshot: projectModel.snapshot)
                    if !destinations.isEmpty {
                        Section {
                            MemoryThreadLink(destinations: destinations, onSelect: { threadDestination = $0 })
                                .accessibilityIdentifier("evidence-thread-link")
                        } header: { Text("Thread context") } footer: {
                            Text("Opens the current thread history at this saved revision, not a reconstruction of the thread at that time.")
                        }
                    }
                }
            } else if let errorMessage {
                Section {
                    Label(errorMessage, systemImage: "exclamationmark.triangle")
                    Button("Try again") { retry += 1 }
                }
            } else {
                ProgressView("Opening saved evidence…")
            }
        }
        .rememberGroupedList()
        .memoryThreadNavigation(selection: $threadDestination, model: projectModel)
        .navigationTitle("Saved source")
        .navigationBarTitleDisplayMode(.inline)
        .accessibilityIdentifier("evidence-detail")
        .quickLookPreview($preview)
        .task(id: retry) {
            guard resolved == nil else { return }
            errorMessage = nil
            do {
                let value = try await model.resolve(hit, through: sequence)
                try Task.checkCancellation()
                resolved = value
            } catch is CancellationError {
            } catch { errorMessage = SourceEvidenceBrowserModel.message(for: error) }
        }
    }

    private var status: String {
        let revision = hit.isCurrentVersion ? "Current revision at the time of search" : "Earlier revision—not the current version"
        return revision + (hit.isArchived ? ". Memory archived at the time of search." : "")
    }
}
