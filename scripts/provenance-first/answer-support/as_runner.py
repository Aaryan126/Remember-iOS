"""Stage A only: reviewed fixtures, native evidence, fixed retrieval and controls."""
import argparse
import hashlib
import json
import subprocess

import as_control as c
import as_fixtures as f
import as_native as native
import as_policy as policy
import rk_policy as ranking_policy
import rk_runtime as old_runtime


def corpus_binding(): return c.digest(c.WORK/"corpus-frozen.json")


def all_libraries(): return [lib for doc in f.documents() for lib in doc["libraries"]]


def prepare(maximum=None):
    f.verify_corpus()
    made=0
    for library in all_libraries():
        c.boundary()
        path=c.RUN/"source-only"/(library["id"]+".json")
        existed=path.exists()
        c.unit(path,f.source_packet(library),corpus_binding())
        c.unit(c.RUN/"compiled"/(library["id"]+".json"),f.native_run(library),corpus_binding())
        if not existed:
            made+=1
            if maximum is not None and made>=maximum: raise c.Paused("bounded preparation unit")
    c.publish(c.RUN/"input.json",dict(schemaVersion=1,runs=[f.native_run(lib) for lib in all_libraries()]))
    paths=[c.RUN/"input.json"]+list((c.RUN/"source-only").glob("*.json"))+list((c.RUN/"compiled").glob("*.json"))
    c.publish(c.WORK/"preparation.json",dict(corpusBindingSHA256=corpus_binding(),
                hashes={str(p.relative_to(c.ROOT)):c.digest(p) for p in sorted(paths)}))


def native_status(complete=False):
    f.verify_corpus()
    preparation=c.load(c.WORK/"preparation.json")
    c.require(preparation["corpusBindingSHA256"]==corpus_binding(),"preparation binding changed")
    paths=[c.RUN/"input.json"]+list((c.RUN/"source-only").glob("*.json"))+list((c.RUN/"compiled").glob("*.json"))
    c.require(preparation["hashes"]=={str(p.relative_to(c.ROOT)):c.digest(p) for p in sorted(paths)},"prepared native input changed")
    batch=c.load(c.RUN/"input.json")
    runs=[c.read_unit(c.RUN/"compiled"/(key+".json"),corpus_binding())
          for prefix in ("dev","eval") for key in (f"{prefix}{i:02}" for i in range(1,9))]
    c.require(batch==dict(schemaVersion=1,runs=runs),"compiled batch changed")
    result=[v for run in batch["runs"] if (v:=native.verify_run(run,c.RUN/"input.json")) is not None]
    if complete: c.require(len(result)==16,"native replay incomplete")
    return dict(completed=len(result),prefixes=sum(v["prefixes"] for v in result),queries=sum(v["queries"] for v in result),libraries=result)


def candidates(library_id):
    # Source-only packet and native projection only. Never reads authored gold.
    observed=c.read_unit(c.RUN/"source-only"/(library_id+".json"),corpus_binding())
    run=c.read_unit(c.RUN/"compiled"/(library_id+".json"),corpus_binding())
    c.require(native.verify_run(run,c.RUN/"input.json") is not None,"native projection unavailable")
    key=hashlib.sha256(run["id"].encode()).hexdigest()
    projection=c.load(native.OUTPUT/(key+".projection.json"))
    by_id={q["id"]:q for q in projection["queries"]}
    results=[]
    for query in observed["queries"]:
        c.require(set(query)=={"id","atEvent","scope","question"},"query label leakage")
        visible=[]
        for event in observed["events"]:
            visible.append(event)
            if event["id"]==query["atEvent"]: break
        sources={native.source_uuid("localc"+e["sourceId"][1:]):(e["sourceId"],i)
                 for i,e in enumerate(visible) if e["kind"]=="capture"}
        rows=[]
        for item in by_id[query["id"]]["candidates"]:
            sid,created=sources[item["sourceID"].upper()]
            rows.append(dict(id=item["id"],sourceId=sid,sourceID=item["sourceID"],revision=item["revision"],quote=item["quote"],
                             versionID=item["versionID"],snapshotID=item["snapshotID"],locator=item["locator"],
                             isArchived=item["isArchived"],isCurrentVersion=item["isCurrentVersion"],
                             created=created,ordinal=item["ordinal"]))
        results.append(dict(**query,candidates=rows))
    return results


