"""Scoped v2 preparation/control lifecycle; prior experiment remains read-only."""
from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
import signal
import sys
import time

CODE=Path(__file__).resolve().parent
sys.path.insert(0,str(CODE.parent/'answer-support'))
import as_control as previous
import as_approved as approved
import as_runner as prior_runner

ROOT,PF=previous.ROOT,previous.PF
WORK,RUN=PF/'answer-support-format-v2',PF/'runs/answer-support-format-v2'
load,digest,encoded,require=previous.load,previous.digest,previous.encoded,previous.require
atomic=previous.atomic
CAP,RESERVE=approved.CAP,previous.RESERVE
GLOBAL_LIMIT,CONTROL_LIMIT=145,8
_paused=False


def checked(path):
    path=Path(path).absolute()
    require(path.resolve()==path and any(path!=root and path.is_relative_to(root) for root in (WORK,RUN)),
            'v2 output escaped isolated scope or contains symlink')
    return path


def publish(path,value):
    path=checked(path)
    if path.exists():require(path.read_bytes()==encoded(value),'immutable v2 artifact changed: '+str(path))
    else:atomic(path,value)


def unit(path,payload,binding):
    publish(path,dict(bindingSHA256=binding,payloadSHA256=hashlib.sha256(encoded(payload)).hexdigest(),payload=payload))


def read_unit(path,binding):
    value=load(path)
    require(set(value)=={'bindingSHA256','payloadSHA256','payload'} and value['bindingSHA256']==binding
            and value['payloadSHA256']==hashlib.sha256(encoded(value['payload'])).hexdigest(),'v2 unit binding changed')
    return value['payload']


def verify_prior():
    approved.verify_amendment()
    prior_runner.verify()
    stop=load(previous.WORK/'stage-a-stop.json')
    for name,expected in stop['hashes'].items():
        require(digest(previous.WORK/name)==expected,'v1 stopped artifact changed: '+name)
    reservations=list((previous.WORK/'generation-reservations').glob('*.json'))
    require(len(reservations)==1 and reservations[0].stem=='control-extract-1','v1 generation history changed')
    require(load(previous.WORK/'worker.json')['running'] is False,'v1 worker still active')


def resources():return approved.resources()


def register():
    verify_prior()
    identity=dict(stage='v2 preparation and controls only',stageBAllowed=False,
                  newControlLimit=CONTROL_LIMIT,cumulativeRequestLimit=GLOBAL_LIMIT,priorRequests=1,
                  capBytes=CAP,reserveBytes=RESERVE,baselineReset=False,
                  baselineSHA256=digest(PF/'resources.json'),
                  priorStopSHA256=digest(previous.WORK/'stage-a-stop.json'),
                  reviewSHA256=digest(WORK/'REVIEW.md'),approvalSHA256=digest(WORK/'APPROVAL.md'))
    publish(WORK/'approval.json',identity)
    return identity


def verify_frozen():
    value=load(WORK/'frozen.json')
    for name,expected in value['hashes'].items():
        path=ROOT/name
        require(path.resolve()==path and digest(path)==expected,'v2 frozen artifact changed: '+name)
    sources={str(path.relative_to(ROOT)) for path in CODE.glob('*.py')}
    require(sources==set(value['sourceFiles']),'v2 source set changed')
    require(value['stageBAllowed'] is False,'Stage B is not authorized')
    return value


class Paused(Exception):pass


def boundary():
    if _paused or (WORK/'pause.request.json').exists():raise Paused('saved v2 unit boundary')
    return resources()


@contextmanager
def worker(resume=False):
    global _paused
    WORK.mkdir(parents=True,exist_ok=True)
    # Advisory lock on the existing v1 file coordinates with old entry points
    # without changing its content or any prior worker state/artifact.
    with (previous.WORK/'worker.lock').open('rb') as shared,checked(WORK/'worker.lock').open('a+') as lock:
        fcntl.flock(shared,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        register()
        marker=WORK/'pause.request.json'
        if resume and marker.exists():marker.rename(WORK/f'pause-resumed-{time.time_ns()}.json')
        _paused=False
        def requested(signum,frame):
            global _paused
            _paused=True
        handlers={s:signal.signal(s,requested) for s in (signal.SIGINT,signal.SIGTERM)}
        atomic(checked(WORK/'worker.json'),dict(pid=os.getpid(),running=True))
        try:
            boundary()
            yield
        finally:
            atomic(checked(WORK/'worker.json'),dict(pid=os.getpid(),running=False))
            for signum,handler in handlers.items():signal.signal(signum,handler)
