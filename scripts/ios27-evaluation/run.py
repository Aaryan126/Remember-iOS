#!/usr/bin/env python3
"""Isolated stage-one runner; no Git, paid API, or personal-vault operations."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'Evaluation/iOS27/stage1'
SCRIPT = Path(__file__).resolve().parent
WORK = RUN / 'build'
BUNDLE = 'SimpleStudio.Remember.IOS27Compatibility'
UNITS = ['environment'] + [f'parity-{i:02}' for i in range(16)] + [f'embedding-{i:02}' for i in range(16)] + ['generation']
GIB = 1024 ** 3
STOP = False


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def publish(path, value):
    """Exclusive publication; repeats must reproduce exactly the same bytes."""
    path = Path(path)
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == data, f'Refusing to replace {path}')
        return
    temp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    try:
        with temp.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def space():
    free = shutil.disk_usage(ROOT).free
    size = sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file()) if RUN.exists() else 0
    require(free >= 10 * GIB, '10 GiB free-space reserve reached')
    require(size < 8 * GIB, '8 GiB experiment cap reached')
    return {'freeBytes': free, 'experimentBytes': size}


@contextmanager
def lock():
    RUN.mkdir(parents=True, exist_ok=True)
    with (RUN / 'worker.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def active():
    try:
        with lock():
            return False
    except BlockingIOError:
        return True


def sources():
    paths = [ROOT/'Evaluation/AppMatcher/parity-inputs.json',
             ROOT/'Remember/Remember/ProjectIntelligence.swift',
             ROOT/'Remember/Remember.xcodeproj/project.pbxproj']
    paths += list(SCRIPT.glob('*.swift')) + list(SCRIPT.glob('*.py')) + list(SCRIPT.glob('*.template'))
    paths += [ROOT/f'Remember/Remember/{n}.swift' for n in
              ['D3Tokenizer', 'D3Features', 'D3PairMatcher', 'D3OrganizationPolicy']]
    paths += [p for p in (ROOT/'Remember/Remember/MatcherAssets').rglob('*') if p.is_file()]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def command(args, timeout=120):
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout)


def prepare():
    space()
    require(not (RUN/'manifest.json').exists(), 'Already frozen; preserve this attempt')
    base = WORK/'Sources'
    base.mkdir(parents=True, exist_ok=True)
    for name in ['D3Tokenizer', 'D3Features', 'D3PairMatcher', 'D3OrganizationPolicy']:
        shutil.copy2(ROOT/f'Remember/Remember/{name}.swift', base/f'{name}.swift')
    shutil.copy2(SCRIPT/'CompatibilityProbe.swift', base/'CompatibilityProbe.swift')
    original = (ROOT/'Remember/Remember/ProjectIntelligence.swift').read_text()
    start, end = 'nonisolated struct ProjectEmbedding:', 'nonisolated struct ProjectTopicEvidence'
    require(original.count(start) == original.count(end) == 1, 'Production extraction boundaries changed')
    fragment = original[original.index(start):original.index(end)]
    # Copy declarations verbatim, retaining the production provider and math. No rewritten pooling.
    (base/'ProductionEmbedding.swift').write_text('import Foundation\nimport NaturalLanguage\n'
        'enum ProjectPreferences { static let embeddingsAvailable = Notification.Name("remember.project.embeddingsAvailable") }\n' + fragment)
    resources = WORK/'Resources'
    resources.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'Evaluation/AppMatcher/parity-inputs.json', resources/'parity-inputs.json')
    shutil.copytree(ROOT/'Remember/Remember/MatcherAssets', resources/'MatcherAssets', dirs_exist_ok=True)
    # A standalone synchronized Xcode target; no package resolution or app group entitlements.
    import re
    team = re.search(r'DEVELOPMENT_TEAM = ([A-Z0-9]+);', (ROOT/'Remember/Remember.xcodeproj/project.pbxproj').read_text())
    require(team, 'Missing signing team')
    template = (SCRIPT/'project.pbxproj.template').read_text()
    project = WORK/'CompatibilityProbe.xcodeproj'
    project.mkdir(exist_ok=True)
    (project/'project.pbxproj').write_text(template.replace('__TEAM__', team[1]))
    publish(RUN/f'preparations/{time.time_ns()}.json', {'sources': sources(), 'limits': {'freeGiB': 10, 'capGiB': 8}})
    return {'prepared': True, 'unitsPerPlatform': len(UNITS)}


def build(platform):
    require(not (RUN/'manifest.json').exists(), 'Frozen; do not rebuild')
    space()
    if platform == 'mac':
        args = ['xcrun', 'swiftc', '-parse-as-library', '-O', '-module-cache-path', str(WORK/'module-cache')]
        args += [str(p) for p in sorted((WORK/'Sources').glob('*.swift'))]
        args += ['-o', str(WORK/'compatibility-probe')]
    else:
        args = ['xcodebuild', '-project', str(WORK/'CompatibilityProbe.xcodeproj'),
                '-scheme', 'CompatibilityProbe', '-destination', 'generic/platform=iOS',
                '-derivedDataPath', str(WORK/'device-build'), '-disableAutomaticPackageResolution',
                '-skipPackageUpdates', 'build', '-quiet']
    result = command(args, timeout=600)
    receipt = {'command': args, 'returnCode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
               'sources': sources(), 'platform': platform}
    publish(RUN/f'build-attempts/{time.time_ns()}.json', receipt)
    require(result.returncode == 0, 'Build failed; see build-attempts')
    if platform == 'mac':
        # Compile once into the budgeted workspace, rather than 16 temporary model caches.
        model = WORK/'Resources/MatcherAssets/D3Matcher.mlmodelc'
        if not model.exists():
            compiled = command(['xcrun', 'coremlcompiler', 'compile',
                str(WORK/'Resources/MatcherAssets/D3Matcher.mlpackage'), str(model.parent)], 120)
            publish(RUN/f'build-attempts/{time.time_ns()}.json', {'platform': 'mac-model',
                'returnCode': compiled.returncode, 'stdout': compiled.stdout, 'stderr': compiled.stderr})
            require(compiled.returncode == 0, 'Model compilation failed')
    return {'built': platform, 'resources': space()}


def freeze():
    require((WORK/'compatibility-probe').is_file(), 'Build Mac probe first')
    generated = {str(p.relative_to(RUN)): digest(p) for p in WORK.rglob('*')
                 if p.is_file() and ('Sources' in p.parts or 'Resources' in p.parts or p.suffix == '.pbxproj')}
    value = {'schemaVersion': 1, 'sources': sources(), 'generated': generated, 'units': UNITS,
             'macBinarySHA256': digest(WORK/'compatibility-probe'),
             'stage': 1, 'stage2AuthorizedToStart': False,
             'system': command(['sw_vers']).stdout, 'xcode': command(['xcodebuild', '-version']).stdout}
    app = WORK/'device-build/Build/Products/Debug-iphoneos/CompatibilityProbe.app'
    if app.exists():
        value['phoneFiles'] = {str(p.relative_to(RUN)): digest(p) for p in app.rglob('*') if p.is_file()}
    publish(RUN/'manifest.json', value)


def verify():
    manifest = read(RUN/'manifest.json')
    require(manifest['sources'] == sources(), 'Frozen source hash changed')
    for name, value in {**manifest['generated'], **manifest.get('phoneFiles', {})}.items():
        require(digest(RUN/name) == value, f'Frozen artifact changed: {name}')
    require(digest(WORK/'compatibility-probe') == manifest['macBinarySHA256'], 'Mac binary changed')
    for p in (RUN/'units').glob('*/*.json'):
        envelope = read(p)
        require(digest(RUN/envelope['rawPath']) == envelope['rawSHA256'], 'Raw result checksum mismatch')
        require(parse_result(read(RUN/envelope['rawPath'])['stdout'], p.stem) == envelope['result'],
                'Interpreted output differs from saved raw result')
    return {'verified': True}


def boundary():
    space()
    if STOP or (RUN/'pause.request.json').exists():
        raise InterruptedError('Saved boundary; safe to close')


def parse_result(output, unit):
    lines = [line.removeprefix('IOS27_RESULT ') for line in output.splitlines() if line.startswith('IOS27_RESULT ')]
    require(len(lines) == 1, 'Missing/duplicate native result')
    value = json.loads(lines[0])
    require(value.get('schemaVersion') == 1 and value.get('unit') == unit and value.get('syntheticOnly') is True,
            'Native result identity mismatch')
    require(value.get('status') in ('ok', 'error'), 'Invalid status')
    return value


def run(platform, device, maximum, resuming=False):
    if not (RUN/'manifest.json').exists():
        freeze()
    verify()
    if resuming and (RUN/'pause.request.json').exists():
        p = RUN/'pause.request.json'
        publish(RUN/f'resumes/{time.time_ns()}.json', {'pauseSHA256': digest(p)})
        p.unlink()  # Only this runner's owned request; completed results remain immutable.
    if platform == 'phone':
        require(device and 'phoneFiles' in read(RUN/'manifest.json'), 'Phone/device build missing')
    done = 0
    for unit in UNITS:
        boundary()
        dest = RUN/f'units/{platform}/{unit}.json'
        if dest.exists():
            check_result(read(dest)['result'], unit)
            continue
        reservation = RUN/f'attempts/{platform}/{unit}/reserved.json'
        require(not reservation.exists(), f'Unresolved attempt {platform}/{unit}; collect/review it before any retry')
        publish(reservation, {'unit': unit, 'platform': platform, 'startedUnix': time.time()})
        args = [str(WORK/'compatibility-probe'), '--root', str(WORK/'Resources'), '--unit', unit]
        if platform == 'phone':
            args = ['xcrun', 'devicectl', 'device', 'process', 'launch', '--device', device,
                    '--console', '--timeout', '120', BUNDLE, '--unit', unit]
        try:
            response = command(args, timeout=150)
            raw = {'stdout': response.stdout, 'stderr': response.stderr, 'returnCode': response.returncode}
        except subprocess.TimeoutExpired as e:
            raw = {'timeout': True, 'stdout': str(e.stdout or ''), 'stderr': str(e.stderr or '')}
        raw_path = reservation.parent/'raw.json'
        publish(raw_path, raw)
        require(raw.get('returnCode') == 0, f'Native process failed: {platform}/{unit}; raw result saved')
        result = parse_result(raw['stdout'], unit)
        publish(dest, {'result': result, 'rawPath': str(raw_path.relative_to(RUN)), 'rawSHA256': digest(raw_path)})
        print(json.dumps({'saved': f'{platform}/{unit}', 'status': result['status']}), flush=True)
        check_result(result, unit)
        done += 1
        if maximum and done >= maximum:
            break
    return {'savedThisRun': done, 'platform': platform}


def check_result(result, unit):
    require(result['status'] == 'ok', f'Native unit error: {unit}')
    if unit.startswith('parity'):
        require(result['result']['passed'], 'Parity failed; do not weaken tolerances')
    if unit.startswith('embedding'):
        require(result['result']['compatible'] and result['result']['decisionUnchanged'], 'Embedding compatibility failed')
    if unit == 'generation':
        require(result['result']['passed'], 'Generation smoke check failed')


def safe_to_close():
    if active():
        return False
    # A lost phone console does not prove the remote process has exited.
    return all((RUN/f'units/phone/{p.parent.name}.json').exists()
               for p in (RUN/'attempts/phone').glob('*/reserved.json'))


def collect(device, unit):
    """Recover a final device checkpoint without launching or rerunning inference."""
    verify()
    require(device and unit in UNITS, 'Specify a device and known --unit')
    dest = RUN/f'units/phone/{unit}.json'
    require(not dest.exists(), 'Unit already saved')
    attempt = RUN/f'attempts/phone/{unit}'
    require((attempt/'reserved.json').exists(), 'No corresponding attempt')
    recovered = attempt/f'recovered-{time.time_ns()}.json'
    response = command(['xcrun', 'devicectl', 'device', 'copy', 'from', '--device', device,
        '--source', f'Documents/unit-{unit}.json', '--destination', str(recovered),
        '--domain-type', 'appDataContainer', '--domain-identifier', BUNDLE], 60)
    require(response.returncode == 0 and recovered.exists(), 'Device checkpoint unavailable; attempt preserved')
    result = parse_result('IOS27_RESULT ' + json.dumps(read(recovered)), unit)
    raw = attempt/f'collected-{time.time_ns()}.json'
    publish(raw, {'stdout': 'IOS27_RESULT ' + json.dumps(result), 'deviceFileSHA256': digest(recovered),
                  'deviceFile': str(recovered.relative_to(RUN)), 'collectedWithoutInference': True})
    publish(dest, {'result': result, 'rawPath': str(raw.relative_to(RUN)), 'rawSHA256': digest(raw)})
    return {'collected': unit, 'newInference': False}


def evaluate():
    verify()
    report = {'stage': 1, 'stage2Started': False, 'platforms': {},
              'organizerSafeguards': 'pending isolated store tests',
              'pcc': 'not requested; account eligibility unverified'}
    for platform in ['mac', 'phone']:
        values = {p.stem: read(p)['result'] for p in (RUN/f'units/{platform}').glob('*.json')}
        report['platforms'][platform] = {'completed': len(values), 'requiredNativeUnits': len(UNITS),
            'errors': [k for k, v in values.items() if v['status'] != 'ok'],
            'environment': values.get('environment'),
            'parityPassed': sum(v.get('result', {}).get('passed', False) for k, v in values.items() if k.startswith('parity')),
            'embeddingCompatible': sum(v.get('result', {}).get('compatible', False) and v.get('result', {}).get('decisionUnchanged', False)
                for k, v in values.items() if k.startswith('embedding'))}
    ledger = RUN/'ledger-verification.json'
    proof = RUN/'resume-proof.json'
    report['organizerSafeguards'] = read(ledger) if ledger.exists() else {'passed': False, 'status': 'pending isolated store tests'}
    report['resumeProof'] = read(proof) if proof.exists() else {'passed': False, 'status': 'pending'}
    phone = report['platforms']['phone']
    phone_environment = (phone['environment'] or {}).get('result', {})
    report['stage1Complete'] = bool(phone['completed'] == len(UNITS) and not phone['errors']
        and phone['parityPassed'] == 16 and phone['embeddingCompatible'] == 16
        and phone_environment.get('foundationModelsAvailable')
        and report['organizerSafeguards'].get('passed') and report['resumeProof'].get('passed'))
    publish(RUN/f'evaluations/{time.time_ns()}.json', report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'build', 'run', 'resume', 'pause', 'status', 'evaluate', 'verify', 'freeze', 'install', 'collect'])
    parser.add_argument('--platform', choices=['mac', 'phone'], default='mac')
    parser.add_argument('--device')
    parser.add_argument('--max-units', type=int, default=0)
    parser.add_argument('--unit')
    args = parser.parse_args()
    require(args.max_units >= 0, 'Invalid max-units')
    if args.action == 'pause':
        if not (RUN/'pause.request.json').exists():
            publish(RUN/'pause.request.json', {'requestedUnix': time.time()})
        result = {'pauseRequested': True, 'safeToClose': safe_to_close()}
    elif args.action == 'status':
        result = {'safeToClose': safe_to_close(), 'paused': (RUN/'pause.request.json').exists(),
            'savedUnits': {p: len(list((RUN/f'units/{p}').glob('*.json'))) for p in ['mac', 'phone']}, **space()}
    else:
        with lock():
            if args.action == 'prepare': result = prepare()
            elif args.action == 'build': result = build(args.platform)
            elif args.action == 'freeze': freeze(); result = {'frozen': True}
            elif args.action == 'verify': result = verify()
            elif args.action == 'evaluate': result = evaluate()
            elif args.action == 'collect': result = collect(args.device, args.unit)
            elif args.action == 'install':
                verify()
                require(args.device and 'phoneFiles' in read(RUN/'manifest.json'), 'Missing device/build')
                app = WORK/'device-build/Build/Products/Debug-iphoneos/CompatibilityProbe.app'
                response = command(['xcrun', 'devicectl', 'device', 'install', 'app', '--device', args.device, str(app)], 120)
                publish(RUN/f'installations/{time.time_ns()}.json', {'returnCode': response.returncode,
                    'stdout': response.stdout, 'stderr': response.stderr})
                require(response.returncode == 0, 'Isolated probe install failed')
                result = {'installed': BUNDLE}
            else: result = run(args.platform, args.device, args.max_units, args.action == 'resume')
    print(json.dumps(result, sort_keys=True))


def stop_signal(_signal, _frame):
    global STOP
    STOP = True


if __name__ == '__main__':
    signal.signal(signal.SIGINT, stop_signal)
    signal.signal(signal.SIGTERM, stop_signal)
    try:
        main()
    except InterruptedError as e:
        print(json.dumps({'paused': True, 'safeToClose': True, 'detail': str(e)})); sys.exit(75)
    except (ValueError, OSError, subprocess.SubprocessError) as e:
        print(json.dumps({'error': str(e), 'stage2Started': False}), file=sys.stderr); sys.exit(1)
