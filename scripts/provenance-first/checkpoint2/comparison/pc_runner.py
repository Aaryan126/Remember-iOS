#!/usr/bin/env python3
"""Frozen current-runtime comparison coordinator. Evaluation follows dev selection."""
import argparse
from itertools import combinations, product
from pathlib import Path
import sys
import time

from pc_native import c, Native, build, BUILD
import pc_policy as policy
import preflight

CODE = Path(__file__).resolve().parent
RUN = c.WORK / "runs/comparison-01"
PUBLIC = c.WORK / "comparison"
REFERENCE = "d3-seed29-mac27-pf2-reference-v1"


def streams_for(library):
    # observed_packet is the frozen allowlist. Dependency/gold data is used by
    # the scheduler/evaluator only, never copied to the execution streams.
    packets = {event["id"]: c.fixtures.observed_packet(library, event["id"]) for event in library["events"]}
    events = {eid: packet["events"][-1] for eid, packet in packets.items()}
    chronological = [event["id"] for event in library["events"]]
    alternate = [event["id"] for event in c.fixtures.alternate_events(library["events"])]
    queries = [{"id": task["id"], "atEvent": task["atEvent"],
                "question": c.fixtures.observed_packet(library, task["atEvent"], task["id"])["query"]}
               for task in library["tasks"]]
    return [{"id": library["id"], "order": name, "events": [events[eid] for eid in order],
             "queries": queries if name == "chronological" else []}
            for name, order in (("chronological", chronological), ("alternate", alternate))]


def catalogue(streams):
    texts, pairs = {}, {}
    for stream in streams:
        versions = {}
        for event in stream["events"]:
            policy.validate_event(event)
            if event["kind"] in ("capture", "revise"):
                text = event["text"]
                c.require(text and len(text) <= 16000, "source outside D3 text scope")
                key = c.text_hash(text)
                c.require(key not in texts or texts[key] == text, "text hash collision")
                texts[key] = text
                versions.setdefault(event["sourceId"], set()).add(key)
        for first, second in combinations(sorted(versions), 2):
            for a, b in product(sorted(versions[first]), sorted(versions[second])):
                left, right = sorted((a,b))
                pairs[left + "--" + right] = {"first":left,"second":right}
    return {"texts":dict(sorted(texts.items())), "pairs":dict(sorted(pairs.items()))}


def verify_base(runtime=False):
    c.pf1.verify_manifest(c.PF)
    c.verify_saved_preflight()
    manifest = c.read(RUN / "manifest.json")
    for path, expected in manifest["hashes"].items():
        c.require(c.digest(path) == expected, f"comparison binding changed: {path}")
    c.require(manifest["reference"] == REFERENCE, "reference changed")
    if runtime:
        preflight.inputs()  # Exact runtime/assets check, NOT the failed equivalence gate.
    return c.digest(RUN / "manifest.json")


def prepare():
    c.boundary()
    _,_,_,_,_,parent = preflight.inputs()
    native = build()
    qualification = c.WORK / "runtime-qualification/checkpoint.json"
    c.require(c.read(qualification)["qualificationComplete"], "runtime diagnostic incomplete")
    paths = list(CODE.glob("*.py")) + list(CODE.glob("*.swift"))
    paths += [PUBLIC / "PROTOCOL.md", c.PF / "frozen.json", c.WORK / "runs/preflight/binding.json",
              qualification, c.WORK / "runtime-qualification/result.json", BUILD / "build.json", BUILD / "ComparisonProbe"]
    paths += [Path(name) for name in native["sources"]]
    manifest = {"reference": REFERENCE, "preflightBindingSHA256": parent,
                "historicalEquivalencePassed": False, "currentRuntimeReferenceApproved": True,
                "thresholds": list(policy.THRESHOLDS), "hashes": {str(path): c.digest(path) for path in sorted(set(paths))}}
    c.publish(RUN / "manifest.json", manifest)
    prepare_split("development")


def verify_selection():
    value = c.read(PUBLIC / "selection.json")
    c.require(value["manifestSHA256"] == verify_base(), "selection parent changed")
    for path, expected in value["developmentHashes"].items():
        c.require(c.digest(path) == expected, f"development freeze changed: {path}")
    c.require(value["policyKey"] in ("C0", "C1", "C2", "Coff"), "invalid selected policy")
    return value


def prepare_split(split):
    c.require(split in ("development", "evaluation"), "invalid split")
    base = verify_base()
    selection = None
    if split == "evaluation":
        verify_selection()
        selection = c.digest(PUBLIC / "selection.json")
    folder = RUN / split
    document = c.read(c.PF / f"authored/{split}.json")
    streams = [stream for library in document["libraries"] for stream in streams_for(library)]
    c.publish(folder / "inputs.json", {"streams":streams})
    c.publish(folder / "catalogue.json", catalogue(streams))
    c.publish(folder / "job.json", {"split": split, "baseSHA256": base, "selectionSHA256": selection,
              "inputSHA256": c.digest(folder / "inputs.json"), "catalogueSHA256": c.digest(folder / "catalogue.json")})
    c.log(phase="split-prepared", split=split, streams=len(streams),
          texts=len(c.read(folder / "catalogue.json")["texts"]), pairs=len(c.read(folder / "catalogue.json")["pairs"]))


