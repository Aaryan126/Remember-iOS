#!/usr/bin/env python3
"""Device-only diagnostic; preserves the frozen Stage 1 gate and app binary."""
import argparse
from contextlib import contextmanager
import fcntl
import importlib.util
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('mac_diagnostic', ROOT/'scripts/ios27-parity-diagnostic/diagnose.py')
mac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mac)
c = mac.c
RUN = ROOT/'Evaluation/iOS27/phone-diagnostic'
UNITS = ['environment'] + [f'parity-{i:02}' for i in range(16)] + [f'embedding-{i:02}' for i in range(16)]
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


def safe_to_close():
    return not active() and c.safe_to_close() and all(
        (RUN/f'units/{p.parent.name}.json').exists()
        for p in (RUN/'attempts').glob('*/reserved.json'))


def hashes():
    paths = list(Path(__file__).parent.glob('*.py')) + [
        mac.RUN/'manifest.json', mac.RUN/'summary.json',
        c.RUN/'units/phone/environment.json', c.RUN/'units/phone/parity-00.json']
    return {str(p.relative_to(ROOT)): c.digest(p) for p in paths}


def verify():
    mac.verify()
    c.require(c.read(RUN/'manifest.json')['hashes'] == hashes(), 'Frozen diagnostic inputs changed')
    for p in (RUN/'units').glob('*.json'):
        row = c.read(p); raw = ROOT/row['rawPath']
        c.require(c.digest(raw) == row['rawSHA256'], 'Raw output changed')
        c.require(c.parse_result(c.read(raw)['stdout'], p.stem) == row['result'], 'Interpretation changed')
    return {'verified': True}


def boundary():
    observed = c.space()
    extra = sum(p.stat().st_size for base in [RUN, mac.RUN] for p in base.rglob('*') if p.is_file())
    c.require(observed['experimentBytes'] + extra < 8*c.GIB, 'Combined artifact cap reached')
    if STOP or (RUN/'pause.request.json').exists(): raise InterruptedError('Saved boundary')


def freeze(device):
    c.require(device, 'Device required')
    mac.verify()
    c.publish(RUN/'manifest.json', {'hashes': hashes(), 'device': device, 'units': UNITS,
        'maximumNewDeviceRequests': 31, 'reusedStage1Requests': 2,
        'purpose': 'collect diagnostic numeric failures; do not reinterpret as passes',
        'generation': False, 'stage2Started': False, 'originalScoreTolerance': 1e-7,
        'originalFeatureTolerance': 1e-8, 'originalNeuralTolerance': .002})


def save(unit, raw, origin):
    result = c.parse_result(c.read(raw)['stdout'], unit)
    c.publish(RUN/f'units/{unit}.json', {'result': result, 'origin': origin,
        'rawPath': str(raw.relative_to(ROOT)), 'rawSHA256': c.digest(raw)})
    return result


def check_native(result, unit):
    c.require(result['status'] == 'ok', 'Native error saved; stop diagnostic: '+unit)
    if unit.startswith('embedding'):
        c.require(result['result']['compatible'] and result['result']['decisionUnchanged'],
                  'Embedding incompatibility saved; stop diagnostic: '+unit)


def run(maximum):
    verify(); count = 0
    device = c.read(RUN/'manifest.json')['device']
    for unit in UNITS:
        boundary()
        dest = RUN/f'units/{unit}.json'
        if dest.exists():
            check_native(c.read(dest)['result'], unit)
            continue
        existing = c.RUN/f'units/phone/{unit}.json'
        if existing.exists():
            result = save(unit, c.RUN/c.read(existing)['rawPath'], 'reused-stage1')
        else:
            attempt = RUN/f'attempts/{unit}'
            c.require(not (attempt/'reserved.json').exists(), 'Unresolved request; collect without retry: '+unit)
            c.publish(attempt/'reserved.json', {'unit': unit, 'startedUnix': time.time()})
            args = ['xcrun', 'devicectl', 'device', 'process', 'launch', '--device', device,
                    '--console', '--timeout', '120', c.BUNDLE, '--unit', unit]
            try:
                response = c.command(args, timeout=150)
                wire = {'stdout': response.stdout, 'stderr': response.stderr, 'returnCode': response.returncode}
            except subprocess.TimeoutExpired:
                wire = {'timeout': True}
            raw = attempt/'raw.json'; c.publish(raw, wire)
            c.require(wire.get('returnCode') == 0, 'Device/console failure saved; collect before retry')
            result = save(unit, raw, 'new-device-observation')
        print(c.json.dumps({'saved': unit, 'status': result['status'],
            'originalGatePassed': result.get('result', {}).get('passed')}), flush=True)
        check_native(result, unit)
        count += 1
        if maximum and count >= maximum: break
    return {'savedThisRun': count}


