"""Adjudication and reproducible P1 release, using only old train/development text."""
import argparse
from collections import Counter
from copy import deepcopy
import itertools
import heapq
import json
import re

import p1
from p1_history import build as build_history
from prepare import DATA, ROOT, digest, publish, read, require, shingles, validate_corpus

RUN = p1.RUN
RELEASE = DATA / "releases/v1"


def libraries():
    return [lib for author in p1.REVIEWER for lib in p1.author_libraries(author)]


def relation(a, b, links):
    if not a or not b:
        return "uncertain"
    if set(a) & set(b):
        return "same"
    return "related" if any(frozenset((x, y)) in links for x in a for y in b) else "unrelated"


def collect_issues(corpus, reviews, pair_reviews):
    """Review disagreement is evidence for adjudication, never a majority-vote gold rewrite."""
    reviewed = {lib["id"]: lib for review in reviews for lib in review["libraries"]}
    pairs = {p["id"]: p for review in pair_reviews for p in review["pairs"]}
    issues = []
    for lib in corpus:
        candidate = reviewed[lib["id"]]
        proposed = {i["id"]: i for i in candidate["assignments"]}
        for source in lib["items"]:
            other = proposed[source["id"]]
            if set(source["memberships"]) != set(other["memberships"]):
                issues.append({"id": "membership:" + source["id"], "kind": "membership", "library": lib["id"],
                               "source": source["id"], "author": source["memberships"], "reviewer": other["memberships"],
                               "authorReason": source["rationale"], "reviewerReason": other["reason"]})
        author_links = {frozenset(p) for p in lib["relatedThreads"]}
        if author_links != {frozenset(p) for p in candidate["relatedThreads"]}:
            issues.append({"id": "links:" + lib["id"], "kind": "links", "library": lib["id"],
                           "author": lib["relatedThreads"], "reviewer": candidate["relatedThreads"]})
        if candidate["historyVerdict"] != "supported":
            issues.append({"id": "history:" + lib["id"], "kind": "history", "library": lib["id"],
                           "reviewerReason": candidate["historyEvidence"]})
        for a, b in itertools.combinations(lib["items"], 2):
            key = a["id"] + "--" + b["id"]
            if key not in pairs:
                continue
            review = pairs[key]
            gold = relation(a["memberships"], b["memberships"], author_links)
            if review["relation"] != gold or (gold != "uncertain" and review["sufficiency"] == "needs-context"):
                issues.append({"id": "pair:" + key, "kind": "pair", "library": lib["id"], "pair": key,
                               "author": gold, "reviewer": review["relation"], "sufficiency": review["sufficiency"],
                               "reviewerReason": review["evidence"]})
    require(len({i["id"] for i in issues}) == len(issues), "duplicate issue ID")
    return sorted(issues, key=lambda i: i["id"])


def issue_report():
    p1.capacity()
    for author in p1.REVIEWER:
        p1.seal_context(author)
    corpus = libraries()
    reviews = [read(DATA / "reviews" / f"{reviewer}-context.json") for reviewer in p1.REVIEWER.values()]
    pair_reviews = [read(DATA / "reviews" / f"{reviewer}-pairs.json") for reviewer in p1.REVIEWER.values()]
    result = {"issues": collect_issues(corpus, reviews, pair_reviews),
              "authorHashes": {lib["id"]: digest(DATA / "authoring" / f'{lib["id"]}.json') for lib in corpus},
              "reviewHashes": {p.name: digest(p) for p in sorted((DATA / "reviews").glob("*.json"))}}
    publish(RUN / "issues.json", result)
    return result