def verify_job(split):
    base = verify_base()
    folder = RUN / split
    c.require(folder.resolve().is_relative_to(RUN.resolve()), "job path escaped")
    job = c.read(folder / "job.json")
    c.require(job["split"] == split and job["baseSHA256"] == base, "job identity mismatch")
    for name, key in (("inputs.json","inputSHA256"),("catalogue.json","catalogueSHA256")):
        c.require(c.digest(folder / name) == job[key], f"job input changed: {name}")
    if split == "evaluation":
        verify_selection()
        c.require(job["selectionSHA256"] == c.digest(PUBLIC / "selection.json"), "evaluation selection changed")
    binding = c.digest(folder / "job.json")
    catalog = c.read(folder / "catalogue.json")
    expected = {"embeddings":set(catalog["texts"]), "neural":set(catalog["pairs"]), "pairs":set(catalog["pairs"])}
    counts = {}
    for kind, names in expected.items():
        paths = list((folder / kind).glob("*"))
        c.require(all(p.suffix == ".json" and p.stem in names and p.is_file() and not p.is_symlink()
                      and p.resolve().is_relative_to(folder.resolve()) for p in paths), "unexpected cache unit")
        for path in paths:
            value = c.read_unit(path, binding)
            c.require(value["id"] == path.stem, "cache unit identity mismatch")
        counts[kind] = len(paths)
    return folder, binding, catalog, counts


def bounded(made, maximum):
    if maximum and made >= maximum:
        raise c.Paused("comparison bounded unit limit")


def cache(split, maximum=None):
    verify_base(runtime=True)
    folder,binding,catalog,counts = verify_job(split)
    Features, Neural, _ = preflight.legacy()
    import qualify_runtime as validation
    made = 0
    for key, text in catalog["texts"].items():
        c.boundary()
        path = folder / f"embeddings/{key}.json"
        if not path.exists():
            value = preflight.embedding(key, text)
            validation.valid_vector(value,key,text)
            c.unit(path, value, binding)
            made += 1
            counts["embeddings"] += 1
            if counts["embeddings"] % 10 == 0:
                c.log(phase="embeddings", split=split, completed=counts["embeddings"], total=len(catalog["texts"]))
            bounded(made,maximum)
    missing = [key for key in catalog["pairs"] if not (folder / f"neural/{key}.json").exists()]
    if missing:
        c.boundary()
        with Neural("29") as model:
            for start in range(0,len(missing),8):
                c.boundary()
                keys = missing[start:start+min(8,maximum-made if maximum else 8)]
                pairs = [catalog["pairs"][key] for key in keys]
                began = time.monotonic()
                scores = model.predict([(catalog["texts"][p["first"]],catalog["texts"][p["second"]]) for p in pairs])
                c.require(len(scores) == len(keys), "neural batch incomplete")
                elapsed = time.monotonic()-began
                for key,score in zip(keys,scores):
                    value = {"id":key,**score,"amortizedSeconds":elapsed/len(keys)}
                    validation.valid_neural(value,key,model.record["SHA256"])
                    c.unit(folder / f"neural/{key}.json",value,binding)
                    made += 1
                    counts["neural"] += 1
                c.log(phase="neural", split=split, completed=counts["neural"], total=len(catalog["pairs"]))
                bounded(made,maximum)
    embeddings = {key:c.read_unit(folder/f"embeddings/{key}.json",binding) for key in catalog["texts"]}
    for key,value in embeddings.items():
        validation.valid_vector(value,key,catalog["texts"][key])
    features = Features(catalog["texts"],embeddings)
    for index,(key,pair) in enumerate(catalog["pairs"].items()):
        path = folder/f"pairs/{key}.json"
        if not path.exists():
            if index % 8 == 0: c.boundary()
            raw = c.read_unit(folder/f"neural/{key}.json",binding)
            values = features.values(pair["first"],pair["second"])
            score = features.scores(values,{"29":raw["score"]})["hybrid"]["29"]
            c.unit(path,{"id":key,"contextual":values[0],"lexical":values[2],"score":score,"features":values},binding)
            made += 1
            bounded(made,maximum)
    _,_,_,counts = verify_job(split)
    c.publish(folder/"cache-complete.json",{"jobSHA256":binding,"counts":counts,
              "hashes":{str(p):c.digest(p) for kind in ("embeddings","neural","pairs") for p in sorted((folder/kind).glob("*.json"))}})
    c.log(phase="cache-complete",split=split,counts=counts)


def settings(key):
    if key == "A": return "A",policy.THRESHOLDS[0],True
    if key == "Coff": return "C",policy.THRESHOLDS[0],False
    c.require(key in ("C0","C1","C2"),"invalid policy key")
    return "C",policy.THRESHOLDS[int(key[1])],True


