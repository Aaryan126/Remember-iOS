"""Prepare independent source-only review packets without opening author labels."""
import argparse
import hashlib
import json

import c2_common as c
from c5_data import validate_packet
from c5_metrics import validate_prediction

RUN = c.DATA / "runs/c6-01"


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def prepare():
    import c5_run
    c5_run.verify()
    packets = c.read(c5_run.RUN / "release/inputs.json")["packets"]
    unique, mappings = {}, {}
    for view in ("pair", "context"):
        for packet in packets:
            if packet["view"] != view:
                continue
            validate_packet(packet)
            key = signature({"pair": packet["pair"], "sources": packet["sources"]})
            if key not in unique:
                unique[key] = packet
            mappings[packet["queryID"]] = unique[key]["queryID"]
    for view in ("pair", "context"):
        selected = sorted((p for p in unique.values() if p["view"] == view), key=lambda p: p["queryID"])
        c.publish(RUN / f"review-inputs/{view}.json", {"packets": selected})
    c.publish(RUN / "review-inputs/mapping.json", mappings)
    paths = [RUN / f"review-inputs/{name}.json" for name in ("pair", "context", "mapping")]
    paths += [c.DATA / "C6_REVIEW_CONTRACT.md", c5_run.CURATED / "complete.json"]
    c.publish(RUN / "review-inputs/freeze.json", {"originalPackets": len(packets), "uniquePackets": len(unique),
        "inputSHA256": c.digest(c5_run.RUN / "release/inputs.json"),
        "sources": {str(p.relative_to(c.ROOT)): c.digest(p) for p in paths}, "dedupIgnoresOnlyQueryIDAndView": True})
    return {"original": len(packets), "unique": len(unique), "byPhase": {v: sum(p["view"] == v for p in unique.values()) for v in ("pair", "context")}}


def seal(reviewer, phase):
    c.require(reviewer in ("alpha", "beta") and phase in ("pair", "context"), "Invalid reviewer phase")
    path = RUN / f"reviews/{reviewer}-{phase}.json"
    if phase == "context":
        previous = c.read(RUN / f"reviews/{reviewer}-pair-seal.json")
        c.require(c.digest(RUN / f"reviews/{reviewer}-pair.json") == previous["reviewSHA256"], "Pair review changed before context")
    value = c.read(path)
    c.require(set(value) == {"reviewer", "phase", "predictions"} and value["reviewer"] == reviewer and value["phase"] == phase,
              "Invalid review identity/schema")
    packets = {p["queryID"]: p for p in c.read(RUN / f"review-inputs/{phase}.json")["packets"]}
    rows = value["predictions"]
    c.require(len(rows) == len(packets) and {r["queryID"] for r in rows} == set(packets), "Incomplete/duplicate review")
    for row in rows:
        c.require(set(row) == {"queryID", "verdict", "rationale", "evidence"} and isinstance(row["rationale"], str)
                  and row["rationale"].strip(), "Invalid review rationale")
        validate_prediction(packets[row["queryID"]], {k: v for k, v in row.items() if k != "rationale"})
    c.publish(RUN / f"reviews/{reviewer}-{phase}-seal.json", {"reviewer": reviewer, "phase": phase,
        "reviewSHA256": c.digest(path), "packetSHA256": c.digest(RUN / f"review-inputs/{phase}.json"), "count": len(rows)})
    return {"sealed": True, "reviewer": reviewer, "view": phase, "count": len(rows)}


def comparison():
    reviews = {}
    for reviewer in ("alpha", "beta"):
        reviews[reviewer] = {}
        for phase in ("pair", "context"):
            seal(reviewer, phase)
            reviews[reviewer].update({p["queryID"]: p for p in c.read(RUN / f"reviews/{reviewer}-{phase}.json")["predictions"]})
    import c5_run
    mapping = c.read(RUN / "review-inputs/mapping.json")
    author = c.read(c5_run.RUN / "release/gold.json")["labels"]
    rows = []
    for key in sorted(reviews["alpha"]):
        originals = [r for r in author if mapping[r["queryID"]] == key]
        c.require(len({r["verdict"] for r in originals}) == 1, "Identical inputs have conflicting initial labels")
        a, b = reviews["alpha"][key], reviews["beta"][key]
        rows.append({"queryID": key, "originalVerdict": originals[0]["verdict"], "alpha": a, "beta": b,
                     "needsAdjudication": a["verdict"] != b["verdict"] or a["verdict"] != originals[0]["verdict"]})
    c.publish(RUN / "review-comparison.json", {"rows": rows})
    return {"compared": len(rows), "needsAdjudication": sum(r["needsAdjudication"] for r in rows)}


def adjudicate():
    comparison()
    rows = c.read(RUN / "review-comparison.json")["rows"]
    required = {r["queryID"] for r in rows if r["needsAdjudication"]}
    decisions = c.read(RUN / "adjudication-decisions.json")["decisions"]
    c.require(len(decisions) == len(required) and {r["queryID"] for r in decisions} == required, "Missing/extra adjudication")
    index = {p["queryID"]: p for phase in ("pair", "context") for p in c.read(RUN / f"review-inputs/{phase}.json")["packets"]}
    selected = {}
    for row in rows:
        choice = next(d for d in decisions if d["queryID"] == row["queryID"]) if row["needsAdjudication"] else row["alpha"]
        c.require(set(choice) == {"queryID", "verdict", "rationale", "evidence"} and isinstance(choice["rationale"], str)
                  and choice["rationale"].strip(), "Invalid adjudication rationale")
        validate_prediction(index[row["queryID"]], {k: v for k, v in choice.items() if k != "rationale"})
        selected[row["queryID"]] = choice
    import c5_run
    mapping = c.read(RUN / "review-inputs/mapping.json")
    author = c.read(c5_run.RUN / "release/gold.json")["labels"]
    release, changes = [], []
    for original in author:
        choice = selected[mapping[original["queryID"]]]
        release.append({**original, "verdict": choice["verdict"], "evidence": choice["evidence"], "rationale": choice["rationale"],
                        "annotationStatus": "two-independent-agent-reviews-plus-root-adjudication"})
        if choice["verdict"] != original["verdict"]:
            changes.append({"queryID": original["queryID"], "canonicalID": choice["queryID"],
                            "before": original["verdict"], "after": choice["verdict"], "rationale": choice["rationale"]})
    c.publish(RUN / "adjudicated-gold.json", {"labels": release, "amendments": changes,
        "originalGoldSHA256": c.digest(c5_run.RUN / "release/gold.json"), "independentHumans": False})
    paths = list((RUN / "reviews").glob("*.json")) + [RUN / name for name in
        ("review-comparison.json", "adjudication-decisions.json", "adjudicated-gold.json")]
    c.publish(RUN / "review-complete.json", {"files": {str(p.relative_to(RUN)): c.digest(p) for p in sorted(paths)},
        "uniqueContextsPerReviewer": len(rows), "expandedPackets": len(release), "amendedPackets": len(changes),
        "rootAdjudicatedContexts": len(required), "blindness": "procedural packet restrictions; shared filesystem and model-family limitations"})
    return {"reviewComplete": True, "amendedPackets": len(changes), "adjudicatedContexts": len(required)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "seal", "compare", "adjudicate"))
    parser.add_argument("--reviewer", choices=("alpha", "beta"))
    parser.add_argument("--view", choices=("pair", "context"))
    args = parser.parse_args()
    with c.worker():
        c.log("review", **{"prepare": prepare, "seal": lambda: seal(args.reviewer, args.view),
                           "compare": comparison, "adjudicate": adjudicate}[args.phase]())