def apply_decisions(corpus, issues, adjudication):
    require(adjudication["reviewer"] == "root-adjudicator" and isinstance(adjudication["method"], str)
            and adjudication["method"].strip(), "adjudication identity/method")
    decisions = adjudication["decisions"]
    require(len(decisions) == len(issues) and {d["id"] for d in decisions} == {i["id"] for i in issues}, "unresolved or duplicate decisions")
    by_issue = {i["id"]: i for i in issues}
    final = deepcopy(corpus)
    libs = {lib["id"]: lib for lib in final}
    pair_overrides = {}
    for decision in decisions:
        require(isinstance(decision["reason"], str) and decision["reason"].strip(), "adjudication missing evidence")
        issue = by_issue[decision["id"]]
        action = decision["resolution"]
        if action == "retain-author":
            continue
        lib = libs[issue["library"]]
        if action == "use-context-gold" and issue["kind"] == "pair":
            # Re-derive after membership/link adjudication; do not freeze the author's old pair class.
            continue
        if action == "accept-reviewer" and issue["kind"] == "membership":
            source = next(i for i in lib["items"] if i["id"] == issue["source"])
            source["memberships"] = issue["reviewer"]
            source["rationale"] = decision["reason"]
        elif action == "accept-reviewer" and issue["kind"] == "links":
            lib["relatedThreads"] = issue["reviewer"]
        elif action == "set-links" and issue["kind"] == "links":
            lib["relatedThreads"] = decision["relatedThreads"]
        elif action == "pair-uncertain" and issue["kind"] == "pair":
            # Pair-only insufficiency need not erase a source's contextual history membership.
            pair_overrides[issue["pair"]] = {"relation": "uncertain", "reason": decision["reason"]}
        elif action == "replace-history" and issue["kind"] == "history":
            lib["historyChecks"] = decision["historyChecks"]
        else:
            raise ValueError("unsupported adjudication action")
    # Consensus is not proof of correctness. Preserve any root-discovered link
    # correction separately instead of rewriting the sealed disagreement report.
    additional = adjudication.get("additionalLinkDecisions", [])
    seen = set()
    for decision in additional:
        lid = decision["library"]
        require(lid in libs and lid not in seen and "links:" + lid not in by_issue,
                "additional link correction must address one previously undisputed library")
        require(decision["resolution"] == "set-links" and isinstance(decision["reason"], str)
                and decision["reason"].strip(), "additional link correction needs explicit evidence")
        require(decision["before"] == libs[lid]["relatedThreads"], "additional link correction original mismatch")
        links = decision["relatedThreads"]
        require(isinstance(links, list) and all(isinstance(p, list) and len(p) == 2
                and all(isinstance(t, str) for t in p) and p[0] != p[1]
                and set(p) <= set(libs[lid]["threads"]) for p in links), "invalid additional link endpoints")
        require(len({frozenset(p) for p in links}) == len(links), "duplicate additional links")
        libs[lid]["relatedThreads"] = deepcopy(links)
        seen.add(lid)
    return final, pair_overrides


def final_pair_requirements(original, final, pair_reviews, initial_issues):
    old_libraries = {lib["id"]: lib for lib in original}
    final_libraries = {lib["id"]: lib for lib in final}
    sampled = {r["id"]: r for review in pair_reviews for r in review["pairs"]}
    initial_ids = {i["id"] for i in initial_issues}
    required = []
    for lid, lib in final_libraries.items():
        old = old_libraries[lid]
        old_items = {i["id"]: i for i in old["items"]}
        old_links = {frozenset(p) for p in old["relatedThreads"]}
        new_links = {frozenset(p) for p in lib["relatedThreads"]}
        for a, b in itertools.combinations(lib["items"], 2):
            key = a["id"] + "--" + b["id"]
            if key not in sampled:
                continue
            review = sampled[key]
            before = relation(old_items[a["id"]]["memberships"], old_items[b["id"]]["memberships"], old_links)
            after = relation(a["memberships"], b["memberships"], new_links)
            new_conflict = (after != review["relation"] or after != "uncertain" and review["sufficiency"] == "needs-context")
            if before != after or new_conflict and "pair:" + key not in initial_ids:
                required.append({"id": "pair:" + key, "pair": key, "library": lid, "before": before,
                                 "contextRelation": after, "pairReview": review["relation"],
                                 "sufficiency": review["sufficiency"], "evidence": review["evidence"],
                                 "firstText": a["text"], "secondText": b["text"]})
    return sorted(required, key=lambda r: r["id"])


def resolve_final_pairs(required, decisions, overrides):
    require(len(decisions) == len(required) and {d["id"] for d in decisions} == {r["id"] for r in required},
            "changed/newly disputed sampled pairs need explicit final dispositions")
    result = deepcopy(overrides)
    indexed = {r["id"]: r for r in required}
    for decision in decisions:
        require(isinstance(decision["reason"], str) and decision["reason"].strip(), "final pair reason missing")
        key = indexed[decision["id"]]["pair"]
        if decision["resolution"] == "pair-uncertain":
            result[key] = {"relation": "uncertain", "reason": decision["reason"]}
        elif decision["resolution"] == "use-context-gold":
            result.pop(key, None)
        else:
            raise ValueError("invalid final pair disposition")
    return result