def traces(split,key):
    folder,binding,_,_ = verify_job(split)
    streams = c.read(folder/"inputs.json")["streams"]
    values = []
    for stream in streams:
        path = folder/f"predictions/{stream['id']}-{stream['order']}-{key}.json"
        value = c.read_unit(path,binding)
        c.require(value["id"] == stream["id"] and value["order"] == stream["order"]
                  and [r["event"] for r in value["events"]] == stream["events"], "prediction input identity mismatch")
        c.require((value["variant"],value["threshold"],value["automatic"]) == settings(key),"prediction policy identity mismatch")
        values.append(value)
    return values


def predict(split,maximum=None):
    folder,binding,catalog,_ = verify_job(split)
    cache_receipt = c.read(folder/"cache-complete.json")
    c.require(cache_receipt["jobSHA256"] == binding, "cache-completion identity mismatch")
    for path,digest in cache_receipt["hashes"].items():
        c.require(c.digest(path) == digest,"sealed model cache changed")
    pairs = {key:c.read_unit(folder/f"pairs/{key}.json",binding) for key in catalog["pairs"]}
    def score(first,second):
        key = "--".join(sorted((c.text_hash(first),c.text_hash(second))))
        c.require(key in pairs, "observed pair absent from catalogue")
        return {field:pairs[key][field] for field in ("contextual","lexical","score")}
    keys = ("A","C0","C1","C2","Coff") if split == "development" else ("A",verify_selection()["policyKey"])
    native = Native()
    made = 0
    for stream in c.read(folder/"inputs.json")["streams"]:
        for key in keys:
            c.boundary()
            path = folder/f"predictions/{stream['id']}-{stream['order']}-{key}.json"
            if not path.exists():
                variant,threshold,automatic = settings(key)
                value = policy.run_stream(stream,score,native,variant,threshold,automatic)
                c.unit(path,value,binding)
                made += 1
                c.log(phase="prediction",split=split,library=stream["id"],order=stream["order"],policy=key)
                bounded(made,maximum)
            c.read_unit(path,binding)
    for key in keys: traces(split,key)


def score_split(split):
    from pc_metrics import evaluate
    keys = ("A","C0","C1","C2","Coff") if split == "development" else ("A",verify_selection()["policyKey"])
    predictions = {key:traces(split,key) for key in keys}
    # Labels are opened by the evaluator only after all required predictions exist.
    libraries = c.read(c.PF/f"authored/{split}.json")["libraries"]
    reports = {key:evaluate(value,libraries,"A" if key == "A" else "C") for key,value in predictions.items()}
    reports["B"] = evaluate(predictions["A"],libraries,"B")
    c.require(reports["A"]["edges"] == reports["B"]["edges"],"B changed placements")
    c.publish(RUN/split/"metrics.json",reports)
    c.log(phase="scored",split=split,policies={key:{k:value[k] for k in ("automaticEdges","precision","wrongEdges")}
                                                for key,value in reports.items()})
    return reports


def select():
    from pc_metrics import choose
    reports = score_split("development")
    choice = choose([(t,reports[f"C{i}"]) for i,t in enumerate(policy.THRESHOLDS)])
    key = f"C{policy.THRESHOLDS.index(choice['threshold'])}" if choice["automatic"] else "Coff"
    paths = [RUN/"development"/name for name in ("job.json","inputs.json","catalogue.json","cache-complete.json","metrics.json")]
    paths += list((RUN/"development/predictions").glob("*.json"))
    result = {**choice,"policyKey":key,"manifestSHA256":verify_base(),
              "developmentHashes":{str(path):c.digest(path) for path in sorted(paths)},"evaluationPredictionsOpened":False}
    c.publish(PUBLIC/"selection.json",result)
    c.log(phase="selected",automatic=choice["automatic"],threshold=choice["threshold"],policyKey=key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("prepare","prepare-evaluation","cache","predict","score","select","verify"))
    parser.add_argument("--split",choices=("development","evaluation"),default="development")
    parser.add_argument("--max-units",type=int)
    parser.add_argument("--resume",action="store_true")
    args = parser.parse_args()
    c.require(args.max_units is None or args.max_units > 0,"max-units must be positive")
    try:
        with c.worker(resume=False):
            if args.command != "prepare":
                verify_base(runtime=args.command == "cache")
                if args.command != "prepare-evaluation": verify_job(args.split)
            marker = c.WORK/"pause.request.json"
            if args.resume and marker.exists():
                c.require(args.command not in ("prepare","prepare-evaluation"),"prepare cannot resume inference")
                marker.rename(RUN/f"pause-{time.time_ns()}.json")
            c.boundary()
            if args.command == "prepare": prepare()
            elif args.command == "prepare-evaluation": prepare_split("evaluation")
            elif args.command == "cache": cache(args.split,args.max_units)
            elif args.command == "predict": predict(args.split,args.max_units)
            elif args.command == "select": select()
            elif args.command == "score": score_split(args.split)
            else: c.log(verified=True,split=args.split,counts=verify_job(args.split)[3])
    except c.Paused as error:
        c.log(status="paused",reason=str(error),workerStopped=True)
    except Exception as error:
        c.pf1.atomic(c.WORK/f"runs/failures/{time.time_ns()}.json",{"phase":"comparison","type":type(error).__name__,"message":str(error)})
        raise


if __name__ == "__main__": main()
