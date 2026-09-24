#!/usr/bin/env python3
"""Resume the frozen phone screen without mutating/retrying historical evidence."""
import argparse
import importlib.util
from pathlib import Path
import signal
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('frozen_quality', ROOT/'scripts/ios27-quality/run.py')
q = importlib.util.module_from_spec(spec); spec.loader.exec_module(q)
c = q.c
ORIGINAL = c.RUN
RUN = ROOT/'Evaluation/iOS27/quality-continuation'
EXCEPTION = 'c7-004'
STOP = False


def sources():
    paths = list(SCRIPT.glob('*.py')) + [RUN/'PROTOCOL.md', ORIGINAL/'checkpoint.json']
    return {str(p.relative_to(ROOT)): c.digest(p) for p in sorted(paths)}


def historical_verify():
    q.verify()
    for name, sha in c.read(ORIGINAL/'checkpoint.json')['files'].items():
        c.require(c.digest(ORIGINAL/name) == sha, 'Historical checkpoint changed: '+name)


def freeze():
    historical_verify(); q.space()
    c.require(not (ORIGINAL/f'units/phone/{EXCEPTION}.json').exists(), 'Unexpected historical outcome; review rather than discard')
    c.require(c.read(ORIGINAL/'process-closure.json')['safeToClose'], 'Historical process not closed')
    raw = c.read(ORIGINAL/f'attempts/phone/{EXCEPTION}/raw.json')
    c.require(raw['returnCode'] != 0 and not raw['stdout'] and 'Unexpected EOF' in raw['stderr'], 'Exception evidence mismatch')
    remaining = [u for u in q.schedule() if u != EXCEPTION and not (ORIGINAL/f'units/phone/{u}.json').exists()]
    c.require(len(remaining) == 223 and remaining[0] == 'boundary-004', 'Continuation inventory mismatch')
    c.publish(RUN/'disposition.json', {'unit': EXCEPTION, 'origin': 'host-transport-disposition',
        'status': 'error', 'errorKind': 'transport-unknown-execution', 'prediction': None,
        'retryAllowed': False, 'countAgainstBudget': True,
        'rawSHA256': c.digest(ORIGINAL/f'attempts/phone/{EXCEPTION}/raw.json'),
        'closureSHA256': c.digest(ORIGINAL/'process-closure.json')})
    c.publish(RUN/'manifest.json', {'sources': sources(), 'remaining': remaining,
        'dispositionSHA256': c.digest(RUN/'disposition.json'), 'unchangedNativeManifestSHA256': c.digest(ORIGINAL/'manifest.json'),
        'maximumTotalAttempts': q.CAP, 'scheduledTotalIncludingPrior': 234, 'noRetries': True})
    return {'frozen': True, 'remainingRequests': len(remaining)}


def verify():
    historical_verify()
    manifest = c.read(RUN/'manifest.json')
    c.require(manifest['sources'] == sources(), 'Continuation sources changed')
    c.require(c.digest(RUN/'disposition.json') == manifest['dispositionSHA256'], 'Disposition changed')
    c.require(c.digest(ORIGINAL/'manifest.json') == manifest['unchangedNativeManifestSHA256'], 'Native build changed')
    for path in (RUN/'units').glob('*.json'):
        c.require(path.stem in manifest['remaining'], 'Unscheduled/duplicate unit')
        row = c.read(path); raw = RUN/row['rawPath']
        c.require(c.digest(raw) == row['rawSHA256'], 'Raw continuation evidence changed')
        c.require(c.parse_result(c.read(raw)['stdout'], path.stem) == row['result'], 'Native interpretation changed')
        if 'deviceFile' in c.read(raw):
            r = c.read(raw)
            c.require(c.digest(RUN/r['deviceFile']) == r['deviceFileSHA256'], 'Collected checkpoint changed')
    return {'verified': True}


def native(unit):
    c.require(unit != EXCEPTION, 'Transport disposition is not a native response')
    path = ORIGINAL/f'units/phone/{unit}.json'
    return c.read(path if path.exists() else RUN/f'units/{unit}.json')['result']


def outcome(packet, unit):
    if unit == EXCEPTION:
        disposition = c.read(RUN/'disposition.json')
        return {k: disposition[k] for k in ('status', 'errorKind', 'prediction')}
    return q.interpretation(packet, native(unit))