def final_pairs():
    report = issue_report()
    adjudication = read(DATA / "adjudication.json")
    require(adjudication["issuesSHA256"] == digest(RUN / "issues.json"), "adjudication binding")
    original = libraries()
    final, _ = apply_decisions(original, report["issues"], adjudication)
    reviews = [read(DATA / "reviews" / f"{r}-pairs.json") for r in p1.REVIEWER.values()]
    return final_pair_requirements(original, final, reviews, report["issues"])


def historical_overlap(corpus):
    """These are the only previous-data paths opened. Never glob a release directory."""
    paths = [ROOT / "Evaluation/MatcherFeasibility/releases/v1" / f"inputs-{split}.json"
             for split in ("train", "development")]
    # Include the already-inspected pilot as development-only contamination screening.
    paths.append(DATA / "runs/preparation-01/pilot-inputs.json")
    threshold = read(DATA / "contract.json")["nearDuplicateJaccard"]
    older = [(item["id"], item["text"]) for path in paths for lib in read(path)["libraries"] for item in lib["items"]]
    normalize = lambda text: " ".join(re.findall(r"\w+", text.casefold()))
    index = [(iid, normalize(text), shingles(text)) for iid, text in older]
    findings, largest = [], (0, None, None)
    for lib in corpus:
        for item in lib["items"]:
            normalized, tokens = normalize(item["text"]), shingles(item["text"])
            for old_id, old_text, old_tokens in index:
                similarity = len(tokens & old_tokens) / len(tokens | old_tokens) if tokens | old_tokens else 1.
                if similarity > largest[0]:
                    largest = (similarity, item["id"], old_id)
                if normalized == old_text or similarity >= threshold:
                    findings.append({"source": item["id"], "oldSource": old_id, "jaccard": similarity})
    return {"checkedSourceCount": len(older), "sources": {str(p.relative_to(ROOT)): digest(p) for p in paths},
            "findings": findings, "maximumObserved": {"jaccard": largest[0], "source": largest[1], "oldSource": largest[2]},
            "oldTestOpened": False, "limitation": "Lexical duplicate screen, not semantic independence proof"}


def independent_pair_audit(corpus, projected_gold, overrides):
    expected = {}
    for lib in corpus:
        items = {i["id"]: i for i in lib["items"]}
        shared_pairs = set()
        for thread in lib["threads"]:
            members = sorted(i["id"] for i in lib["items"] if thread in i["memberships"])
            shared_pairs.update(itertools.combinations(members, 2))
        linked_pairs = set()
        for x, y in lib["relatedThreads"]:
            first = [i["id"] for i in lib["items"] if x in i["memberships"]]
            second = [i["id"] for i in lib["items"] if y in i["memberships"]]
            linked_pairs.update(tuple(sorted((a, b))) for a in first for b in second if a != b)
        for a, b in itertools.combinations(sorted(items), 2):
            key = a + "--" + b
            uncertain = not items[a]["memberships"] or not items[b]["memberships"] or key in overrides
            expected[key] = "uncertain" if uncertain else "same" if (a, b) in shared_pairs else "related" if (a, b) in linked_pairs else "unrelated"
    actual = {p["id"]: p["relation"] for p in projected_gold}
    require(len(projected_gold) == len(expected) and actual == expected, "independent pair-gold audit failed")
    return {"passed": True, "checkedPairs": len(expected), "implementation": "thread-member set expansion, separate from projection"}


def diversity(corpus):
    indexed = [(lib["split"], i["id"], shingles(i["text"])) for lib in corpus for i in lib["items"]]
    nearest = []
    for (split_a, id_a, a), (split_b, id_b, b) in itertools.combinations(indexed, 2):
        if split_a == split_b:
            continue
        score = len(a & b) / len(a | b) if a | b else 1.
        value = (score, id_a, id_b)
        if len(nearest) < 24:
            heapq.heappush(nearest, value)
        elif value > nearest[0]:
            heapq.heapreplace(nearest, value)
    return {"threadCountHistogram": dict(Counter(len(lib["threads"]) for lib in corpus)),
            "sourceWordCounts": {split: {"minimum": min(counts), "maximum": max(counts), "mean": sum(counts) / len(counts)}
                                 for split in sorted({lib["split"] for lib in corpus})
                                 for counts in [[len(i["text"].split()) for lib in corpus if lib["split"] == split for i in lib["items"]]]},
            "topCrossSplitLexicalPairs": [{"jaccard": s, "first": a, "second": b} for s, a, b in sorted(nearest, reverse=True)],
            "limitation": "Descriptive diversity/lexical checks cannot certify semantic independence"}


