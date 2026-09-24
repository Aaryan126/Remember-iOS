"""Synthetic native receipt verification, not a substitute for actual replay."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pc_ledger as ledger
from pc_native import c


class ReplayTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="remember-pf2-replay-test-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        self.output = root / "native/output"
        self.public = root / "public"
        bindings = root / "bindings.json"
        c.pf1.atomic(bindings, {"synthetic": True})
        c.pf1.atomic(self.public / "selection.json", {"synthetic": True})
        self.runs = [{"id": f"synthetic-{i:02}", "events": [{"id": f"e{j:02}"} for j in range(12)]} for i in range(96)]
        batch = {"schemaVersion": 1, "runs": self.runs}
        c.pf1.atomic(root / "native/input.json", batch)
        self.receipt = dict(batchSHA256=c.digest(root / "native/input.json"), bindingsSHA256=c.digest(bindings),
                            manifestSHA256="synthetic", selectionSHA256=c.digest(self.public / "selection.json"), BAliases={})
        c.pf1.atomic(self.public / "ledger-input.json", self.receipt)
        for target, name, value in ((ledger, "NATIVE", root / "native"), (ledger, "BINDINGS", bindings),
                                    (ledger.runner, "PUBLIC", self.public)):
            override = patch.object(target, name, value)
            override.start()
            self.addCleanup(override.stop)
        for target, name, value in ((ledger.runner, "verify_base", "synthetic"), (ledger, "batch", (batch, {}))):
            override = patch.object(target, name, return_value=value)
            override.start()
            self.addCleanup(override.stop)

    def receipt_for(self, run):
        attempt = run["id"] + "-attempt"
        path = self.output / attempt / "ledger.json"
        c.pf1.atomic(path, [{"synthetic": True}])
        receipt = {"id": run["id"], "batchSHA256": self.receipt["batchSHA256"],
                   "bindingsSHA256": self.receipt["bindingsSHA256"], "restartVerified": True,
                   "prefixCount": 12, "historicalPrefixesVerified": 12, "prefixes": run["events"],
                   "attempt": attempt, "ledgerSHA256": c.digest(path), "ledgerCount": 1}
        target = self.output / (c.text_hash(run["id"]) + ".receipt.json")
        c.pf1.atomic(target, receipt)
        return target, receipt

    def complete(self):
        for run in self.runs: self.receipt_for(run)
        c.pf1.atomic(self.output / "status.json", {**self.receipt, "status": "complete", "completed": "96"})
        path = self.output / "invariant-attempt/ledger.json"
        c.pf1.atomic(path, [])
        c.pf1.atomic(self.output / "invariants.receipt.json", dict(status="passed", checks="31",
                      attempt="invariant-attempt", ledgerSHA256=c.digest(path)))
        c.pf1.atomic(self.output / "invariant-execution.json", {**self.receipt,
                      "invariantReceiptSHA256": c.digest(self.output / "invariants.receipt.json")})

    def test_missing_output_is_resumable_not_complete(self):
        self.assertEqual(ledger.verify()["completed"], 0)
        with self.assertRaises(FileNotFoundError): ledger.verify(complete=True)

    def test_one_receipt_verified(self):
        self.receipt_for(self.runs[0])
        self.assertEqual(ledger.verify()["completed"], 1)

    def test_all_receipts_and_invariants_required(self):
        self.complete()
        self.assertEqual(ledger.verify(complete=True)["completed"], 96)

    def test_changed_ledger_rejected(self):
        _, receipt = self.receipt_for(self.runs[0])
        c.pf1.atomic(self.output / receipt["attempt"] / "ledger.json", [])
        with self.assertRaisesRegex(ValueError, "ledger mismatch"): ledger.verify()

    def test_wrong_prefix_rejected(self):
        path, receipt = self.receipt_for(self.runs[0])
        receipt["prefixes"] = [{"id": "wrong"}] * 12
        c.pf1.atomic(path, receipt)
        with self.assertRaisesRegex(ValueError, "prefix identity"): ledger.verify()

    def test_escape_rejected(self):
        path, receipt = self.receipt_for(self.runs[0])
        receipt["attempt"] = "../escape"
        c.pf1.atomic(path, receipt)
        with self.assertRaisesRegex(ValueError, "path escape"): ledger.verify()

    def test_changed_selection_rejected(self):
        c.pf1.atomic(self.public / "selection.json", {"changed": True})
        with self.assertRaisesRegex(ValueError, "comparison identity"): ledger.verify()

    def test_stale_invariant_binding_rejected(self):
        self.complete()
        path = self.output / "invariant-execution.json"
        receipt = c.read(path)
        receipt["batchSHA256"] = "old"
        c.pf1.atomic(path, receipt)
        with self.assertRaisesRegex(ValueError, "stale"): ledger.verify(complete=True)

    def test_incomplete_status_rejected(self):
        self.complete()
        path = self.output / "status.json"
        receipt = c.read(path)
        receipt["completed"] = "95"
        c.pf1.atomic(path, receipt)
        with self.assertRaisesRegex(ValueError, "incomplete"): ledger.verify(complete=True)


if __name__ == "__main__": unittest.main()
