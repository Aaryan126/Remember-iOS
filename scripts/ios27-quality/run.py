#!/usr/bin/env python3
"""Frozen, pauseable Stage 2 screen. Existing experiments are read-only inputs."""
import importlib.util
from functools import lru_cache
import math
from pathlib import Path
import re
import shutil
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('quality_base', ROOT/'scripts/ios27-evaluation/run.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
sys.path.insert(0, str(ROOT/'scripts/organization-diagnostics'))
import c7_run as old
import c6_run

c.RUN = ROOT/'Evaluation/iOS27/quality'
c.WORK = c.RUN/'build'
c.BUNDLE = 'SimpleStudio.Remember.GroupingQuality'
TEMPLATE = ROOT/'scripts/ios27-evaluation/project.pbxproj.template'
REVIEWERS = ('c7', 'boundary')
REPEATS = (0, 28, 56, 84)
PRIOR_REQUESTS = 2
CAP = 256


@lru_cache(maxsize=1)
def inventory():
    data = old.catalogue()
    pair_data = c6_run.catalogue()
    c.require((len(data['contexts']), len(data['mapping']), len(pair_data['pairs'])) == (112, 160, 56), 'Dataset inventory changed')
    return data, pair_data


def schedule():
    units = [f'control-{i:02}' for i in range(56)]
    for i in range(112):
        units += [f'{reviewer}-{i:03}' for reviewer in (REVIEWERS if i % 2 == 0 else REVIEWERS[::-1])]
    units += [f'repeat-{reviewer}-{i:03}' for i in REPEATS for reviewer in REVIEWERS]
    return units


c.UNITS = schedule()


def source_paths():
    paths = list(SCRIPT.glob('*.py')) + list(SCRIPT.glob('*.swift')) + list(SCRIPT.glob('*.txt'))
    paths += [TEMPLATE, ROOT/'scripts/ios27-evaluation/run.py', c.RUN/'PROTOCOL.md',
              old.PROMPT, c6_run.RUN/'adjudicated-gold.json', old.c5_run.RUN/'release/inputs.json',
              old.c5_run.RUN/'release/gold.json', c6_run.RUN/'predictions/baseline.json',
              c6_run.RUN/'predictions/29.json', ROOT/'Evaluation/iOS27/generation-trace/checkpoint.json',
              ROOT/'Evaluation/iOS27/readiness/closure.json']
    paths += list((ROOT/'scripts/organization-diagnostics').glob('*.py'))
    paths += [ROOT/f'Remember/Remember/{name}.swift' for name in
              ('D3Tokenizer', 'D3Features', 'D3PairMatcher', 'D3OrganizationPolicy', 'ProjectIntelligence')]
    paths += [p for p in (ROOT/'Remember/Remember/MatcherAssets').rglob('*') if p.is_file()]
    paths += [p for p in (ROOT/'Evaluation/iOS27/precision/export-fp32/models/D3MatcherFP32.mlpackage').rglob('*') if p.is_file()]
    return sorted(set(paths))


def sources():
    return {str(p.relative_to(ROOT)): c.digest(p) for p in source_paths()}


def space():
    free = shutil.disk_usage(ROOT).free
    size = sum(p.stat().st_size for p in (ROOT/'Evaluation/iOS27').rglob('*') if p.is_file())
    c.require(free >= 10*c.GIB and size < 8*c.GIB, 'Experiment storage limit reached')
    return {'freeBytes': free, 'experimentBytes': size}


@lru_cache(maxsize=1)
def inputs():
    data, pairs = inventory()
    prompts = {'c7': old.PROMPT.read_text(), 'boundary': (SCRIPT/'boundary-prompt.txt').read_text()}
    requests = {}
    for i, (key, packet) in enumerate(data['contexts'].items()):
        payload = old.request(packet)['packet']
        for reviewer in REVIEWERS:
            row = {'packet': payload, 'instructions': prompts[reviewer], 'context': key, 'reviewer': reviewer}
            requests[f'{reviewer}-{i:03}'] = row
            if i in REPEATS:
                requests[f'repeat-{reviewer}-{i:03}'] = row
    controls = {f'control-{i:02}': {'key': key, 'first': pairs['texts'][row['first']],
                'second': pairs['texts'][row['second']]} for i, (key, row) in enumerate(pairs['pairs'].items())}
    return {'requests': requests, 'controls': controls}


def prepare():
    space()
    c.require(not c.WORK.exists() and not (c.RUN/'manifest.json').exists(), 'Preserve existing preparation')
    # Verify historical completion receipts without invoking old runtime checks/writers.
    for name in ('c6', 'c7'):
        receipt = c.read(ROOT/f'Evaluation/OrganizationDiagnostics/{name}/complete.json')
        for path, sha in receipt['sources'].items():
            c.require(c.digest(ROOT/path) == sha, 'Historical completion binding changed: '+path)
    c.require(c.read(ROOT/'Evaluation/iOS27/readiness/closure.json')['safeToClose'], 'Prior timeout remains unresolved')
    export = ROOT/'Evaluation/iOS27/precision/export-fp32'
    for path, sha in c.read(export/'export-result.json')['files'].items():
        c.require(c.digest(export/path) == sha, 'FP32 export changed')
    source = c.WORK/'Sources'; source.mkdir(parents=True)
    resources = c.WORK/'Resources'; resources.mkdir()
    shutil.copy2(SCRIPT/'QualityProbe.swift', source/'QualityProbe.swift')
    for name in ('D3Tokenizer', 'D3Features', 'D3PairMatcher', 'D3OrganizationPolicy'):
        shutil.copy2(ROOT/f'Remember/Remember/{name}.swift', source/f'{name}.swift')
    original = (ROOT/'Remember/Remember/ProjectIntelligence.swift').read_text()
    start, end = 'nonisolated struct ProjectEmbedding:', 'nonisolated struct ProjectTopicEvidence'
    c.require(original.count(start) == original.count(end) == 1, 'Embedding extraction boundaries changed')
    (source/'ProductionEmbedding.swift').write_text('import Foundation\nimport NaturalLanguage\n'
        'enum ProjectPreferences { static let embeddingsAvailable = Notification.Name("remember.project.embeddingsAvailable") }\n'
        + original[original.index(start):original.index(end)])
    shutil.copytree(ROOT/'Remember/Remember/MatcherAssets', resources/'MatcherAssets')
    shutil.copytree(export/'models/D3MatcherFP32.mlpackage', resources/'MatcherAssets/D3MatcherFP32.mlpackage')
    c.publish(resources/'inputs.json', inputs())
    c.publish(c.RUN/'catalogue.json', inventory()[0])
    c.publish(c.RUN/'schedule.json', {'units': c.UNITS, 'priorRequests': PRIOR_REQUESTS,
        'scheduledGenerations': 232, 'maximumTotalAttempts': CAP, 'pilotPrimaryRequests': 8})
    team = re.search(r'DEVELOPMENT_TEAM = ([A-Z0-9]+);', (ROOT/'Remember/Remember.xcodeproj/project.pbxproj').read_text())[1]
    project = c.WORK/'CompatibilityProbe.xcodeproj'; project.mkdir()
    (project/'project.pbxproj').write_text(TEMPLATE.read_text().replace('__TEAM__', team)
        .replace('SimpleStudio.Remember.IOS27Compatibility', c.BUNDLE).replace('Remember Compatibility', 'Grouping Quality'))
    c.publish(c.RUN/'prepared.json', {'sources': sources(), 'units': len(c.UNITS), 'storage': space()})
    return {'prepared': True, 'controls': 56, 'generations': 232, 'totalIncludingPrior': 234}


base_build = c.build
def build(platform):
    c.require(platform == 'phone', 'Quality screen targets the physical phone only')
    return base_build(platform)


def freeze():
    app = c.WORK/'device-build/Build/Products/Debug-iphoneos/CompatibilityProbe.app'
    c.require((app/'CompatibilityProbe').is_file(), 'Missing phone build')
    generated = list((c.WORK/'Sources').glob('*.swift')) + [c.WORK/'Resources/inputs.json',
        c.WORK/'CompatibilityProbe.xcodeproj/project.pbxproj', c.RUN/'catalogue.json', c.RUN/'schedule.json']
    c.publish(c.RUN/'manifest.json', {'sources': sources(),
        'generated': {str(p.relative_to(c.RUN)): c.digest(p) for p in generated},
        'phoneFiles': {str(p.relative_to(c.RUN)): c.digest(p) for p in app.rglob('*') if p.is_file()},
        'units': c.UNITS, 'system': c.command(['sw_vers']).stdout,
        'xcode': c.command(['xcodebuild', '-version']).stdout, 'productionQualified': False})


def verify():
    manifest = c.read(c.RUN/'manifest.json')
    c.require(manifest['sources'] == sources() and manifest['units'] == c.UNITS, 'Frozen sources/schedule changed')
    for path, sha in {**manifest['generated'], **manifest['phoneFiles']}.items():
        c.require(c.digest(c.RUN/path) == sha, 'Frozen artifact changed: '+path)
    for path in (c.RUN/'units/phone').glob('*.json'):
        c.require(path.stem in c.UNITS, 'Unscheduled unit')
        row = c.read(path); raw = c.RUN/row['rawPath']
        c.require(c.digest(raw) == row['rawSHA256'], 'Raw evidence changed')
        c.require(c.parse_result(c.read(raw)['stdout'], path.stem) == row['result'], 'Saved interpretation changed')
        if 'deviceFile' in c.read(raw):
            r = c.read(raw)
            c.require(c.digest(c.RUN/r['deviceFile']) == r['deviceFileSHA256'], 'Recovered device file changed')
    return {'verified': True}


def interpretation(packet, result):
    if result['status'] != 'ok':
        return {'status': 'error', 'errorKind': 'native', 'prediction': None}
    try:
        return {'status': 'ok', 'prediction': old.validate_output(packet, result['result']['output'])}
    except (ValueError, KeyError, TypeError) as error:
        return {'status': 'error', 'errorKind': 'invalid-output', 'detail': str(error), 'prediction': None}


def check_result(result, unit):
    c.require(result['status'] == 'ok', 'Native error saved; stop without retry: '+unit)
    if unit.startswith('control-'):
        expected = inputs()['controls'][unit]
        row = result['result']
        c.require(row['key'] == expected['key'], 'Pair control identity changed')
        c.require(row['threshold'] == 0.9804276486193665, 'Control threshold changed')
        for value in row['scores'].values():
            c.require(math.isfinite(value['score']) and 0 <= value['score'] <= 1, 'Invalid score')
            c.require(value['accepted'] == (value['score'] >= row['threshold']), 'Decision mismatch')
        return
    request = inputs()['requests'][unit]
    c.require(all(result['result'][k] == request[k] for k in ('context', 'reviewer')), 'Reviewer identity changed')
    # Output validation errors are retained; three consecutive such units stop the screen.
    invalid = 0
    data = inventory()[0]
    for prior in c.UNITS:
        if not prior.startswith('control-'):
            path = c.RUN/f'units/phone/{prior}.json'
            if path.exists():
                saved = c.read(path)['result']
                context = inputs()['requests'][prior]['context']
                outcome = interpretation(data['contexts'][context], saved)
                invalid = invalid+1 if outcome['status'] != 'ok' else 0
                c.require(invalid < 3, 'Three consecutive invalid outputs; stop without prompt changes')
        if prior == unit:
            break


base_command = c.command
def command(args, timeout=120):
    if 'launch' in args and c.BUNDLE in args:
        reserved = [p for p in (c.RUN/'attempts/phone').glob('*/reserved.json') if not p.parent.name.startswith('control-')]
        c.require(PRIOR_REQUESTS+len(reserved) <= CAP, 'Generation request cap exceeded')
    return base_command(args, timeout)


def prediction(packet, accepted):
    return {'queryID': packet['queryID'], 'verdict': 'same_project' if accepted else 'abstain',
            'evidence': [{'sourceID': s['id'], 'quote': s['text']} for s in packet['sources'] if s['id'] in packet['pair']] if accepted else []}


def changes(packets, labels, reference, candidate):
    gold = {x['queryID']: x['verdict'] for x in labels}
    a = {x['queryID']: x for x in reference}; b = {x['queryID']: x for x in candidate}
    result = {}
    for view in ('pair', 'context'):
        counts = dict(fixed=0, damaged=0, newFalseSame=0, newFalseSeparate=0)
        for packet in packets:
            if packet['view'] != view:
                continue
            key = packet['queryID']; target = gold[key]
            before = a[key]['prediction']['verdict'] if a[key]['status'] == 'ok' else 'error'
            after = b[key]['prediction']['verdict'] if b[key]['status'] == 'ok' else 'error'
            counts['fixed'] += before != target and after == target
            counts['damaged'] += before == target and after != target
            counts['newFalseSame'] += after == 'same_project' and target != after and before != after
            counts['newFalseSeparate'] += after == 'separate_projects' and target != after and before != after
        result[view] = counts
    return result


def gate(summary, delta):
    checks = {}
    for name, threshold, lower in [('samePrecision', .95, True), ('sameRecall', .75, True),
        ('conflictPrecision', .90, True), ('conflictRecall', .80, True),
        ('unsupportedAssertionRate', .10, False), ('errorRate', .05, False)]:
        value = summary['view:context'][name]['value']
        checks[name] = {'value': value, 'threshold': threshold,
            'passed': value is not None and (value >= threshold if lower else value <= threshold)}
    checks['fixesExceedDamages'] = {**delta['context'], 'passed': delta['context']['fixed'] > delta['context']['damaged']}
    return {'checks': checks, 'passed': all(x['passed'] for x in checks.values()), 'productionQualified': False}


def evaluate():
    verify()
    c.require(all((c.RUN/f'units/phone/{unit}.json').exists() for unit in c.UNITS), 'Partial screen cannot be evaluated as complete')
    packets = old.packets(); data = inventory()[0]
    controls = {c.read(p)['result']['result']['key']: c.read(p)['result']['result'] for p in (c.RUN/'units/phone').glob('control-*.json')}
    context_indices = {key: i for i, key in enumerate(data['contexts'])}
    historical = {name: {x['queryID']: x for x in old.c.read_unit(c6_run.RUN/f'predictions/{name}.json')} for name in ('baseline', '29')}
    output = {name: [] for name in ('historical-baseline', 'historical-29', 'fp16', 'fp32', 'always-abstain')}
    for reviewer in REVIEWERS:
        for suffix in ('', '-fp16-veto', '-fp16-confirm', '-fp32-veto', '-fp32-confirm'):
            output[reviewer+suffix] = []
    for packet in packets:
        key = packet['queryID']; visible = {x['id']: x['text'] for x in packet['sources']}
        pair_key = old.c.pair_key(*(visible[x] for x in packet['pair']))
        pair_predictions = {precision: prediction(packet, controls[pair_key]['scores'][precision]['accepted']) for precision in ('fp16', 'fp32')}
        for name, pred in [('historical-'+n, historical[n][key]) for n in historical] + list(pair_predictions.items()) + [('always-abstain', prediction(packet, False))]:
            output[name].append({'queryID': key, 'status': 'ok', 'prediction': pred})
        index = context_indices[data['mapping'][key]]
        for reviewer in REVIEWERS:
            native = c.read(c.RUN/f'units/phone/{reviewer}-{index:03}.json')['result']
            local = interpretation(packet, native)
            output[reviewer].append({'queryID': key, **local})
            for precision, pred in pair_predictions.items():
                for mode in ('veto', 'confirm'):
                    output[f'{reviewer}-{precision}-{mode}'].append({'queryID': key, **old.combine(pred, local, mode)})
    result = {'exposedDiagnostic': True, 'productionQualified': False, 'pairControlsNotWholeOrganizer': True,
              'primaryRequests': 224, 'repeatRequests': 8, 'expandedPacketsPerReviewer': 160, 'priorRequests': PRIOR_REQUESTS}
    for kind, path in [('original', old.c5_run.RUN/'release/gold.json'), ('adjudicated', c6_run.RUN/'adjudicated-gold.json')]:
        labels = c.read(path)['labels']
        metrics = {name: old.metrics(packets, labels, rows) for name, rows in output.items()}
        deltas = {name: changes(packets, labels, output['fp16'], rows) for name, rows in output.items()}
        result[kind] = {'metrics': metrics, 'changesVsFP16': deltas,
            'gates': {name: gate(metrics[name], deltas[name]) for name in output if name.startswith(REVIEWERS)}}
    repeats = []
    for reviewer in REVIEWERS:
        latencies = []
        for i in range(112):
            row = c.read(c.RUN/f'units/phone/{reviewer}-{i:03}.json')['result']
            if row['status'] == 'ok':
                latencies.append(row['result']['generationSeconds'])
        result.setdefault('generationSeconds', {})[reviewer] = {'median': statistics.median(latencies) if latencies else None,
            'maximum': max(latencies) if latencies else None, 'count': len(latencies)}
        for i in REPEATS:
            packet = list(data['contexts'].values())[i]
            a = interpretation(packet, c.read(c.RUN/f'units/phone/{reviewer}-{i:03}.json')['result'])
            b = interpretation(packet, c.read(c.RUN/f'units/phone/repeat-{reviewer}-{i:03}.json')['result'])
            repeats.append({'reviewer': reviewer, 'index': i, 'bothValid': a['status'] == b['status'] == 'ok',
                'verdictAgreement': a['status'] == b['status'] == 'ok' and a['prediction']['verdict'] == b['prediction']['verdict'],
                'exactPredictionAgreement': a == b and a['status'] == 'ok'})
    result['repeats'] = repeats
    result['precisionDecisionDifferences'] = sum(row['scores']['fp16']['accepted'] != row['scores']['fp32']['accepted'] for row in controls.values())
    for name, rows in output.items():
        c.publish(c.RUN/f'predictions/{name}.json', rows)
    c.publish(c.RUN/'summary.json', result)
    paths = list((c.RUN/'units/phone').glob('*.json')) + list((c.RUN/'predictions').glob('*.json')) + [c.RUN/'summary.json']
    c.publish(c.RUN/'complete.json', {'files': {str(p.relative_to(c.RUN)): c.digest(p) for p in paths}, 'productionQualified': False})
    return {'evaluated': True, 'gates': {name: row['passed'] for name, row in result['adjudicated']['gates'].items()}}


c.sources = sources; c.space = space; c.prepare = prepare; c.build = build; c.freeze = freeze
c.verify = verify; c.check_result = check_result; c.command = command; c.evaluate = evaluate
if __name__ == '__main__':
    c.signal.signal(c.signal.SIGINT, c.stop_signal); c.signal.signal(c.signal.SIGTERM, c.stop_signal)
    try:
        c.main()
    except InterruptedError:
        print(c.json.dumps({'paused': True, 'safeToClose': c.safe_to_close()})); raise SystemExit(75)
    except (ValueError, OSError, c.subprocess.SubprocessError) as error:
        print(c.json.dumps({'error': str(error), 'safeToClose': c.safe_to_close()})); raise SystemExit(1)