def completed(unit):
    return unit == EXCEPTION or (ORIGINAL/f'units/phone/{unit}.json').exists() or (RUN/f'units/{unit}.json').exists()


def check_stops():
    invalid = 0
    for unit in q.schedule():
        if unit.startswith('control-'):
            continue
        if not completed(unit):
            break
        if unit == EXCEPTION:
            invalid = 0
            continue
        row = native(unit)
        c.require(row['status'] == 'ok', 'Native failure retained; stop: '+unit)
        request = q.inputs()['requests'][unit]
        c.require(all(row['result'][k] == request[k] for k in ('context', 'reviewer')), 'Request identity mismatch')
        packet = q.inventory()[0]['contexts'][request['context']]
        invalid = invalid+1 if outcome(packet, unit)['status'] == 'error' else 0
        c.require(invalid < 3, 'Three consecutive invalid outputs; stop without changes')


def attempt_count():
    original = sum(not p.parent.name.startswith('control-') for p in (ORIGINAL/'attempts/phone').glob('*/reserved.json'))
    return q.PRIOR_REQUESTS + original + len(list((RUN/'attempts').glob('*/reserved.json')))


def safe_to_close():
    return not c.active() and all((RUN/f'units/{p.parent.name}.json').exists() for p in (RUN/'attempts').glob('*/reserved.json'))


def boundary():
    q.space()
    if STOP or (RUN/'pause.request.json').exists():
        raise InterruptedError('Pause saved at atomic boundary')


def inspect(device):
    results = {}
    for name, options in [('lockState', []), ('apps', ['--bundle-id', c.BUNDLE]),
                          ('processes', ['--search', 'CompatibilityProbe'])]:
        args = ['xcrun', 'devicectl', 'device', 'info', name, '--device', device, *options, '--json-output', '-']
        response = q.base_command(args, 30)
        record = {'command': args, 'returnCode': response.returncode, 'stdout': response.stdout, 'stderr': response.stderr}
        c.publish(RUN/f'inspections/{c.time.time_ns()}-{name}.json', record)
        c.require(response.returncode == 0, 'Read-only device preflight failed: '+name)
        results[name] = c.json.loads(response.stdout)['result']
    c.require(not results['lockState']['passcodeRequired'] and results['lockState']['unlockedSinceBoot'], 'Unlock the phone before continuing')
    c.require(len(results['apps']['apps']) == 1 and results['apps']['apps'][0]['bundleIdentifier'] == c.BUNDLE, 'Isolated app unavailable')
    c.require(not results['processes']['runningProcesses'], 'A probe is already running; do not launch another')
    return {'devicePreflightPassed': True, 'modelRequests': 0}


def run(device, maximum, resume):
    verify(); check_stops()
    if resume and (RUN/'pause.request.json').exists():
        marker = RUN/'pause.request.json'
        c.publish(RUN/f'resumptions/{c.time.time_ns()}.json', {'pauseSHA256': c.digest(marker)})
        marker.unlink()  # Only this continuation's marker, never historical evidence.
    boundary(); inspect(device)
    done = 0
    for unit in c.read(RUN/'manifest.json')['remaining']:
        boundary()
        if completed(unit):
            continue
        reservation = RUN/f'attempts/{unit}/reserved.json'
        c.require(not reservation.exists(), 'Unresolved launch; collect without inference: '+unit)
        c.require(attempt_count() < q.CAP, 'Generation cap reached')
        c.publish(reservation, {'unit': unit, 'device': device, 'startedUnix': c.time.time(), 'request': q.inputs()['requests'][unit]})
        args = ['xcrun', 'devicectl', 'device', 'process', 'launch', '--device', device, '--console', '--timeout', '120', c.BUNDLE, '--unit', unit]
        try:
            response = q.base_command(args, 150)
            raw = {'returnCode': response.returncode, 'stdout': response.stdout, 'stderr': response.stderr}
        except c.subprocess.TimeoutExpired as error:
            raw = {'timeout': True, 'stdout': str(error.stdout or ''), 'stderr': str(error.stderr or '')}
        path = reservation.parent/'raw.json'; c.publish(path, raw)
        c.require(raw.get('returnCode') == 0, 'Native process/transport failure saved: '+unit)
        result = c.parse_result(raw['stdout'], unit)
        c.publish(RUN/f'units/{unit}.json', {'result': result, 'origin': 'native-continuation',
            'rawPath': str(path.relative_to(RUN)), 'rawSHA256': c.digest(path)})
        check_stops(); done += 1
        request = q.inputs()['requests'][unit]
        valid = outcome(q.inventory()[0]['contexts'][request['context']], unit)['status']
        print(c.json.dumps({'saved': unit, 'validation': valid, 'newCompleted': len(list((RUN/'units').glob('*.json'))), 'attemptsIncludingPrior': attempt_count()}), flush=True)
        if maximum and done >= maximum:
            break
    return {'savedThisRun': done}


