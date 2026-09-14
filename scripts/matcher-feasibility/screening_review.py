"""Deterministic error sampling and honest pair-first/context-second review receipts."""
from collections import Counter
import hashlib
from pathlib import Path

from screening_common import BASELINE, NEURAL, read, save, sha, require, load_split, now
from stage2_metrics import accepted


def sample_cases():
    baseline = read(BASELINE / "baseline/C-10.json")
    baseline_rows = [r | {"id": r["first"] + "--" + r["second"]} for r in baseline["predictions"]["development"]]
    threshold = read(BASELINE / "baseline-selected.json")["threshold"]
    neural = read(NEURAL / "evaluations/seed-17-epoch-3/development/summary.json")
    neural_rows = {r["id"]: r for r in neural["rows"]}
    # Post-run diagnostic threshold is solely for sampling errors, never new selection.
    neural_threshold = .9831428229808807
    inputs, _ = load_split("development")
    texts = {i["id"]: i["text"] for lib in inputs["libraries"] for i in lib["items"]}
    selected = []
    for lib in inputs["libraries"]:
        rows = [r for r in baseline_rows if r["library"] == lib["id"]]
        rows.sort(key=lambda r: hashlib.sha256(("screening-review-17:"+r["id"]).encode()).hexdigest())
        chosen = set()
        def yes(r):
            return accepted(r,threshold) or accepted(neural_rows[r["id"]],neural_threshold)
        categories = [
            ("false_join", 2, lambda r: r["relation"] not in ("same","uncertain") and yes(r)),
            ("missed_same", 3, lambda r: r["relation"] == "same" and (not accepted(r,threshold) or not accepted(neural_rows[r["id"]],neural_threshold))),
            ("ambiguous", 2, lambda r: r["relation"] == "uncertain"),
            ("correct_accept", 2, lambda r: r["relation"] == "same" and yes(r)),
            ("correct_reject", 1, lambda r: r["relation"] in ("related","unrelated") and not yes(r)),
            ("coverage_fill", 10, lambda r: True)]
        for category, count, predicate in categories:
            for row in [r for r in rows if r["id"] not in chosen and predicate(r)][:min(count,10-len(chosen))]:
                chosen.add(row["id"])
                selected.append({"id": row["id"], "library": lib["id"], "first": row["first"], "second": row["second"],
                    "texts": [texts[row["first"]],texts[row["second"]]], "category": category, "gold": row["relation"],
                    "baselineAccepted": accepted(row,threshold), "neuralDiagnosticAccepted": accepted(neural_rows[row["id"]],neural_threshold)})
    require(len(selected) == 60 and len({r["id"] for r in selected}) == 60, "review sample incomplete")
    return selected


def prepare_review(run):
    if (run / "review/selection.json").exists():
        return
    cases = sample_cases()
    save(run / "review/selection.json", {"cases": cases, "perLibrary": dict(Counter(r["library"] for r in cases)),
        "policy": "10 per library; prioritized error/ambiguity/control strata, stable SHA256 order; not a prevalence estimate"})
    save(run / "review/pair-inputs.json", {"cases": [{k: r[k] for k in ("id","texts")} for r in cases],
        "reviewerContext": "Executing agent has previously seen summary reports and some development examples; pair-first protocol is not an independent blinded annotation audit."})


def publish_context(run):
    cases = read(run / "review/selection.json")["cases"]
    require(all((run / "review/pair" / f"{r['id']}.json").exists() for r in cases), "complete pair-only review before context release")
    path = run / "review/context-inputs.json"
    if not path.exists():
        inputs, labels = load_split("development")
        save(path, {"releasedAt": now(), "pairReviewHashes": {r["id"]: sha(run/"review/pair"/f"{r['id']}.json") for r in cases},
                    "libraries": inputs["libraries"], "annotations": labels["libraries"], "cases": cases})


def import_reviews(run, file):
    payload = read(file)
    require(set(payload) == {"phase","reviewer","records"} and payload["reviewer"] == "executing_agent", "invalid review author/schema")
    phase = payload["phase"]
    require(phase in ("pair","context"), "invalid review phase")
    if phase == "context":
        require((run/"review/context-inputs.json").exists(), "context review not released")
    cases = {r["id"]: r for r in read(run / "review/selection.json")["cases"]}
    require(len({r["id"] for r in payload["records"]}) == len(payload["records"]), "duplicate review record")
    for row in payload["records"]:
        require(row["id"] in cases and isinstance(row.get("note"),str) and len(row["note"].strip()) >= 20, "missing review evidence")
        if phase == "pair":
            require(set(row) == {"id","relation","sufficiency","note"}, "invalid pair review fields")
            require(row["relation"] in ("same","related","unrelated","uncertain") and row["sufficiency"] in ("sufficient","needs_context"), "invalid pair review decision")
        else:
            require(set(row) == {"id","labelAssessment","cause","note"}, "invalid contextual review fields")
            require(row["labelAssessment"] in ("supported","insufficient_evidence","possible_label_issue"), "invalid label assessment")
            require(row["cause"] in ("decision_error","missing_context","ambiguity_appropriate","no_issue","uncertain"), "invalid cause")
        path = run / "review" / phase / f"{row['id']}.json"
        if path.exists():
            require(read(path)["review"] == row, "review is immutable")
        else:
            save(path, {"review": row, "recordedAt": now(), "reviewer": payload["reviewer"], "importSHA256": sha(file)})
    if phase == "pair" and all((run/"review/pair"/f"{r}.json").exists() for r in cases):
        publish_context(run)


def summarize_review(run):
    cases = read(run / "review/selection.json")["cases"]
    result = []
    for case in cases:
        pair = read(run / "review/pair" / f"{case['id']}.json")["review"]
        context = read(run / "review/context" / f"{case['id']}.json")["review"]
        result.append({"id": case["id"], "category": case["category"], "gold": case["gold"],
                       "pair": pair, "context": context})
    return {"reviewedPairs": len(result), "cases": result,
            "pairSufficiency": dict(Counter(r["pair"]["sufficiency"] for r in result)),
            "labelAssessments": dict(Counter(r["context"]["labelAssessment"] for r in result)),
            "causes": dict(Counter(r["context"]["cause"] for r in result)),
            "labelsChanged": False, "independentBlindReview": False,
            "limitation": "Single executing-agent diagnostic with prior report exposure; sample enriched for failures. Not human validation or an unbiased error-frequency estimate."}
