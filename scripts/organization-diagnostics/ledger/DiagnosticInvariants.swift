import Foundation
import GRDB

enum DiagnosticInvariants {
    static func run(output: URL) async throws {
        let root = output.appendingPathComponent("invariants-\(UUID().uuidString)")
        let harness = try DiagnosticHarness(root: root)
        var expected: [String: DiagnosticExpected] = [:]
        var checks = 0
        func check() async throws {
            let events = try await harness.store.provenanceEvents()
            try harness.verifyLedger(events)
            try await harness.verifyState(expected, events: events, checkStore: true)
            checks += 1
        }
        func expectRejection(_ operation: () async throws -> Void) async throws {
            let before = try await harness.store.provenanceEvents().count
            do {
                try await operation()
                throw DiagnosticFailure(description: "invalid command unexpectedly accepted")
            } catch is ProvenanceError { }
            let after = try await harness.store.provenanceEvents().count
            try diagnosticRequire(before == after, "rejected command appended history")
            try await check()
        }
        do {
            for index in 1...3 {
                let name = "localc0\(index)"
                let text = "Fictional invariant source \(index)"
                expected[name] = DiagnosticExpected(memberships: ["t:c0\(index)"], archived: false,
                    textSHA256: diagnosticHash(Data(text.utf8)), revision: 0)
                try await harness.apply(DiagnosticCommand(id: "capture-\(index)", kind: "capture",
                    source: DiagnosticSource(id: name, text: text, modality: "text"), target: nil,
                    text: nil, assignments: nil, expectedState: expected))
                try await check()
            }
            let a = diagnosticID("localc01"), b = diagnosticID("localc02"), c = diagnosticID("localc03")
            // Duplicate capture is idempotent even though policy traces reject duplicate input IDs.
            let existing = try await harness.store.databasePool.read { try MemoryItem.fetchOne($0, key: a) }
            let beforeDuplicate = try await harness.store.provenanceEvents().count
            try await harness.store.insertIfNeeded(existing!)
            let afterDuplicate = try await harness.store.provenanceEvents().count
            try diagnosticRequire(afterDuplicate == beforeDuplicate, "duplicate capture appended history")
            try await check()

            let merged = diagnosticID("invariant-merged")
            var mergePayload = ProvenancePayload()
            mergePayload.clusterID = merged
            mergePayload.title = "Explicit diagnostic merge"
            mergePayload.parents = [a, b]
            mergePayload.assignments = [a.uuidString: [merged], b.uuidString: [merged]]
            mergePayload.previousAssignments = [a.uuidString: [a], b.uuidString: [b]]
            let merge = try ProvenanceEvent(kind: .merge, origin: "user", payload: mergePayload)
            try await harness.store.appendProvenance(merge, expectedSequence: await harness.store.provenanceEvents().last?.sequence)
            harness.pinned.formUnion([a, b])
            expected["localc01"]?.memberships = ["invariant-merged"]
            expected["localc02"]?.memberships = ["invariant-merged"]
            try await check()
            var snapshot = try ProvenanceSnapshot.replay(await harness.store.provenanceEvents())
            try diagnosticRequire(snapshot.ancestors(of: merged) == [merged, a, b]
                && snapshot.clusters[a]?.retired == true && snapshot.clusters[b]?.retired == true, "merge lineage/retirement differs")
            try await harness.store.renameProjectCluster(id: c, title: "Unrelated user correction")
            try await check()
            try await harness.store.undoProjectEvent(id: merge.id)
            expected["localc01"]?.memberships = ["t:c01"]
            expected["localc02"]?.memberships = ["t:c02"]
            try await check()
            snapshot = try ProvenanceSnapshot.replay(await harness.store.provenanceEvents())
            try diagnosticRequire(snapshot.blockedPairs.contains(ProvenanceSnapshot.pair(a, b))
                && snapshot.clusters[c]?.title == "Unrelated user correction"
                && snapshot.clusters[a]?.retired == false && snapshot.clusters[b]?.retired == false,
                "merge undo lost correction/block or failed to restore parents")
            try await expectRejection { try await harness.store.undoProjectEvent(id: merge.id) }

            try await harness.store.assignProjectMemory(id: b, clusters: [a])
            expected["localc02"]?.memberships = ["t:c01"]
            try await check()
            let splitID = diagnosticID("invariant-split")
            var splitPayload = ProvenancePayload()
            splitPayload.clusterID = a
            splitPayload.parents = [splitID]
            splitPayload.title = "Explicit diagnostic split"
            splitPayload.assignments = [b.uuidString: [splitID]]
            splitPayload.previousAssignments = [b.uuidString: [a]]
            let proposal = try ProvenanceEvent(kind: .splitProposal, payload: splitPayload)
            try await harness.store.appendProvenance(proposal, expectedSequence: await harness.store.provenanceEvents().last?.sequence)
            try await check() // Proposal alone must leave assignments unchanged.
            try await harness.store.resolveProjectSplit(id: proposal.id, accept: true)
            expected["localc02"]?.memberships = ["invariant-split"]
            try await check()
            let split = try await harness.store.provenanceEvents().last!
            try await harness.store.undoProjectEvent(id: split.id)
            expected["localc02"]?.memberships = ["t:c01"]
            try await check()
            try await expectRejection { try await harness.store.resolveProjectSplit(id: proposal.id, accept: true) }

            try await harness.store.setArchived(id: b, archived: true)
            expected["localc02"]?.archived = true
            try await check()
            let beforeArchive = try await harness.store.provenanceEvents().count
            try await harness.store.setArchived(id: b, archived: true)
            let afterArchive = try await harness.store.provenanceEvents().count
            try diagnosticRequire(afterArchive == beforeArchive, "duplicate archive appended history")
            try await check()
            try await expectRejection { try await harness.store.assignProjectMemory(id: b, clusters: [c]) }
            try await harness.store.setArchived(id: b, archived: false)
            expected["localc02"]?.archived = false
            try await check()

            let staleProposal = try ProvenanceEvent(kind: .splitProposal, payload: splitPayload)
            try await harness.store.appendProvenance(staleProposal, expectedSequence: await harness.store.provenanceEvents().last?.sequence)
            try await check()
            try await harness.store.assignProjectMemory(id: b, clusters: [c])
            expected["localc02"]?.memberships = ["t:c03"]
            try await check()
            try await expectRejection { try await harness.store.resolveProjectSplit(id: staleProposal.id, accept: true) }

            // A shared thread archive hides its grouping while retaining every memory and assignment.
            try await harness.store.setProjectThreadArchived(id: c, archived: true)
            harness.archivedThreads.insert(c)
            try await check()
            try await expectRejection { try await harness.store.assignProjectMemory(id: a, clusters: [c]) }
            try await harness.store.setProjectThreadArchived(id: c, archived: false)
            harness.archivedThreads.remove(c)
            try await check()

            try await harness.store.assignProjectMemory(id: b, clusters: [a])
            expected["localc02"]?.memberships = ["t:c01"]
            try await check()
            let placement = try await harness.store.provenanceEvents().last!
            try await harness.store.assignProjectMemory(id: b, clusters: [c])
            expected["localc02"]?.memberships = ["t:c03"]
            try await check()
            try await expectRejection { try await harness.store.undoProjectEvent(id: placement.id) }

            let staleSequence = try await harness.store.provenanceEvents().last?.sequence
            try await harness.store.renameProjectCluster(id: c, title: "Later correction")
            try await check()
            try await expectRejection {
                try await harness.store.appendProvenance(ProvenanceEvent(kind: .checkpoint, payload: ProvenancePayload()),
                                                        expectedSequence: staleSequence)
            }
            // Exercise actual SQLite append-only triggers. No production table content is changed.
            for statement in ["UPDATE provenanceEvent SET origin = 'invalid'", "DELETE FROM provenanceEvent"] {
                do {
                    try await harness.store.databasePool.write { try $0.execute(sql: statement) }
                    throw DiagnosticFailure(description: "append-only trigger failed")
                } catch is DatabaseError { }
                try await check()
            }
            try await harness.reopen()
            try await check()
            let ledger = try diagnosticJSON(await harness.store.provenanceEvents())
            try ledger.write(to: root.appendingPathComponent("ledger.json"), options: .atomic)
            try await harness.close()
            try diagnosticJSON(["status": "passed", "checks": String(checks), "attempt": root.lastPathComponent,
                                "ledgerSHA256": diagnosticHash(ledger)])
                .write(to: output.appendingPathComponent("invariants.receipt.json"), options: .atomic)
        } catch {
            try? await harness.close()
            throw error
        }
    }
}
