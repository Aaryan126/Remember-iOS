"""Exact evidence validation and semantic metrics; no inference or filesystem I/O."""
from copy import deepcopy

VERDICTS={"supported","explicit_missing","conflicting","not_established"}


def require(ok,message):
    if not ok: raise ValueError(message)


def validate_output(output,packet):
    require(isinstance(output,dict) and set(output)=={"verdict","answer","evidence"},"output schema")
    require(output["verdict"] in VERDICTS and isinstance(output["answer"],str),"output types")
    answer=output["answer"]
    require(len(answer)<=160 and answer==answer.strip(),"invalid answer span")
    require(bool(answer)==(output["verdict"]=="supported"),"answer/verdict mismatch")
    references=output["evidence"]
    require(isinstance(references,list) and len(references)<=3,"evidence limit")
    by_id={row["id"]:row for row in packet["candidates"]}
    require(len(by_id)==len(packet["candidates"]),"duplicate packet candidate")
    seen=set()
    for ref in references:
        require(isinstance(ref,dict) and set(ref)=={"candidateID","quote"},"reference schema")
        require(isinstance(ref["candidateID"],str) and ref["candidateID"] in by_id,"unknown candidate")
        quote=ref["quote"]
        require(isinstance(quote,str) and 4<=len(quote)<=480 and quote==quote.strip(),"quote length/whitespace")
        require(quote in by_id[ref["candidateID"]]["quote"],"quote not verbatim")
        identity=(ref["candidateID"],quote)
        require(identity not in seen,"duplicate evidence")
        seen.add(identity)
    if output["verdict"] in {"supported","explicit_missing"}: require(bool(references),"missing evidence")
    if output["verdict"]=="supported": require(any(answer in ref["quote"] for ref in references),"answer outside evidence")
    if output["verdict"]=="conflicting": require(len(references)>=2,"conflict needs two passages")
    # Citation metadata is always copied from host evidence, not generated fields.
    return dict(verdict=output["verdict"],answer=answer,
                evidence=[dict(candidate=deepcopy(by_id[r["candidateID"]]),quote=r["quote"]) for r in references])


def in_packet(evidence,packet):
    return any(row["sourceId"]==evidence["sourceId"] and row["revision"]==evidence["revision"]
               and evidence["quote"] in row["quote"] for row in packet["candidates"])


def packet_gold(gold,packet):
    answers=[deepcopy(e) for e in gold["answers"] if in_packet(e,packet)]
    missing=[deepcopy(e) for e in gold["missingEvidence"] if in_packet(e,packet)]
    keys={e["answerKey"] for e in answers}
    verdict="conflicting" if len(keys)>1 else "supported" if keys else "explicit_missing" if missing else "not_established"
    return dict(verdict=verdict,answers=answers,missingEvidence=missing,
                rationale="Derived from frozen corpus annotations and fixed packet; requires independent packet review.")


def semantic_correct(validated,gold):
    if validated["verdict"]!=gold["verdict"]: return False
    if gold["verdict"]=="not_established": return True
    targets=gold["missingEvidence"] if gold["verdict"]=="explicit_missing" else gold["answers"]
    matched=[]
    for reference in validated["evidence"]:
        row=reference["candidate"]
        acceptable=[e for e in targets if row["sourceId"]==e["sourceId"] and row["revision"]==e["revision"]
                    and e["quote"] in reference["quote"]]
        if not acceptable: return False
        matched.extend(acceptable)
    if gold["verdict"]=="conflicting": return len({e["answerKey"] for e in matched})>=2
    if gold["verdict"]=="supported":
        # Equivalent citations need not use the same surface wording. The answer
        # must be accepted by one cited passage; every citation must support that
        # same independently reviewed fact.
        answer_keys={e["answerKey"] for e in matched if validated["answer"] in e["answerSpans"]}
        return bool(answer_keys) and {e["answerKey"] for e in matched}==answer_keys
    return bool(matched)


