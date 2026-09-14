"""Extra read-only regression checks against the frozen, non-test baseline."""
import unittest
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from stage5_common import STAGE2,RELEASE,read
from stage2 import pair_features,exported_probabilities


class FrozenBaselineReconstructionTests(unittest.TestCase):
    def test_reconstructs_development_features_without_refitting(self):
        baseline=read(STAGE2/"baseline-selected.json")
        vectorizer=TfidfVectorizer(vocabulary=baseline["tfidf"]["vocabulary"],lowercase=True,ngram_range=(1,2),dtype=np.float64)
        vectorizer.idf_=np.asarray(baseline["tfidf"]["idf"])
        rows=read(STAGE2/"features.json")["splits"]["development"]["pairs"]
        originals={(r["first"],r["second"]):r for r in rows}
        count=0
        for library in read(RELEASE/"inputs-development.json")["libraries"]:
            items=library["items"]; vectors=vectorizer.transform([item["text"] for item in items]);lexical=(vectors@vectors.T).toarray()
            embeddings=[read(STAGE2/"embeddings"/f"{item['id']}.json") for item in items]
            for a in range(len(items)):
                for b in range(a+1,len(items)):
                    expected=originals[items[a]["id"],items[b]["id"]]
                    actual=pair_features(items[a],items[b],embeddings[a],embeddings[b],lexical[a,b])
                    self.assertTrue(np.allclose(actual,expected["features"],atol=1e-12,rtol=0))
                    first=exported_probabilities(baseline["model"],[actual])
                    second=exported_probabilities(baseline["model"],[expected["features"]])
                    self.assertTrue(np.allclose(first,second,atol=1e-12,rtol=0));count+=1
        self.assertEqual(count,1140)


if __name__=="__main__":unittest.main()
