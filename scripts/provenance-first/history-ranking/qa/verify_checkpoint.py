"""Post-selection audit only: no inference, selection, or policy changes."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import rk_runner as runner
import rk_control as control


def verify():
    runner.verify()
    selection = runner.verify_selection()
    paths = [control.WORK / "results.json", control.RUN / "evaluation/predictions.json"]
    before = {str(p): (control.digest(p), p.stat().st_mtime_ns) for p in paths}
    results = runner.evaluate()
    control.require(before == {str(p): (control.digest(p), p.stat().st_mtime_ns) for p in paths},
                    "metric replay modified immutable results")
    predictions = control.read_unit(paths[1], runner.binding())
    labels = {library["id"]: library for library in runner.labels("evaluation")}
    metrics = dict(A=results["baseline"], B0=results["historyControl"])
    metrics.update({family: row["metrics"] for family, row in results["comparisons"].items()})
    expected_families = {"A", "B0", *selection["families"]}
    control.require(set(predictions) == expected_families, "unexpected prediction family")
    checked_hits, checked_queries = 0, 0
    for family, libraries in predictions.items():
        control.require(set(libraries) == set(labels), "prediction libraries differ from evaluation")
        correct = returned = false_returns = 0
        correct_by_mode = {"current": 0, "historical": 0, "overlap": 0}
        mode_sizes = dict.fromkeys(correct_by_mode, 0)
        for library_id, query_hits in libraries.items():
            packets = {q["id"]: q for q in runner.packets(library_id)}
            tasks = {task["id"]: task for task in labels[library_id]["tasks"]}
            control.require(set(query_hits) == set(packets) == set(tasks), "query set differs")
            for query_id, hits in query_hits.items():
                checked_queries += 1
                task, packet = tasks[query_id], packets[query_id]
                eligible = {row["id"]: row for row in packet["current" if family == "A" else "scoped"]}
                control.require(len(hits) <= 3, "result limit exceeded")
                control.require(len({(h["sourceId"], h["revision"]) for h in hits}) == len(hits),
                                "duplicate source revision")
                relevant = 0
                for hit in hits:
                    control.require(hit["id"] in eligible, "citation is outside native query scope/prefix")
                    native = eligible[hit["id"]]
                    control.require(all(hit.get(key) == value for key, value in native.items()),
                                    "native evidence or citation was changed")
                    relevant += int(any(hit["sourceId"] == gold["sourceId"]
                                        and hit["revision"] == gold["revision"]
                                        and gold["quote"] in hit["quote"]
                                        for gold in task["expectedEvidence"]))
                    checked_hits += 1
                returned += len(hits)
                correct += relevant
                if task["answerable"]:
                    control.require(len(task["expectedEvidence"]) == 1, "audit assumes one evidence target")
                    correct_by_mode[task["mode"]] += relevant
                    mode_sizes[task["mode"]] += 1
                else:
                    false_returns += int(bool(hits))
        metric = metrics[family]
        control.require((correct, returned, false_returns) ==
                        (metric["correct"], metric["returned"], metric["falseReturns"]),
                        "independent outcome counts differ")
        control.require(all(mode_sizes[mode] == 12 for mode in mode_sizes), "unbalanced modes")
        control.require(abs(metric["macroRecall"] - correct / 36) < 1e-12,
                        "independent balanced-library recall differs")
        control.require(all(abs(metric["modeRecall"][mode] - count / 12) < 1e-12
                            for mode, count in correct_by_mode.items()), "independent mode recall differs")
    result = dict(status="passed", checkedQueries=checked_queries, checkedReturnedCitations=checked_hits,
                  metricReplayIdentical=True, metricReplayPreservedMtime=True,
                  independentOutcomeCounts=True, scopeAndNativeEvidencePreserved=True,
                  priorCheckpointBindingsPreserved=True, bindingSHA256=runner.binding(),
                  selectionSHA256=control.digest(control.WORK / "selection.json"),
                  resultsSHA256=control.digest(paths[0]), auditCodeSHA256=control.digest(Path(__file__).resolve()))
    control.publish(control.WORK / "final-verification.json", result)
    print(result)


if __name__ == "__main__":
    with control.worker():
        verify()
