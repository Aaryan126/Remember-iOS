"""Reproducible Stage A regression tests and saved-result audit (no inference)."""
import argparse
import subprocess

import as_control as c
import as_fixtures as f
import as_runner as r
import as_policy as p
import as_native as n
import as_generation as g

SUITES=("scripts/provenance-first", "scripts/provenance-first/checkpoint2",
        "scripts/provenance-first/checkpoint2/comparison", "scripts/provenance-first/checkpoint2/budget5",
        "scripts/provenance-first/checkpoint2/budget8", "scripts/provenance-first/history",
        "scripts/provenance-first/history-ranking", "scripts/provenance-first/answer-support")


def tests():
    import re
    results=[]
    for folder in SUITES:
        c.boundary()
        command=["python3","-B","-m","unittest","discover","-s",folder,"-p","test_*.py"]
        run=subprocess.run(command,cwd=c.ROOT,capture_output=True,text=True,timeout=120)
        result=dict(command=command,exitCode=run.returncode,stdout=run.stdout,stderr=run.stderr)
        results.append(result)
        if run.returncode!=0:
            c.publish(c.WORK/"tests-failed.json",dict(status="failed",suites=results))
            raise ValueError(f"tests failed: {folder}")
        result["count"]=int(re.search(r"Ran (\d+) tests?",run.stderr)[1])
    c.publish(c.WORK/"tests.json",dict(status="passed",testCount=sum(x["count"] for x in results),suites=results))
    print("Tests passed:",sum(x["count"] for x in results))


def audit():
    native=r.verify()
    r.verify_packet_reviews()
    binding=r.corpus_binding()
    packet_count,citation_count=0,0
    for lib in r.all_libraries():
        source={q["id"]:q for q in r.candidates(lib["id"])}
        rows=c.read_unit(c.RUN/"retrieval"/(lib["id"]+".json"),binding)
        c.require({q["id"] for q in rows}=={t["id"] for t in lib["tasks"]},"retrieval query set changed")
        for row in rows:
            packet_count+=1
            original=source[row["id"]]
            c.require(all(row[k]==original[k] for k in ("question","scope","atEvent")),"query metadata changed")
            originals={x["id"]:x for x in original["candidates"]}
            c.require(len(row["candidates"])<=3,"retrieval output overflow")
            identities=set()
            for candidate in row["candidates"]:
                c.require(candidate==originals[candidate["id"]],"retrieved evidence differs from native candidate")
                identity=(candidate["sourceId"],candidate["revision"])
                c.require(identity not in identities,"duplicate retrieval revision")
                identities.add(identity);citation_count+=1
            chosen=r.ranking_policy.predict(dict(scoped=row["allScores"]),dict(family="B0",minScore=0,margin=0,limit=3))
            c.require([x["id"] for x in chosen]==[x["id"] for x in row["candidates"]],"B0 ranking replay differs")
        # Model serialization cannot carry scoring/label fields.
        for packet in r.packets(lib["id"]).values():
            visible=g.model_packet(packet)
            c.require(set(visible)=={"question","scope","candidates"},"model packet metadata leak")
    label_paths=[c.WORK/"packet-labels"/(split+".json") for split in ("development","evaluation")]
    before={str(path):(c.digest(path),path.stat().st_mtime_ns) for path in label_paths}
    r.derive_packet_labels()
    c.require(before=={str(path):(c.digest(path),path.stat().st_mtime_ns) for path in label_paths},"packet label replay changed artifacts")
    result=dict(status="passed",queries=packet_count,returnedCitations=citation_count,
                prefixes=native["prefixes"],reopenChecks=native["completed"],
                sourceScopeVersionChecks=True,modelAllowlistChecks=True,B0ReplayIdentical=True,
                packetLabelReplayPreservedHashAndMtime=True,priorCheckpointPreserved=True)
    c.publish(c.WORK/"audit.json",result)
    print(result)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("tests","audit"))
    args=parser.parse_args()
    with c.worker():
        tests() if args.command=="tests" else audit()
