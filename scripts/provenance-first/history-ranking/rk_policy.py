"""Finite query-to-evidence policies and metrics; no model or filesystem access."""
from functools import cmp_to_key
import math

THRESHOLDS = (0, .20, .35, .50, .65, .80, .90, .95)
MARGINS = (0, .05, .10)
LIMITS = (1, 3)


def cosine(first, second):
    if len(first) != len(second) or not first: raise ValueError("embedding dimensions differ")
    if any(not math.isfinite(x) for vector in (first, second) for x in vector): raise ValueError("nonfinite embedding")
    norm = math.sqrt(sum(x*x for x in first) * sum(x*x for x in second))
    if norm == 0: raise ValueError("zero embedding")
    return max(-1.0, min(1.0, sum(a*b for a,b in zip(first, second))/norm))


def grid(family):
    return [dict(family=family, minScore=threshold, margin=margin, limit=limit)
            for threshold in THRESHOLDS for margin in MARGINS for limit in LIMITS]


def config_id(config):
    return f"{config['family']}-s{config['minScore']:.2f}-m{config['margin']:.2f}-k{config['limit']}"


def ordered(rows, channel):
    def compare(a,b):
        if abs(a[channel]-b[channel]) > .0001: return -1 if a[channel] > b[channel] else 1
        left, right = (-a["created"], a["ordinal"], a["id"]), (-b["created"], b["ordinal"], b["id"])
        return (left > right) - (left < right)
    return sorted(rows, key=cmp_to_key(compare))


def predict(query, config):
    channel = "hybrid" if config["family"] == "C" else "lexical"
    eligible = query["current"] if config["family"] == "A" else query["scoped"]
    ranked, seen = [], set()
    for row in ordered(eligible, channel):
        if not math.isfinite(row[channel]) or not 0 <= row[channel] <= 1: raise ValueError("invalid score")
        identity = (row["sourceId"], row["revision"])
        if identity in seen: continue
        seen.add(identity)
        ranked.append(row)
    if not ranked: return []
    runner_up = ranked[1][channel] if len(ranked) > 1 else 0
    if ranked[0][channel] - runner_up < config["margin"]: return []
    return [dict(row, score=row[channel]) for row in ranked
            if row[channel] > 0 and row[channel] >= config["minScore"]][:config["limit"]]


def metrics(libraries, predictions):
    counts = dict(correct=0, returned=0, expected=0, answerable=0, correctHits=0,
                  unanswerable=0, falseReturns=0, librariesWithReturns=0)
    recalls, modes, per_library = [], {}, []
    distribution = {str(i):0 for i in range(4)}
    for library in libraries:
        query_recalls, rows, has_returns = [], [], False
        for task in library["tasks"]:
            hits = predictions[library["id"]][task["id"]]
            if len(hits) > 3: raise ValueError("more than three returned identities")
            identities = {(hit["sourceId"], hit["revision"]) for hit in hits}
            if len(identities) != len(hits): raise ValueError("duplicate returned source/revision")
            expected = {(e["sourceId"], e["revision"]) for e in task["expectedEvidence"]}
            supported = {(hit["sourceId"],hit["revision"]) for hit in hits
                         if any((hit["sourceId"],hit["revision"]) == (e["sourceId"],e["revision"])
                                and e["quote"] in hit["quote"] for e in task["expectedEvidence"])}
            correct = len(supported)
            counts["correct"] += correct
            counts["returned"] += len(hits)
            counts["expected"] += len(expected)
            distribution[str(len(hits))] += 1
            has_returns |= bool(hits)
            if task["answerable"]:
                if not expected: raise ValueError("answerable task lacks labels")
                recall = correct/len(expected)
                query_recalls.append(recall)
                modes.setdefault(task["mode"], []).append(recall)
                counts["answerable"] += 1
                counts["correctHits"] += int(correct > 0)
            else:
                if expected: raise ValueError("unanswerable task has evidence")
                recall = None
                counts["unanswerable"] += 1
                counts["falseReturns"] += bool(hits)
            rows.append(dict(id=task["id"], mode=task["mode"], correct=correct, returned=len(hits), recall=recall))
        if query_recalls: recalls.append(sum(query_recalls)/len(query_recalls))
        counts["librariesWithReturns"] += has_returns
        per_library.append(dict(id=library["id"], queries=rows))
    return dict(**counts, precision=counts["correct"]/counts["returned"] if counts["returned"] else None,
                macroRecall=sum(recalls)/len(recalls) if recalls else 0,
                modeRecall={mode:sum(values)/len(values) for mode,values in modes.items()},
                hitCoverage=counts["correctHits"]/counts["answerable"] if counts["answerable"] else 0,
                falseReturnRate=counts["falseReturns"]/counts["unanswerable"] if counts["unanswerable"] else 0,
                returnedDistribution=distribution, libraries=per_library)


def gates(value, baseline):
    # Integer arithmetic for precision/count gates avoids rounding a near miss into a pass.
    return dict(precision=value["returned"] > 0 and value["correct"]*10 >= value["returned"]*9,
        support=value["returned"] >= 20 and value["librariesWithReturns"] >= 8,
        recallGain=value["macroRecall"] - baseline["macroRecall"] >= .10,
        current=value["modeRecall"].get("current",0) >= baseline["modeRecall"].get("current",0),
        overlap=value["modeRecall"].get("overlap",0) >= baseline["modeRecall"].get("overlap",0),
        historical=value["modeRecall"].get("historical",0) >= .50,
        coverage=value["correctHits"]*3 >= value["answerable"]*2 and value["hitCoverage"] >= baseline["hitCoverage"],
        abstention=value["unanswerable"] > 0 and value["falseReturns"]*10 <= value["unanswerable"])


def select(rows, baseline):
    qualified = [row for row in rows if all(gates(row["metrics"],baseline).values())]
    def order(row):
        metric, config = row["metrics"], row["config"]
        precision = metric["precision"] if metric["precision"] is not None else -1
        primary = (metric["macroRecall"], precision) if qualified else (precision, metric["macroRecall"])
        return (*primary, -metric["falseReturns"], -config["limit"], config["minScore"], config["margin"], config["family"] == "B")
    winner = max(qualified or rows, key=order)
    return dict(config=winner["config"], qualified=bool(qualified), gates=gates(winner["metrics"], baseline),
                metrics=winner["metrics"], diagnosticOnly=not bool(qualified))
