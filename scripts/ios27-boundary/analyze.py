"""Keep historical, fresh-reference and candidate-specific gates distinct."""
import importlib.util
from pathlib import Path

s=importlib.util.spec_from_file_location('runner',Path(__file__).with_name('run.py'))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
c=r.c


def main():
    c.verify()
    selected=c.read(c.RUN/'selection.json');threshold=selected['threshold']
    refs=[c.read(c.RUN/f'references/{i:02}.json') for i in range(24)]
    summary={'candidate':'d3-seed29-fp32-ios27-evaluation-v1','productionChanged':False,'stage2Started':False,
        'pairs':24,'libraries':len({p['library'] for p in selected['pairs']}),'groups':{},
        'minimumHistoricalThresholdMargin':min(abs(p['score']-threshold) for p in selected['pairs']),
        'freshPyTorchVsHistoricalDecisionChanges':sum((ref['historicalScore']>=threshold)!=(ref['fixture']['expectedScore']>=threshold) for ref in refs)}
    for platform in ['mac','phone']:
        for precision in ['fp16','fp32']:
            rows=[]
            for i in range(24):
                raw=c.read(c.RUN/f'units/{platform}/{precision}-{i:02}.json')['result']
                c.require(raw['status']=='ok','Native error')
                rows.append(raw['result'])
            neural=[abs(p-d['probability']) for i,row in enumerate(rows) for p,d in zip(row['probabilities'],refs[i]['fixture']['directions'])]
            score_deltas=[abs(row['fixedScore']-(refs[i]['fixture']['coreMLScore'] if precision=='fp16' else refs[i]['fp32Score'])) for i,row in enumerate(rows)]
            flips=[{'fixture':row['fixture'],'fixed':not row['fixedDecisionUnchanged'],'fresh':not row['freshDecisionUnchanged'],
                'referenceScore':refs[i]['fixture']['expectedScore'],'fixedScore':row['fixedScore'],'freshScore':row['freshScore']}
                for i,row in enumerate(rows) if not row['fixedDecisionUnchanged'] or not row['freshDecisionUnchanged']]
            summary['groups'][platform+'-'+precision]={
                'unchangedFixedDecisions':sum(row['fixedDecisionUnchanged'] for row in rows),
                'unchangedFreshDecisions':sum(row['freshDecisionUnchanged'] for row in rows),
                'directionsWithinOriginalBound':sum(d<=.002 for d in neural),'directions':48,
                'maximumNeuralDeltaVsPyTorch':max(neural),'ownConversionScoreGatePasses':sum(d<=1e-7 for d in score_deltas),
                'maximumOwnConversionScoreDelta':max(score_deltas),
                'maximumFreshVsFixedScoreDelta':max(abs(row['freshScore']-row['fixedScore']) for row in rows),
                'minimumFreshThresholdMargin':min(abs(row['freshScore']-threshold) for row in rows),'decisionChanges':flips}
    candidate=summary['groups']['phone-fp32']
    summary['candidateBoundaryGatePassed']=bool(candidate['unchangedFixedDecisions']==24 and candidate['unchangedFreshDecisions']==24
        and candidate['directionsWithinOriginalBound']==48 and candidate['ownConversionScoreGatePasses']==24)
    c.publish(c.RUN/'summary.json',summary)
    print(c.json.dumps(summary,indent=2))


if __name__=='__main__':main()
