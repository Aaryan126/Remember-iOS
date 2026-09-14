"""Authorized English-only P2 amendment; preserve the original frozen runner."""
from contextlib import contextmanager
import subprocess

import numpy as np

import p2
import p2_common as c
import p2_data as data

OLD_RUN = c.RUN
OLD_EXTERNAL = c.EXTERNAL
NEW_RUN = c.DATA / "runs/validation-02"
NEW_EXTERNAL = c.WORKSPACE / "validation/validation-02"
LANGUAGE_GUARD = "guard let language = NLLanguageRecognizer.dominantLanguage(for: text) else { return nil }"
POLICY = "explicit English for every source in all splits, shared by baseline and hybrid"


def inventory(root):
    return {str(p.relative_to(root)): c.digest(p) for p in sorted(root.rglob("*"))
            if p.is_file() and p.name != "worker.lock"}


def preservation():
    return {"run": inventory(OLD_RUN), "external": inventory(OLD_EXTERNAL)}


def english_provider(source):
    provider = source.split("nonisolated struct ProjectEmbedding:", 1)[1].split("nonisolated enum ProjectMath", 1)[0]
    normalization = source.split("    static func normalized(_ vector:", 1)[1].split("    static func cosine(", 1)[0]
    c.require(provider.count(LANGUAGE_GUARD) == 1, "expected exactly one language routing guard")
    provider = provider.replace(LANGUAGE_GUARD, "let language = NLLanguage.english")
    return ("import Foundation\nimport NaturalLanguage\nnonisolated struct ProjectEmbedding:" + provider
            + "nonisolated enum ProjectMath {\n    static func normalized(_ vector:" + normalization + "}\n")


def probe():
    from environment import publish_bytes
    source = c.ROOT / "Remember/Remember/ProjectIntelligence.swift"
    body = english_provider(source.read_text())
    generated = c.EXTERNAL / "probe/EnglishEmbedding.swift"
    if generated.exists():
        c.require(generated.read_text() == body, "generated English provider changed")
    else:
        publish_bytes(generated, body.encode())
    executable = generated.parent / "EmbeddingProbe"
    receipt = c.RUN / "probe.json"
    if receipt.exists():
        record = c.read(receipt)
        c.require(record == {"SHA256": c.digest(executable), "generatedSHA256": c.digest(generated),
                             "productionSourceSHA256": c.digest(source), "languagePolicy": POLICY,
                             "downloadsAllowed": False}, "English probe binding changed")
    else:
        c.require(not executable.exists(), "orphan executable; inspect before retry")
        result = subprocess.run(["xcrun", "swiftc", "-parse-as-library", "-O", "-target", "arm64-apple-macos26.0",
                                 str(generated), str(c.ROOT / "scripts/matcher-validation/P2EmbeddingProbe.swift"),
                                 "-o", str(executable)], capture_output=True, text=True, timeout=180)
        c.require(result.returncode == 0, "English probe build failed: " + result.stderr)
        c.publish(receipt, {"SHA256": c.digest(executable), "generatedSHA256": c.digest(generated),
                           "productionSourceSHA256": c.digest(source), "languagePolicy": POLICY,
                           "downloadsAllowed": False})
    return executable


def compare_embeddings(previous, current):
    c.require(set(previous) == set(current), "embedding source inventory changed")
    unchanged, restored = [], []
    for identifier, value in current.items():
        old = previous[identifier]
        c.require(old["textSHA256"] == value["textSHA256"], "source text changed")
        c.require(value["status"] == "ok" and value["space"].startswith("apple-dual:en:"), "English coverage incomplete")
        for key in ("contextual", "sentence"):
            vector = np.array(value[key])
            c.require(vector.shape == (512,) and np.isfinite(vector).all()
                      and abs(np.linalg.norm(vector) - 1) < 1e-5, "invalid English vector")
        if old["status"] == "ok":
            c.require(old == value, "previously available embedding changed")
            unchanged.append(identifier)
        else:
            c.require(old["status"] == "unavailable", "unexpected original embedding status")
            restored.append(identifier)
    return {"exactlyUnchanged": unchanged, "restored": restored}


def coverage():
    train = data.embeddings("train")
    previous = {key: c.read(OLD_RUN / "embeddings" / f"{key}.json") for key in train}
    parity = compare_embeddings(previous, train)
    calibration = data.embeddings("calibration")
    # Validate dimensions/norms for calibration too, without using labels or opening evaluation.
    compare_embeddings(calibration, calibration)
    counts = {}
    for split in ("train", "calibration"):
        rows = data.features(split)
        c.require(all(p2.models.usable(row) for row in rows), "incomplete pair feature coverage")
        counts[split] = {"allPairs": len(rows), "completePairs": len(rows)}
    report = {"passed": True, "languagePolicy": POLICY, "trainingSources": len(train),
              "calibrationSources": len(calibration), "parity": parity, "coverage": counts,
              "evaluationOpened": False, "productionChanges": False}
    c.publish(c.RUN / "english-coverage.json", report)
    c.log("english-coverage", trainingSources=len(train), calibrationSources=len(calibration),
          unchanged=len(parity["exactlyUnchanged"]), restored=len(parity["restored"]), coverage=counts)


@contextmanager
def adapted():
    """Scope all overrides to this CLI invocation; never edit the frozen modules."""
    original_bindings, original_verify = c.source_bindings, c.verify
    original_prepare, original_run = p2.prepare, p2.run
    original_publish = c.publish

    def bindings():
        extra = [c.ROOT / "scripts/matcher-validation" / name for name in ("p2_english.py", "test_p2_english.py")]
        extra += [c.DATA / "P2_ENGLISH_AMENDMENT.md", OLD_RUN / "manifest.json"]
        return original_bindings() | {str(p.relative_to(c.ROOT)): c.digest(p) for p in extra}

    def verify():
        manifest = original_verify()
        c.require(manifest["languagePolicy"] == POLICY, "language policy changed")
        c.require(manifest["preservedAttempt"] == preservation(), "original P2 attempt changed")
        return manifest

    def prepare():
        if (c.RUN / "manifest.json").exists():
            return verify()
        # Check the original experiment before taking its immutable inventory.
        with override(c, "RUN", OLD_RUN), override(c, "source_bindings", original_bindings):
            original_verify()
        saved = preservation()

        def publish_manifest(path, document):
            if path == c.RUN / "manifest.json":
                document = document | {"authorizedBy": "user: Carry on with ur recoemmednation (English amendment)",
                                       "languagePolicy": POLICY, "preservedAttempt": saved,
                                       "amendment": "P2_ENGLISH_AMENDMENT.md"}
            return original_publish(path, document)

        with override(c, "publish", publish_manifest):
            original_prepare()
        return verify()

    def run(pause_after=None):
        coverage()
        return original_run(pause_after)

    with override(c, "RUN", NEW_RUN), override(c, "EXTERNAL", NEW_EXTERNAL), \
            override(c, "source_bindings", bindings), override(c, "verify", verify), \
            override(data, "probe", probe), override(p2, "prepare", prepare), override(p2, "run", run):
        yield


@contextmanager
def override(module, name, value):
    original = getattr(module, name)
    setattr(module, name, value)
    try:
        yield
    finally:
        setattr(module, name, original)


if __name__ == "__main__":
    with adapted():
        p2.main()
