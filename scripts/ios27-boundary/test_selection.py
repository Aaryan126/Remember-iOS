import importlib.util
from pathlib import Path
import unittest

s=importlib.util.spec_from_file_location('selection',Path(__file__).with_name('prepare_inputs.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class SelectionTests(unittest.TestCase):
    def rows(self):
        return [{'id':f'{side}-{lib}-{n}','library':str(lib),'score':.5+side*(n+lib/10+1)/1000}
                for side in [-1,1] for lib in range(8) for n in range(4)]
    def test_balanced_diverse_deterministic(self):
        rows=self.rows();chosen=m.select(rows,.5)
        self.assertEqual(chosen,m.select(list(reversed(rows)),.5))
        self.assertEqual(len(chosen),24)
        for side in [False,True]:
            selected=[r for r in chosen if (r['score']>=.5)==side]
            self.assertEqual(len(selected),12)
            self.assertTrue(all(sum(r['library']==str(lib) for r in selected)<=2 for lib in range(8)))
    def test_insufficient_diversity_rejected(self):
        with self.assertRaises(ValueError):m.select([r for r in self.rows() if r['library']=='0'],.5)
    def test_labels_not_used(self):
        a=self.rows();b=[{**r,'relation':'anything'} for r in a]
        self.assertEqual([r['id'] for r in m.select(a,.5)],[r['id'] for r in m.select(b,.5)])

if __name__=='__main__':unittest.main()
