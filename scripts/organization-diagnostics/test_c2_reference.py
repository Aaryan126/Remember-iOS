"""Deterministic hand-vector checks of the native production placement adaptation."""
import math
import platform
from pathlib import Path
import tempfile
import unittest

from c2_reference import ADAPTER, INTELLIGENCE, ReferenceClient, _production_blocks, build


TOPIC = "Marine coral restoration protects ocean reefs and coastal biodiversity."
OTHER = "Sourdough fermentation develops bread flavor through yeast and flour."


def source(identifier, text=TOPIC, contextual=None, sentence=None, space="fixture-dual-v1"):
    return {"id": identifier, "text": text, "embedding": {
        "contextual": [1.0, 0.0] if contextual is None else contextual,
        "sentence": [1.0, 0.0] if sentence is None else sentence,
        "space": space}}


@unittest.skipUnless(platform.system() == "Darwin" and platform.machine() == "arm64",
                     "Native arm64 Mac Swift/NaturalLanguage reference")
class NativeReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="c2-reference-tests-")
        cls.runpath = Path(cls.temporary.name)
        cls.executable = build(cls.runpath)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.client = ReferenceClient(self.executable, lambda _: None)
        self.addCleanup(self.client.close)

    def test_exact_self_match(self):
        result = self.client(source("new"), {"river": [source("old")]})
        self.assertEqual(result["selected"], ["river"])
        self.assertEqual(result["scores"]["sentenceSimilarity"], 1.0)
        self.assertTrue(result["grounding"][0]["allMembersSupported"])

    def test_unrelated_topic_cannot_be_rescued_by_identical_vectors(self):
        result = self.client(source("new"), {"river": [source("old", OTHER)]})
        self.assertEqual(result["selected"], [])
        self.assertEqual(len(result["candidates"]), 1)
        self.assertFalse(result["candidates"][0]["grounded"])

    def test_two_equal_candidates_are_ambiguous_and_ties_are_lexical(self):
        result = self.client(source("new"), {"z": [source("z-old")], "a": [source("a-old")]})
        self.assertEqual(result["selected"], [])
        self.assertEqual([row["threadID"] for row in result["candidates"]], ["a", "z"])

    def test_missing_source_embedding(self):
        result = self.client({"id": "new", "text": TOPIC, "embedding": None},
                             {"river": [source("old")]})
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["candidates"], [])

    def test_missing_member_embedding(self):
        result = self.client(source("new"), {"river": [{"id": "old", "text": TOPIC}]})
        self.assertEqual(result["candidates"], [])

    def test_member_support_rejects_weak_contextual_match(self):
        result = self.client(source("new"), {"river": [source("old", contextual=[0.8, 0.6])]})
        self.assertEqual(result["candidates"], [])

    def test_member_supported_candidate_below_placement_threshold(self):
        result = self.client(source("new"), {"river": [
            source("old", contextual=[0.93, math.sqrt(1 - 0.93**2)])]})
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["selected"], [])

    def test_request_larger_than_pipe_buffer_and_multiple_responses(self):
        vector = [1.0] + [0.0] * 8191
        new = source("new", contextual=vector, sentence=vector)
        old = source("old", contextual=vector, sentence=vector)
        for _ in range(2):
            self.assertEqual(self.client(new, {"river": [old]})["selected"], ["river"])

    def test_member_semantic_guard(self):
        result = self.client(source("new"), {"river": [source("old", sentence=[0.2, math.sqrt(0.96)])]})
        self.assertEqual(result["candidates"], [])

    def test_candidate_semantic_score_guard(self):
        result = self.client(source("new"), {"river": [source("old", sentence=[0.35, math.sqrt(1 - 0.35**2)])]})
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["selected"], [])
        self.assertLess(result["candidates"][0]["semanticScore"], 0.4)

    def test_incoherent_members_rejected(self):
        sine = math.sqrt(1 - 0.94**2)
        result = self.client(source("new"), {"river": [
            source("left", contextual=[0.94, sine]),
            source("right", contextual=[0.94, -sine])]})
        self.assertEqual(result["candidates"], [])

    def test_grounding_requires_every_member(self):
        result = self.client(source("new"), {"river": [source("old", OTHER), source("other")]})
        self.assertEqual(result["selected"], [])
        self.assertFalse(result["grounding"][0]["allMembersSupported"])

    def test_incompatible_embedding_spaces(self):
        result = self.client(source("new"), {"river": [source("old", space="unsupported-other-space")]})
        self.assertEqual(result["candidates"], [])

    def test_no_candidates_for_zero_vector_or_empty_cluster(self):
        result = self.client(source("new", contextual=[0, 0]), {"river": [source("old")], "empty": []})
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["candidates"], [])

    def test_callback_and_stable_source_order(self):
        calls = []
        def embed(text):
            calls.append(text)
            return source("unused")["embedding"]
        with ReferenceClient(self.executable, embed) as client:
            result = client({"id": "new", "text": TOPIC}, {"river": [
                {"id": "z", "text": TOPIC}, {"id": "a", "text": TOPIC}]})
        self.assertEqual(len(calls), 3)
        self.assertEqual(result["selected"], ["river"])
        self.assertEqual([row["sourceID"] for row in result["grounding"][0]["members"]], ["a", "z"])
        self.assertIsNotNone(client.process.poll())

    def test_build_idempotence_and_exact_extracted_source(self):
        self.assertEqual(build(self.runpath), self.executable)
        generated = (self.runpath / "reference/C2ReferenceCompileUnit.swift").read_text()
        for block in _production_blocks(INTELLIGENCE.read_text()).values():
            self.assertIn(block, generated)
        self.assertTrue(generated.startswith(ADAPTER.read_text()))


if __name__ == "__main__":
    unittest.main()
