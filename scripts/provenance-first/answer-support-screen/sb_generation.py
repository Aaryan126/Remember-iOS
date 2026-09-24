"""Bounded serial dispatch of predeclared Stage B packets; no rubric in requests."""
import json
import subprocess
import time
import sb_control as c
import sb_data as data

g=c.generation


def request(spec):
    runtime=c.load(c.previous.WORK/'generation-build.json')['runtime']
    result=dict(schemaVersion=1,unit=spec['id'],instructions=g.instructions(),
        packet=json.dumps(g.old.model_packet(spec['packet']),ensure_ascii=False,sort_keys=True),expectedRuntime=runtime)
    c.require(len(c.encoded(result))<=32768,'oversized context; never truncate')
    return result


def reservations():
    old=list((c.previous.previous.WORK/'generation-reservations').glob('*.json'))
    controls=list((c.previous.WORK/'generation-reservations').glob('*.json'))
    current=list((c.WORK/'reservations').glob('*.json'))
    c.require(len(old)==1 and len(controls)==8,'prior request count changed')
    return old+controls,current


def read(spec):
    name=spec['id'];binding=c.digest(c.WORK/'frozen.json')
    row=c.read_unit(c.WORK/'units'/(name+'.json'),binding)
    raw=c.RUN/'raw'/(name+'.log');inp=c.RUN/'inputs'/(name+'.json');reserved=c.WORK/'reservations'/(name+'.json')
    c.require(row['id']==name and row['requestCount']==1 and row['hostProcessExited'] is True,'unit identity/process exit')
    for path,key in [(raw,'rawSHA256'),(inp,'inputSHA256'),(reserved,'reservationSHA256')]:
        c.require(c.digest(path)==row[key],'saved input/raw/reservation changed')
    c.require(c.load(inp)==request(spec),'saved request changed')
    reservation=c.load(reserved)
    c.require(reservation['id']==name and reservation['bindingSHA256']==binding
              and reservation['inputSHA256']==c.digest(inp) and reservation['requestCount']==1,'reservation mismatch')
    terminal,error=g.interpret(raw.read_text(),spec,request(spec)['expectedRuntime'])
    c.require(row['terminal']==terminal and row['validationError']==error and
              row['executionKnown']==(terminal is not None),'saved output interpretation changed')
    return row


def authorize(spec):
    c.verify_frozen()
    schedule=data.specs(spec['split'])
    by_id={s['id']:s for s in schedule}
    c.require(spec.get('id') in by_id and spec==by_id[spec['id']],'packet not in frozen schedule')
    if spec['split']=='evaluation':
        from sb_runner import verify_decision
        c.require(verify_decision('development')['qualified'],'development failed; evaluation forbidden')
    for preceding in schedule:
        if preceding['id']==spec['id']:break
        c.require((c.WORK/'units'/(preceding['id']+'.json')).exists(),'out-of-order request')
        c.require(read(preceding)['executionKnown'],'unknown prior execution; hold, never retry')


def dispatch(spec):
    authorize(spec)
    name=spec['id'];destination=c.WORK/'units'/(name+'.json')
    if destination.exists():return read(spec)
    c.boundary()
    prior,current=reservations()
    c.require(len(prior)+len(current)<c.GLOBAL_LIMIT and len(current)<c.NEW_LIMIT,'request budget exhausted')
    c.require(sum(p.stem.startswith(spec['split']+'-') for p in current)<c.SPLIT_LIMIT,'split request cap exhausted')
    reserved=c.WORK/'reservations'/(name+'.json')
    c.require(not reserved.exists(),'unresolved reservation; no automatic retry')
    inp=c.RUN/'inputs'/(name+'.json')
    c.publish(inp,request(spec))
    c.publish(reserved,dict(id=name,bindingSHA256=c.digest(c.WORK/'frozen.json'),inputSHA256=c.digest(inp),
        requestCount=1,cumulativeRequests=len(prior)+len(current)+1,startedUnix=time.time()))
    raw=c.checked(c.RUN/'raw'/(name+'.log'));raw.parent.mkdir(parents=True,exist_ok=True)
    process=failure=interrupted=None
    started=time.monotonic()
    try:
        with raw.open('xb') as stream:
            process=subprocess.Popen([str(g.BINARY),'--input',str(inp)],stdout=stream,
                                     stderr=subprocess.STDOUT,start_new_session=True)
            while process.poll() is None:
                time.sleep(.25)
                c.boundary()
                if time.monotonic()-started>g.HOST_DEADLINE:raise TimeoutError('Stage B host watchdog')
            c.require(process.returncode==0,'native process failed')
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error));interrupted=error
    finally:
        if process is not None:g.stop_group(process)
    terminal,error=g.interpret(raw.read_text(),spec,request(spec)['expectedRuntime'])
    row=dict(id=name,terminal=terminal,validationError=error,failure=failure,requestCount=1,
        executionKnown=terminal is not None,hostProcessExited=process is None or process.poll() is not None,
        rawSHA256=c.digest(raw),inputSHA256=c.digest(inp),reservationSHA256=c.digest(reserved))
    c.unit(destination,row)
    if interrupted is not None:raise interrupted
    c.require(row['executionKnown'],'unknown execution saved; hold, no automatic retry')
    return row
