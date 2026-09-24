#!/usr/bin/env python3
"""Trace only copied provider guards; never inject logging into production sources."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT/'scripts/ios27-embedding-recovery/run.py'
spec = importlib.util.spec_from_file_location('recovery',PARENT)
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
c = r.c
c.RUN = ROOT/'Evaluation/iOS27/embedding-trace'
c.WORK = c.RUN/'build'
c.BUNDLE = 'SimpleStudio.Remember.EmbeddingTrace'
c.UNITS = ['embedding-00']
base_prepare = c.prepare
base_sources = c.sources


def sources():
    result=base_sources(); result[str(Path(__file__).relative_to(ROOT))]=c.digest(__file__)
    return result


def prepare():
    c.publish(c.RUN/'pre-change.json',c.read(ROOT/'Evaluation/iOS27/embedding-recovery/pre-change.json'))
    result=base_prepare()
    path=c.WORK/'Sources/ProductionEmbedding.swift'
    value=path.read_text()
    replacements={
        'guard let model = load(language) ?? load(language) else { return nil }':
        '''let first = load(language)
        print("RECOVERY_TRACE sentenceFirst=\\(first != nil)")
        let recovered = first ?? load(language)
        print("RECOVERY_TRACE sentenceRecovered=\\(recovered != nil)")
        guard let model = recovered else { return nil }''',
        'guard let language = NLLanguageRecognizer.dominantLanguage(for: text) else { return nil }':
        '''guard let language = NLLanguageRecognizer.dominantLanguage(for: text) else { print("RECOVERY_TRACE noLanguage"); return nil }
        print("RECOVERY_TRACE language=\\(language.rawValue)")''',
        'guard contextual.hasAvailableAssets else {':
        '''print("RECOVERY_TRACE contextualAssets=\\(contextual.hasAvailableAssets)")
        guard contextual.hasAvailableAssets else {''',
        'let vector = ProjectMath.normalized(raw.map(Float.init)) else { return nil }':
        'let vector = ProjectMath.normalized(raw.map(Float.init)) else { print("RECOVERY_TRACE sentenceVectorUnavailable"); return nil }',
        'guard let semantic = ProjectMath.normalized(sum.map(Float.init)) else { return nil }':
        'guard let semantic = ProjectMath.normalized(sum.map(Float.init)) else { print("RECOVERY_TRACE sentenceNormalizationFailed"); return nil }',
        'guard let vector = ProjectMath.normalized(contextualSum.map(Float.init)) else { return nil }':
        'guard let vector = ProjectMath.normalized(contextualSum.map(Float.init)) else { print("RECOVERY_TRACE contextualNormalizationFailed"); return nil }'
    }
    for old,new in replacements.items():
        c.require(value.count(old)==1,'Trace boundary changed: '+old)
        value=value.replace(old,new)
    path.write_text(value)
    return result


c.sources=sources; c.prepare=prepare
if __name__=='__main__':
    try:c.main()
    except (ValueError,OSError,c.subprocess.SubprocessError) as error:
        print(c.json.dumps({'error':str(error)}));raise SystemExit(1)
