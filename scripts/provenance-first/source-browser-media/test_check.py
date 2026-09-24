import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import check


class ArchiveVerificationTests(unittest.TestCase):
    def test_archive_allows_new_app_code_but_not_rewritten_history(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work = root / "followup"
            receipt = root / "prior.json"
            receipt.write_text('{"complete": true}')
            names = ["Remember/Remember/View.swift", "Evaluation/prior/report.md"]
            hashes = {}
            for name in names:
                path = root / name
                archive = work / "baseline" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                archive.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("frozen"); archive.write_text("frozen")
                hashes[name] = check.digest(path)
            receipt.write_text(json.dumps({"complete": True, "hashes": hashes}))
            (work / "baseline.json").write_text(json.dumps({"receiptSHA256": check.digest(receipt), "hashes": hashes}))
            with patch.multiple(check, ROOT=root, WORK=work, RECEIPT=receipt):
                self.assertEqual(check.verify()["archivedFilesVerified"], 2)
                (root / names[0]).write_text("new implementation")
                check.verify()
                (root / names[1]).write_text("rewritten result")
                with self.assertRaises(ValueError): check.verify()

    def test_modified_completion_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            receipt = root / "prior.json"
            receipt.write_text("before")
            (root / "baseline.json").write_text(json.dumps({"receiptSHA256": check.digest(receipt), "hashes": {}}))
            receipt.write_text("after")
            with patch.multiple(check, WORK=root, RECEIPT=receipt):
                with self.assertRaises(ValueError): check.verify()


class ApprovedResourcePolicyTests(unittest.TestCase):
    def setUp(self):
        self.originals = (check.previous.CAP, check.previous.RESOURCE_APPROVAL, check.previous.accounting)
        check.configure_resources()

    def tearDown(self):
        check.previous.CAP, check.previous.RESOURCE_APPROVAL, check.previous.accounting = self.originals

    def test_new_ceiling_retains_conservative_accounting(self):
        g = check.previous.GIB
        value = check.accounting(15*g, 42*g, 3*g, 4*g, g)
        self.assertEqual(value["conservativeGrowthBytes"], 27*g)
        self.assertEqual(value["capBytes"], 28*g)
        self.assertEqual(value["reserveBytes"], 10*g)
        self.assertEqual(check.accounting(40*g, 42*g, 24*g, 3*g)["conservativeGrowthBytes"], 27*g)
        self.assertEqual(check.previous.RESOURCE_APPROVAL, check.RESOURCE_APPROVAL)

    def test_reservations_cannot_cross_ceiling_or_reserve(self):
        g = check.previous.GIB
        with self.assertRaisesRegex(SystemExit, "28 GiB growth cap"):
            check.accounting(15*g, 42*g, 0, 0, g+1)
        with self.assertRaisesRegex(SystemExit, "10 GiB free-space reserve"):
            check.accounting(10*g, 10*g, 0, 0, 1)
        with self.assertRaises(SystemExit):
            check.accounting(40*g, 42*g, 28*g, 1)

    def test_invalid_measurements_are_rejected(self):
        with self.assertRaises(ValueError):
            check.accounting(-1, 0, 0, 0)


if __name__ == "__main__": unittest.main()
