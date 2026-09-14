import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import c2_common as c
import c5_run as run
from c5_data import compile_family, validate_authoring, validate_packet, validate_projection, novelty
from c5_metrics import evaluate, validate_prediction


def document():
    return c.read(run.AUTHORING)


def family():
    return compile_family(document()["families"][0])


def prediction(packet, verdict):
    return {"queryID": packet["queryID"], "verdict": verdict, "evidence": [] if verdict == "abstain" else
            [{"sourceID": s["id"], "quote": s["text"]} for s in packet["sources"]]}


class DataTests(unittest.TestCase):
    def test_all_families_and_views_validate(self):
        authored = validate_authoring(document())
        units = [compile_family(f) for f in authored["families"]]
        self.assertTrue(validate_projection(units))
        self.assertEqual(sum(len(u["packets"]) for u in units), 160)
        self.assertEqual({f["partition"] for f in authored["families"][:4]}, {"discovery"})

    def test_projection_deterministic_and_does_not_mutate_authoring(self):
        authored = document()["families"][0]
        original = copy.deepcopy(authored)
        self.assertEqual(compile_family(authored), compile_family(authored))
        self.assertEqual(authored, original)

    def test_authored_split_and_duplicate_text_fail(self):
        for mutation in ("partition", "duplicate"):
            authored = document()
            if mutation == "partition":
                authored["families"][0]["partition"] = "diagnostic"
            else:
                authored["families"][1]["anchor"] = authored["families"][0]["anchor"]
            with self.assertRaises(ValueError):
                validate_authoring(authored)

    def test_model_packet_omits_all_label_and_author_fields(self):
        for p in family()["packets"]:
            self.assertEqual(set(p), {"queryID", "view", "pair", "sources"})
            for s in p["sources"]:
                self.assertEqual(set(s), {"id", "text"})
        p = family()["packets"][0]
        p["rationale"] = "hidden label"
        with self.assertRaisesRegex(ValueError, "schema"):
            validate_packet(p)

    def test_pair_view_rejects_extra_context_and_bad_pair(self):
        p = family()["packets"][0]
        p["sources"].append({"id": "future", "text": "A later clarification."})
        with self.assertRaisesRegex(ValueError, "Pair-only"):
            validate_packet(p)
        p = family()["packets"][0]
        p["pair"][1] = "unseen"
        with self.assertRaisesRegex(ValueError, "query pair"):
            validate_packet(p)

    def test_context_can_resolve_without_relabeling_identical_pair(self):
        unit = family()
        gold = {r["queryID"]: r for r in unit["gold"]}
        for view in ("pair", "context"):
            initial = [p for p in unit["packets"] if p["view"] == view and gold[p["queryID"]]["episode"] == "before"]
            later = [p for p in unit["packets"] if p["view"] == view and gold[p["queryID"]]["episode"] == "after"]
            self.assertEqual([gold[p["queryID"]]["verdict"] for p in initial], ["abstain", "abstain"])
            if view == "pair":
                self.assertEqual([p["sources"] for p in initial], [p["sources"] for p in later])
                self.assertEqual([gold[p["queryID"]]["verdict"] for p in later], ["abstain", "abstain"])
            else:
                self.assertEqual([gold[p["queryID"]]["verdict"] for p in later], ["same_project", "separate_projects"])

    def test_bridge_is_nontransitive_and_negation_is_continuation(self):
        rows = family()["gold"]
        self.assertEqual({r["verdict"] for r in rows if r["episode"] == "continuation"}, {"same_project"})
        bridge = [r["verdict"] for r in rows if r["episode"] == "bridge"]
        self.assertEqual(bridge.count("same_project"), 4)
        self.assertEqual(bridge.count("separate_projects"), 2)

    def test_historical_reuse_fails_and_novelty_is_not_semantic_proof(self):
        authored = document()
        with self.assertRaisesRegex(ValueError, "reuse"):
            novelty(authored, [authored["families"][0]["anchor"]])
        result = novelty(authored, ["A deliberately different historical example."])
        self.assertFalse(result["semanticIndependenceEstablished"])
        self.assertEqual(result["newTexts"], 56)


