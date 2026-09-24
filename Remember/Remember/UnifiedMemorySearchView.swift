import SwiftUI

/// Content for the Memories screen's persistent native scroll container.
struct UnifiedMemorySearchView: View {
    let viewModel: LibraryViewModel
    var projectModel: ProjectViewModel? = nil
    @Binding var options: UnifiedMemorySearchOptions
    let sources: SourceEvidenceBrowserModel
    @State private var selection: Selection?
    @State private var showsSource = false
    @State private var actionTask: Task<Void, Never>?
    @State private var showsSearchHelp = false

    private struct Selection {
        let hit: SourceEvidenceHit
        let sequence: Int64
    }

    private struct Request: Equatable {
        let query: String
        let options: UnifiedMemorySearchOptions
    }

    private var request: Request { Request(query: viewModel.searchQuery, options: options) }
    private var hasQuery: Bool { !viewModel.searchRequest.normalizedQuery.isEmpty }
    private var currentPage: SourceEvidencePage? {
        guard sources.query == request.query, sources.scope == options.scope else { return nil }
        return sources.page
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            searchHeader
            resultSections
        }
        .padding(.horizontal, 16)
        // Native search chrome already supplies the matching 10pt top gap.
        // Keep the 44pt header touch target; no additional top padding.
        .padding(.bottom, 40)
        .alert("How search works", isPresented: $showsSearchHelp) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("Ordinary search matches titles, summaries, tags and saved text. Include history adds retained earlier revisions and archived memories; these may be out of date. Source text only matches extracted text and your captions, not AI summaries or tags. Saved passages are not verified answers, and extracted text can contain recognition errors. A missing match does not prove something was never recorded.")
        }
        .task(id: request) {
            actionTask?.cancel()
            sources.query = request.query
            sources.scope = request.options.scope
            await sources.search(debounce: true)
        }
        .onChange(of: request) { actionTask?.cancel() }
        .onDisappear { actionTask?.cancel() }
        .navigationDestination(isPresented: $showsSource) {
            if let selection {
                SourceEvidenceDetailView(hit: selection.hit, sequence: selection.sequence,
                    model: sources, projectModel: projectModel)
                    .id(selection.hit.id)
            }
        }
    }

    private var resultSections: some View {
        VStack(alignment: .leading, spacing: 20) {
            if options.hasActiveFilters {
                HStack(alignment: .firstTextBaseline, spacing: 8) {
                    Text(options.activeFilterSummary)
                        .font(.caption).foregroundStyle(RememberPalette.secondaryText)
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("search-active-filters")
                    Spacer(minLength: 0)
                    Button("Reset") { options = UnifiedMemorySearchOptions() }
                        .font(.caption).frame(minHeight: 44)
                        .accessibilityLabel("Reset search filters")
                        .accessibilityIdentifier("search-reset-filters")
                }
            }
            if !options.sourceTextOnly {
                memoryResults
            }
            if hasQuery {
                savedTextResults
            } else if options.sourceTextOnly || options.includeHistory {
                Text("Enter a name, phrase or reference to search saved text\(options.includeHistory ? " and retained history" : "").")
                    .foregroundStyle(RememberPalette.secondaryText)
            }
        }
    }

    private var searchHeader: some View {
        HStack(alignment: .center, spacing: 12) {
            Text(options.sourceTextOnly ? "Saved passages" : "Memories").font(.headline)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("search-results-title")
            Spacer(minLength: 8)
            if !options.sourceTextOnly {
                if viewModel.isSearching { ProgressView().controlSize(.small) }
                Text("\(viewModel.visibleItems.count)").foregroundStyle(RememberPalette.secondaryText)
                    .font(.body)
                    .monospacedDigit()
                    .accessibilityIdentifier("search-results-count")
            }
            Menu {
                Section("Search filters") {
                    Toggle("Include history", isOn: $options.includeHistory)
                        .accessibilityIdentifier("search-include-history")
                    Toggle("Source text only", isOn: $options.sourceTextOnly)
                        .accessibilityIdentifier("search-source-only")
                    if options.hasActiveFilters {
                        Button("Reset filters") { options = UnifiedMemorySearchOptions() }
                    }
                }
                if hasQuery && !options.hasActiveFilters && !viewModel.usedAIForCurrentSearch {
                    Button("Try AI search", systemImage: "sparkles") {
                        actionTask?.cancel()
                        actionTask = Task { await viewModel.searchWithAI() }
                    }
                    .disabled(viewModel.isSearching)
                }
                Button("How search works", systemImage: "info.circle") { showsSearchHelp = true }
            } label: {
                Image(systemName: options.hasActiveFilters ? "line.3.horizontal.decrease.circle.fill" : "line.3.horizontal.decrease.circle")
                    .font(.title3)
                    .frame(minWidth: 44, minHeight: 44)
            }
            .accessibilityLabel("Search options")
            .accessibilityValue(options.hasActiveFilters ? options.activeFilterSummary : "No filters")
            .accessibilityIdentifier("search-options-menu")
            .menuActionDismissBehavior(.enabled)
        }
    }

    private var memoryResults: some View {
        VStack(alignment: .leading, spacing: 12) {
            if viewModel.usedAIForCurrentSearch {
                Label("AI-assisted memory matches", systemImage: "sparkles").font(.caption)
            }
            if viewModel.visibleItems.isEmpty && !viewModel.isSearching {
                    Text("No matching current memories. Try different words or Include history in Search options.")
                    .foregroundStyle(RememberPalette.secondaryText)
            }
            MasonryLayout(spacing: 18) {
                ForEach(viewModel.visibleItems) { item in
                    VStack(alignment: .leading, spacing: 0) {
                        NavigationLink(value: item.id) { MemoryCard(item: item) }
                            .buttonStyle(.plain)
                            .accessibilityIdentifier("library-memory-\(item.id)")
                        if let page = currentPage, let hit = options.snippet(for: item.id, in: page) {
                            Button { open(hit, page: page) } label: {
                                VStack(alignment: .leading, spacing: 6) {
                                    Text(hit.quote).lineLimit(3).foregroundStyle(.primary)
                                    Label("View saved passage", systemImage: "doc.text.magnifyingglass")
                                }
                                .font(.caption).padding(12)
                                .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            .buttonStyle(.plain)
                            .accessibilityIdentifier("search-snippet-\(item.id)")
                        }
                    }
                }
            }
        }
    }

    private var savedTextResults: some View {
        VStack(alignment: .leading, spacing: 12) {
            if sources.isLoading {
                ProgressView("Searching saved text…")
            }
            if let error = sources.errorMessage {
                Label(error, systemImage: "exclamationmark.triangle")
                Button("Retry saved text search") {
                    actionTask?.cancel()
                    actionTask = Task { await sources.search(force: true) }
                }
            }
            if let page = currentPage {
                let hits = options.separateHits(in: page, cardMemoryIDs: Set(viewModel.visibleItems.map(\.id)))
                if !hits.isEmpty || options.sourceTextOnly || options.includeHistory {
                    if !options.sourceTextOnly {
                        Text(options.includeHistory ? "Saved passages & history" : "More saved passages")
                            .font(.headline)
                    }
                    if hits.isEmpty {
                        Text(sources.canLoadMore
                             ? "No additional passages on this page. Load more to continue searching retained matches."
                             : "No additional matching saved text. A missing match does not prove something was never recorded.")
                            .foregroundStyle(RememberPalette.secondaryText)
                            .accessibilityIdentifier("search-no-passages")
                    }
                    ForEach(hits) { hit in
                        Button { open(hit, page: page) } label: {
                            SourceEvidenceResultRow(hit: hit)
                                .padding(.horizontal, 14)
                                .background(RememberPalette.surface, in: .rect(cornerRadius: 16))
                        }
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("search-passage-\(hit.sourceSequence)-\(hit.id.field.rawValue)-\(hit.id.ordinal)")
                    }
                }
                if sources.canLoadMore {
                    Button("Show more saved passages") {
                        actionTask?.cancel()
                        actionTask = Task { await sources.loadMore() }
                    }
                }
            }
        }
    }

    private func open(_ hit: SourceEvidenceHit, page: SourceEvidencePage) {
        selection = Selection(hit: hit, sequence: page.throughSequence)
        showsSource = true
    }
}