def collect(device, unit):
    verify()
    c.require(unit in c.read(RUN/'manifest.json')['remaining'] and not completed(unit), 'Not a missing continuation unit')
    attempt = RUN/f'attempts/{unit}'
    c.require((attempt/'reserved.json').exists(), 'No reserved attempt')
    recovered = attempt/f'recovered-{c.time.time_ns()}.json'
    args = ['xcrun', 'devicectl', 'device', 'copy', 'from', '--device', device, '--source', f'Documents/unit-{unit}.json',
        '--destination', str(recovered), '--domain-type', 'appDataContainer', '--domain-identifier', c.BUNDLE]
    response = q.base_command(args, 30)
    c.publish(attempt/f'collection-{c.time.time_ns()}.json', {'command': args, 'returnCode': response.returncode, 'stdout': response.stdout, 'stderr': response.stderr})
    c.require(response.returncode == 0 and recovered.exists(), 'Device result unavailable; no retry')
    result = c.parse_result('IOS27_RESULT '+c.json.dumps(c.read(recovered)), unit)
    raw = attempt/f'collected-{c.time.time_ns()}.json'
    c.publish(raw, {'stdout': 'IOS27_RESULT '+c.json.dumps(result), 'deviceFile': str(recovered.relative_to(RUN)), 'deviceFileSHA256': c.digest(recovered)})
    c.publish(RUN/f'units/{unit}.json', {'result': result, 'origin': 'native-device-recovery', 'rawPath': str(raw.relative_to(RUN)), 'rawSHA256': c.digest(raw)})
    return {'collectedWithoutInference': unit}