def source_paths():
    bound = [DATA / "families.json", DATA / "P1_PROTOCOL.md", DATA / "contract.json", DATA / "source-review.md",
             DATA / "adjudication.json", RUN / "assignment-freeze.json", RUN / "issues.json", RUN / "source-audit.json",
             DATA / "runs/preparation-01/complete.json"]
    bound += [DATA / "authoring" / f"{lid}.json" for lid in sorted(p1.assignment())]
    bound += [DATA / "reviews" / f"{reviewer}-{phase}.json" for reviewer in sorted(p1.REVIEWER.values()) for phase in ("pairs", "context")]
    bound += [RUN / "packets" / f"{author}-{phase}.json" for author in sorted(p1.REVIEWER) for phase in ("pairs", "context")]
    bound += [RUN / "receipts" / f"{author}-{phase}-review.json" for author in sorted(p1.REVIEWER) for phase in ("pair", "context")]
    bound += [ROOT / "scripts/matcher-validation" / name for name in
              ("p1.py", "p1_history.py", "p1_release.py", "test_p1.py", "test_p1_release.py", "test_p1_release_guards.py")]
    return bound


def expected_artifacts():
    names = [f"{kind}-{split}.json" for split in ("train", "calibration", "evaluation")
             for kind in ("inputs", "gold", "context-gold", "histories")]
    return [RELEASE / name for name in names + ["splits.json", "pair-overrides.json", "final-pair-review.json", "audit.json"]]


def source_audit():
    p1.capacity()
    corpus = libraries()
    _, _, structural = validate_corpus({"schemaVersion": 1, "purpose": "qualification-release", "libraries": corpus},
                                       read(DATA / "contract.json"), release=True)
    report = {"structural": structural, "historicalOverlap": historical_overlap(corpus), "diversity": diversity(corpus),
              "authorsSHA256": {lib["id"]: digest(DATA / "authoring" / f'{lib["id"]}.json') for lib in corpus},
              "reviewComplete": False, "purpose": "pre-adjudication source audit"}
    require(not report["historicalOverlap"]["findings"], "historical overlap requires review")
    publish(RUN / "source-audit.json", report)
    return report


