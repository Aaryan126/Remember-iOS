"""Tamper checks on synthetic receipts; real ledger execution is a separate check."""
import json
from pathlib import Path
import unittest

import checkpoint as cp
from fixtures import InvalidFixture, load, sha
import test_checkpoint


class NativeVerificationTests(unittest.TestCase):
    setUp = test_checkpoint.CheckpointTests.setUp

    def prepare_native(self):
        cp.run(self.work)
        self.folder = self.work / "runs/checkpoint1"
        self.project = self.folder / "ledger/project"
        package = self.root / "local-package"
        package.mkdir()
        (package / "Package.swift").write_text("Synthetic dependency.")
        native = self.project / "ProvenanceFirstProbe.xcodeproj/project.pbxproj"
        native.parent.mkdir(parents=True)
        native.write_text("relativePath = " + json.dumps(str(package)) + ";")
        source = self.root / "native-source.swift"
        source.write_text("Synthetic binding, not compiled.")
        binding = {"production": {"native-source.swift": sha(source.read_bytes())}, "harness": {}, "tooling": {},
                   "generated": {"ProvenanceFirstProbe.xcodeproj/project.pbxproj": sha(native.read_bytes())},
                   "grdb": {"Package.swift": sha((package / "Package.swift").read_bytes())}}
        binding_path = self.project / "Sources/bindings.json"
        cp.atomic(binding_path, binding)
        batch_hash = sha((self.folder / "input.json").read_bytes())
        binding_hash = sha(binding_path.read_bytes())
        self.output = self.folder / "output"
        self.receipt_paths = []
        for run in load(self.folder / "input.json")["runs"]:
            attempt = run["id"] + "-attempt"
            ledger = self.output / attempt / "ledger.json"
            cp.atomic(ledger, [{"synthetic": True}])
            receipt = {"id": run["id"], "batchSHA256": batch_hash, "bindingsSHA256": binding_hash,
                       "restartVerified": True, "prefixCount": 12, "historicalPrefixesVerified": 12,
                       "prefixes": [{"id": e["id"]} for e in run["events"]], "attempt": attempt,
                       "ledgerSHA256": sha(ledger.read_bytes()), "ledgerCount": 1}
            path = self.output / (sha(run["id"].encode()) + ".receipt.json")
            cp.atomic(path, receipt)
            self.receipt_paths.append(path)
        ledger = self.output / "invariant-attempt/ledger.json"
        cp.atomic(ledger, [{"syntheticInvariant": True}])
        cp.atomic(self.output / "invariants.receipt.json", {"status": "passed", "checks": "1",
                  "attempt": "invariant-attempt", "ledgerSHA256": sha(ledger.read_bytes())})
        cp.atomic(self.output / "invariant-execution.json", {"batchSHA256": batch_hash, "bindingsSHA256": binding_hash,
                  "invariantReceiptSHA256": sha((self.output / "invariants.receipt.json").read_bytes()), "executedInvariants": True})
        cp.atomic(self.output / "status.json", {"status": "complete", "completed": "24",
                  "batchSHA256": batch_hash, "bindingsSHA256": binding_hash})

    def test_complete_receipt_collection(self):
        self.prepare_native()
        result = cp.verify_native(self.work)
        self.assertEqual(result["prefixes"], 288)
        self.assertFalse(result["semanticQualityMeasured"])

    def test_changed_bound_source_rejected(self):
        self.prepare_native()
        (self.root / "native-source.swift").write_text("Changed")
        with self.assertRaisesRegex(InvalidFixture, "binding changed"):
            cp.verify_native(self.work)

    def test_changed_ledger_rejected(self):
        self.prepare_native()
        receipt = load(self.receipt_paths[0])
        cp.atomic(self.output / receipt["attempt"] / "ledger.json", [])
        with self.assertRaisesRegex(InvalidFixture, "ledger hash"):
            cp.verify_native(self.work)

    def test_incomplete_historical_replay_rejected(self):
        self.prepare_native()
        receipt = load(self.receipt_paths[0])
        receipt["historicalPrefixesVerified"] = 11
        cp.atomic(self.receipt_paths[0], receipt)
        with self.assertRaisesRegex(InvalidFixture, "prefix/restart"):
            cp.verify_native(self.work)

    def test_forged_receipt_path_rejected(self):
        self.prepare_native()
        receipt = load(self.receipt_paths[0])
        receipt["attempt"] = "../../../../escape"
        cp.atomic(self.receipt_paths[0], receipt)
        with self.assertRaisesRegex(InvalidFixture, "path escape"):
            cp.verify_native(self.work)

    def test_paused_native_cannot_pass(self):
        self.prepare_native()
        state = load(self.output / "status.json")
        state["status"] = "paused"
        cp.atomic(self.output / "status.json", state)
        with self.assertRaisesRegex(InvalidFixture, "incomplete"):
            cp.verify_native(self.work)

    def test_invariant_execution_must_match_build(self):
        self.prepare_native()
        path = self.output / "invariant-execution.json"
        value = load(path)
        value["bindingsSHA256"] = "older-build"
        cp.atomic(path, value)
        with self.assertRaisesRegex(InvalidFixture, "not bound"):
            cp.verify_native(self.work)

    def test_resume_path_checked_before_swift_launch(self):
        self.prepare_native()
        path = self.receipt_paths[0]
        value = load(path)
        value["attempt"] = "../../escape"
        cp.atomic(path, value)
        with self.assertRaisesRegex(InvalidFixture, "path escape"):
            cp.verify_native_paths(self.output)
