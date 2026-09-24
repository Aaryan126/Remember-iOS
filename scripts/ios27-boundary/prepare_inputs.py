"""Freeze a label-blind, threshold-near diagnostic; no fitting or production writes."""
import gzip
import importlib.util
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'Evaluation/iOS27/boundary'
P2 = ROOT / 'Evaluation/MatcherValidation/runs/validation-02'
WORKSPACE = Path('/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1')
s = importlib.util.spec_from_file_location('prior', ROOT/'scripts/ios27-precision/run.py')
prior = importlib.util.module_from_spec(s); s.loader.exec_module(prior)
c = prior.c


def select(rows, threshold):
    selected = []
    for positive in [False, True]:
        counts = {}
        candidates = sorted((r for r in rows if (r['score'] >= threshold) == positive),
                            key=lambda r: (abs(r['score']-threshold), r['id']))
        side = []
        for row in candidates:
            if counts.get(row['library'], 0) >= 2:
                continue
            side.append(row); counts[row['library']] = counts.get(row['library'], 0)+1
            if len(side) == 12:
                break
        c.require(len(side) == 12, 'Insufficient diverse boundary examples')
        selected.extend(side)
    c.require(len({r['id'] for r in selected}) == 24, 'Duplicate pairs')
    return selected


def main():
    c.verify(); c.space()
    c.require(not (RUN/'pause.request.json').exists(), 'Paused before input preparation')
    parameters = c.read(ROOT/'Remember/Remember/MatcherAssets/D3Parameters.json')
    source = ROOT/'Evaluation/MatcherValidation/releases/v1/inputs-evaluation.json'
    prediction = P2/'evaluation/seed-29.json'
    chosen = select(c.read(prediction)['predictions']['hybrid'], parameters['threshold'])
    selection = {'rule':'12 per threshold side, nearest historical score, at most 2 per library per side; no labels used',
        'threshold':parameters['threshold'], 'sources':{str(p.relative_to(ROOT)):c.digest(p) for p in [source,prediction,Path(__file__)]},
        'pairs':[{k:r[k] for k in ['id','first','second','library','score']} for r in chosen],
        'qualityBenchmark':False, 'stage2Started':False}
    c.publish(RUN/'selection.json',selection)
    items = {item['id']:item for library in c.read(source)['libraries'] for item in library['items']}
    sys.path.insert(0,str(ROOT/'Evaluation/iOS27/precision/build/python-overrides'))
    os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
    os.environ['TOKENIZERS_PARALLELISM']='false'
    import torch
    import coremltools as ct
    import numpy as np
    from transformers import AutoTokenizer, BertConfig, BertForSequenceClassification
    sys.path.insert(0,str(ROOT/'scripts/organization-diagnostics'))
    from c2_models import Features
    record = c.read(P2/'hybrid-29.json')
    weights = WORKSPACE/'validation/validation-02'/record['final']['file']
    c.require(c.digest(weights)==record['final']['SHA256'],'Weights changed')
    assets_manifest=c.read(ROOT/'Evaluation/MatcherFeasibility/model-manifest.json')
    assets=WORKSPACE/assets_manifest['workspaceRelativeDirectory']
    for name,entry in assets_manifest['assets'].items():
        c.require(c.digest(assets/name)==entry['sha256'],'Model asset changed')
    torch.set_num_threads(4)
    config=BertConfig.from_pretrained(str(assets),local_files_only=True,num_labels=2)
    config._attn_implementation='eager'
    model=BertForSequenceClassification(config).eval()
    with gzip.open(weights,'rb') as stream: saved=torch.load(stream,map_location='cpu',weights_only=True)
    c.require(saved['fingerprint']==record['final']['fingerprint'],'Weight fingerprint changed')
    model.load_state_dict(saved['model'],strict=True)
    tokenizer=AutoTokenizer.from_pretrained(str(assets),local_files_only=True,trust_remote_code=False)
    ids=sorted({r[k] for r in chosen for k in ['first','second']})
    texts={key:items[key]['text'] for key in ids}
    embeddings={key:c.read(P2/f'embeddings/{key}.json') for key in ids}
    for key in ids:
        c.require(embeddings[key]['status']=='ok' and embeddings[key]['space']==parameters.get('embeddingSpace',embeddings[key]['expectedSpace']), 'Invalid embedding')
        c.require(embeddings[key]['textSHA256']==c.hashlib.sha256(texts[key].encode()).hexdigest(),'Embedding text mismatch')
    features=Features(texts,embeddings)
    models={'fp16':ct.models.MLModel(str(ROOT/'Remember/Remember/MatcherAssets/D3Matcher.mlpackage'),compute_units=ct.ComputeUnit.CPU_ONLY),
            'fp32':ct.models.MLModel(str(prior.EXPORT/'models/D3MatcherFP32.mlpackage'),compute_units=ct.ComputeUnit.CPU_ONLY)}
    bindings={str(p):c.digest(p) for p in [weights, P2/'tfidf.json', ROOT/'Remember/Remember/MatcherAssets/D3Parameters.json']}
    bindings.update({str(P2/f'embeddings/{key}.json'):c.digest(P2/f'embeddings/{key}.json') for key in ids})
    c.publish(RUN/'reference-inputs.json',{'bindings':bindings,'precisionManifestSHA256':c.digest(prior.c.RUN/'manifest.json'),
        'selectionSHA256':c.digest(RUN/'selection.json'),'candidate':'d3-seed29-fp32-ios27-evaluation-v1','productionChanged':False})
    for i,row in enumerate(chosen):
        destination=RUN/f'references/{i:02}.json'
        if destination.exists():
            continue
        c.require(not (RUN/'pause.request.json').exists(),'Paused at reference boundary')
        left,right=row['first'],row['second']; directions=[]; converted={k:[] for k in models}
        for a,b in [(left,right),(right,left)]:
            tokens=tokenizer(texts[a],texts[b],padding='max_length',truncation='longest_first',max_length=512,return_tensors='pt')
            with torch.inference_mode(): probability=model(**tokens).logits.softmax(-1)[0,1].item()
            token_values={k:v.tolist() for k,v in tokens.items()}
            directions.append({'tokens':token_values,'probability':probability})
            for precision,converted_model in models.items():
                converted[precision].append(float(converted_model.predict({k:np.asarray(v,dtype=np.int32) for k,v in token_values.items()})['probabilities'][0,1]))
        values=features.values(left,right)
        def score(p):return features.scores(values,{'29':sum(p)/2})['hybrid']['29']
        fixture={'id':row['id'],'first':texts[left],'second':texts[right],'embeddingA':embeddings[left],
            'embeddingB':embeddings[right],'directions':directions,'features':values,
            'expectedScore':score([d['probability'] for d in directions]),'coreMLScore':score(converted['fp16'])}
        c.publish(destination,{'fixture':fixture,'conversion':converted,'fp32Score':score(converted['fp32']),
            'historicalScore':row['score'],'selectionSHA256':c.digest(RUN/'selection.json')})
        print('Saved reference',i,flush=True)
    records=[c.read(RUN/f'references/{i:02}.json') for i in range(24)]
    c.publish(RUN/'parity-inputs.json',{'fixtures':[r['fixture'] for r in records]})


if __name__=='__main__': main()
