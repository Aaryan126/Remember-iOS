"""Evaluator-only labels. Never imported by scorer, placement or search adapters."""
from statistics import mean

from pc_policy import THRESHOLDS


def fraction(a, b):
    return a / b if b else None


def identity(hit):
    return hit["sourceId"], hit["revision"]


def evaluate(traces, libraries, variant):
    by_library = {lib["id"]: lib for lib in libraries}
    edges, captures, queries, proposals, finals = [], [], [], [], []
    for trace in traces:
        library = by_library[trace["id"]]
        root_projects = {p["rootSourceId"]: p["id"] for p in library["projects"]}
        project_roots = {p["id"]: p["rootSourceId"] for p in library["projects"]}
        anchor_projects = {e["sourceId"]: e["gold"]["memberships"] for e in library["events"] if e["kind"] == "capture"}
        gold_events = {e["id"]: e for e in library["events"]}
        def semantic(thread):
            values = anchor_projects[thread]
            return values[0] if len(values) == 1 else f"unsupported:{thread}"
        final_gold = {}
        for row in trace["events"]:
            event, decision = row["event"], row["decision"]
            expected = gold_events[event["id"]]["gold"]
            final_gold[event["sourceId"]] = expected
            if event["kind"] != "capture":
                continue
            prefix = [trace["id"], trace["order"], event["id"]]
            predicted = [semantic(t) for t in decision["selected"]]
            for project in predicted:
                edges.append({"key": prefix+[project], "correct": project in expected["memberships"]})
            # A fresh singleton is not an inferred membership; only a canonical root
            # introduces its own project without an automatic attachment.
            resolved = predicted or ([root_projects[event["sourceId"]]] if event["sourceId"] in root_projects else [])
            captures.append({"library": trace["id"], "order": trace["order"], "event": event["id"],
                             "exact": set(resolved) == set(expected["memberships"]),
                             "unresolved": expected["disposition"] == "unresolved", "automatic": bool(predicted)})
            if variant == "C":
                proposed = {semantic(t) for t in decision["proposals"]}
                proposals.append({"library": trace["id"], "order": trace["order"], "event": event["id"],
                                  "returned": len(proposed), "correct": len(proposed & set(expected["memberships"])),
                                  "expected": len(expected["memberships"]),
                                  "shared": len(expected["memberships"]) > 1,
                                  "allSharedRecovered": len(expected["memberships"]) > 1 and set(expected["memberships"]) <= proposed})
        final = trace["events"][-1]["state"]
        occupied = {p: {thread for sid, value in final.items() if not value["archived"] and p in final_gold[sid]["memberships"]
                        for thread in value["memberships"]} for p in project_roots}
        roots = list(root_projects)
        fusions = sum(bool(set(final[a]["memberships"]) & set(final[b]["memberships"]))
                      for i, a in enumerate(roots) for b in roots[i+1:])
        shared = [sid for sid, label in final_gold.items() if len(label["memberships"]) > 1 and not final[sid]["archived"]]
        recovered = [sid for sid in shared if {project_roots[p] for p in final_gold[sid]["memberships"]} <= set(final[sid]["memberships"])]
        finals.append({"library": trace["id"], "order": trace["order"], "additionalFragments": {p:max(0,len(v)-1) for p,v in occupied.items()},
                       "rootPairsSharingThread": fusions, "sharedSources": len(shared), "sharedInBothRivers": len(recovered),
                       "recoveredSharedWithUserCorrection": sum(final[sid]["pinned"] for sid in recovered)})
        labels = {q["id"]: q for q in library["tasks"]}
        states = {r["event"]["id"]: r["state"] for r in trace["events"]}
        for row in trace["queries"]:
            label = labels[row["id"]]
            expected = {identity(e) for e in label["expectedEvidence"]}
            results = row["confirmed"] if variant == "A" else row["combined"]
            suggestions = [] if variant == "A" else row["suggested"]
            returned = {identity(e) for e in results}
            outside = {identity(e) for e in suggestions}
            queries.append({"library": trace["id"], "id": row["id"], "mode": label["mode"],
                            "answerable": label["answerable"], "expected": len(expected), "returned": len(returned),
                            "correct": len(expected & returned), "recall": fraction(len(expected & returned),len(expected)),
                            "suggested": len(outside), "suggestionCorrect": len(outside & expected),
                            "requiresOldRevision": any(states[row["atEvent"]][sid]["revision"] != rev for sid, rev in expected)})
    correct = sum(row["correct"] for row in edges)
    unresolved = [row for row in captures if row["unresolved"]]
    bylib = {}
    for key in sorted(by_library):
        subset = [r for r in queries if r["library"] == key and r["answerable"]]
        libedges = [r for r in edges if r["key"][0] == key]
        bylib[key] = {"automaticEdges": len(libedges), "correctEdges": sum(r["correct"] for r in libedges),
                      "recall": mean(r["recall"] for r in subset) if subset else None}
    modes = {}
    for mode in ("current", "historical", "overlap", "uncertain"):
        subset = [r for r in queries if r["mode"] == mode and r["answerable"]]
        modes[mode] = {"answerableQueries": len(subset), "macroRecall": mean(r["recall"] for r in subset) if subset else None}
    total_returned = sum(r["returned"] for r in queries)
    relevant = sum(r["correct"] for r in queries)
    suggestions = sum(r["suggested"] for r in queries)
    old = [r for r in queries if r["requiresOldRevision"]]
    unanswered = [r for r in queries if not r["answerable"]]
    library_recalls = [r["recall"] for r in bylib.values() if r["recall"] is not None]
    return {"variant": variant, "automaticEdges": len(edges), "correctEdges": correct,
            "wrongEdges": len(edges)-correct, "precision": fraction(correct,len(edges)),
            "captureOpportunities": len(captures), "automaticCoverage": fraction(sum(r["automatic"] for r in captures),len(captures)),
            "exactMembershipSets": sum(r["exact"] for r in captures),
            "unresolvedCaptures": len(unresolved), "unsupportedAutomatic": sum(r["automatic"] for r in unresolved),
            "unsupportedRate": fraction(sum(r["automatic"] for r in unresolved),len(unresolved)),
            "queries": {"count": len(queries), "returned": total_returned, "correct": relevant,
                        "precisionAt3": fraction(relevant,total_returned),
                        "pooledRecallAt3": fraction(relevant,sum(r["expected"] for r in queries)),
                        "libraryMacroRecallAt3": mean(library_recalls) if library_recalls else None,
                        "resultCountDistribution": {str(n):sum(r["returned"]==n for r in queries) for n in range(4)},
                        "suggestions": suggestions, "suggestionPrecisionAt3": fraction(sum(r["suggestionCorrect"] for r in queries),suggestions),
                        "unanswerableQueries": len(unanswered), "unanswerableWithReturns": sum(bool(r["returned"]) for r in unanswered),
                        "oldRevisionTasks": len(old), "oldRevisionTaskRecall": mean(r["recall"] for r in old) if old else None,
                        "byMode": modes},
            "perLibrary": bylib, "edges": edges, "captures": captures, "queryRows": queries, "finalStates": finals,
            "proposals": {"returned": sum(r["returned"] for r in proposals), "correct": sum(r["correct"] for r in proposals),
                          "expected": sum(r["expected"] for r in proposals), "sharedOpportunities": sum(r["shared"] for r in proposals),
                          "allSharedRecovered": sum(r["allSharedRecovered"] for r in proposals)},
            "proposalRows": proposals}


