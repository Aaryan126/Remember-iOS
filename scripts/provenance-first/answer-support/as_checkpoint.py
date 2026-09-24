"""Save a stopped resource-hold checkpoint; never build, launch, or retry work."""
import fcntl
import json
from pathlib import Path
import shutil
import subprocess

import as_control as c
import as_fixtures as f
import as_native as n
import as_runner as r


def save():
    with (c.WORK/"worker.lock").open("a+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        c.require(c.load(c.WORK/"worker.json")["running"] is False,"worker still running")
        c.verify_prior()
        f.verify_corpus()
        n.verify_build()
        devices=json.loads(subprocess.check_output(["xcrun","simctl","list","devices","--json"],text=True,timeout=15))["devices"]
        c.require(any(d["udid"]==n.DEVICE and d["state"]=="Shutdown" for group in devices.values() for d in group),"simulator not shut down")
        native=r.native_status()
        # An app may finish successfully just as the host's resource guard fires.
        # Revalidate its durable ledger/reopen proof; do not rerun it.
        recovered=[]
        for row in native["libraries"]:
            import hashlib
            key=hashlib.sha256(row["id"].encode()).hexdigest()
            path=c.WORK/"native-units"/(key+".json")
            if not path.exists(): recovered.append(row["id"])
            c.publish(path,row)
        baseline=c.load(c.PF/"resources.json")
        old=c.ranking.history.previous
        free=shutil.disk_usage(c.PF).free
        scoped=old.allocated(c.PF)+old.allocated(old.CODE)
        external=sum(max(0,old.allocated(Path(path))-start) for path,start in baseline["externalBaselines"].items())
        resources=dict(freeBytes=free,initialFreeBytes=baseline["initialFreeBytes"],scopedBytes=scoped,
                       externalGrowthBytes=external,conservativeGrowthBytes=max(scoped+external,max(0,baseline["initialFreeBytes"]-free)),
                       capBytes=c.CAP,reserveBytes=c.RESERVE)
        paths=list(c.CODE.glob("*.py"))+list(c.CODE.glob("*.swift"))
        paths += [c.WORK/name for name in ("corpus-frozen.json","preparation.json","native-build-v2.json","native-preparation-v2.json","pause-proof.json","SCORING.md")]
        paths += list((c.WORK/"native-units").glob("*.json"))
        paths += list((c.RUN/"native-reservations-v2").glob("*.json"))+list((c.RUN/"native-recoveries").glob("*.json"))
        paths += list(n.OUTPUT.glob("*.json"))+list(n.OUTPUT.glob("*/ledger.json"))
        result=dict(status="resource-hold",stageAComplete=False,stageBAllowed=False,
                    simulatorShutdown=True,workerStopped=True,native=native,
                    recoveredVerifiedHostUnits=recovered,resources=resources,
                    generationReservations=len(list((c.WORK/"generation-reservations").glob("*.json"))),
                    hashes={str(p.relative_to(c.ROOT)):c.digest(p) for p in sorted(paths)})
        c.publish(c.WORK/"resource-hold-checkpoint.json",result)
        print(json.dumps({k:v for k,v in result.items() if k!="hashes"},indent=2))


if __name__=="__main__": save()
