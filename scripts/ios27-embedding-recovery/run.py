#!/usr/bin/env python3
"""Versioned recovery check using the patched production provider and frozen fixtures."""
import importlib.util
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('compatibility', ROOT/'scripts/ios27-evaluation/run.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
c.RUN = ROOT/'Evaluation/iOS27/embedding-recovery'
c.WORK = c.RUN/'build'
c.BUNDLE = 'SimpleStudio.Remember.EmbeddingRecovery'
c.UNITS = [f'embedding-{i:02}' for i in range(16)]
base_sources = c.sources
base_prepare = c.prepare
base_verify = c.verify
TEST = ROOT/'Remember/RememberTests/SentenceModelRecoveryTests.swift'


def sources():
    result = base_sources()
    for path in [Path(__file__), TEST]: result[str(path.relative_to(ROOT))] = c.digest(path)
    return result


def verify_history():
    """Do not rewrite old manifests to conceal the explicitly authorized source change."""
    old_root = ROOT/'Evaluation/iOS27/stage1'
    old = c.read(old_root/'manifest.json')
    before = c.read(c.RUN/'pre-change.json')
    c.require(c.digest(old_root/'manifest.json') == before['manifestSHA256'], 'Historical manifest changed')
    changed = [path for path, value in old['sources'].items() if c.digest(ROOT/path) != value]
    c.require(changed == ['Remember/Remember/ProjectIntelligence.swift'], 'Unexpected historical source change')
    for path,value in {**old['generated'], **old['phoneFiles']}.items():
        c.require(c.digest(old_root/path) == value, 'Historical artifact changed: '+path)
    c.require(c.digest(old_root/'build/compatibility-probe') == old['macBinarySHA256'], 'Historical binary changed')


def prepare():
    verify_history()
    result = base_prepare()
    project = c.WORK/'CompatibilityProbe.xcodeproj/project.pbxproj'
    project.write_text(project.read_text().replace('SimpleStudio.Remember.IOS27Compatibility', c.BUNDLE)
                      .replace('Remember Compatibility', 'Embedding Recovery'))
    # Run the exact production declarations and real regression tests without GRDB/app dependencies.
    package = c.WORK/'unit-tests'
    (package/'Sources/EmbeddingRecovery').mkdir(parents=True, exist_ok=True)
    (package/'Tests/EmbeddingRecoveryTests').mkdir(parents=True, exist_ok=True)
    shutil.copy2(c.WORK/'Sources/ProductionEmbedding.swift', package/'Sources/EmbeddingRecovery/ProductionEmbedding.swift')
    (package/'Tests/EmbeddingRecoveryTests/SentenceModelRecoveryTests.swift').write_text(
        TEST.read_text().replace('@testable import Remember', '@testable import EmbeddingRecovery'))
    (package/'Package.swift').write_text('''// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "EmbeddingRecovery", platforms: [.macOS(.v15)], targets: [
    .target(name: "EmbeddingRecovery"),
    .testTarget(name: "EmbeddingRecoveryTests", dependencies: ["EmbeddingRecovery"])
])
''')
    return result


def verify():
    verify_history()
    return base_verify()


c.sources = sources
c.prepare = prepare
c.verify = verify

if __name__ == '__main__':
    c.signal.signal(c.signal.SIGINT,c.stop_signal); c.signal.signal(c.signal.SIGTERM,c.stop_signal)
    try: c.main()
    except InterruptedError:
        print(c.json.dumps({'paused':True,'safeToClose':c.safe_to_close()})); raise SystemExit(75)
    except (ValueError,OSError,c.subprocess.SubprocessError) as error:
        print(c.json.dumps({'error':str(error),'stage2Started':False})); raise SystemExit(1)