def choose(candidates):
    eligible = [(threshold, report) for threshold, report in candidates
                if report["automaticEdges"] >= 20 and report["precision"] is not None and report["precision"] >= .95]
    if not eligible:
        return {"automatic": False, "threshold": THRESHOLDS[0], "reason": "no development candidate met precision/denominator gates"}
    threshold, _ = max(eligible, key=lambda item: (item[1]["automaticEdges"], item[0]))
    return {"automatic": True, "threshold": threshold, "reason": "highest eligible development coverage; stricter threshold wins ties"}


def gates(reference, candidate):
    a = {tuple(r["key"]) for r in reference["edges"] if r["correct"]}
    b = {tuple(r["key"]) for r in candidate["edges"] if r["correct"]}
    retention = fraction(len(a & b), len(a))
    recall_a = reference["queries"]["libraryMacroRecallAt3"]
    recall_b = candidate["queries"]["libraryMacroRecallAt3"]
    gain = recall_b-recall_a if recall_a is not None and recall_b is not None else None
    precision = candidate["queries"]["suggestionPrecisionAt3"]
    checks = {"denominator": candidate["automaticEdges"] >= 20,
              "precision": candidate["precision"] is not None and candidate["precision"] >= .95,
              "wrongEdges": candidate["wrongEdges"] <= reference["wrongEdges"],
              "retention": retention is not None and retention >= .8,
              "unsupported": candidate["unsupportedRate"] is not None and candidate["unsupportedRate"] <= .1}
    return {"automaticChecks": checks, "automaticPointTargetsMet": all(checks.values()),
            "retainedCorrectEdges": len(a & b), "referenceCorrectEdges": len(a), "missingCorrectEdges": [list(x) for x in sorted(a-b)],
            "retention": retention, "recallGain": gain,
            "suggestionPointTargetsMet": precision is not None and precision >= .9 and gain is not None and gain >= .1,
            "nativeIntegrityStillRequired": True}
