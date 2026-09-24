"""Fictional corpus validation and source-only native replay compilation."""
from copy import deepcopy
import hashlib
import re

import as_control as c

CATEGORIES = {"current_a":"supported", "current_b":"supported", "archived":"supported",
              "superseded":"supported", "explicit_missing":"explicit_missing",
              "topical_only":"not_established", "conflict":"conflicting", "wrong_scope":"not_established"}


def text(value, maximum=10000):
    return isinstance(value,str) and bool(value.strip()) and value==value.strip() and len(value)<=maximum


def prefixes(library):
    state, versions, result, modalities = {}, {}, {}, set()
    c.require(1 <= len(library["events"]) <= 16, "event limit")
    for number,event in enumerate(library["events"],1):
        eid, sid, kind = event["id"], event["sourceId"], event["kind"]
        c.require(eid==f"e{number:02}" and re.fullmatch(r"s0[1-8]",sid), "invalid event/source identity")
        fields={"id","sourceId","kind"}
        if kind=="capture": fields|={"text","modality","locator"}
        elif kind=="revise": fields|={"text","locator"}
        c.require(set(event)==fields and kind in {"capture","revise","archive","restore"}, "invalid event fields/kind")
        if kind in {"capture","revise"}:
            c.require(text(event["text"],800) and text(event["locator"],200), "invalid source text/locator")
        if kind=="capture":
            c.require(sid not in state and event["modality"] in {"note","photo","voice","video","pdf","link"}, "invalid capture")
            state[sid]=dict(revision=0,archived=False,modality=event["modality"],created=number)
            modalities.add(event["modality"])
            versions[(sid,0)]=event["text"]
        else:
            c.require(sid in state, "unknown source")
            entry=state[sid]
            if kind=="revise":
                c.require(entry["modality"]=="note" and not entry["archived"], "revision requires active note")
                entry["revision"]+=1
                versions[(sid,entry["revision"])]=event["text"]
            else:
                c.require(entry["archived"]==(kind=="restore"), "redundant visibility change")
                entry["archived"]=kind=="archive"
        result[eid]=(deepcopy(state),dict(versions))
    c.require(len(modalities)>=2 and any(e["kind"]=="archive" for e in library["events"])
              and any(e["kind"]=="revise" for e in library["events"]), "lifecycle/modality coverage missing")
    return result


def eligible(task, states):
    state, versions=states[task["atEvent"]]
    return {key:value for key,value in versions.items() if task["scope"]=="includeHistory"
            or (not state[key[0]]["archived"] and state[key[0]]["revision"]==key[1])}


def validate_library(library):
    c.require(set(library)=={"id","family","description","events","tasks"}, "invalid library fields")
    c.require(re.fullmatch(r"(?:dev|eval)0[1-8]",library["id"]) and text(library["family"])
              and text(library["description"]), "invalid library metadata")
    states=prefixes(library)
    c.require(len(library["tasks"])==8 and {t["id"] for t in library["tasks"]}=={f"q{i}" for i in range(1,9)}, "eight tasks required")
    c.require({t["category"] for t in library["tasks"]}==set(CATEGORIES), "category coverage differs")
    c.require(any(t["atEvent"]!=library["events"][-1]["id"] for t in library["tasks"]), "prefix query required")
    for task in library["tasks"]:
        label=library["id"]+"/"+task["id"]
        c.require(set(task)=={"id","category","atEvent","scope","question","gold"}, f"{label}: task fields")
        c.require(task["atEvent"] in states and text(task["question"],500), f"{label}: query boundary/text")
        category=task["category"]
        c.require(task["scope"]==("includeHistory" if category in {"archived","superseded"} else "current"), f"{label}: explicit scope")
        gold=task["gold"]
        c.require(set(gold)=={"verdict","answers","missingEvidence","rationale"}
                  and gold["verdict"]==CATEGORIES[category] and text(gold["rationale"]), f"{label}: gold schema")
        c.require(isinstance(gold["answers"],list) and isinstance(gold["missingEvidence"],list), f"{label}: gold lists")
        available=eligible(task,states)
        for evidence in gold["answers"]+gold["missingEvidence"]:
            is_answer="answerSpans" in evidence
            fields={"sourceId","revision","quote"}|({"answerSpans","answerKey"} if is_answer else set())
            c.require(set(evidence)==fields and type(evidence["revision"]) is int, f"{label}: evidence fields")
            key=(evidence["sourceId"],evidence["revision"])
            c.require(key in available and text(evidence["quote"],480) and evidence["quote"] in available[key], f"{label}: evidence absent/ineligible")
            if is_answer:
                c.require(text(evidence["answerKey"],160) and isinstance(evidence["answerSpans"],list)
                          and 1<=len(evidence["answerSpans"])<=12, f"{label}: answer variants")
                c.require(all(text(span,160) and span in evidence["quote"] for span in evidence["answerSpans"]), f"{label}: invalid answer span")
        c.require(all("answerSpans" in a for a in gold["answers"])
                  and all("answerSpans" not in a for a in gold["missingEvidence"]), f"{label}: mixed evidence roles")
        keys={a["answerKey"] for a in gold["answers"]}
        c.require((gold["verdict"]=="supported" and len(keys)==1 and not gold["missingEvidence"])
                  or (gold["verdict"]=="conflicting" and len(keys)>=2 and not gold["missingEvidence"])
                  or (gold["verdict"]=="explicit_missing" and not keys and bool(gold["missingEvidence"]))
                  or (gold["verdict"]=="not_established" and not keys and not gold["missingEvidence"]), f"{label}: verdict/evidence")
        if category in {"archived","superseded"}:
            state=states[task["atEvent"]][0]
            historical_target=False
            for answer in gold["answers"]:
                item=state[answer["sourceId"]]
                historical_target |= ((item["archived"] and item["revision"]==answer["revision"]) if category=="archived"
                                      else (not item["archived"] and item["revision"]>answer["revision"]))
            c.require(historical_target,f"{label}: history target required")
    return states