def lexical(question,rows,identity):
    if not rows: return {}
    c.boundary()
    request=dict(kind="search",query=question,documents=[dict(id=r["id"],text=r["quote"],revision=r["revision"],
                                                           locator=r["locator"],created=r["created"]) for r in rows])
    reply=subprocess.run([str(old_runtime.LEXICAL/"ComparisonProbe")],input=json.dumps(request)+"\n",
                         text=True,capture_output=True,timeout=15,check=True)
    lines=reply.stdout.splitlines()
    c.require(len(lines)==1,"lexical result count")
    result=json.loads(lines[0])
    c.require(result["locale"]==identity["locale"],"lexical locale changed")
    by_id={r["id"]:r for r in rows}
    hits=result["hits"]
    c.require(len({h["sourceId"] for h in hits})==len(hits),"duplicate lexical identity")
    for hit in hits:
        c.require(hit["sourceId"] in by_id and hit["quote"]==by_id[hit["sourceId"]]["quote"]
                  and hit["revision"]==by_id[hit["sourceId"]]["revision"] and 0<hit["score"]<=1,"lexical evidence mismatch")
    return {h["sourceId"]:h["score"] for h in hits}


def retrieve(maximum=None):
    f.verify_corpus()
    native_status(complete=True)
    identity=old_runtime.identity()
    c.publish(c.WORK/"retrieval-runtime.json",identity)
    made=0
    # IDs come from already-frozen source exports; no answer annotations needed.
    for path in sorted((c.RUN/"source-only").glob("*.json")):
        c.boundary()
        target=c.RUN/"retrieval"/path.name
        if target.exists():
            c.read_unit(target,corpus_binding())
            continue
        scored=[]
        for query in candidates(path.stem):
            scores=lexical(query["question"],query["candidates"],identity)
            rows=[dict(row,lexical=scores.get(row["id"],0)) for row in query["candidates"]]
            selected=ranking_policy.predict(dict(scoped=rows),dict(family="B0",minScore=0,margin=0,limit=3))
            fallback=ranking_policy.predict(dict(scoped=rows),dict(family="B",minScore=.5,margin=.1,limit=1))
            # Keep scores for diagnostic replay, exclude them from verifier packets.
            scored.append(dict(id=query["id"],question=query["question"],scope=query["scope"],atEvent=query["atEvent"],
                               candidates=[{k:v for k,v in row.items() if k not in {"lexical","score"}} for row in selected],
                               allScores=rows,scoreOnlyDiagnostic=[r["id"] for r in fallback]))
        c.unit(target,scored,corpus_binding())
        made+=1
        print(json.dumps(dict(phase="retrieval",library=path.stem)),flush=True)
        if maximum is not None and made>=maximum: raise c.Paused("bounded retrieval unit")


def packets(library_id):
    rows=c.read_unit(c.RUN/"retrieval"/(library_id+".json"),corpus_binding())
    return {r["id"]:{k:r[k] for k in ("id","question","scope","atEvent","candidates")} for r in rows}


def derive_packet_labels():
    f.verify_corpus()
    results=[]
    for doc in f.documents():
        libraries=[]
        for lib in doc["libraries"]:
            observed=packets(lib["id"])
            tasks=[]
            for task in lib["tasks"]:
                packet=observed[task["id"]]
                tasks.append(dict(id=task["id"],gold=policy.packet_gold(task["gold"],packet),
                                  corpusVerdict=task["gold"]["verdict"],candidateIDs=[r["id"] for r in packet["candidates"]]))
            libraries.append(dict(id=lib["id"],tasks=tasks))
        value=dict(split=doc["split"],libraries=libraries,corpusBindingSHA256=corpus_binding(),
                   retrievalFiles={lib["id"]:c.digest(c.RUN/"retrieval"/(lib["id"]+".json")) for lib in doc["libraries"]})
        c.publish(c.WORK/"packet-labels"/(doc["split"]+".json"),value)
        results.append(value)
    return results


