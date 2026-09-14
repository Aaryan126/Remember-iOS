"""Finalize/verify checkpoint 1 only. No scoring, training or production replay."""
import argparse
from collections import Counter
import json
import os

import checkpoint as c
import integrity
import review_stories
import stories


def check_space():
    stats = os.statvfs(c.ROOT)
    free = stats.f_bavail * stats.f_frsize
    paths = [p for root in (c.DATA, c.ROOT / "scripts/organization-diagnostics")
             for p in root.rglob("*") if p.is_file()]
    allocated = sum(p.stat().st_blocks * 512 for p in paths)
    c.require(free >= 10 * 1024**3, "Less than 10 GiB free; pause and request space, do not delete other work")
    c.require(allocated <= 4 * 1024**3, "Diagnostic storage exceeds 4 GiB cap")
    return {"freeBytes": free, "diagnosticAllocatedBytes": allocated}


def pair_results():
    integrity.verify()
    reviews = {}
    for reviewer in c.REVIEWERS:
        for phase in ("pair", "context"):
            c.require((c.DATA / f"receipts/{reviewer}-{phase}.json").is_file(), "Missing sealed pair/context receipt")
            c.seal(reviewer, phase)
            reviews[(reviewer, phase)] = {r["id"]: r for r in c.read(c.DATA / f"reviews/{reviewer}-{phase}.json")["judgments"]}
    alpha, beta = reviews[("alpha", "context")], reviews[("beta", "context")]
    adjudication = c.read(c.DATA / "pair-adjudication.json")
    c.require(adjudication["schemaVersion"] == 1, "Invalid pair adjudication version")
    differences = {key for key in alpha if alpha[key]["relation"] != beta[key]["relation"]}
    decisions = {r["id"]: r for r in adjudication["decisions"]}
    c.require(len(decisions) == len(adjudication["decisions"]) and set(decisions) == differences,
              "Adjudication must cover every contextual disagreement exactly once")
    packet = c.read(c.DATA / "packets/context.json")
    pairs = {r["id"]: r for r in packet["pairs"]}
    for key, decision in decisions.items():
        c.require(set(decision) == {"id", "alpha", "beta", "final", "evidenceIds", "rationale"}, "Invalid pair decision keys")
        c.require(decision["alpha"] == alpha[key]["relation"] and decision["beta"] == beta[key]["relation"], "Decision changed original judgments")
        c.require(decision["final"] in c.RELATIONS and len(decision["rationale"].strip()) >= 20, "Invalid final relation/rationale")
        allowed = {item["id"] for item in packet["libraries"][pairs[key]["contextId"]]}
        c.require(decision["evidenceIds"] and set(decision["evidenceIds"]) <= allowed, "Adjudication evidence outside library")
    selection = {r["id"]: r for r in c.read(c.DATA / "selection.json")["items"]}
    rows = []
    for key in sorted(alpha):
        final = decisions[key]["final"] if key in decisions else alpha[key]["relation"]
        pair_labels = {name: reviews[(name, "pair")][key]["relation"] for name in c.REVIEWERS}
        rows.append({"id": key, "stratum": selection[key]["stratum"],
                     "oldRelation": selection[key]["originalRelation"], "finalRelation": final,
                     "decisionBy": "root-adjudication" if key in decisions else "independent-agreement",
                     "pairLabels": pair_labels,
                     "contextRequiredByEitherReviewer": any(not reviews[(name, "context")][key]["pairSufficient"] for name in c.REVIEWERS),
                     "oldSeedOutcomes": selection[key]["outcomes"]})
    summary = {
        "pairs": len(rows), "diagnosticOnly": True, "accuracyEstimate": None,
        "selectionIsErrorEnriched": True, "oldQualificationChanged": False,
        "pairOnlyAgreement": sum(reviews[("alpha", "pair")][key]["relation"] == reviews[("beta", "pair")][key]["relation"] for key in alpha),
        "contextAgreement": len(alpha) - len(differences), "contextAdjudications": len(differences),
        "contextChangesByReviewer": {name: sum(reviews[(name, "pair")][key]["relation"] != reviews[(name, "context")][key]["relation"] for key in alpha) for name in c.REVIEWERS},
        "finalRelationsByHistoricalStratum": {stratum: dict(Counter(row["finalRelation"] for row in rows if row["stratum"] == stratum)) for stratum in ("FP", "FN", "TP", "TN")},
        "finalUncertain": sum(row["finalRelation"] == "uncertain" for row in rows),
        "contextRequiredByEitherReviewer": sum(row["contextRequiredByEitherReviewer"] for row in rows),
        "retrievalEvaluated": False, "productionReplayRun": False,
    }
    return {"schemaVersion": 1, "summary": summary, "pairs": rows}


