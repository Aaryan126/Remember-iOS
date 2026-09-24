#!/usr/bin/env python3
"""Offline FP32 ablation from original trained weights; never upcast FP16 weights."""
import gzip
import importlib.metadata
import importlib.util
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('recovery', ROOT/'scripts/ios27-embedding-recovery-v2/run.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
c = r.c
RUN = ROOT/'Evaluation/iOS27/precision'
WORKSPACE = Path('/Users/aaryan/Library/Application Support/RememberMatcherFeasibility/v1')


def main():
    c.verify()
    c.require(not (RUN/'pause.request.json').exists(), 'Paused before export')
    free = c.shutil.disk_usage(ROOT).free
    allocated = sum(p.stat().st_size for p in (ROOT/'Evaluation/iOS27').rglob('*') if p.is_file())
    c.require(free-2*c.GIB >= 10*c.GIB and allocated+2*c.GIB < 8*c.GIB, 'Export reserve exceeded')
    record = c.read(ROOT/'Evaluation/MatcherValidation/runs/validation-02/hybrid-29.json')
    weights = WORKSPACE/'validation/validation-02'/record['final']['file']
    c.require(c.digest(weights)==record['final']['SHA256'], 'Trained weights changed')
    asset_manifest = c.read(ROOT/'Evaluation/MatcherFeasibility/model-manifest.json')
    assets = WORKSPACE/asset_manifest['workspaceRelativeDirectory']
    for name, entry in asset_manifest['assets'].items():
        c.require(c.digest(assets/name)==entry['sha256'], 'Original model asset changed: '+name)
    fixture_path = ROOT/'Evaluation/AppMatcher/parity-inputs.json'
    bindings = {str(p):c.digest(p) for p in [Path(__file__), weights, fixture_path, assets/'config.json']}
    manifest = {'bindings':bindings,'weightSHA256':record['final']['SHA256'],
        'versions':{name:importlib.metadata.version(name) for name in ['torch','coremltools','transformers','numpy']},
        'python':sys.version,'precision':'FLOAT32','computeUnits':'CPU_ONLY','minimumTarget':'iOS18',
        'trained':False,'downloads':False,'originalNeuralTolerance':.002}
    c.publish(RUN/'export-inputs.json',manifest)
    if (RUN/'export-result.json').exists():
        saved=c.read(RUN/'export-result.json')
        for p,h in saved['files'].items(): c.require(c.digest(RUN/p)==h,'Export artifact changed')
        print('Export already complete; preserved'); return
    c.require(not (RUN/'export-reserved.json').exists(),'Unresolved export; inspect before retry')
    c.publish(RUN/'export-reserved.json',{'inputSHA256':c.digest(RUN/'export-inputs.json')})
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
    import numpy as np
    import torch
    import coremltools as ct
    from transformers import BertConfig, BertForSequenceClassification, BertModel
    torch.set_num_threads(4)
    config=BertConfig.from_pretrained(str(assets),local_files_only=True,num_labels=2)
    config._attn_implementation='eager'
    model=BertForSequenceClassification(config).eval()
    with gzip.open(weights,'rb') as stream: saved=torch.load(stream,map_location='cpu',weights_only=True)
    c.require(saved['fingerprint']==record['final']['fingerprint'],'Checkpoint fingerprint mismatch')
    model.load_state_dict(saved['model'],strict=True);del saved
    fixtures=c.read(fixture_path)['fixtures']; names=('input_ids','attention_mask','token_type_ids')
    reference=[]
    for fixture in fixtures:
        probabilities=[]
        for direction in fixture['directions']:
            tokens={name:torch.tensor(direction['tokens'][name],dtype=torch.long) for name in names}
            with torch.inference_mode(): probabilities.append(model(**tokens).logits.softmax(-1)[0,1].item())
        reference.append({'fixture':fixture['id'],'probabilities':probabilities})
    reference_delta=max(abs(p-d['probability']) for f,row in zip(fixtures,reference) for p,d in zip(row['probabilities'],f['directions']))
    c.publish(RUN/'pytorch-reference.json',{'rows':reference,'maximumDeltaVsHistorical':reference_delta})
    c.require(reference_delta<=1e-7,'PyTorch reference moved; inspect before converting')

    class FiniteMaskBert(BertModel):
        def get_extended_attention_mask(self,attention_mask,input_shape,device=None,dtype=None):
            return (1.0-attention_mask[:,None,None,:].to(dtype or self.dtype))*-10000.0
    backbone=FiniteMaskBert(model.config);backbone.load_state_dict(model.bert.state_dict(),strict=True)
    model.bert=backbone;model.eval()
    class Wrapper(torch.nn.Module):
        def __init__(self,model): super().__init__();self.model=model
        def forward(self,input_ids,attention_mask,token_type_ids):
            return self.model(input_ids=input_ids.long(),attention_mask=attention_mask.long(),token_type_ids=token_type_ids.long()).logits.softmax(-1)
    tensors=tuple(torch.tensor(fixtures[0]['directions'][0]['tokens'][name],dtype=torch.int32) for name in names)
    with torch.inference_mode(): traced=torch.jit.trace(Wrapper(model).eval(),tensors)
    print('Converting original seed-29 weights to FP32',flush=True)
    converted=ct.convert(traced,convert_to='mlprogram',minimum_deployment_target=ct.target.iOS18,
        inputs=[ct.TensorType(name=name,shape=(1,512),dtype=np.int32) for name in names],
        outputs=[ct.TensorType(name='probabilities',dtype=np.float32)],compute_precision=ct.precision.FLOAT32,
        compute_units=ct.ComputeUnit.CPU_ONLY)
    converted.user_defined_metadata['class_order']='["not_same", "same"]'
    converted.user_defined_metadata['weights_sha256']=record['final']['SHA256']
    package=RUN/'models/D3MatcherFP32.mlpackage';package.parent.mkdir(exist_ok=True)
    c.require(not package.exists(),'Unrecorded package exists')
    converted.save(str(package))
    rows=[]
    for fixture in fixtures:
        p=[float(converted.predict({name:np.asarray(d['tokens'][name],dtype=np.int32) for name in names})['probabilities'][0,1]) for d in fixture['directions']]
        rows.append({'fixture':fixture['id'],'probabilities':p})
    delta=max(abs(p-d['probability']) for f,row in zip(fixtures,rows) for p,d in zip(row['probabilities'],f['directions']))
    files={str(p.relative_to(RUN)):c.digest(p) for p in package.rglob('*') if p.is_file()}
    c.publish(RUN/'export-result.json',{'files':files,'rows':rows,'maximumNeuralDeltaVsPyTorch':delta,
        'originalConversionBoundMet':delta<=.002,'packageBytes':sum(p.stat().st_size for p in package.rglob('*') if p.is_file())})
    print({'maximumNeuralDeltaVsPyTorch':delta,'originalConversionBoundMet':delta<=.002},flush=True)


if __name__=='__main__':
    with c.lock(): main()