class MetricsTests(unittest.TestCase):
    def test_hand_supplied_correct_answers_are_contract_fixture_not_model_accuracy(self):
        unit = family()
        predictions = [prediction(p, g["verdict"]) for p, g in zip(unit["packets"], unit["gold"])]
        result = evaluate(unit["packets"], unit["gold"], predictions)
        self.assertEqual(result["all"]["counts"]["correctThreeWay"], 20)
        self.assertEqual(result["all"]["conflictPrecision"]["value"], 1)
        self.assertIn("behavior:bridge-link", result)

    def test_always_abstain_has_zero_recall_and_undefined_precision(self):
        unit = family()
        result = evaluate(unit["packets"], unit["gold"], [prediction(p, "abstain") for p in unit["packets"]])["all"]
        self.assertEqual(result["coverage"]["value"], 0)
        self.assertEqual(result["conflictRecall"]["value"], 0)
        self.assertIsNone(result["conflictPrecision"]["value"])

    def test_contrast_success_requires_all_related_decisions_correct(self):
        unit = family()
        predictions = [prediction(p, g["verdict"]) for p, g in zip(unit["packets"], unit["gold"])]
        first = evaluate(unit["packets"], unit["gold"], predictions)
        self.assertEqual(first["contrastChecks"]["bridgeTriple:context"]["value"], 1)
        index = next(i for i, (p, g) in enumerate(zip(unit["packets"], unit["gold"]))
                     if p["view"] == "context" and g["episode"] == "bridge")
        predictions[index] = prediction(unit["packets"][index], "abstain")
        second = evaluate(unit["packets"], unit["gold"], predictions)
        self.assertEqual(second["contrastChecks"]["bridgeTriple:context"]["value"], 0)
        self.assertEqual(second["contrastChecks"]["bridgeTriple:pair"]["value"], 1)

    def test_incomplete_contrast_has_undefined_success(self):
        unit = family()
        result = evaluate(unit["packets"][:1], unit["gold"][:1], [prediction(unit["packets"][0], "abstain")])
        self.assertIsNone(result["contrastChecks"]["scopeContrast:pair"]["value"])

    def test_uncertainty_is_not_a_negative_label(self):
        unit = family()
        result = evaluate(unit["packets"], unit["gold"], [prediction(p, "separate_projects") for p in unit["packets"]])["all"]
        self.assertGreater(result["counts"]["unsupportedSeparate"], 0)
        self.assertGreater(result["counts"]["falseSeparateOnSame"], 0)
        self.assertEqual(result["conflictPrecision"]["denominator"], 20)
        self.assertEqual(result["unsupportedAssertionRate"]["value"], 1)

    def test_missing_duplicate_predictions_fail_not_abstain(self):
        unit = family()
        predictions = [prediction(p, "abstain") for p in unit["packets"]]
        for invalid in (predictions[:-1], predictions + predictions[:1]):
            with self.assertRaisesRegex(ValueError, "predictions"):
                evaluate(unit["packets"], unit["gold"], invalid)

    def test_missing_fabricated_and_future_quotes_fail(self):
        p = family()["packets"][0]
        for evidence in ([], [{"sourceID": "future", "quote": "Invisible text"}],
                         [{"sourceID": p["pair"][0], "quote": "Fabricated phrase."}]):
            value = prediction(p, "same_project")
            value["evidence"] = evidence
            with self.assertRaises(ValueError):
                validate_prediction(p, value)

    def test_unsupported_same_assertion_counted_on_uncertain(self):
        unit = family()
        result = evaluate(unit["packets"], unit["gold"], [prediction(p, "same_project") for p in unit["packets"]])["all"]
        self.assertGreater(result["counts"]["falseSameOnSeparate"], 0)
        self.assertEqual(result["counts"]["unsupportedDecisive"], result["counts"]["unknown"])


class RecoveryTests(unittest.TestCase):
    def test_pause_ack_and_idempotent_request(self):
        with tempfile.TemporaryDirectory() as d, patch.object(run, "RUN", Path(d)), patch.object(c, "space", return_value={}):
            run.pause()
            marker = Path(d) / "control/pause-requested.json"
            before = marker.stat().st_mtime_ns
            run.pause()
            self.assertEqual(marker.stat().st_mtime_ns, before)
            with run.worker():
                with self.assertRaises(c.Paused):
                    run.boundary("test")
            with run.worker(resume=True):
                self.assertFalse(marker.exists())
                run.boundary("resumed")

    def test_changed_unit_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "unit.json"
            c.unit(path, family())
            before = (c.digest(path), path.stat().st_mtime_ns)
            c.unit(path, family())
            self.assertEqual(before, (c.digest(path), path.stat().st_mtime_ns))
            with self.assertRaises(ValueError):
                c.unit(path, {"bad": True})

    def test_disk_reserve_and_path_escape_fail_closed(self):
        with patch.object(c, "space", side_effect=ValueError("reserve")):
            with self.assertRaisesRegex(ValueError, "reserve"):
                run.boundary("test")
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                run.check_files({"../outside": "bad"}, Path(d))


if __name__ == "__main__":
    unittest.main()