def outcome(task,packet,response):
    original=deepcopy(packet)
    result=dict(id=task["id"],category=task["category"],goldVerdict=task["gold"]["verdict"],
                packetVerdict=packet_gold(task["gold"],packet)["verdict"],error=None,
                verdict=None,rawVerdict=None,correct=False,packetCorrect=False,scoringIssue=None,sourceListPreserved=True)
    if isinstance(response,dict) and isinstance(response.get("output"),dict):
        result["rawVerdict"]=response["output"].get("verdict")
    if not isinstance(response,dict) or response.get("status")!="ok":
        result["error"]="execution-error"
        result["sourceListPreserved"]=packet==original
        return result
    try: validated=validate_output(response["output"],packet)
    except (ValueError,KeyError,TypeError) as error:
        result["error"]="validation-error: "+str(error)
        result["sourceListPreserved"]=packet==original
        return result
    result.update(verdict=validated["verdict"],correct=semantic_correct(validated,task["gold"]),
                  packetCorrect=semantic_correct(validated,packet_gold(task["gold"],packet)),sourceListPreserved=packet==original)
    if not result["correct"] and unreviewed_support_span(validated,task["gold"]):
        result["scoringIssue"]="unreviewed_support_span"
    return result


def unreviewed_support_span(validated,gold):
    """Diagnostic only; a plausible shorter quote never receives automatic credit."""
    if validated["verdict"]!=gold["verdict"] or gold["verdict"]!="supported": return False
    matched=[]
    for ref in validated["evidence"]:
        row=ref["candidate"]
        targets=[e for e in gold["answers"] if row["sourceId"]==e["sourceId"]
                 and row["revision"]==e["revision"] and ref["quote"] in e["quote"]]
        if not targets: return False
        matched.extend(targets)
    return bool(matched) and any(validated["answer"] in e["answerSpans"] for e in matched)


def metrics(libraries,packets,responses):
    rows=[]
    for library in libraries:
        for task in library["tasks"]:
            row=outcome(task,packets[library["id"]][task["id"]],responses[library["id"]][task["id"]])
            row["library"]=library["id"]
            rows.append(row)
    supported=[r for r in rows if r["goldVerdict"]=="supported"]
    nonanswer=[r for r in rows if r["goldVerdict"]!="supported"]
    assertions=[r for r in rows if r["verdict"]=="supported"]
    correct=[r for r in assertions if r["correct"]]
    def state_values(state):
        actual=[r for r in rows if r["packetVerdict"]==state]
        predicted=[r for r in rows if r["verdict"]==state]
        right=sum(r["packetCorrect"] for r in predicted)
        return dict(gold=len(actual),predicted=len(predicted),correct=right,
                    precision=right/len(predicted) if predicted else None,recall=right/len(actual) if actual else None)
    conditional=[r for r in supported if r["packetVerdict"]=="supported"]
    return dict(queries=len(rows),answerable=len(supported),nonanswerable=len(nonanswer),assertions=len(assertions),
                correctAnswers=len(correct),precision=len(correct)/len(assertions) if assertions else None,
                recall=len(correct)/len(supported) if supported else None,
                correctCurrent=sum(r["category"] in {"current_a","current_b"} for r in correct),
                correctHistorical=sum(r["category"] in {"archived","superseded"} for r in correct),
                correctLibraries=len({r["library"] for r in correct}),
                falseSupport=sum(r["verdict"]=="supported" for r in nonanswer),
                rawFalseSupport=sum(r["rawVerdict"]=="supported" for r in nonanswer),
                errors=sum(r["error"] is not None for r in rows),
                retrievedSupport=len(conditional),conditionalCorrect=sum(r["correct"] for r in conditional),
                states={s:state_values(s) for s in ("explicit_missing","conflicting")},rows=rows)


def gates(value,integrity,repeats):
    result=dict(sampleSize=value["queries"]==64 and value["answerable"]==32 and value["nonanswerable"]==32,
        retrieval=value["retrievedSupport"]>=29,
        precision=value["assertions"]>0 and value["correctAnswers"]*10>=value["assertions"]*9,
        coverage=value["correctAnswers"]>=24 and value["correctCurrent"]>=12
            and value["correctHistorical"]>=12 and value["correctLibraries"]>=6,
        falseSupport=value["falseSupport"]<=1,errors=value["errors"]<=3,
        integrity=integrity is True,repeats=repeats is True)
    for state,m in value["states"].items():
        result[state]=m["gold"]>=6 and m["predicted"]>0 and m["correct"]*10>=m["predicted"]*9 and m["correct"]*4>=m["gold"]*3
    return result
