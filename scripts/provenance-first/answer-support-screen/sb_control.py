"""Stage B scope, immutable units, resource checks and safe serial ownership."""
from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
import signal
import sys
import time

CODE=Path(__file__).resolve().parent
sys.path.insert(0,str(CODE.parent/'answer-support-format-v2'))
import v2_control as previous
import v2_generation as generation

ROOT,PF=previous.ROOT,previous.PF
WORK,RUN=PF/'answer-support-screen',PF/'runs/answer-support-screen'
load,digest,encoded,require=previous.load,previous.digest,previous.encoded,previous.require
atomic=previous.atomic
read_unit=previous.read_unit
GLOBAL_LIMIT,NEW_LIMIT,SPLIT_LIMIT=145,136,68
_paused=False


def checked(path):
    path=Path(path).absolute()
    require(path.resolve()==path and any(path!=root and path.is_relative_to(root) for root in (WORK,RUN)),
            'Stage B output escaped scope or contains symlink')
    return path


def publish(path,value):
    path=checked(path)
    if path.exists():require(path.read_bytes()==encoded(value),'immutable Stage B artifact changed: '+str(path))
    else:atomic(path,value)


def unit(path,value):
    publish(path,dict(bindingSHA256=digest(WORK/'frozen.json'),
        payloadSHA256=hashlib.sha256(encoded(value)).hexdigest(),payload=value))


def verify_prior():
    previous.verify_prior()
    previous.verify_frozen()
    for name,expected in load(previous.WORK/'checkpoint-stop.json')['hashes'].items():
        require(digest(previous.WORK/name)==expected,'qualified checkpoint changed: '+name)
    generation.verify_build()
    record=load(previous.WORK/'controls.json')
    require(record['qualified'] and record['controls']==8 and record['cumulativeReservations']==9,'v2 not qualified')
    require(load(previous.WORK/'worker.json')['running'] is False,'v2 worker active')


def register():
    verify_prior()
    value=dict(stage='B',developmentFirst=True,newRequestLimit=NEW_LIMIT,cumulativeRequestLimit=GLOBAL_LIMIT,
        priorRequests=9,capBytes=previous.CAP,reserveBytes=previous.RESERVE,baselineReset=False,
        baselineSHA256=digest(PF/'resources.json'),protocolSHA256=digest(WORK/'PROTOCOL.md'),
        qualificationStopSHA256=digest(previous.WORK/'checkpoint-stop.json'),appIntegrationAllowed=False)
    publish(WORK/'approval.json',value)
    return value


def verify_frozen():
    value=load(WORK/'frozen.json')
    require(set(value['sourceFiles'])=={str(p.relative_to(ROOT)) for p in CODE.glob('*.py')},'Stage B source set changed')
    for name,expected in value['hashes'].items():
        path=ROOT/name
        require(path.resolve()==path and digest(path)==expected,'Stage B frozen input changed: '+name)
    return value


class Paused(Exception):pass


def boundary():
    if _paused or (WORK/'pause.request.json').exists():raise Paused('saved Stage B boundary')
    return previous.resources()


@contextmanager
def worker(resume=False):
    global _paused
    WORK.mkdir(parents=True,exist_ok=True)
    with (previous.previous.WORK/'worker.lock').open('rb') as shared,checked(WORK/'worker.lock').open('a+') as lock:
        fcntl.flock(shared,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        register()
        marker=WORK/'pause.request.json'
        if resume and marker.exists():marker.rename(WORK/f'pause-resumed-{time.time_ns()}.json')
        _paused=False
        def pause(signum,frame):
            global _paused
            _paused=True
        handlers={s:signal.signal(s,pause) for s in (signal.SIGINT,signal.SIGTERM)}
        atomic(checked(WORK/'worker.json'),dict(pid=os.getpid(),running=True))
        try:
            boundary()
            yield
        finally:
            atomic(checked(WORK/'worker.json'),dict(pid=os.getpid(),running=False))
            for s,h in handlers.items():signal.signal(s,h)
