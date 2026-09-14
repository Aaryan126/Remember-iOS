"""Contract-level metrics for future predictions; C5 executes fixtures, not models."""
from collections import Counter

import c2_common as c
from c5_data import LABELS, validate_packet


def validate_prediction(packet, prediction):
    validate_packet(packet)
    c.require(set(prediction) == {"queryID", "verdict", "evidence"}, "Invalid prediction schema")
    c.require(prediction["queryID"] == packet["queryID"] and prediction["verdict"] in LABELS, "Invalid prediction identity/verdict")
    c.require(isinstance(prediction["evidence"], list), "Invalid evidence list")
    texts = {s["id"]: s["text"] for s in packet["sources"]}
    cited = set()
    for item in prediction["evidence"]:
        c.require(set(item) == {"sourceID", "quote"} and isinstance(item["sourceID"], str) and item["sourceID"] in texts,
                  "Evidence source is not visible")
        c.require(isinstance(item["quote"], str) and item["quote"].strip() and item["quote"] in texts[item["sourceID"]],
                  "Evidence quote is not grounded")
        cited.add(item["sourceID"])
    if prediction["verdict"] != "abstain":
        c.require(len(cited) >= 2 and bool(cited & set(packet["pair"])), "Decisive assertion needs visible evidence")
    return prediction


def evaluate(packets, labels, predictions):
    expected_ids = [p["queryID"] for p in packets]
    c.require(len(expected_ids) == len(set(expected_ids)) and expected_ids, "Invalid packet inventory")
    ids = set(expected_ids)
    gold = {r["queryID"]: r for r in labels}
    proposed = {r["queryID"]: r for r in predictions}
    c.require(len(gold) == len(labels) and set(gold) == ids, "Missing/duplicate gold")
    c.require(len(proposed) == len(predictions) and set(proposed) == ids, "Missing/duplicate predictions; not abstentions")
    groups = {}
    for packet in packets:
        key = packet["queryID"]
        prediction = validate_prediction(packet, proposed[key])
        truth = gold[key]
        c.require(truth["verdict"] in LABELS, "Invalid gold verdict")
        scopes = ["all", "view:" + packet["view"], "family:" + truth["family"], "partition:" + truth["partition"],
                  "behavior:" + truth["behavior"]]
        for scope in scopes:
            counter = groups.setdefault(scope, Counter())
            actual, target = prediction["verdict"], truth["verdict"]
            counter["queries"] += 1
            counter["correctThreeWay"] += int(actual == target)
            counter["decisive"] += int(actual != "abstain")
            counter["knownSeparate"] += int(target == "separate_projects")
            counter["predictedSeparate"] += int(actual == "separate_projects")
            counter["trueSeparate"] += int(actual == target == "separate_projects")
            counter["falseSeparateOnSame"] += int(actual == "separate_projects" and target == "same_project")
            counter["unsupportedSeparate"] += int(actual == "separate_projects" and target == "abstain")
            counter["knownSame"] += int(target == "same_project")
            counter["predictedSame"] += int(actual == "same_project")
            counter["trueSame"] += int(actual == target == "same_project")
            counter["falseSameOnSeparate"] += int(actual == "same_project" and target == "separate_projects")
            counter["unknown"] += int(target == "abstain")
            counter["unsupportedDecisive"] += int(target == "abstain" and actual != "abstain")
    def rate(n, d):
        return {"numerator": n, "denominator": d, "value": n / d if d else None}
    result = {scope: {"counts": dict(row), "conflictPrecision": rate(row["trueSeparate"], row["predictedSeparate"]),
        "conflictRecall": rate(row["trueSeparate"], row["knownSeparate"]), "coverage": rate(row["decisive"], row["queries"]),
        "falseConflictRateOnSame": rate(row["falseSeparateOnSame"], row["knownSame"]),
        "unsupportedAssertionRate": rate(row["unsupportedDecisive"], row["unknown"])} for scope, row in sorted(groups.items())}
    contrasts = {}
    for name, episodes, count in (("scopeContrast", {"scope-contrast", "continuation"}, 2),
                                  ("bridgeTriple", {"bridge"}, 3),
                                  ("referenceBeforeAfter", {"before", "after"}, 4)):
        for view in ("pair", "context"):
            passed, total = 0, 0
            for family in sorted({row["family"] for row in labels}):
                selected = [p["queryID"] for p in packets if p["view"] == view and gold[p["queryID"]]["family"] == family
                            and gold[p["queryID"]]["episode"] in episodes]
                # Subset evaluation must not silently count incomplete contrast groups.
                if len(selected) == count:
                    total += 1
                    passed += int(all(proposed[key]["verdict"] == gold[key]["verdict"] for key in selected))
            contrasts[name + ":" + view] = rate(passed, total)
    result["contrastChecks"] = contrasts
    return result