def evaluate():
    verify()
    c.require(all(completed(unit) for unit in q.schedule()), 'Incomplete screen: cannot evaluate as complete')
    packets = q.old.packets(); data = q.inventory()[0]
    controls = {native(u)['result']['key']: native(u)['result'] for u in q.schedule() if u.startswith('control-')}
    indices = {key: i for i, key in enumerate(data['contexts'])}
    historical = {name: {x['queryID']: x for x in q.old.c.read_unit(q.c6_run.RUN/f'predictions/{name}.json')} for name in ('baseline', '29')}
    output = {name: [] for name in ('historical-baseline', 'historical-29', 'fp16', 'fp32', 'always-abstain')}
    for reviewer in q.REVIEWERS:
        for suffix in ('', '-fp16-veto', '-fp16-confirm', '-fp32-veto', '-fp32-confirm'):
            output[reviewer+suffix] = []
    for packet in packets:
        key = packet['queryID']; visible = {x['id']: x['text'] for x in packet['sources']}
        pair_key = q.old.c.pair_key(*(visible[x] for x in packet['pair']))
        pair_predictions = {p: q.prediction(packet, controls[pair_key]['scores'][p]['accepted']) for p in ('fp16', 'fp32')}
        for name, pred in [('historical-'+n, historical[n][key]) for n in historical] + list(pair_predictions.items()) + [('always-abstain', q.prediction(packet, False))]:
            output[name].append({'queryID': key, 'status': 'ok', 'prediction': pred})
        index = indices[data['mapping'][key]]
        for reviewer in q.REVIEWERS:
            local = outcome(packet, f'{reviewer}-{index:03}')
            output[reviewer].append({'queryID': key, **local})
            for precision, pred in pair_predictions.items():
                for mode in ('veto', 'confirm'):
                    output[f'{reviewer}-{precision}-{mode}'].append({'queryID': key, **q.old.combine(pred, local, mode)})
    result = {'exposedDiagnostic': True, 'productionQualified': False, 'pairControlsNotWholeOrganizer': True,
        'scheduledPrimary': 224, 'scheduledRepeats': 8, 'transportUnknownOutcomes': [EXCEPTION],
        'expandedPacketsPerReviewer': 160, 'attemptsIncludingPrior': attempt_count()}
    for kind, path in [('original', q.old.c5_run.RUN/'release/gold.json'), ('adjudicated', q.c6_run.RUN/'adjudicated-gold.json')]:
        labels = c.read(path)['labels']
        metrics = {name: q.old.metrics(packets, labels, rows) for name, rows in output.items()}
        deltas = {name: q.changes(packets, labels, output['fp16'], rows) for name, rows in output.items()}
        result[kind] = {'metrics': metrics, 'changesVsFP16': deltas,
            'gates': {name: q.gate(metrics[name], deltas[name]) for name in output if name.startswith(q.REVIEWERS)}}
    result['repeats'] = []
    for reviewer in q.REVIEWERS:
        rows = [native(f'{reviewer}-{i:03}') for i in range(112) if f'{reviewer}-{i:03}' != EXCEPTION]
        seconds = [r['result']['generationSeconds'] for r in rows if r['status'] == 'ok']
        result.setdefault('generationSeconds', {})[reviewer] = {'median': statistics.median(seconds) if seconds else None,
            'maximum': max(seconds) if seconds else None, 'count': len(seconds)}
        for i in q.REPEATS:
            packet = list(data['contexts'].values())[i]
            a = outcome(packet, f'{reviewer}-{i:03}'); b = outcome(packet, f'repeat-{reviewer}-{i:03}')
            valid = a['status'] == b['status'] == 'ok'
            result['repeats'].append({'reviewer': reviewer, 'index': i, 'bothValid': valid,
                'verdictAgreement': valid and a['prediction']['verdict'] == b['prediction']['verdict'],
                'exactPredictionAgreement': valid and a == b})
    result['precisionDecisionDifferences'] = sum(x['scores']['fp16']['accepted'] != x['scores']['fp32']['accepted'] for x in controls.values())
    for name, rows in output.items():
        c.publish(RUN/f'predictions/{name}.json', rows)
    c.publish(RUN/'summary.json', result)
    paths = list((RUN/'predictions').glob('*.json')) + list((RUN/'units').glob('*.json')) + [RUN/'summary.json', RUN/'disposition.json']
    c.publish(RUN/'complete.json', {'files': {str(p.relative_to(RUN)): c.digest(p) for p in paths}, 'originalCheckpointSHA256': c.digest(ORIGINAL/'checkpoint.json'), 'productionQualified': False})
    return {'evaluated': True, 'gates': {name: x['passed'] for name, x in result['adjudicated']['gates'].items()}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'verify', 'inspect', 'run', 'resume', 'pause', 'status', 'collect', 'evaluate'])
    parser.add_argument('--device'); parser.add_argument('--max-units', type=int, default=0); parser.add_argument('--unit')
    args = parser.parse_args(); c.require(args.max_units >= 0, 'Invalid limit')
    if args.action == 'pause':
        marker = RUN/'pause.request.json'
        if not marker.exists(): c.publish(marker, {'requestedUnix': c.time.time()})
        return {'pauseRequested': True, 'safeToClose': safe_to_close()}
    if args.action == 'status':
        return {'safeToClose': safe_to_close(), 'paused': (RUN/'pause.request.json').exists(), 'savedNewUnits': len(list((RUN/'units').glob('*.json'))), 'attemptsIncludingPrior': attempt_count(), **q.space()}
    with c.lock():  # Shared with original worker; no historical evidence writes.
        if args.action == 'freeze': return freeze()
        if args.action == 'verify': return verify()
        if args.action == 'evaluate': return evaluate()
        c.require(args.device, 'Specify --device')
        if args.action == 'inspect': return inspect(args.device)
        if args.action == 'collect': return collect(args.device, args.unit)
        return run(args.device, args.max_units, args.action == 'resume')


def stop_signal(_signal, _frame):
    global STOP
    STOP = True


if __name__ == '__main__':
    signal.signal(signal.SIGINT, stop_signal); signal.signal(signal.SIGTERM, stop_signal)
    try: print(c.json.dumps(main(), sort_keys=True))
    except InterruptedError:
        print(c.json.dumps({'paused': True, 'safeToClose': safe_to_close()})); sys.exit(75)
    except (ValueError, OSError, c.subprocess.SubprocessError) as error:
        print(c.json.dumps({'error': str(error), 'safeToClose': safe_to_close()})); sys.exit(1)
