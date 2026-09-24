"""Bounded current/history lexical/semantic recovery experiment. No app writes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import rk_control as c
import rk_policy as policy
import rk_runtime as runtime
from verify_coverage import source_uuid

REFERENCE = dict(family="A", minScore=0, margin=0, limit=3)
HISTORY_CONTROL = dict(family="B0", minScore=0, margin=0, limit=3)


def hash_text(text): return hashlib.sha256(text.encode()).hexdigest()


def paths():
    result = list(c.CODE.glob("*.py")) + [c.WORK / "PROTOCOL.md"]
    result += [c.history.WORK / name for name in ("frozen.json", "checkpoint1-complete.json", "coverage.json")]
    result += list((c.history.WORK / "units").glob("*/source-only.json"))
    result += list((c.history.RUN / "output").glob("*.projection.json"))
    result += list((c.history.RUN / "output").glob("*.history.receipt.json"))
    result += [c.history.WORK / "authored" / f"{split}.json" for split in ("development", "evaluation")]
    return {str(p.relative_to(c.ROOT)): c.digest(p) for p in sorted(result)}


def freeze():
    c.verify_prior()
    record = dict(schemaVersion=1, approvalReply="carrry on sorry", checkpoint="history-ranking-2",
                  capBytes=18*c.history.GIB, reserveBytes=10*c.history.GIB, baselineReset=False,
                  hashes=paths(), runtime=runtime.identity(), configurationCountPerFamily=48,
                  appIntegrationAllowed=False, resources=c.resources())
    if (c.WORK / "frozen.json").exists(): return verify()
    c.publish(c.WORK / "frozen.json", record)
    return record


def verify():
    record = c.load(c.WORK / "frozen.json")
    c.require(record["hashes"] == paths(), "ranking frozen inputs/code changed")
    c.require(record["runtime"] == runtime.identity(), "ranking runtime changed")
    c.verify_prior()
    return record


def binding(): return c.digest(c.WORK / "frozen.json")


def qualify():
    verify()
    path = c.WORK / "compatibility.json"
    if path.exists(): return c.read_unit(path, binding())
    try: result = runtime.qualify()
    except (ValueError, TimeoutError) as error:
        result = dict(status="unsupported", supported=False, error=str(error),
                      action="C excluded; A/B can continue without substitution")
    c.unit(path, result, binding())
    return result


def allowed(split):
    c.require(split in ("development", "evaluation"), "invalid split")
    if split == "evaluation": verify_selection()


def library_ids(split):
    return [f"{'dev' if split=='development' else 'eval'}{i:02d}" for i in range(1,13)]


def packets(library_id):
    # Allowlists keep metrics labels/ideal assignments out of scoring. This code
    # reads native evidence projections and source-only packets, never authored gold.
    observed = c.load(c.history.WORK / "units" / library_id / "source-only.json")
    run_id = f"history-{library_id}-chronological"
    key = hash_text(run_id)
    output = c.history.RUN / "output"
    receipt = c.load(output / (key + ".history.receipt.json"))
    projection_path = output / (key + ".projection.json")
    c.require(receipt["projectionSHA256"] == c.digest(projection_path), "native projection changed")
    projection = c.load(projection_path)
    prefixes = {p["id"]:p for p in projection["prefixes"]}
    result = []
    for query in observed["queries"]:
        c.require(set(query) == {"id","atEvent","question","scope"}, "query includes unexpected metadata")
        prefix = prefixes[query["atEvent"]]
        visible = []
        for event in observed["events"]:
            visible.append(event)
            if event["id"] == query["atEvent"]: break
        sources = {source_uuid(e["sourceId"]): (e["sourceId"],i)
                   for i,e in enumerate(visible) if e["kind"] == "capture"}
        def safe(row):
            source_id, created = sources[row["sourceID"].upper()]
            c.require(row["sourceSequence"] <= prefix["sequence"] and row["snapshotSequence"] <= prefix["sequence"],
                      "candidate exceeds query boundary")
            return dict(id=row["id"], sourceId=source_id, revision=row["revision"], versionID=row["versionID"],
                        snapshotID=row["snapshotID"], quote=row["quote"], locator=row["locator"],
                        evidenceField=row["evidenceField"], ordinal=row["ordinal"], created=created,
                        isArchived=row["isArchived"], isCurrentVersion=row["isCurrentVersion"])
        c.require(query["scope"] in ("current","includeHistory"), "invalid explicit scope")
        result.append(dict(id=query["id"], question=query["question"], scope=query["scope"],
                           atEvent=query["atEvent"], current=[safe(r) for r in prefix["current"]],
                           scoped=[safe(r) for r in prefix[query["scope"]]]))
    return result


def catalog(split):
    texts = {}
    for library in library_ids(split):
        for query in packets(library):
            for text in [query["question"], *[row["quote"] for row in query["scoped"] + query["current"]]]:
                texts[hash_text(text)] = text
    return dict(sorted(texts.items()))


def cache(split, maximum=None):
    verify()
    allowed(split)
    compatible = c.read_unit(c.WORK / "compatibility.json", binding())
    c.require(compatible["supported"], "semantic candidate unsupported; do not create embedding cache")
    texts = catalog(split)
    c.publish(c.RUN / split / "catalogue.json", texts)
    made = 0
    for key,text in texts.items():
        c.boundary()
        path = c.RUN / split / "embeddings" / (key + ".json")
        if path.exists(): runtime.valid_embedding(c.read_unit(path,binding()), text)
        else:
            c.unit(path,runtime.embed(text),binding())
            made += 1
            if made % 10 == 0: print(json.dumps(dict(phase="embeddings",split=split,newUnits=made,total=len(texts))),flush=True)
            if maximum is not None and made >= maximum: raise c.Paused("bounded embedding limit")


def scored_library(library_id, split, compatible, locale):
    queries = packets(library_id)
    for query in queries:
        c.boundary()
        rows = {row["id"]:row for row in query["current"] + query["scoped"]}
        lexical = runtime.lexical(query["question"], list(rows.values()), locale)
        if compatible:
            def vector(text):
                value = c.read_unit(c.RUN / split / "embeddings" / (hash_text(text) + ".json"),binding())
                return runtime.valid_embedding(value,text)["sentence"]
            query_vector = vector(query["question"])
        scored = {}
        for key,row in rows.items():
            lex = lexical.get(key,0)
            semantic = max(0,policy.cosine(query_vector,vector(row["quote"]))) if compatible else None
            scored[key] = dict(row, lexical=lex, semantic=semantic,
                               hybrid=.35*lex+.65*semantic if compatible else None)
        query["current"] = [scored[row["id"]] for row in query["current"]]
        query["scoped"] = [scored[row["id"]] for row in query["scoped"]]
    return queries


def score(split, maximum=None):
    record = verify()
    allowed(split)
    compatible = c.read_unit(c.WORK / "compatibility.json",binding())["supported"]
    made = 0
    for library_id in library_ids(split):
        c.boundary()
        path = c.RUN / split / "scores" / (library_id + ".json")
        if path.exists(): c.read_unit(path,binding())
        else:
            value = scored_library(library_id,split,compatible,record["runtime"]["locale"])
            c.unit(path,value,binding())
            made += 1
            print(json.dumps(dict(phase="scores",split=split,library=library_id)),flush=True)
            if maximum is not None and made >= maximum: raise c.Paused("bounded library limit")


def labels(split):
    allowed(split)
    # Only metric computation calls this boundary; scorers never call it.
    return c.load(c.history.WORK / "authored" / (split+".json"))["libraries"]


def predict(split, config):
    return {key:{q["id"]:policy.predict(q,config)
                 for q in c.read_unit(c.RUN / split / "scores" / (key+".json"),binding())}
            for key in library_ids(split)}


def select():
    verify()
    target = c.WORK / "selection.json"
    if target.exists(): return verify_selection()
    c.require(not (c.RUN / "evaluation").exists(), "evaluation work started before selection")
    libs = labels("development")
    baseline = policy.metrics(libs,predict("development",REFERENCE))
    compatible = c.read_unit(c.WORK / "compatibility.json",binding())["supported"]
    selections, all_rows = {}, []
    for family in (["B","C"] if compatible else ["B"]):
        rows = []
        for config in policy.grid(family):
            row = dict(config=config,metrics=policy.metrics(libs,predict("development",config)))
            rows.append(row)
        all_rows += rows
        selections[family] = policy.select(rows,baseline)
    qualified = [dict(config=s["config"],metrics=s["metrics"]) for s in selections.values() if s["qualified"]]
    winner = policy.select(qualified,baseline)["config"]["family"] if qualified else None
    c.unit(c.RUN / "development/grid.json",all_rows,binding())
    dev_files = list((c.RUN / "development").rglob("*.json"))
    record = dict(bindingSHA256=binding(),families=selections,winnerFamily=winner,
                  baseline=baseline,diagnosticControl=policy.metrics(libs,predict("development",HISTORY_CONTROL)),
                  evaluationOpened=False,developmentFiles={str(p.relative_to(c.ROOT)):c.digest(p) for p in dev_files},
                  compatibilitySHA256=c.digest(c.WORK / "compatibility.json"))
    c.publish(target,record)
    c.publish(c.WORK / "selection.seal.json",dict(selectionSHA256=c.digest(target),bindingSHA256=binding()))
    return record


def verify_selection():
    value = c.load(c.WORK / "selection.json")
    seal = c.load(c.WORK / "selection.seal.json")
    c.require(seal == dict(selectionSHA256=c.digest(c.WORK / "selection.json"),bindingSHA256=binding()),
              "sealed selection changed")
    c.require(value["bindingSHA256"] == binding() and value["evaluationOpened"] is False,
              "selection binding changed")
    c.require(value["compatibilitySHA256"] == c.digest(c.WORK / "compatibility.json"), "compatibility changed")
    for name,expected in value["developmentFiles"].items():
        path = c.ROOT / name
        c.require(path.resolve().is_relative_to(c.RUN / "development") and c.digest(path) == expected,
                  "selected development cache changed")
    return value


def evaluate():
    verify()
    selected = verify_selection()
    libraries = labels("evaluation")
    configs = [REFERENCE,HISTORY_CONTROL]+[item["config"] for item in selected["families"].values()]
    predictions = {config["family"]:predict("evaluation",config) for config in configs}
    results = {family:policy.metrics(libraries,value) for family,value in predictions.items()}
    comparisons = {family:dict(metrics=results[family],gates=policy.gates(results[family],results["A"]),
                               developmentQualified=selected["families"][family]["qualified"])
                   for family in selected["families"]}
    winner = selected["winnerFamily"]
    qualified = winner is not None and all(comparisons[winner]["gates"].values())
    c.unit(c.RUN / "evaluation/predictions.json",predictions,binding())
    result = dict(status="complete-awaiting-user-review",selectedWinner=winner,recoveryQualified=qualified,
                  outsideRiverGateMeasured=False,appIntegrationAllowed=False,baseline=results["A"],
                  historyControl=results["B0"],comparisons=comparisons,
                  selectionSHA256=c.digest(c.WORK / "selection.json"),bindingSHA256=binding(),
                  predictionsSHA256=c.digest(c.RUN / "evaluation/predictions.json"))
    c.publish(c.WORK / "results.json",result)
    return result


def snapshot():
    files = {str(p.relative_to(c.ROOT)):dict(sha256=c.digest(p),mtimeNS=p.stat().st_mtime_ns)
             for p in c.RUN.rglob("*.json") if p.is_file()}
    c.require(bool(files), "no completed ranking units")
    c.publish(c.WORK / "pause-before.json",dict(files=files,boundedUnitsComplete=True))


def pause_verify():
    value = c.load(c.WORK / "pause-before.json")
    c.require(bool(list(c.WORK.glob("pause-resumed-*.json"))), "pause was not acknowledged")
    for name,expected in value["files"].items():
        path = c.ROOT / name
        c.require(dict(sha256=c.digest(path),mtimeNS=path.stat().st_mtime_ns) == expected, "saved ranking unit changed")
    c.publish(c.WORK / "pause-proof.json",dict(status="passed",preservedFiles=len(value["files"]),
                                              beforeSHA256=c.digest(c.WORK / "pause-before.json")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze","qualify","cache","score","select","evaluate","verify","pause","snapshot","pause-verify"))
    parser.add_argument("--split", choices=("development","evaluation"),default="development")
    parser.add_argument("--max-units",type=int)
    parser.add_argument("--resume",action="store_true")
    args = parser.parse_args()
    c.require(args.max_units is None or args.max_units > 0,"max-units must be positive")
    if args.command == "pause":
        c.atomic(c.checked(c.WORK / "pause.request.json"),dict(reason="user-request"))
        print("Pause requested; wait for saved-unit/worker confirmation.")
        return
    try:
        with c.worker(resume=args.resume):
            if args.command == "freeze": freeze()
            elif args.command == "qualify":
                value=qualify(); print(json.dumps(dict(status=value["status"],supported=value["supported"],
                                                       controls=len(value.get("controls",[])),error=value.get("error"))))
            elif args.command == "cache": cache(args.split,args.max_units)
            elif args.command == "score": score(args.split,args.max_units)
            elif args.command == "select":
                value=select(); print(json.dumps(dict(winnerFamily=value["winnerFamily"],
                                                     families={k:v["qualified"] for k,v in value["families"].items()})))
            elif args.command == "evaluate": print(json.dumps(dict(recoveryQualified=evaluate()["recoveryQualified"])))
            elif args.command == "verify": verify()
            elif args.command == "snapshot": snapshot()
            else: pause_verify()
        print(json.dumps(dict(command=args.command,status="complete",workerStopped=True)))
    except c.Paused as error: print(json.dumps(dict(status="paused",reason=str(error),workerStopped=True)))


if __name__ == "__main__": main()
