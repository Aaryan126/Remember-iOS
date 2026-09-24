#!/usr/bin/env python3
"""Report original gates and candidate parity separately; never promote automatically."""
import importlib.util
import math
from pathlib import Path
import statistics

s=importlib.util.spec_from_file_location('precision',Path(__file__).with_name('run.py'))
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
c=p.c


def score(values, probability, model):
    probability=max(1e-6,min(1-1e-6,probability))
    values=values+[math.log(probability/(1-probability))]
    c.require(len(values)==len(model['mean'])==len(model['scale'])==len(model['coefficient']),'Feature shape mismatch')
    z=model['intercept']+math.fsum((v-m)/s*w for v,m,s,w in zip(values,model['mean'],model['scale'],model['coefficient']))
    return 1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z))


def main():
    c.verify()
    fixtures=c.read(p.ROOT/'Evaluation/AppMatcher/parity-inputs.json')['fixtures']
    parameters=c.read(p.ROOT/'Remember/Remember/MatcherAssets/D3Parameters.json')
    exported=c.read(p.EXPORT/'export-result.json')['rows']
    report={'stage1Complete':False,'stage2Started':False,'productionModelChanged':False,'groups':{}}
    for platform in ['phone','mac']:
        for precision in ['fp16','fp32']:
            paths=[c.RUN/f'units/{platform}/{precision}-{i:02}.json' for i in range(16)]
            c.require(all(path.exists() for path in paths),'Incomplete collection; stop')
            envelopes=[c.read(path)['result'] for path in paths]
            c.require(all(row['status']=='ok' for row in envelopes),'Native error present')
            rows=[row['result'] for row in envelopes]
            native_deltas=[]; independent=[]; fresh=[]
            for i,row in enumerate(rows):
                mean=sum(row['probabilities'])/2
                independent += [abs(score(row['fixedFeatures'],mean,parameters['combiner'])-row['fixedScore']),
                                abs(score(row['freshFeatures'],mean,parameters['combiner'])-row['freshScore'])]
                own_reference=fixtures[i]['coreMLScore'] if precision=='fp16' else score(fixtures[i]['features'],sum(exported[i]['probabilities'])/2,parameters['combiner'])
                native_deltas.append(abs(own_reference-row['fixedScore']))
                fresh.append({'fixture':row['fixture'],'fixedScore':row['fixedScore'],'freshScore':row['freshScore'],
                    'combinedDeltaVsOriginalPyTorch':abs(row['freshScore']-fixtures[i]['expectedScore']),
                    'ownConversionScoreDelta':native_deltas[-1]})
            report['groups'][platform+'-'+precision]={
                'pairs':16,'unchangedFixedDecisions':sum(row['fixedDecisionUnchanged'] for row in rows),
                'unchangedFreshDecisions':sum(row['freshDecisionUnchanged'] for row in rows),
                'originalStrictGatePasses':sum(row['originalStrictGatePassed'] for row in rows),
                'originalNeuralBoundPasses':sum(row['originalNeuralBoundMet'] for row in rows),
                'maximumNeuralDeltaVsPyTorch':max(row['maximumNeuralDelta'] for row in rows),
                'maximumScoreDeltaVsOwnConversion':max(native_deltas),
                'ownConversionScoreGatePasses':sum(delta<=1e-7 for delta in native_deltas),
                'maximumIndependentCombinerDelta':max(independent),
                'maximumFreshScoreDeltaVsOriginalPyTorch':max(row['combinedDeltaVsOriginalPyTorch'] for row in fresh),
                'minimumFreshThresholdMargin':min(abs(row['freshScore']-parameters['threshold']) for row in rows),
                'maximumWarmRepeatDelta':max(row['warmRepeatDelta'] for row in rows),
                'medianLoadSeconds':statistics.median(row['loadSeconds'] for row in rows),
                'medianFirstInferenceSeconds':statistics.median(row['inferenceSeconds'][0] for row in rows),
                'medianSecondInferenceSeconds':statistics.median(row['inferenceSeconds'][1] for row in rows),
                'medianWarmRepeatSeconds':statistics.median(row['warmRepeatSeconds'] for row in rows),
                'medianProcessPeakResidentBytes':statistics.median(row['memoryAfter']['processPeakResident'] for row in envelopes),
                'maximumProcessPeakResidentBytes':max(row['memoryAfter']['processPeakResident'] for row in envelopes),
                'perPair':fresh}
            c.require(max(independent)<=1e-8,'Independent arithmetic audit failed')
    report['modelPackageBytes']={'fp16':c.read(p.ROOT/'Evaluation/AppMatcher/conversion.json')['packageBytes'],
        'fp32':c.read(p.EXPORT/'export-result.json')['packageBytes']}
    report['compiledPhoneModelBytes']={}
    app=c.WORK/'device-build/Build/Products/Debug-iphoneos/CompatibilityProbe.app'
    for precision,name in [('fp16','D3Matcher.mlmodelc'),('fp32','D3MatcherFP32.mlmodelc')]:
        matches=list(app.rglob(name));c.require(len(matches)==1,'Ambiguous compiled model')
        report['compiledPhoneModelBytes'][precision]=sum(q.stat().st_size for q in matches[0].rglob('*') if q.is_file())
    c.publish(c.RUN/'summary.json',report)
    print(c.json.dumps({**report,'groups':{k:{a:b for a,b in v.items() if a!='perPair'} for k,v in report['groups'].items()}},indent=2))


if __name__=='__main__': main()
