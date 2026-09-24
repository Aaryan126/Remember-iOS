from copy import deepcopy
import hashlib
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import rk_control as c
import rk_policy as p
import rk_runner as r
import rk_runtime as runtime


def row(key, score, source="s01", revision=0, quote="support", created=1, ordinal=0):
    return dict(id=key,sourceId=source,revision=revision,quote=quote,created=created,ordinal=ordinal,
                lexical=score,hybrid=score)


def task(key="q1",mode="current",answerable=True):
    return dict(id=key,mode=mode,answerable=answerable,
                expectedEvidence=[dict(sourceId="s01",revision=0,quote="support")] if answerable else [])


class Policy(unittest.TestCase):
    def test_fixed_grid(self):
        for family in ("B","C"):
            values=p.grid(family)
            self.assertEqual(len(values),48)
            self.assertEqual(len({p.config_id(v) for v in values}),48)

    def test_current_reference_cannot_use_history(self):
        query=dict(current=[row("a",.4)],scoped=[row("a",.4),row("old",.9,revision=1)])
        self.assertEqual([v["id"] for v in p.predict(query,r.REFERENCE)],["a"])
        self.assertEqual([v["id"] for v in p.predict(query,r.HISTORY_CONTROL)],["old","a"])

    def test_zero_scores_never_fill_slots(self):
        query=dict(current=[],scoped=[row("a",0)])
        self.assertEqual(p.predict(query,r.HISTORY_CONTROL),[])

    def test_margin_abstains_whole_query(self):
        query=dict(scoped=[row("a",.8),row("b",.79,source="s02")])
        self.assertEqual(p.predict(query,dict(family="B",minScore=.2,margin=.05,limit=3)),[])

    def test_threshold_inclusive(self):
        query=dict(scoped=[row("a",.5),row("b",.4,source="s02")])
        result=p.predict(query,dict(family="B",minScore=.5,margin=0,limit=3))
        self.assertEqual(len(result),1)

    def test_duplicate_chunks_collapse_before_margin(self):
        query=dict(scoped=[row("a",.9),row("b",.89),row("c",.5,source="s02")])
        result=p.predict(query,dict(family="B",minScore=.6,margin=.1,limit=3))
        self.assertEqual([v["id"] for v in result],["a"])

    def test_distinct_revisions_not_collapsed(self):
        query=dict(scoped=[row("a",.8),row("b",.7,revision=1)])
        self.assertEqual(len(p.predict(query,r.HISTORY_CONTROL)),2)

    def test_tie_uses_source_creation_then_ordinal(self):
        query=dict(scoped=[row("a",.7,created=1),row("b",.7,source="s02",created=2)])
        self.assertEqual(p.predict(query,r.HISTORY_CONTROL)[0]["id"],"b")

    def test_nan_and_infinity_rejected(self):
        for score in (float("nan"),float("inf"),-1,2):
            with self.assertRaises(ValueError): p.predict(dict(scoped=[row("a",score)]),r.HISTORY_CONTROL)

    def test_empty_candidates(self):
        self.assertEqual(p.predict(dict(scoped=[]),r.HISTORY_CONTROL),[])

    def test_single_result_margin_compares_zero(self):
        self.assertEqual(p.predict(dict(scoped=[row("a",.02)]),
                                  dict(family="B",minScore=0,margin=.05,limit=1)),[])

    def test_cosine(self):
        self.assertEqual(p.cosine([1,0],[1,0]),1)
        self.assertEqual(p.cosine([1,0],[-1,0]),-1)
        for a,b in (([],[]),([1],[1,2]),([0],[0]),([math.nan],[1])):
            with self.assertRaises(ValueError): p.cosine(a,b)