def coverage():
    result={}
    for doc in f.documents():
        counts=dict(queries=0,answerable=0,retrievedSupport=0,explicitMissingPackets=0,conflictingPackets=0,
                    historicalQuestions=0,historicalAlsoSupportedByCurrentEvidence=0)
        libraries=[]
        for lib in doc["libraries"]:
            observed=packets(lib["id"])
            all_rows={q["id"]:q for q in candidates(lib["id"])}
            tasks=[]
            for task in lib["tasks"]:
                gold=task["gold"]
                packet=observed[task["id"]]
                derived=policy.packet_gold(gold,packet)
                counts["queries"]+=1
                answerable=gold["verdict"]=="supported"
                counts["answerable"]+=answerable
                counts["retrievedSupport"]+=answerable and derived["verdict"]=="supported"
                counts["explicitMissingPackets"]+=derived["verdict"]=="explicit_missing"
                counts["conflictingPackets"]+=derived["verdict"]=="conflicting"
                if task["category"] in {"archived","superseded"}:
                    counts["historicalQuestions"]+=1
                    current=dict(candidates=[r for r in all_rows[task["id"]]["candidates"] if r["isCurrentVersion"] and not r["isArchived"]])
                    counts["historicalAlsoSupportedByCurrentEvidence"]+=any(policy.in_packet(e,current) for e in gold["answers"])
                tasks.append(dict(id=task["id"],category=task["category"],corpusVerdict=gold["verdict"],
                                  packetVerdict=derived["verdict"],returned=len(packet["candidates"])))
            libraries.append(dict(id=lib["id"],tasks=tasks))
        result[doc["split"]]=dict(**counts,libraries=libraries,
            retrievalGateReady=counts["retrievedSupport"]>=29,
            stateSupportReady=counts["explicitMissingPackets"]>=6 and counts["conflictingPackets"]>=6)
    return result


def verify_packet_reviews():
    for doc in f.documents():
        path=c.WORK/"packet-labels"/(doc["split"]+".json")
        review=c.load(c.WORK/"packet-reviews"/(doc["split"]+".json"))
        c.require(review["inputSHA256"]==c.digest(path) and review["reviewer"]!=doc["author"]
                  and review["author"]==doc["author"],"packet review stale/not independent")
        c.require(len(review["libraries"])==8 and {r["id"] for r in review["libraries"]}=={l["id"] for l in doc["libraries"]}
                  and all(r["verdict"]=="pass" for r in review["libraries"]),"packet review incomplete")
        c.require(all(v["severity"]=="warning" for v in review["crossLibraryIssues"]+[v for r in review["libraries"] for v in r["issues"]]),"packet review unresolved")


def freeze():
    import as_generation as generation
    import as_native_build
    f.verify_corpus()
    native_status(complete=True)
    derive_packet_labels()
    verify_packet_reviews()
    generation.verify_build()
    paths=list(c.CODE.glob("*.py"))+list(c.CODE.glob("*.swift"))
    paths += [c.WORK/name for name in ("corpus-frozen.json","retrieval-runtime.json","mac-readiness.json","preparation.json","SCORING.md")]
    paths += list((c.WORK/"packet-labels").glob("*.json"))+list((c.WORK/"packet-reviews").glob("*.json"))
    paths += list((c.RUN/"retrieval").glob("*.json"))
    paths += list((c.RUN/"source-only").glob("*.json"))+list((c.RUN/"compiled").glob("*.json"))
    paths += [c.RUN/"input.json"]+list((c.WORK/"native-units").glob("*.json"))
    paths += list(native.OUTPUT.glob("*.projection.json"))+list(native.OUTPUT.glob("*.receipt.json"))
    paths += list(native.OUTPUT.glob("*/ledger.json"))
    paths += [c.WORK/"generation-build.json",c.WORK/"generation-build-reserved.json",generation.BINARY]
    paths += [c.WORK/name for name in ("native-preparation-v2.json","native-build-v2.json","native-build-v2-reserved.json")]
    paths += [as_native_build.BINDINGS,as_native_build.APP/as_native_build.NAME]
    paths += list((c.RUN/"native-reservations").glob("*.json"))
    paths += list((c.RUN/"native-reservations-v2").glob("*.json"))
    paths += list((c.RUN/"native-recoveries").glob("*.json"))
    value=dict(stage="A",stageBAllowed=False,hashes={str(p.relative_to(c.ROOT)):c.digest(p) for p in sorted(paths)},
               coverage=coverage(),nativeBuild=native.verify_build())
    c.publish(c.WORK/"frozen.json",value)
    return value


