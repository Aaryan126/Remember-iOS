#!/usr/bin/env python3
"""Collect cross-runtime drift without changing Stage 1's frozen pass/fail rules."""
import argparse
from contextlib import contextmanager
import fcntl
import importlib.util
import json
import math
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('stage1', ROOT/'scripts/ios27-evaluation/run.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
RUN = ROOT/'Evaluation/iOS27/parity-diagnostic'
KEYS = [f'parity-{i:02}' for i in range(16)] + ['repeat-00', 'repeat-15']
STOP = False


@contextmanager
def lock():
    RUN.mkdir(parents=True, exist_ok=True)
    with (RUN/'worker.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def active():
    try:
        with lock(): return False
    except BlockingIOError: return True


def hashes():
    files = list(Path(__file__).parent.glob('*.py')) + [c.RUN/'manifest.json',
        c.RUN/'units/mac/parity-00.json', ROOT/'Evaluation/AppMatcher/conversion.json']
    return {str(p.relative_to(ROOT)): c.digest(p) for p in files}


def verify():
    c.verify()
    c.require(c.read(RUN/'manifest.json')['hashes'] == hashes(), 'Diagnostic inputs changed')
    for p in (RUN/'units').glob('*.json'):
        row = c.read(p)
        raw = ROOT/row['rawPath']
        c.require(c.digest(raw) == row['rawSHA256'], 'Raw hash mismatch')
        c.require(c.parse_result(c.read(raw)['stdout'], row['nativeUnit']) == row['result'], 'Result interpretation changed')
    return {'verified': True}


def resources():
    observed = c.space()
    extra = sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
    c.require(observed['experimentBytes'] + extra < 8*c.GIB, 'Combined experiment cap reached')


def boundary():
    resources()
    if STOP or (RUN/'pause.request.json').exists(): raise InterruptedError('saved boundary')


def freeze():
    c.verify()
    c.publish(RUN/'manifest.json', {'hashes': hashes(), 'units': KEYS,
        'purpose': 'diagnostic-only; original failed gate retained', 'stage2Started': False,
        'originalFeatureTolerance': 1e-8, 'originalCombinedScoreTolerance': 1e-7,
        'originalConversionProbabilityTolerance': .002, 'newMacRequestsMaximum': 17,
        'phoneInference': False, 'generativeInference': False})


def run(maximum):
    verify()
    count = 0
    for key in KEYS:
        boundary()
        dest = RUN/f'units/{key}.json'
        if dest.exists(): continue
        native = key.replace('repeat-', 'parity-')
        if key == 'parity-00':
            saved = c.read(c.RUN/'units/mac/parity-00.json')
            raw = c.RUN/saved['rawPath']
            result = saved['result']
            origin = 'existing-stage1-failure-reused'
        else:
            attempt = RUN/f'attempts/{key}'
            c.require(not (attempt/'reserved.json').exists(), 'Unresolved attempt; no blind retry: '+key)
            c.publish(attempt/'reserved.json', {'nativeUnit': native, 'startedUnix': time.time()})
            args = [str(c.WORK/'compatibility-probe'), '--root', str(c.WORK/'Resources'), '--unit', native]
            try:
                response = c.command(args, timeout=150)
                wire = {'stdout': response.stdout, 'stderr': response.stderr, 'returnCode': response.returncode}
            except subprocess.TimeoutExpired:
                wire = {'timeout': True}
            raw = attempt/'raw.json'
            c.publish(raw, wire)
            c.require(wire.get('returnCode') == 0, 'Native failure saved: '+key)
            result = c.parse_result(wire['stdout'], native)
            origin = 'new-native-observation'
        c.publish(dest, {'nativeUnit': native, 'origin': origin, 'rawPath': str(raw.relative_to(ROOT)),
                        'rawSHA256': c.digest(raw), 'result': result})
        # Numeric gate failures are measured, not suppressed or turned into passes.
        c.require(result['status'] == 'ok', 'Native/schema error; stop collection')
        print(json.dumps({'saved':key, 'originalGatePassed':result['result']['passed']}), flush=True)
        count += 1
        if maximum and count >= maximum: break
    return {'savedThisRun':count}


def sigmoid(x):
    return 1/(1+math.exp(-x)) if x >= 0 else math.exp(x)/(1+math.exp(x))


def combined(features, probability, model):
    p = max(1e-6, min(1-1e-6, probability))
    values = features + [math.log(p/(1-p))]
    return sigmoid(model['intercept'] + sum((v-m)/s*w for v,m,s,w in
        zip(values,model['mean'],model['scale'],model['coefficient'])))


def metrics(fixtures, rows, parameters):
    threshold = parameters['threshold']
    output = []
    for i, f in enumerate(fixtures):
        native = rows[f'parity-{i:02}']['result']['result']
        reference = [d['probability'] for d in f['directions']]
        probabilities = native['probabilities']
        mean = sum(probabilities)/2
        reconstructed = combined(f['features'], mean, parameters['combiner'])
        original_reconstructed = combined(f['features'], sum(reference)/2, parameters['combiner'])
        output.append({'fixture': f['id'], 'tokenParity': native['tokenParity'],
            'featureDelta': native['maximumFeatureDelta'],
            'combinedDeltaVsOldCoreML': abs(native['score']-f['coreMLScore']),
            'combinedDeltaVsPyTorch': abs(native['score']-f['expectedScore']),
            'maxNeuralDeltaVsPyTorch': max(abs(a-b) for a,b in zip(reference, probabilities)),
            'independentCombinerDelta': abs(reconstructed-native['score']),
            'originalPyTorchCombinerReconstructionDelta': abs(original_reconstructed-f['expectedScore']),
            'oldScore': f['coreMLScore'], 'newScore': native['score'],
            'distanceFromThreshold': abs(f['coreMLScore']-threshold),
            'oldAccepted': f['coreMLScore']>=threshold, 'newAccepted': native['score']>=threshold,
            'originalStrictGatePassed': native['passed']})
    return output


def evaluate():
    verify()
    rows = {p.stem:c.read(p) for p in (RUN/'units').glob('*.json')}
    c.require(set(rows) == set(KEYS), 'Incomplete collection; do not summarize as complete')
    fixtures = c.read(ROOT/'Evaluation/AppMatcher/parity-inputs.json')['fixtures']
    parameters = c.read(ROOT/'Remember/Remember/MatcherAssets/D3Parameters.json')
    table = metrics(fixtures, rows, parameters)
    repeats = []
    for i in [0, 15]:
        a,b = [rows[k]['result']['result'] for k in [f'parity-{i:02}',f'repeat-{i:02}']]
        repeats.append({'fixture':i, 'probabilitiesExactlyEqual':a['probabilities']==b['probabilities'],
                        'scoreDelta':abs(a['score']-b['score'])})
    summary = {'diagnosticComplete':True, 'stage1Complete':False, 'stage2Started':False,
        'uniquePairs':16, 'newNativeRequests':17, 'reusedRequests':1,
        'unchangedDecisions':sum(r['oldAccepted']==r['newAccepted'] for r in table),
        'strictGatePasses':sum(r['originalStrictGatePassed'] for r in table),
        'maximumCombinedDeltaVsOldCoreML':max(r['combinedDeltaVsOldCoreML'] for r in table),
        'maximumNeuralDeltaVsPyTorch':max(r['maxNeuralDeltaVsPyTorch'] for r in table),
        'maximumIndependentCombinerDelta':max(r['independentCombinerDelta'] for r in table),
        'maximumFeatureDelta':max(r['featureDelta'] for r in table),
        'minimumReferenceThresholdMargin':min(r['distanceFromThreshold'] for r in table),
        'conversionProbabilityBoundMet':all(r['maxNeuralDeltaVsPyTorch']<=.002 for r in table),
        'repeatability':repeats, 'pairs':table}
    c.publish(RUN/'summary.json', summary)
    return {k:v for k,v in summary.items() if k!='pairs'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('action', choices=['freeze','run','resume','pause','status','evaluate','verify'])
    p.add_argument('--max-units',type=int,default=0)
    args=p.parse_args()
    c.require(args.max_units>=0, 'Invalid unit bound')
    if args.action=='pause':
        if not (RUN/'pause.request.json').exists(): c.publish(RUN/'pause.request.json', {'requestedUnix':time.time()})
        result={'paused':True,'safeToClose':not active()}
    elif args.action=='status':
        result={'safeToClose':not active(), 'savedUnits':len(list((RUN/'units').glob('*.json')))}
    else:
        with lock(), c.lock():
            if args.action=='freeze': freeze(); result={'frozen':True}
            elif args.action=='verify': result=verify()
            elif args.action=='evaluate': result=evaluate()
            else:
                marker=RUN/'pause.request.json'
                if args.action=='resume' and marker.exists():
                    c.publish(RUN/f'resumes/{time.time_ns()}.json',{'pauseSHA256':c.digest(marker)})
                    marker.unlink()
                result=run(args.max_units)
    print(json.dumps(result))


def stop(_s,_f):
    global STOP
    STOP=True


if __name__=='__main__':
    signal.signal(signal.SIGINT,stop); signal.signal(signal.SIGTERM,stop)
    try: main()
    except InterruptedError:
        print(json.dumps({'paused':True,'safeToClose':True})); raise SystemExit(75)
    except (ValueError,OSError,subprocess.SubprocessError) as e:
        print(json.dumps({'error':str(e),'stage2Started':False})); raise SystemExit(1)
