#!/usr/bin/env python3
"""Independent read-only Stage 2 artifact audit; writes only its new report."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from experiment import DATA, ROOT, read, save, sha, require, verify_freeze
import stage2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, default=Path.home() / "Library/Application Support/RememberMatcherFeasibility/v1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run, workspace = args.run.resolve(), args.workspace.resolve()
    frozen = verify_freeze(DATA / "freeze.json")
    verified = stage2.verify_run(run, workspace)
    selected = read(run / "baseline-selected.json")
    summary = read(run / "baseline-summary.json")
    features = read(run / "features.json")
    result = read(run / "baseline" / f"C-{selected['model']['C']:g}.json")
    train = stage2.load_split("train")
    development = stage2.load_split("development")
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), dtype=np.float64)
    vectorizer.fit([i["text"] for lib in train["libraries"] for i in lib["items"]])
    require(vectorizer.vocabulary_ == selected["tfidf"]["vocabulary"], "TF-IDF vocabulary not reproducible from training only")
    require(np.max(np.abs(vectorizer.idf_ - selected["tfidf"]["idf"])) < 1e-12, "TF-IDF IDF differs")
    export_difference = 0.0
    coverage = {}
    for split, inputs in (("train", train), ("development", development)):
        rows = result["predictions"][split]
        expected = {(lib["id"], a, b) for lib in inputs["libraries"]
                    for a, b in combinations(sorted(i["id"] for i in lib["items"]), 2)}
        actual = {(r["library"], r["first"], r["second"]) for r in rows}
        require(actual == expected and len(rows) == len(expected), "missing/duplicate prediction coverage")
        gold = read(DATA / "releases/v1" / f"labels-{split}.json")
        by_library = {r["id"]: r for r in gold["libraries"]}
        independent_gold = {}
        for lib in inputs["libraries"]:
            label = by_library[lib["id"]]
            ambiguous = {i["id"] for i in label["ambiguous"]}
            memberships = {i["id"]: {g["id"] for g in label["groups"] if i["id"] in g["members"]} for i in lib["items"]}
            related = {frozenset(pair) for pair in label["relatedGroupPairs"]}
            for a, b in combinations(sorted(memberships), 2):
                relation = "uncertain" if a in ambiguous or b in ambiguous else "same" if memberships[a] & memberships[b] else (
                    "related" if any(frozenset((x, y)) in related for x in memberships[a] for y in memberships[b]) else "unrelated")
                independent_gold[a, b] = relation
        require(all(r["relation"] == independent_gold[r["first"], r["second"]] for r in rows), "prediction/gold join mismatch")
        valid = [r for r in rows if r["probabilities"] is not None]
        reproduced = stage2.exported_probabilities(selected["model"], [r["features"] for r in valid])
        export_difference = max(export_difference, float(np.max(np.abs(reproduced - [r["probabilities"] for r in valid]))))
        require(export_difference < 1e-12, "exported baseline does not reproduce probabilities")
        candidates = features["splits"][split]["candidates"]
        for lib in inputs["libraries"]:
            ids = {i["id"] for i in lib["items"]}
            for item in ids:
                values = candidates[item]
                require(len(values) <= 10 and len(set(values)) == len(values)
                        and set(values).issubset(ids - {item}), "candidate leak, duplicate or self candidate")
        coverage[split] = {"pairs": len(rows), "withProbabilities": len(valid), "classes": dict(Counter(r["relation"] for r in rows))}
    rows = result["predictions"]["development"]
    threshold = selected["threshold"]
    accepted = [r for r in rows if r["probabilities"] is not None and r["probabilities"][0] >= threshold
                and r["probabilities"].index(max(r["probabilities"])) == 0]
    counts = Counter(r["relation"] for r in accepted)
    tp = counts["same"]
    fp = counts["related"] + counts["unrelated"]
    fn = sum(r["relation"] == "same" for r in rows) - tp
    recorded = summary["selectedMetrics"]["development"]["allPairs"]
    require([tp, fp, fn] == [recorded[k] for k in ("tp", "fp", "fn")], "confusion counts differ")
    # An independent brute-force threshold sweep confirms the optimized selector.
    ranking = []
    for candidate_path in sorted((run / "baseline").glob("C-*.json")):
        candidate = read(candidate_path)
        known = [r for r in candidate["predictions"]["development"] if r["relation"] != "uncertain"]
        positives = Counter(r["library"] for r in known if r["relation"] == "same")
        options = []
        for cutoff in sorted({r["probabilities"][0] for r in known if r["probabilities"] is not None}):
            chosen = [r for r in known if r["probabilities"] is not None and r["probabilities"][0] >= cutoff
                      and r["probabilities"].index(max(r["probabilities"])) == 0]
            if len(chosen) < 30:
                continue
            hits = [r for r in chosen if r["relation"] == "same"]
            precision = len(hits) / len(chosen)
            if precision >= .95:
                hit_libraries = Counter(r["library"] for r in hits)
                recall = sum(hit_libraries[k] / n for k, n in positives.items()) / len(positives)
                options.append((recall, precision, cutoff, -candidate["model"]["C"]))
        if options:
            best = max(options)
            require(best[2] == candidate["selection"]["threshold"], "optimized threshold search disagrees with brute force")
            ranking.append(best)
        else:
            require(candidate["selection"] is None, "nonqualifying candidate selected")
    require(max(ranking)[2:] == (threshold, -selected["model"]["C"]), "selected C/tie break differs")
    pauses = [read(p) for p in sorted((run / "pauses").glob("*.json"))]
    kept_before_pause = None
    if pauses:
        first_pause = pauses[0]
        kept_before_pause = sum(read(p)["recordedAt"] < first_pause["at"] for p in (run / "embeddings").glob("*.json"))
        require(kept_before_pause == first_pause["completedEmbeddingItems"], "pre-pause records were rewritten or lost")
    original = read(DATA / "baseline-context.json")
    for group in ("artifacts", "productionSources"):
        require(all(sha(ROOT / p) == expected for p, expected in original[group].items()), "historical or production files changed")
    report = {"schemaVersion": 1, "auditedAt": datetime.now(timezone.utc).isoformat(), "passed": True,
              "stage1": frozen, "stage2": verified, "auditorSHA256": sha(__file__), "coverage": coverage,
              "trainingOnlyTFIDFReproduced": True, "portableClassifierMaxProbabilityDifference": export_difference,
              "thresholdSelectionReproducedByBruteForce": True, "independentDevelopmentCounts": {"tp": tp, "fp": fp, "fn": fn},
              "pauseEvents": len(pauses), "prePauseEmbeddingsPreserved": kept_before_pause,
              "historicalArtifactsUnchanged": len(original["artifacts"]), "productionSourcesUnchanged": len(original["productionSources"]),
              "testLabelsRead": False}
    save(args.output, report)
    print(__import__("json").dumps(report, indent=2))


if __name__ == "__main__":
    main()
