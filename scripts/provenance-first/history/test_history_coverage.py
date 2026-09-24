from copy import deepcopy
import hashlib
import json
import unittest

import verify_coverage as v


class EvidenceVerification(unittest.TestCase):
    def setUp(self):
        self.source = v.source_uuid("s01")
        self.version = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"
        self.ledger = [dict(id=self.version, sequence=1, kind="capture", memoryID=self.source,
                            payloadJSON=json.dumps(dict(memory=dict(extractedText="The original was blue."))))]
        self.candidate = dict(id=hashlib.sha256(f"{self.source}:{self.version}:{self.version}:extractedText:0".encode()).hexdigest(),
            sourceID=self.source, versionID=self.version, snapshotID=self.version, sourceSequence=1,
            snapshotSequence=1, revision=0, ordinal=0, evidenceField="extractedText", quote="The original was blue.",
            isCurrentVersion=True, locatorAvailability="retained-ledger-text", mediaLocatorAvailability="unavailable",
            originalAssetAvailability="unavailable")

    def verify(self, candidate=None, expected=None):
        v.check_candidates([self.candidate if candidate is None else candidate], self.ledger, 1,
                           {("s01", 0)} if expected is None else expected, {self.source: "s01"})

    def test_valid_evidence(self): self.verify()

    def test_fabricated_quote_rejected(self):
        altered = dict(self.candidate, quote="The original was red.")
        with self.assertRaisesRegex(ValueError, "quote"): self.verify(altered)

    def test_multiline_source_preserves_internal_whitespace(self):
        text = "First line.\r\nSecond  line."
        self.ledger[0]["payloadJSON"] = json.dumps(dict(memory=dict(extractedText=text)))
        self.verify(dict(self.candidate, quote="First line.\nSecond  line."))
        with self.assertRaisesRegex(ValueError, "quote"):
            self.verify(dict(self.candidate, quote="First line. Second line."))

    def test_future_sequence_rejected(self):
        with self.assertRaisesRegex(ValueError, "sequence"): self.verify(dict(self.candidate, snapshotSequence=2))

    def test_wrong_version_rejected(self):
        with self.assertRaisesRegex(ValueError, "revision"): self.verify(dict(self.candidate, revision=1))

    def test_generated_summary_rejected(self):
        with self.assertRaisesRegex(ValueError, "metadata"): self.verify(dict(self.candidate, evidenceField="summary"))

    def test_fabricated_media_locator_rejected(self):
        with self.assertRaisesRegex(ValueError, "locator"): self.verify(dict(self.candidate, mediaLocatorAvailability="page1"))

    def test_missing_expected_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing"): self.verify(expected={("s01", 0), ("s02", 0)})

    def test_no_cross_source_duplicate_identity(self):
        self.assertNotEqual(v.source_uuid("s01"), v.source_uuid("s02"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            v.check_candidates([self.candidate, self.candidate], self.ledger, 1, {("s01", 0)}, {self.source: "s01"})


if __name__ == "__main__": unittest.main()