def collect(unit):
    verify()
    c.require(unit in UNITS, 'Unknown unit')
    attempt = RUN/f'attempts/{unit}'
    c.require((attempt/'reserved.json').exists() and not (RUN/f'units/{unit}.json').exists(),
              'No unresolved request to collect')
    recovered = attempt/f'recovered-{time.time_ns()}.json'
    device = c.read(RUN/'manifest.json')['device']
    response = c.command(['xcrun', 'devicectl', 'device', 'copy', 'from', '--device', device,
        '--source', f'Documents/unit-{unit}.json', '--destination', str(recovered),
        '--domain-type', 'appDataContainer', '--domain-identifier', c.BUNDLE], 60)
    c.require(response.returncode == 0 and recovered.exists(), 'Checkpoint unavailable; do not rerun')
    result = c.parse_result('IOS27_RESULT '+c.json.dumps(c.read(recovered)), unit)
    raw = attempt/f'collected-{time.time_ns()}.json'
    c.publish(raw, {'stdout': 'IOS27_RESULT '+c.json.dumps(result),
        'deviceFileSHA256': c.digest(recovered), 'collectedWithoutInference': True})
    save(unit, raw, 'device-checkpoint-recovery')
    return {'collected': unit, 'newInference': False}


def evaluate():
    verify()
    rows = {p.stem: c.read(p) for p in (RUN/'units').glob('*.json')}
    c.require(all(f'parity-{i:02}' in rows for i in range(16)), 'Incomplete parity collection')
    fixtures = c.read(ROOT/'Evaluation/AppMatcher/parity-inputs.json')['fixtures']
    params = c.read(ROOT/'Remember/Remember/MatcherAssets/D3Parameters.json')
    pairs = mac.metrics(fixtures, rows, params)
    comparisons = []
    for i in range(16):
        key = f'parity-{i:02}'
        a, b = [r['result']['result'] for r in [rows[key], c.read(mac.RUN/f'units/{key}.json')]]
        comparisons.append({'unit': key, 'probabilitiesExactlyEqual': a['probabilities'] == b['probabilities'],
                            'scoreDelta': abs(a['score']-b['score'])})
    errors = {key: r['result'].get('error') for key,r in rows.items() if r['result']['status'] != 'ok'}
    summary = {'stage1Complete': False, 'stage2Started': False, 'parityCollectionComplete': True,
        'plannedUnits': len(UNITS), 'savedUnits': len(rows), 'nativeErrors': errors,
        'environment': rows['environment']['result']['result'], 'pairs': pairs,
        'macComparison': comparisons, 'strictGatePasses': sum(r['originalStrictGatePassed'] for r in pairs),
        'unchangedDecisions': sum(r['oldAccepted'] == r['newAccepted'] for r in pairs),
        'maximumNeuralDeltaVsPyTorch': max(r['maxNeuralDeltaVsPyTorch'] for r in pairs),
        'maximumCombinedDeltaVsOldCoreML': max(r['combinedDeltaVsOldCoreML'] for r in pairs),
        'embeddingUnitsSaved': sum(key.startswith('embedding') for key in rows),
        'embeddingUnitsPassed': sum(key.startswith('embedding') and r['result']['status']=='ok'
            and r['result']['result'].get('compatible',False)
            and r['result']['result'].get('decisionUnchanged',False) for key,r in rows.items())}
    c.publish(RUN/f'evaluations/{time.time_ns()}.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze','run','pause','resume','collect','evaluate','verify','status'])
    parser.add_argument('--device'); parser.add_argument('--unit'); parser.add_argument('--max-units',type=int,default=0)
    args = parser.parse_args(); c.require(args.max_units >= 0, 'Invalid bound')
    if args.action == 'pause':
        if not (RUN/'pause.request.json').exists(): c.publish(RUN/'pause.request.json', {'requestedUnix': time.time()})
        result = {'paused': True, 'safeToClose': safe_to_close()}
    elif args.action == 'status':
        result = {'safeToClose': safe_to_close(), 'savedUnits': len(list((RUN/'units').glob('*.json')))}
    else:
        with lock(), c.lock():
            if args.action == 'freeze': freeze(args.device); result = {'frozen': True}
            elif args.action == 'verify': result = verify()
            elif args.action == 'evaluate': result = evaluate()
            elif args.action == 'collect': result = collect(args.unit)
            else:
                marker = RUN/'pause.request.json'
                if args.action == 'resume' and marker.exists():
                    c.publish(RUN/f'resumes/{time.time_ns()}.json', {'pauseSHA256': c.digest(marker)})
                    marker.unlink()
                result = run(args.max_units)
    print(c.json.dumps(result))


def stop(_signal, _frame):
    global STOP
    STOP = True


if __name__ == '__main__':
    signal.signal(signal.SIGINT, stop); signal.signal(signal.SIGTERM, stop)
    try: main()
    except InterruptedError:
        print(c.json.dumps({'paused': True, 'safeToClose': safe_to_close()})); raise SystemExit(75)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(c.json.dumps({'error': str(error), 'stage2Started': False})); raise SystemExit(1)
