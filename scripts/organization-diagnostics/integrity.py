"""Additional source/packet checks without editing the frozen packet builder."""
import math

import checkpoint as c


def expected_context(selection, libraries, pair_packet):
    aliases = selection["sourceAliases"]
    contexts = {selection["libraryAliases"][library["id"]]: [
        {"id": aliases[item["id"]], "text": item["text"], "modality": item["modality"]}
        for item in library["items"]] for library in libraries}
    selected = {item["id"]: item for item in selection["items"]}
    pairs = [row | {"contextId": selection["libraryAliases"][selected[row["id"]]["library"]]}
             for row in pair_packet["pairs"]]
    return {"schemaVersion": 1, "phase": "context", "pairs": pairs, "libraries": contexts,
            "retrospectiveContextNotOnlinePrefix": True}


def check_context(actual, expected):
    c.require(actual == expected, "Context packet differs from independently projected source whitelist")


def validate_reports(reports, libraries):
    ids = [item["id"] for library in libraries for item in library["items"]]
    c.require(len(ids) == len(set(ids)), "Duplicate source identity")
    by_library = {library["id"]: {item["id"] for item in library["items"]} for library in libraries}
    c.require(len(by_library) == len(libraries), "Duplicate library identity")
    expected_ids = None
    for report in reports.values():
        for threshold in report["thresholds"].values():
            c.require(threshold is None or (type(threshold) in (int, float) and math.isfinite(threshold)
                                            and 0 <= threshold <= 1), "Invalid threshold")
        sides = {}
        for model in ("baseline", "hybrid"):
            rows = report["predictions"][model]
            row_ids = [row["id"] for row in rows]
            c.require(len(row_ids) == len(set(row_ids)), "Duplicate prediction pair")
            if expected_ids is None:
                expected_ids = set(row_ids)
            c.require(set(row_ids) == expected_ids, "Model/seed pair coverage mismatch")
            for row in rows:
                c.require(row["split"] == "evaluation" and row["library"] in by_library,
                          "Prediction outside evaluation/source library")
                c.require(row["first"] != row["second"] and {row["first"], row["second"]} <= by_library[row["library"]],
                          "Prediction source identities outside its library")
                c.require(row["id"] == "--".join(sorted((row["first"], row["second"]))), "Noncanonical pair identity")
                c.require(type(row.get("eligible", True)) is bool, "Invalid eligibility")
                c.require(row["score"] is None or (type(row["score"]) in (int, float) and math.isfinite(row["score"])
                                                    and 0 <= row["score"] <= 1), "Invalid score")
            sides[model] = {row["id"]: {key: row[key] for key in ("library", "first", "second", "relation", "split")} for row in rows}
        c.require(sides["baseline"] == sides["hybrid"], "Baseline/hybrid identity or relation mismatch")


def verify():
    selection = c.verify_selection()
    libraries = c.read(c.RELEASE / "inputs-evaluation.json")["libraries"]
    reports = {str(seed): c.read(c.RUN / f"evaluation/seed-{seed}.json") for seed in (17, 29, 41)}
    validate_reports(reports, libraries)
    # Reconstruct both pair text and context, not just a self-reported reviewer hash.
    pair_packet = c.read(c.DATA / "packets/pairs.json")
    source_items = {item["id"]: item for library in libraries for item in library["items"]}
    source_rows = {row["id"]: row for row in reports["17"]["predictions"]["hybrid"]}
    chosen = {row["id"]: row for row in selection["items"]}
    c.require(set(pair_packet) == {"schemaVersion", "phase", "pairs"} and pair_packet["phase"] == "pair", "Invalid pair packet header")
    c.require(len(pair_packet["pairs"]) == 80 and len(chosen) == 80, "Invalid sampled pair count")
    for shown in pair_packet["pairs"]:
        c.require(set(shown) == {"id", "first", "second"}, "Non-source pair metadata")
        original = source_rows[chosen[shown["id"]]["originalPair"]]
        for side in ("first", "second"):
            item = source_items[original[side]]
            expected = {"id": selection["sourceAliases"][item["id"]], "text": item["text"], "modality": item["modality"]}
            c.require(shown[side] == expected, "Pair projection differs from source-only evidence")
    selected, counts = c.select(reports)
    projected = [{key: item[key] for key in ("originalPair", "stratum", "outcomes")} for item in selection["items"]]
    c.require(sorted(selected, key=lambda x: x["originalPair"]) == sorted(projected, key=lambda x: x["originalPair"])
              and counts == selection["availableAfterExcludingEarlierStrata"], "Sampling provenance mismatch")
    check_context(c.read(c.DATA / "packets/context.json"), expected_context(selection, libraries, pair_packet))
    return {"sourceReportsValidated": True, "sourceOnlyPacketsReconstructed": True}