def verify():
    c.verify_prior()
    f.verify_corpus()
    if (c.WORK/"frozen.json").exists():
        for name,expected in c.load(c.WORK/"frozen.json")["hashes"].items():
            c.require(c.digest(c.ROOT/name)==expected,"frozen Stage A changed")
    return native_status(complete=True)


def snapshot():
    files={str(p.relative_to(c.ROOT)):dict(sha256=c.digest(p),mtimeNS=p.stat().st_mtime_ns)
           for folder in (c.RUN/"source-only",c.RUN/"compiled") for p in folder.glob("*.json")}
    c.require(bool(files),"no completed units to snapshot")
    c.publish(c.WORK/"pause-before.json",dict(files=files))


def pause_verify():
    c.require(bool(list(c.WORK.glob("pause-resumed-*.json"))),"pause not acknowledged")
    before=c.load(c.WORK/"pause-before.json")
    for name,expected in before["files"].items():
        path=c.ROOT/name
        c.require(dict(sha256=c.digest(path),mtimeNS=path.stat().st_mtime_ns)==expected,"completed unit changed")
    c.publish(c.WORK/"pause-proof.json",dict(preservedFiles=len(before["files"]),status="passed"))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("register","readiness","validate","freeze-corpus","prepare","build-native","native","retrieve","packet-labels","freeze","verify","snapshot","pause-verify","pause","status","build-controls","controls"))
    parser.add_argument("--max-units",type=int)
    parser.add_argument("--resume",action="store_true")
    args=parser.parse_args()
    c.require(args.max_units is None or args.max_units>0,"max-units must be positive")
    if args.command=="pause":
        c.atomic(c.checked(c.WORK/"pause.request.json"),dict(reason="user-request"))
        print("Pause requested. Wait for worker and owned-process confirmation before closing.")
        return
    if args.command=="status":
        print(json.dumps(dict(worker=c.load(c.WORK/"worker.json") if (c.WORK/"worker.json").exists() else None,
                              paused=(c.WORK/"pause.request.json").exists(),stageBAllowed=False)))
        return
    try:
        with c.worker(resume=args.resume):
            if args.command=="register": value=c.register()
            elif args.command=="readiness": value=native.mac_readiness()
            elif args.command=="validate": value=dict(libraries=sum(len(d["libraries"]) for d in f.validate_documents()))
            elif args.command=="freeze-corpus": value=f.freeze_corpus()
            elif args.command=="prepare": value=prepare(args.max_units)
            elif args.command=="build-native":
                import as_native_build
                value=as_native_build.build()
            elif args.command=="native":
                native_status(complete=False)
                value=native.run(c.RUN/"input.json",maximum=args.max_units or 16,resume=args.resume)
            elif args.command=="retrieve": value=retrieve(args.max_units)
            elif args.command=="packet-labels": value=derive_packet_labels()
            elif args.command=="freeze": value=freeze()
            elif args.command=="verify": value=verify()
            elif args.command=="snapshot": value=snapshot()
            elif args.command=="pause-verify": value=pause_verify()
            else:
                import as_generation as generation
                if args.command=="build-controls": value=generation.build()
                else:
                    verify()
                    c.require((c.WORK/"frozen.json").exists(),"Stage A must be frozen before controls")
                    value=generation.controls(maximum=args.max_units,resume=args.resume)
        print(json.dumps(dict(command=args.command,status="complete",workerStopped=True,stageBAllowed=False)))
    except c.Paused as error: print(json.dumps(dict(status="paused",reason=str(error),workerStopped=True)))


if __name__=="__main__": main()