class Metrics(unittest.TestCase):
    def test_missing_slots_are_not_correct(self):
        metric=p.metrics([dict(id="dev01",tasks=[task()])],{"dev01":{"q1":[row("a",.5)]}})
        self.assertEqual((metric["correct"],metric["returned"]),(1,1))
        self.assertEqual(metric["returnedDistribution"],{"0":0,"1":1,"2":0,"3":0})

    def test_zero_returns_not_perfect_precision(self):
        metric=p.metrics([dict(id="dev01",tasks=[task()])],{"dev01":{"q1":[]}})
        self.assertIsNone(metric["precision"])
        self.assertEqual(metric["hitCoverage"],0)

    def test_wrong_quote_does_not_get_identity_credit(self):
        metric=p.metrics([dict(id="dev01",tasks=[task()])],{"dev01":{"q1":[row("a",.8,quote="unrelated")]}})
        self.assertEqual(metric["correct"],0)

    def test_unanswerable_returns_are_errors(self):
        metric=p.metrics([dict(id="dev01",tasks=[task(answerable=False,mode="uncertain")])],
                         {"dev01":{"q1":[row("a",.8)]}})
        self.assertEqual(metric["precision"],0)
        self.assertEqual(metric["falseReturnRate"],1)

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):
            p.metrics([dict(id="dev01",tasks=[task()])],{"dev01":{"q1":[row("a",.8),row("b",.7)]}})

    def test_four_results_rejected(self):
        with self.assertRaises(ValueError):
            p.metrics([dict(id="dev01",tasks=[task()])],{"dev01":{"q1":[row(str(i),.8,source=str(i)) for i in range(4)]}})

    def test_macro_is_library_balanced(self):
        libraries=[dict(id="a",tasks=[task()]),dict(id="b",tasks=[task("q1"),task("q2")])]
        metric=p.metrics(libraries,{"a":{"q1":[row("a",1)]},"b":{"q1":[],"q2":[]}})
        self.assertEqual(metric["macroRecall"],.5)
        self.assertAlmostEqual(metric["hitCoverage"],1/3)

    def base(self):
        return dict(returned=30,correct=27,precision=.9,librariesWithReturns=9,
                    macroRecall=.75,modeRecall={"current":1,"overlap":1,"historical":.5},
                    correctHits=27,answerable=36,hitCoverage=.75,unanswerable=12,falseReturns=1)

    def test_gates_and_near_miss(self):
        value=self.base(); baseline=dict(value,macroRecall=.6)
        self.assertTrue(all(p.gates(value,baseline).values()))
        self.assertFalse(p.gates(dict(value,macroRecall=.697222),baseline)["recallGain"])
        self.assertFalse(p.gates(dict(value,falseReturns=2),baseline)["abstention"])
        self.assertFalse(p.gates(dict(value,returned=31),baseline)["precision"])

    def test_selection_diagnostic_cannot_qualify(self):
        value=self.base(); baseline=dict(value,macroRecall=.8)
        selected=p.select([dict(config=p.grid("B")[0],metrics=value)],baseline)
        self.assertFalse(selected["qualified"])
        self.assertTrue(selected["diagnosticOnly"])

    def test_overall_exact_tie_prefers_lexical(self):
        value=self.base(); baseline=dict(value,macroRecall=.6)
        selected=p.select([dict(config=p.grid(f)[0],metrics=value) for f in ("C","B")],baseline)
        self.assertEqual(selected["config"]["family"],"B")


class Runtime(unittest.TestCase):
    def vector(self):
        return dict(id=hashlib.sha256(b"text").hexdigest(),status="ok",space=runtime.SPACE,
                    expectedSpace=runtime.SPACE,sentence=[1.0]+[0.0]*511,contextual=[1.0]+[0.0]*511)

    def test_compatible_vector(self): runtime.valid_embedding(self.vector(),"text")

    def test_bad_space_dimension_norm_nonfinite(self):
        for changes in ({"space":"other"},{"sentence":[1.0]},{"sentence":[0.0]*512},
                        {"sentence":[math.nan]+[0.0]*511},{"status":"unavailable"}):
            with self.assertRaises(ValueError): runtime.valid_embedding(dict(self.vector(),**changes),"text")

    def test_query_id_tied_to_actual_text(self):
        with self.assertRaises(ValueError): runtime.valid_embedding(self.vector(),"different")

    def test_resource_failure_is_not_semantic_fallback(self):
        with patch.object(c.history,"resources",side_effect=ValueError("budget")):
            with self.assertRaises(c.ResourceBlocked): c.resources()


class Boundaries(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name).resolve()
        self.work=self.root/"work"; self.run=self.root/"run";self.work.mkdir()
        self.patches=[patch.object(c,"WORK",self.work),patch.object(c,"RUN",self.run)]
        for item in self.patches:item.start()

    def tearDown(self):
        for item in reversed(self.patches):item.stop()
        self.temp.cleanup()

    def test_immutable_receipt_and_integrity(self):
        path=self.run/"cache.json"
        c.unit(path,{"x":1},"frozen")
        before=path.stat().st_mtime_ns
        c.unit(path,{"x":1},"frozen")
        self.assertEqual(before,path.stat().st_mtime_ns)
        self.assertEqual(c.read_unit(path,"frozen"),{"x":1})
        with self.assertRaises(ValueError):c.unit(path,{"x":2},"frozen")
        with self.assertRaises(ValueError):c.read_unit(path,"changed")

    def test_output_escape(self):
        with self.assertRaises(ValueError):c.publish(self.root/"escaped.json",{})
        (self.work/"link").symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):c.publish(self.work/"link/escaped.json",{})

    def test_evaluation_requires_sealed_selection(self):
        with patch.object(r,"verify_selection",side_effect=ValueError("not selected")):
            with self.assertRaisesRegex(ValueError,"selected"):r.allowed("evaluation")
            r.allowed("development")

    def test_scorer_and_catalog_do_not_call_gold_loader(self):
        fake=[dict(id="q",question="query",current=[],scoped=[])]
        with patch.object(r,"packets",return_value=fake),patch.object(r,"labels",side_effect=AssertionError("gold read")),\
             patch.object(c,"boundary",return_value={}),patch.object(runtime,"lexical",return_value={}):
            self.assertEqual(len(r.catalog("development")),1)
            self.assertEqual(r.scored_library("dev01","development",False,"locale")[0]["current"],[])

    def test_worker_stops_and_resumes(self):
        with patch.object(c,"verify_prior"),patch.object(c,"resources",return_value={}):
            c.atomic(self.work/"pause.request.json",{})
            with self.assertRaises(c.Paused):
                with c.worker():pass
            with c.worker(resume=True):
                self.assertTrue(c.load(self.work/"worker.json")["running"])
            self.assertFalse(c.load(self.work/"worker.json")["running"])


if __name__ == "__main__":unittest.main()
