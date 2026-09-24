import Foundation

struct HistoryInvariantReceipt: Codable {
    let schemaVersion: Int
    let batchSHA256: String
    let bindingsSHA256: String
    let artifacts: [String: String]
}

enum HistoryInvariants {
    static func runBound(output: URL, input: URL, bindings: URL) async throws {
        try HistoryProbe.validateOutput(output)
        let batchHash = diagnosticHash(try Data(contentsOf: input))
        let bindingsHash = diagnosticHash(try Data(contentsOf: bindings))
        let receiptURL = output.appendingPathComponent("history-invariants.bound.receipt.json")
        func artifactURL(_ path: String) throws -> URL {
            let parts = path.split(separator: "/", omittingEmptySubsequences: false)
            if parts.count == 1 {
                try diagnosticRequire(["invariants.receipt.json", "history-invariants.json"].contains(path),
                                      "unknown invariant artifact")
            } else {
                try diagnosticRequire(parts.count == 2 && ["ledger.json", "synthetic-ledger.json"].contains(String(parts[1])),
                                      "invalid invariant artifact path")
                let name = String(parts[0])
                let key = name.hasPrefix("history-invariants-") ? "history-invariants" : "invariants"
                _ = try HistoryProbe.checkedAttempt(name, key: key, output: output)
            }
            return output.appendingPathComponent(path)
        }
        if FileManager.default.fileExists(atPath: receiptURL.path) {
            let saved = try JSONDecoder().decode(HistoryInvariantReceipt.self, from: Data(contentsOf: receiptURL))
            try diagnosticRequire(saved.schemaVersion == 1 && saved.batchSHA256 == batchHash
                && saved.bindingsSHA256 == bindingsHash && saved.artifacts.count == 5,
                "invariant resume identity mismatch")
            for (path, expected) in saved.artifacts {
                let actual = diagnosticHash(try Data(contentsOf: artifactURL(path)))
                try diagnosticRequire(actual == expected, "invariant resume artifact mismatch")
            }
            return
        }
        try await DiagnosticInvariants.run(output: output)
        try await run(output: output)
        let production = try JSONDecoder().decode([String: String].self,
            from: Data(contentsOf: output.appendingPathComponent("invariants.receipt.json")))
        let history = try JSONDecoder().decode([String: String].self,
            from: Data(contentsOf: output.appendingPathComponent("history-invariants.json")))
        guard let productionAttempt = production["attempt"], let historyAttempt = history["attempt"] else {
            throw DiagnosticFailure(description: "invariant reports lack attempts")
        }
        let paths = ["invariants.receipt.json", "history-invariants.json", "\(productionAttempt)/ledger.json",
                     "\(historyAttempt)/ledger.json", "\(historyAttempt)/synthetic-ledger.json"]
        var artifacts: [String: String] = [:]
        for path in paths { artifacts[path] = diagnosticHash(try Data(contentsOf: artifactURL(path))) }
        let receipt = HistoryInvariantReceipt(schemaVersion: 1, batchSHA256: batchHash,
            bindingsSHA256: bindingsHash, artifacts: artifacts)
        try diagnosticJSON(receipt).write(to: receiptURL, options: .atomic)
    }