def validate_story_adjudication():
    c.require(all((c.DATA / f"receipts/{name}.json").is_file() for name in ("story-authoring", "alpha-stories")),
              "Missing existing story author/reviewer seal; do not recreate it during release")
    review_stories.seal()
    review = c.read(c.DATA / "reviews/alpha-stories.json")
    adjudication = c.read(c.DATA / "story-adjudication.json")
    c.require(set(adjudication) == {"schemaVersion", "reviewSHA256", "decisions", "findings", "dependencyAdditions"}
              and adjudication["schemaVersion"] == 1, "Invalid story adjudication schema")
    c.require(adjudication["reviewSHA256"] == c.digest(c.DATA / "reviews/alpha-stories.json"), "Story review hash changed")
    authored = {p.stem: c.read(p) for p in (c.DATA / "stories").glob("story-*.json")}
    expected = {}
    findings = {}
    for story in review["stories"]:
        original = {item["id"]: item for item in authored[story["id"]]["captures"]}
        for assignment in story["assignments"]:
            expected[(story["id"], assignment["capture"])] = (original[assignment["capture"]]["memberships"], assignment["memberships"])
        for index, finding in enumerate(story["findings"]):
            findings[(story["id"], index)] = finding
    decisions, seen = adjudication["decisions"], set()
    for decision in decisions:
        c.require(set(decision) == {"story", "capture", "authored", "reviewed", "final", "rationale"}, "Invalid story decision")
        key = (decision["story"], decision["capture"])
        c.require(key in expected and key not in seen, "Unknown/duplicate story decision")
        a, b = expected[key]
        c.require(decision["authored"] == a and decision["reviewed"] == b and len(decision["rationale"].strip()) >= 20, "Story decision source/rationale invalid")
        stories.memberships(decision["final"], {t["id"] for t in authored[key[0]]["threads"]})
        seen.add(key)
    c.require({key for key, (a, b) in expected.items() if set(a) != set(b)} <= seen,
              "Unresolved story membership disagreement")
    resolved = set()
    for decision in adjudication["findings"]:
        c.require(set(decision) == {"story", "index", "disposition", "rationale"}, "Invalid finding decision")
        key = (decision["story"], decision["index"])
        c.require(key in findings and key not in resolved and len(decision["rationale"].strip()) >= 20, "Invalid/duplicate finding decision")
        c.require(decision["disposition"] in {"fixed", "accepted-limitation", "not-a-defect"}, "Invalid disposition")
        c.require(findings[key]["severity"] != "blocker" or decision["disposition"] != "accepted-limitation", "Unresolved blocker")
        resolved.add(key)
    c.require(resolved == set(findings), "Unresolved story findings")
    for addition in adjudication["dependencyAdditions"]:
        c.require(set(addition) == {"story", "event", "dependsOn", "rationale"}
                  and addition["story"] in authored and len(addition["rationale"].strip()) >= 20, "Invalid dependency decision")
    return {"capturesReviewed": len(expected), "membershipDisagreements": sum(set(a) != set(b) for a, b in expected.values()),
            "membershipAmendments": sum(set(d["authored"]) != set(d["final"]) for d in decisions),
            "reviewFindings": len(findings), "dependencyAmendments": len(adjudication["dependencyAdditions"])}


def build():
    check_space()
    pairs = pair_results()
    story_review = validate_story_adjudication()
    story_release = stories.build()
    c.publish(c.DATA / "analysis.json", pairs | {"storyReview": story_review, "storyRelease": story_release})
    return pairs["summary"] | {"storyReview": story_review, "storyRelease": story_release}


def complete():
    build()
    check_space()
    c.require((c.DATA / "REPORT.md").exists(), "Write checkpoint report before completion")
    paths = sorted(p for p in c.DATA.rglob("*") if p.is_file()
                   and p.name not in {"complete.json", "RESUME.md", "README.md", ".DS_Store"}
                   and "runs" not in p.relative_to(c.DATA).parts)
    c.require(not any("progress" in p.name for p in paths), "Resolve draft/progress files before completion")
    paths += sorted((c.ROOT / "scripts/organization-diagnostics").glob("*.py"))
    receipt = {"schemaVersion": 1, "checkpoint": "organization-diagnostic-1", "complete": True,
               "stopForUserReview": True, "checkpoint2Started": False, "productionQualified": False,
               "trainingRun": False, "phoneTestRun": False, "productionReplayRun": False,
               "sources": {str(path.relative_to(c.ROOT)): c.digest(path) for path in paths}}
    c.publish(c.DATA / "complete.json", receipt)
    return {"complete": True, "stopForUserReview": True, "completeSHA256": c.digest(c.DATA / "complete.json")}


def verify():
    receipt = c.read(c.DATA / "complete.json")
    c.require(receipt["complete"] is True and receipt["checkpoint2Started"] is False, "Invalid completion state")
    for name, expected in receipt["sources"].items():
        path = (c.ROOT / name).resolve()
        c.require(path.is_relative_to(c.ROOT) and path.is_file() and c.digest(path) == expected, "Completed diagnostic source changed: " + name)
    # Recompute without writing so a checkout remains a read-only verification.
    integrity.verify()
    c.require(receipt["productionQualified"] is False, "Diagnostics cannot qualify production")
    return {"verified": True, "completeSHA256": c.digest(c.DATA / "complete.json"), "stopForUserReview": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "complete", "verify"))
    args = parser.parse_args()
    print(json.dumps({"build": build, "complete": complete, "verify": verify}[args.command](), sort_keys=True))


if __name__ == "__main__":
    main()
