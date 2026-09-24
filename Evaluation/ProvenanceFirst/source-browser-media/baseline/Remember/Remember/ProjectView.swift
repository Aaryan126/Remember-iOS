import SwiftUI

struct ProjectView: View {
    let model: ProjectViewModel
    let onAsk: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Namespace private var topicTransition
    @State private var query = ""
    @State private var isSearchPresented = false
    @State private var selectedThread: ThreadDestination?

    private struct ThreadDestination: Hashable {
        // A fresh presentation must not inherit a previously opened thread's detail state.
        let id = UUID()
        let threadID: UUID
        let fromMap: Bool
    }

    private var showsSearchResults: Bool {
        !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Group {
                    if model.isLoading {
                        ProgressView("Opening your threads…").frame(maxHeight: .infinity)
                    } else if model.snapshot.memories.isEmpty {
                        ContentUnavailableView("Every memory starts a thread", systemImage: "point.3.connected.trianglepath.dotted",
                            description: Text("Capture a note, photo, or voice memo in Memories. Its story starts here immediately."))
                    } else {
                        ProjectGraphView(model: model, topicTransition: topicTransition) {
                            openThread($0, fromMap: true)
                        }
                    }
                }
                // Keep the map mounted while the inline results cover it.
                .opacity(showsSearchResults ? 0 : 1)
                .allowsHitTesting(!showsSearchResults)
                .accessibilityHidden(showsSearchResults)
                .ignoresSafeArea(.keyboard, edges: .bottom)

                if showsSearchResults {
                    ThreadSearchResultsView(model: model, query: query) { openThread($0, fromMap: false) }
                }
            }
            .rememberCanvas()
            .navigationTitle("")
            .navigationBarTitleDisplayMode(.inline)
            .searchable(text: $query, isPresented: $isSearchPresented,
                        placement: .navigationBarDrawer(displayMode: .always), prompt: "Find a thread")
            .navigationDestination(item: $selectedThread) { destination in
                if destination.fromMap && !reduceMotion {
                    ClusterRiverView(clusterID: destination.threadID, model: model)
                        .id(destination.id)
                        .navigationTransition(.zoom(sourceID: destination.threadID, in: topicTransition))
                } else {
                    ClusterRiverView(clusterID: destination.threadID, model: model)
                        .id(destination.id)
                }
            }
            .toolbar {
                TopLevelToolbar(title: "Threads", onAsk: onAsk)
                ToolbarItem(placement: .secondaryAction) {
                    NavigationLink { SourceEvidenceSearchView(projectModel: model) } label: {
                        Label("Search saved evidence", systemImage: "doc.text.magnifyingglass")
                    }
                    .accessibilityIdentifier("search-saved-evidence")
                }
                ToolbarItem(placement: .secondaryAction) {
                    NavigationLink { ThreadActivityView(model: model) } label: {
                        Label("Activity & decisions", systemImage: "clock.arrow.circlepath")
                    }
                }
                ToolbarItem(placement: .secondaryAction) {
                    NavigationLink { ProjectArchiveView(model: model) } label: { Label("Archive", systemImage: "archivebox") }
                }
            }
            .safeAreaInset(edge: .bottom) { ProjectStatusView(model: model) }
        }
    }

    private func openThread(_ id: UUID, fromMap: Bool) {
        guard selectedThread == nil else { return }
        selectedThread = ThreadDestination(threadID: id, fromMap: fromMap)
    }
}

private struct ThreadSearchResultsView: View {
    let model: ProjectViewModel
    let query: String
    let onSelect: (UUID) -> Void

    var body: some View {
        let directory = ThreadDirectory(snapshot: model.snapshot)
        let results = directory.matching(query)
        List {
            Section {
                ForEach(results) { thread in
                    Button { onSelect(thread.id) } label: {
                        VStack(alignment: .leading, spacing: 5) {
                            Text(thread.title).font(.body.weight(.medium))
                                .fixedSize(horizontal: false, vertical: true)
                            Text("\(thread.memoryCount) \(thread.memoryCount == 1 ? "memory" : "memories")")
                                .font(.subheadline).foregroundStyle(RememberPalette.secondaryText)
                        }.padding(.vertical, 6)
                    }
                    .buttonStyle(.plain)
                    .accessibilityHint("Opens thread history")
                    .accessibilityLabel(thread.title)
                    .accessibilityValue("\(thread.memoryCount) \(thread.memoryCount == 1 ? "memory" : "memories")")
                    .accessibilityIdentifier("project-topic-\(thread.id)")
                }
            } header: {
                Text("Matching threads")
            }
        }
        .overlay {
            if model.isLoading { ProgressView("Opening your threads…") }
            else if results.isEmpty {
                ContentUnavailableView(directory.entries.isEmpty ? "No active threads" : "No matching threads",
                    systemImage: "magnifyingglass",
                    description: Text(directory.entries.isEmpty
                        ? "Capture a memory or restore a thread from Archive."
                        : "Try another name. Archived threads are in Settings → Archive."))
            }
        }
        .rememberGroupedList()
        .scrollDismissesKeyboard(.interactively)
        .accessibilityIdentifier("thread-search-results")
    }
}