    static func run(output: URL) async throws {
        let root = output.appendingPathComponent("history-invariants-\(UUID().uuidString)")
        let harness = try DiagnosticHarness(root: root)
        var passed: [String] = []
        func check(_ name: String, _ condition: Bool) throws {
            try diagnosticRequire(condition, "history invariant failed: \(name)")
            passed.append(name)
        }
        func rejected(_ operation: () throws -> Void) -> Bool {
            do { try operation(); return false } catch { return true }
        }
        func candidates(_ events: [ProvenanceEvent], _ scope: HistoryScope = .current,
                        sequence: Int64? = nil, tombstones: Set<UUID> = []) throws -> [HistoryCandidate] {
            try HistoryIndex.candidates(events: events, request: HistoryRequest(scope: scope,
                throughSequence: sequence ?? events.last?.sequence ?? 0, tombstonedSourceIDs: tombstones))
        }
        do {
            let source = DiagnosticSource(id: "history-invariant-a", text: "Original permit is violet.", modality: "note")
            try await harness.apply(DiagnosticCommand(id: "capture", kind: "capture", source: source,
                target: nil, text: nil, assignments: nil, expectedState: [:]))
            let first = try await harness.store.provenanceEvents()
            let initial = try candidates(first)
            try check("capture-source-evidence", initial.count == 1 && initial[0].quote == source.text)
            try check("empty-prefix", try candidates(first, sequence: 0).isEmpty)
            let id = diagnosticID(source.id)
            try await harness.apply(DiagnosticCommand(id: "revise", kind: "revise", source: nil,
                target: source.id, text: "Replacement permit is amber.", assignments: nil, expectedState: [:]))
            let revised = try await harness.store.provenanceEvents()
            let current = try candidates(revised)
            let history = try candidates(revised, .includeHistory)
            try check("revision-current-excludes-old", current.count == 1 && current[0].revision == 1)
            try check("revision-history-retained", history.count == 2 && Set(history.map(\.versionID)).count == 2)
            try check("no-future-revision", try candidates(revised, sequence: first.last!.sequence!) == initial)
            try await harness.store.delete(id: id)
            let archived = try await harness.store.provenanceEvents()
            try check("production-delete-is-archive", archived.last?.kind == .archive)
            try check("archive-current-empty", try candidates(archived).isEmpty)
            let archivedHistory = try candidates(archived, .includeHistory)
            try check("archive-history-retained", archivedHistory.count == 2 && archivedHistory.allSatisfy(\.isArchived))
            try check("tombstone-fail-closed", try candidates(archived, .includeHistory, tombstones: [id]).isEmpty)
            try await harness.store.setArchived(id: id, archived: false)
            let restored = try await harness.store.provenanceEvents()
            try check("restore-current", try candidates(restored).map(\.id) == current.map(\.id))
            try await harness.apply(DiagnosticCommand(id: "correct", kind: "correct", source: nil,
                target: source.id, text: nil, assignments: [source.id], expectedState: [:]))
            let corrected = try await harness.store.provenanceEvents()
            try check("organization-correction-preserves-evidence", try candidates(corrected) == current)
            try await harness.reopen()
            let reopened = try await harness.store.provenanceEvents()
            try check("sqlite-reopen-deterministic", try candidates(reopened, .includeHistory) == candidates(corrected, .includeHistory))
            let ledgerData = try diagnosticJSON(reopened)
            try ledgerData.write(to: root.appendingPathComponent("ledger.json"), options: .atomic)
            try await harness.close()

            // Synthetic ledger snapshots cover states absent from DiagnosticCommand.
            // Their payloads/types and sequence replay are production types; no originals
            // or extractors are accessed, and no model is loaded.
            var original = try first[0].payload().memory!
            original.extractedText = nil
            original.userCaption = nil
            original.summary = "Generated summary must never be source evidence."
            func event(_ kind: ProvenanceKind, _ memory: MemoryItem, _ sequence: Int64,
                       reference: UUID? = nil) throws -> ProvenanceEvent {
                var payload = ProvenancePayload()
                payload.memory = memory
                payload.sourceRevisionID = reference
                payload.sourceFilename = memory.originalFilename
                var event = try ProvenanceEvent(kind: kind, memoryID: memory.id, payload: payload,
                    timestamp: Date(timeIntervalSince1970: Double(sequence)),
                    id: diagnosticID("history-synthetic-\(sequence)"))
                event.sequence = sequence
                return event
            }
            let imported = try event(.imported, original, 1)
            try check("summary-not-evidence", try candidates([imported]).isEmpty)
            var enriched = original
            enriched.extractedText = "Late transcript contains cobalt."
            let enrichment = try event(.enrichment, enriched, 2, reference: imported.id)
            let late = try candidates([imported, enrichment])
            try check("late-enrichment-boundary", try candidates([imported, enrichment], sequence: 1).isEmpty)
            try check("import-gap-honest", late.count == 1 && late[0].importedHistoryGap)
            try check("snapshot-revision-association", late[0].versionID == imported.id && late[0].snapshotID == enrichment.id)
            try check("missing-assets-locators-honest", late[0].originalAssetAvailability == "unavailable"
                && late[0].mediaLocatorAvailability == "unavailable" && late[0].locatorAvailability == "retained-ledger-text")
            var replacement = enriched
            replacement.originalFilename = "new.txt"
            replacement.extractedText = "Current revision contains silver."
            let revision = try event(.revision, replacement, 3, reference: imported.id)
            enriched.extractedText = "Old revision late transcript contains copper."
            let oldEnrichment = try event(.enrichment, enriched, 4, reference: imported.id)
            let lateOldEvents = [imported, enrichment, revision, oldEnrichment]
            let lateOldCurrent = try candidates(lateOldEvents)
            let lateOldHistory = try candidates(lateOldEvents, .includeHistory)
            try check("late-old-enrichment-does-not-replace-current", lateOldCurrent.count == 1
                && lateOldCurrent[0].quote == replacement.extractedText)
            try check("late-old-enrichment-associated", lateOldHistory[0].versionID == imported.id
                && lateOldHistory[0].snapshotID == oldEnrichment.id)
            try check("old-prefix-does-not-use-future-enrichment", try candidates(lateOldEvents, sequence: 2) == late)
            var duplicate = replacement
            duplicate.originalFilename = "duplicate.txt"
            let duplicateRevision = try event(.revision, duplicate, 5, reference: revision.id)
            let duplicates = try candidates(lateOldEvents + [duplicateRevision], .includeHistory)
            try check("duplicate-text-distinct-version-identities", duplicates.count == 3
                && duplicates[1].quote == duplicates[2].quote && duplicates[1].id != duplicates[2].id)
            let filtered = try HistoryIndex.candidates(events: lateOldEvents,
                request: HistoryRequest(throughSequence: 4, sourceIDs: []))
            try check("empty-source-filter", filtered.isEmpty)
            let zero = try HistoryIndex.candidates(events: lateOldEvents,
                request: HistoryRequest(throughSequence: 4, limit: 0))
            try check("zero-limit", zero.isEmpty)
            try check("negative-limit-rejected", rejected {
                _ = try HistoryIndex.candidates(events: lateOldEvents, request: HistoryRequest(throughSequence: 4, limit: -1))
            })
            try check("duplicate-event-rejected", rejected { _ = try candidates([imported, imported]) })
            let dangling = try event(.enrichment, enriched, 2, reference: diagnosticID("absent"))
            try check("dangling-enrichment-rejected", rejected { _ = try candidates([imported, dangling]) })
            let mismatched = try event(.enrichment, replacement, 2, reference: imported.id)
            try check("cross-version-enrichment-rejected", rejected { _ = try candidates([imported, mismatched]) })
            let repeatedImport = try event(.imported, original, 2)
            try check("duplicate-import-rejected", rejected { _ = try candidates([imported, repeatedImport]) })
            let repeatedCapture = try event(.capture, original, 2)
            try check("duplicate-capture-rejected", rejected { _ = try candidates([imported, repeatedCapture]) })
            let orphanRevision = try event(.revision, replacement, 1)
            try check("orphan-revision-rejected", rejected { _ = try candidates([orphanRevision]) })
            let staleRevision = try event(.revision, duplicate, 5, reference: imported.id)
            try check("stale-revision-predecessor-rejected", rejected { _ = try candidates(lateOldEvents + [staleRevision]) })
            var archivedMemory = original
            archivedMemory.isArchived = true
            let orphanArchive = try event(.archive, archivedMemory, 2)
            try check("archive-without-source-reference-rejected", rejected { _ = try candidates([imported, orphanArchive]) })
            let silentArchive = try event(.metadata, archivedMemory, 2, reference: imported.id)
            try check("metadata-cannot-change-archive-state", rejected { _ = try candidates([imported, silentArchive]) })
            let syntheticData = try diagnosticJSON(lateOldEvents + [duplicateRevision])
            try syntheticData.write(to: root.appendingPathComponent("synthetic-ledger.json"), options: .atomic)
            try diagnosticJSON(["schemaVersion": "1", "status": "passed", "count": String(passed.count),
                "attempt": root.lastPathComponent, "ledgerSHA256": diagnosticHash(ledgerData),
                "syntheticLedgerSHA256": diagnosticHash(syntheticData),
                "checks": passed.joined(separator: "\n")])
                .write(to: output.appendingPathComponent("history-invariants.json"), options: .atomic)
        } catch { try? await harness.close(); throw error }
    }
}