def documents():
    return [c.load(c.WORK/"authored"/(split+".json")) for split in ("development","evaluation")]


def validate_documents():
    docs=documents()
    families, texts=set(),set()
    old_docs=[c.load(folder/(split+".json")) for folder in (c.PF/"authored",c.ranking.history.WORK/"authored")
              for split in ("development","evaluation")]
    old_families={lib["family"] for doc in old_docs for lib in doc["libraries"]}
    old_texts={e["text"].casefold() for doc in old_docs for lib in doc["libraries"] for e in lib["events"] if "text" in e}
    for doc,split in zip(docs,("development","evaluation")):
        c.require(set(doc)=={"schemaVersion","split","author","libraries"} and doc["schemaVersion"]==1
                  and doc["split"]==split and text(doc["author"]), "split schema")
        prefix="dev" if split=="development" else "eval"
        c.require(len(doc["libraries"])==8 and {x["id"] for x in doc["libraries"]}=={f"{prefix}{i:02}" for i in range(1,9)}, "split libraries")
        split_texts=set()
        for lib in doc["libraries"]:
            validate_library(lib)
            c.require(lib["family"] not in families|old_families,"scenario family reuse")
            families.add(lib["family"])
            split_texts.update(e["text"].casefold() for e in lib["events"] if "text" in e)
        c.require(not split_texts & (texts|old_texts),"cross-split or old source text reuse")
        texts|=split_texts
    return docs


def native_run(library):
    validate_library(library)
    state,commands={},[]
    for event in library["events"]:
        sid,kind=event["sourceId"],event["kind"]
        local="localc"+sid[1:]
        command=dict(id=event["id"],kind=kind)
        if kind=="capture":
            command["source"]=dict(id=local,text=event["text"],modality={"photo":"image"}.get(event["modality"],event["modality"]))
            command["assignments"]=["t:c"+sid[1:]]
            state[local]=dict(memberships=command["assignments"],archived=False,revision=0,
                              textSHA256=hashlib.sha256(event["text"].encode()).hexdigest())
        else:
            command["target"]=local
            if kind=="revise":
                command["text"]=event["text"]
                state[local]["revision"]+=1
                state[local]["textSHA256"]=hashlib.sha256(event["text"].encode()).hexdigest()
            else: state[local]["archived"]=kind=="archive"
        command["expectedState"]=deepcopy(state)
        commands.append(command)
    return dict(id="answer-"+library["id"]+"-chronological",events=commands,
                queries=[dict(id=t["id"],afterEvent=t["atEvent"],scope=t["scope"],limit=10000) for t in library["tasks"]])


def source_packet(library):
    return dict(id=library["id"],events=deepcopy(library["events"]),
                queries=[{k:t[k] for k in ("id","atEvent","scope","question")} for t in library["tasks"]])


def verify_reviews(doc):
    path=c.WORK/"authored"/(doc["split"]+".json")
    review=c.load(c.WORK/"reviews"/(doc["split"]+".json"))
    c.require(review["inputSHA256"]==c.digest(path) and review["author"]==doc["author"]
              and review["reviewer"]!=doc["author"] and text(review["reviewer"]),"review stale/not independent")
    c.require(review["split"]==doc["split"] and len(review["libraries"])==8
              and {x["id"] for x in review["libraries"]}=={x["id"] for x in doc["libraries"]},"review incomplete")
    c.require(all(x["verdict"]=="pass" for x in review["libraries"]),"review not passed")
    c.require(all(issue["severity"]=="warning" for issue in review["crossLibraryIssues"]
                  +[v for x in review["libraries"] for v in x["issues"]]),"unresolved review issue")


def freeze_corpus():
    docs=validate_documents()
    for doc in docs: verify_reviews(doc)
    paths=[c.WORK/name for name in ("PLAN.md","CONTRACT.md","FORMAT.md","APPROVAL.md","approval.json")]
    paths+=list((c.WORK/"authored").glob("*.json"))+list((c.WORK/"reviews").glob("*.json"))
    value=dict(hashes={str(p.relative_to(c.ROOT)):c.digest(p) for p in sorted(paths)},libraries=16,queries=128,
               generationMeasured=False,stageBAllowed=False)
    c.publish(c.WORK/"corpus-frozen.json",value)
    return value


def verify_corpus():
    value=c.load(c.WORK/"corpus-frozen.json")
    for name,expected in value["hashes"].items(): c.require(c.digest(c.ROOT/name)==expected,"frozen corpus changed")
    return value