def freeze():
    if (RUN / "complete.json").exists():
        return verify()
    p1.capacity()
    source_audit()
    issues = issue_report()
    adjudication_path = DATA / "adjudication.json"
    adjudication = read(adjudication_path)
    require(adjudication["issuesSHA256"] == digest(RUN / "issues.json"), "adjudication not bound to issues")
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in source_paths()}
    original = libraries()
    corpus, overrides = apply_decisions(original, issues["issues"], adjudication)
    pair_reviews = [read(DATA / "reviews" / f"{reviewer}-pairs.json") for reviewer in p1.REVIEWER.values()]
    requirements = final_pair_requirements(original, corpus, pair_reviews, issues["issues"])
    overrides = resolve_final_pairs(requirements, adjudication.get("finalPairDecisions", []), overrides)
    assigned = p1.assignment()
    for library in corpus:
        p1.validate_library(library, assigned[library["id"]])
    policy = read(DATA / "contract.json")
    inputs, gold, structural = validate_corpus({"schemaVersion": 1, "purpose": "qualification-release", "libraries": corpus}, policy, release=True)
    for row in gold["pairs"]:
        if row["id"] in overrides:
            row["relation"] = "uncertain"
    pair_audit = independent_pair_audit(corpus, gold["pairs"], overrides)
    overlap = historical_overlap(corpus)
    require(not overlap["findings"], "historical duplicate requires source revision and fresh review")
    histories = [build_history(lib) for lib in corpus]
    artifacts = {}

    def output(name, value):
        path = RELEASE / name
        publish(path, value)
        artifacts[str(path.relative_to(ROOT))] = digest(path)

    split_ids = {split: sorted(lib["id"] for lib in corpus if lib["split"] == split) for split in policy["requiredSplits"]}
    for split, ids in split_ids.items():
        output(f"inputs-{split}.json", {"schemaVersion": 1, "libraries": [lib for lib in inputs["libraries"] if lib["id"] in ids]})
        output(f"gold-{split}.json", {"schemaVersion": 1, "pairs": [p for p in gold["pairs"] if p["library"] in ids]})
        output(f"context-gold-{split}.json", {"schemaVersion": 1, "libraries": [lib for lib in corpus if lib["id"] in ids]})
        output(f"histories-{split}.json", {"schemaVersion": 1, "libraries": [h for h in histories if h["library"] in ids]})
    train_families = sorted({lib["storyFamily"] for lib in corpus if lib["split"] == "train"})
    folds = []
    for n in range(3):
        held = train_families[n::3]
        score_ids = sorted(lib["id"] for lib in corpus if lib["storyFamily"] in held)
        fit_ids = sorted(set(split_ids["train"]) - set(score_ids))
        require(len(score_ids) == 8 and len(fit_ids) == 16 and not set(score_ids) & set(fit_ids), "OOF family partition")
        folds.append({"id": n, "scoreFamilies": held, "scoreLibraries": score_ids, "fitLibraries": fit_ids})
    output("splits.json", {"libraries": split_ids, "innerFolds": folds,
                           "familyByLibrary": {lib["id"]: lib["storyFamily"] for lib in corpus},
                           "evaluationAccess": "after separately authorized P2 model-and-threshold freeze only"})
    output("pair-overrides.json", overrides)
    output("final-pair-review.json", {"requirements": requirements, "decisions": adjudication.get("finalPairDecisions", [])})
    review_stats = {"directPairReviews": 576, "contextSourceReviews": 960, "distinctReviewers": 3,
                    "disagreements": len(issues["issues"]), "kinds": dict(Counter(i["kind"] for i in issues["issues"])),
                    "independentHumanReview": False, "exhaustiveIndependentPairReview": False}
    review_stats["pairFirstRelations"] = dict(Counter(r["relation"] for review in pair_reviews for r in review["pairs"]))
    review_stats["pairFirstSufficiency"] = dict(Counter(r["sufficiency"] for review in pair_reviews for r in review["pairs"]))
    review_stats["postAdjudicationPairDispositions"] = len(requirements)
    review_stats["additionalRootLinkCorrections"] = len(adjudication.get("additionalLinkDecisions", []))
    summary = {"structural": structural, "finalRelations": dict(Counter(p["relation"] for p in gold["pairs"])),
               "bySplit": {s: dict(Counter(p["relation"] for p in gold["pairs"] if p["split"] == s)) for s in split_ids},
               "pairAudit": pair_audit, "historicalOverlap": overlap, "reviews": review_stats,
               "historyFixtures": len(histories), "productionHistoryReplayRun": False,
               "pairOnlyUncertaintyOverrides": len(overrides), "modelScoresUsed": False,
               "diversity": diversity(corpus)}
    output("audit.json", summary)
    require(source_hashes == {str(p.relative_to(ROOT)): digest(p) for p in source_paths()}, "sources changed during freeze")
    manifest = {"checkpoint": "P1", "complete": True, "readyForP2": True, "stopForUserReview": True,
                "trainingStarted": False, "productionQualified": False, "oldTestOpened": False,
                "sources": source_hashes, "artifacts": artifacts}
    publish(RUN / "complete.json", manifest)
    return verify()


def verify():
    p1.assignment()
    manifest = read(RUN / "complete.json")
    flags = {"complete": True, "readyForP2": True, "stopForUserReview": True,
             "trainingStarted": False, "productionQualified": False, "oldTestOpened": False}
    require(set(manifest) == {"checkpoint", "sources", "artifacts"} | set(flags), "unexpected manifest schema")
    require(manifest["checkpoint"] == "P1" and all(manifest[key] is expected for key, expected in flags.items()), "invalid checkpoint flags")
    inventories = {"sources": {str(p.relative_to(ROOT)) for p in source_paths()},
                "artifacts": {str(p.relative_to(ROOT)) for p in expected_artifacts()}}
    for collection in ("sources", "artifacts"):
        require(isinstance(manifest[collection], dict) and set(manifest[collection]) == inventories[collection], "incomplete or unexpected manifest inventory")
        for path, expected in manifest[collection].items():
            resolved = (ROOT / path).resolve()
            require(resolved.is_relative_to(ROOT) and digest(resolved) == expected, f"changed frozen file: {path}")
    return {"verified": True, "checkpoint": "P1", "completeSHA256": digest(RUN / "complete.json"),
            "readyForP2": True, "trainingStarted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("source-audit", "issues", "final-pairs", "freeze", "verify"))
    command = parser.parse_args().command
    actions = {"source-audit": source_audit, "issues": issue_report, "final-pairs": final_pairs, "freeze": freeze, "verify": verify}
    result = actions[command]()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
