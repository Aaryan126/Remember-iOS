import importlib.util
from pathlib import Path
import unittest

s=importlib.util.spec_from_file_location('precision',Path(__file__).with_name('run.py'))
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
s=importlib.util.spec_from_file_location('analysis',Path(__file__).with_name('analyze.py'))
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class PrecisionTests(unittest.TestCase):
    def test_bound_and_paired_order(self):
        self.assertEqual(len(p.c.UNITS),32)
        self.assertEqual(len(set(p.c.UNITS)),32)
        self.assertEqual(p.c.UNITS[:4],['fp16-00','fp32-00','fp16-01','fp32-01'])

    def test_numeric_failure_retained_not_promoted(self):
        r={'status':'ok','result':{'tokenParity':True,'fixedDecisionUnchanged':True,'freshDecisionUnchanged':True,'originalStrictGatePassed':False}}
        p.check_result(r,'fp16-00')
        self.assertFalse(r['result']['originalStrictGatePassed'])

    def test_decision_regression_stops(self):
        for field in ['fixedDecisionUnchanged','freshDecisionUnchanged','tokenParity']:
            r={'tokenParity':True,'fixedDecisionUnchanged':True,'freshDecisionUnchanged':True}
            r[field]=False
            with self.assertRaises(ValueError):p.check_result({'status':'ok','result':r},'fp32-00')

    def test_native_error_stops(self):
        with self.assertRaises(ValueError):p.check_result({'status':'error'},'fp16-00')

    def test_independent_combiner_and_clipping(self):
        model={'intercept':0,'mean':[0,0],'scale':[1,1],'coefficient':[0,1]}
        self.assertAlmostEqual(a.score([42],.8,model),.8)
        self.assertAlmostEqual(a.score([42],0,model),1e-6)
        self.assertAlmostEqual(a.score([42],1,model),1-1e-6)

    def test_combiner_rejects_shape_mismatch(self):
        with self.assertRaises(ValueError):a.score([], .5, {'intercept':0,'mean':[],'scale':[],'coefficient':[]})

if __name__=='__main__':unittest.main()
