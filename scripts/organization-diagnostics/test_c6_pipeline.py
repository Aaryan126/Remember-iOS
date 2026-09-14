import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import c2_common as c
import c6_review as review
import c6_run as run


def packet():
    return {"queryID": "q" + "a" * 24, "view": "pair", "pair": ["x", "y"],
            "sources": [{"id": "x", "text": "An independent invented source."}, {"id": "y", "text": "Another invented source."}]}


THRESHOLDS = {"baseline": .8, "hybrids": {s: .8 for s in ("17", "29", "41")}}


def scores(value=.9):
    return {"baseline": {"score": value, "eligible": True}, "hybrid": {s: value for s in ("17", "29", "41")}}


def scope(p, verdict):
    return {"queryID": p["queryID"], "verdict": verdict, "evidence": [] if verdict == "abstain" else
            [{"sourceID": s["id"], "quote": s["text"]} for s in p["sources"]]}


class AdapterTests(unittest.TestCase):
    def test_failed_match_is_abstention_not_conflict(self):
        for scorer in run.SCORERS:
            self.assertEqual(run.legacy_prediction(packet(), scores(.2), scorer, THRESHOLDS)["verdict"], "abstain")
            self.assertEqual(run.legacy_prediction(packet(), scores(), scorer, THRESHOLDS)["verdict"], "same_project")

    def test_baseline_eligibility_and_finite_validation(self):
        value = scores()
        value["baseline"]["eligible"] = False
        self.assertEqual(run.legacy_prediction(packet(), value, "baseline", THRESHOLDS)["verdict"], "abstain")
        with self.assertRaises(ValueError):
            run.legacy_prediction(packet(), scores(float("nan")), "17", THRESHOLDS)

    def test_extra_context_not_used_as_legacy_explanation(self):
        p = packet(); p["view"] = "context"
        p["sources"].append({"id": "z", "text": "Visible but unused context."})
        result = run.legacy_prediction(p, scores(), "17", THRESHOLDS)
        self.assertEqual({q["sourceID"] for q in result["evidence"]}, {"x", "y"})

    def test_rule_gate_overrides_only_explicit_separation(self):
        p = packet(); key = c.pair_key(*(s["text"] for s in p["sources"]))
        for verdict in ("same_project", "separate_projects", "abstain"):
            with patch.object(run, "packets", return_value=[p]), patch("c6_scope.verify_packet", return_value=scope(p, verdict)):
                result = run.assemble({key: scores(.2)}, THRESHOLDS)
            self.assertEqual(len(result), 9)
            for scorer in run.SCORERS:
                expected = "separate_projects" if verdict == "separate_projects" else "abstain"
                self.assertEqual(result[scorer + "-gated"][0]["verdict"], expected)
                self.assertEqual(result[scorer][0]["verdict"], "abstain")

    def test_catalogue_only_reads_pair_sources_not_context(self):
        p = packet(); p["view"] = "context"
        p["sources"].append({"id": "z", "text": "Extra context must not become neural input."})
        original = copy.deepcopy(p)
        with patch.object(run, "packets", return_value=[p, p]):
            data = run.catalogue()
        self.assertEqual(len(data["texts"]), 2)
        self.assertEqual(len(data["pairs"]), 1)
        self.assertEqual(p, original)


class ReviewTests(unittest.TestCase):
    def test_seal_is_complete_and_immutable(self):
        p = packet()
        with tempfile.TemporaryDirectory() as d, patch.object(review, "RUN", Path(d)):
            root = Path(d)
            c.publish(root / "review-inputs/pair.json", {"packets": [p]})
            c.publish(root / "reviews/alpha-pair.json", {"reviewer": "alpha", "phase": "pair", "predictions": [
                {**scope(p, "abstain"), "rationale": "No affirmative boundary."}]})
            self.assertTrue(review.seal("alpha", "pair")["sealed"])
            sha = c.digest(root / "reviews/alpha-pair-seal.json")
            review.seal("alpha", "pair")
            self.assertEqual(c.digest(root / "reviews/alpha-pair-seal.json"), sha)

    def test_missing_or_duplicate_review_is_rejected(self):
        p = packet()
        for rows in ([], [{**scope(p, "abstain"), "rationale": "Unclear."}] * 2):
            with tempfile.TemporaryDirectory() as d, patch.object(review, "RUN", Path(d)):
                root = Path(d)
                c.publish(root / "review-inputs/pair.json", {"packets": [p]})
                c.publish(root / "reviews/alpha-pair.json", {"reviewer": "alpha", "phase": "pair", "predictions": rows})
                with self.assertRaisesRegex(ValueError, "review"):
                    review.seal("alpha", "pair")

    def test_context_cannot_be_sealed_without_pair_seal(self):
        with tempfile.TemporaryDirectory() as d, patch.object(review, "RUN", Path(d)):
            with self.assertRaises(FileNotFoundError):
                review.seal("alpha", "context")


class RecoveryTests(unittest.TestCase):
    def test_request_ack_and_resume(self):
        with tempfile.TemporaryDirectory() as d, patch.object(run, "RUN", Path(d)), patch.object(c, "space", return_value={}):
            self.assertFalse(run.pause()["safeToClose"])
            with run.worker():
                with self.assertRaises(c.Paused):
                    run.boundary("test")
            with run.worker(resume=True):
                run.boundary("resume")
                self.assertFalse((Path(d) / "control/pause-requested.json").exists())

    def test_resource_and_binding_failures(self):
        with patch.object(c, "space", side_effect=ValueError("reserve")):
            with self.assertRaisesRegex(ValueError, "reserve"):
                run.boundary("test")
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                run.check_files({"../outside": "bad"}, Path(d))


if __name__ == "__main__":
    unittest.main()
