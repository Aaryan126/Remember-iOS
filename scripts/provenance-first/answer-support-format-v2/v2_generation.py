"""One answer-format revision: eight fresh local controls, then a review stop.

Old outputs are read-only and their one spent request remains in the cumulative
budget. No benchmark-dispatch path, model selection, retry or output repair exists.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import time

import v2_control as c
import as_generation as old
import as_policy as host_policy
from as_native import stop_group

ROOT = c.CODE.parents[2]
OLD_WORK = old.c.WORK
OLD_SOURCE = old.SOURCE
SOURCE = c.RUN / "generation-build/AnswerSupportProbe.swift"
BINARY = c.RUN / "generation-build/answer-support-format-v2-probe"
GLOBAL_LIMIT, CHECKPOINT_LIMIT = 145, 8
NATIVE_DEADLINE, GRACE, HOST_DEADLINE = 60, 2, 75
SCHEMA = dict(old.SCHEMA)
OLD_PROMPT_PHRASE = "answer is a minimal exact source\nsubstring"
NEW_PROMPT_PHRASE = "answer is a concise verbatim source\nextract"
OLD_GUIDE = "Minimal verbatim answer span up to 160 characters when supported, otherwise the empty string"
NEW_GUIDE = "Concise verbatim answer extract up to 160 characters when supported, otherwise the empty string"


def sha(value): return hashlib.sha256(c.encoded(value)).hexdigest()


def instructions():
    c.require(old.INSTRUCTIONS.count(OLD_PROMPT_PHRASE) == 1, "old prompt granularity anchor changed")
    return old.INSTRUCTIONS.replace(OLD_PROMPT_PHRASE, NEW_PROMPT_PHRASE)


def generated_source():
    text = OLD_SOURCE.read_text()
    c.require(text.count(OLD_GUIDE) == 1, "old Swift guide anchor changed")
    return text.replace(OLD_GUIDE, NEW_GUIDE)


def controls_spec():
    cases = [
        ("extract", "What exact locker code was recorded?", ["Locker code: LARCH-58."],
         "supported", ["LARCH-58", "Locker code: LARCH-58."], [0]),
        ("missing", "What was the planting bed's measured soil pH?",
         ["The planting bed's soil pH was not measured."], "explicit_missing", [""], [0]),
        ("conflict", "What time does the festival open?",
         ["The festival opens at 10:30.", "The festival opens at 11:00."], "conflicting", [""], [0, 1]),
        ("absent", "What color was the visitor badge?",
         ["The visitor badge was stored in the envelope."], "not_established", [""], []),
    ]
    result = []
    for name, question, quotes, verdict, answers, refs in cases:
        candidates = [dict(id=f"format-v2-source-{i+1}", revision=0, quote=quote,
                           isCurrentVersion=True, isArchived=False) for i, quote in enumerate(quotes)]
        packet = dict(question=question, scope="current", candidates=candidates)
        expected = dict(verdict=verdict, answers=answers,
                        evidence=[dict(candidateID=candidates[i]["id"], quote=quotes[i]) for i in refs])
        for repeat in (1, 2):
            result.append(dict(id=f"v2-control-{name}-{repeat}", pair=name, repeat=repeat,
                               packet=packet, expected=expected))
    return result


def runtime_identity():
    # The native binary independently checks live availability/context/OS before
    # creating a fresh session. A cached availability record cannot qualify it.
    return old.runtime_identity()


def source_bindings():
    paths = [Path(__file__), c.CODE / "v2_control.py", OLD_SOURCE,
             Path(old.__file__), Path(host_policy.__file__), old.c.CODE / "as_native.py"]
    return {str(path.relative_to(ROOT)): c.digest(path) for path in paths}


def prepare_build():
    c.verify_prior()
    c.boundary()
    data = generated_source().encode()
    path = c.checked(SOURCE)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): c.require(path.read_bytes() == data, "generated Swift changed")
    else:
        with path.open("xb") as stream: stream.write(data)
    return dict(oldSwiftSHA256=c.digest(OLD_SOURCE), generatedSwiftSHA256=c.digest(SOURCE),
                soleGuideChange=dict(old=OLD_GUIDE, new=NEW_GUIDE))


def compile_request(command):
    """Resource/pause-aware owned process; logs only in the new run directory."""
    c.boundary()
    log = c.checked(c.RUN / "generation-build/compiler.log")
    process, failure = None, None
    started = time.monotonic()
    try:
        with log.open("xb") as stream:
            process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            while process.poll() is None:
                time.sleep(.25)
                c.boundary()
                if time.monotonic()-started > 180: raise TimeoutError("v2 compiler watchdog")
            c.require(process.returncode == 0, "v2 compile failed; preserve reserved build")
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        if process is not None: stop_group(process)
        c.publish(c.WORK / "generation-build-terminal.json", dict(failure=failure,
                  hostProcessExited=process is None or process.poll() is not None,
                  exitCode=process.returncode if process else None, logSHA256=c.digest(log)))
    return log.read_text()


def build():
    c.verify_prior()
    c.boundary()
    receipt = c.WORK / "generation-build.json"
    if receipt.exists(): return verify_build()
    reservation = c.WORK / "generation-build-reserved.json"
    c.require(not reservation.exists() and not BINARY.exists(), "unresolved v2 build; no automatic retry")
    source = prepare_build()
    command = ["xcrun", "swiftc", "-parse-as-library", "-O", "-module-cache-path",
               str(c.RUN / "generation-build/module-cache"), str(SOURCE), "-o", str(BINARY)]
    before = dict(sourceHashes=source_bindings(), source=source, command=command,
                  instructionsSHA256=sha(instructions()), schema=SCHEMA, schemaSHA256=sha(SCHEMA),
                  controlsSHA256=sha(controls_spec()), runtime=runtime_identity(),
                  oldBuildSHA256=c.digest(OLD_WORK / "generation-build.json"),
                  nativeDeadlineSeconds=NATIVE_DEADLINE, cancellationGraceSeconds=GRACE,
                  hostDeadlineSeconds=HOST_DEADLINE, checkpointRequestLimit=CHECKPOINT_LIMIT,
                  cumulativeRequestLimit=GLOBAL_LIMIT, benchmarkGenerationAllowed=False)
    c.publish(reservation, before)
    output = compile_request(command)
    c.require(source_bindings() == before["sourceHashes"] and runtime_identity() == before["runtime"]
              and c.digest(SOURCE) == source["generatedSwiftSHA256"]
              and SOURCE.read_text() == generated_source(), "v2 source/runtime changed during compile")
    record = dict(**before, binarySHA256=c.digest(BINARY), buildOutput=output,
                  reservationSHA256=c.digest(reservation),
                  terminalSHA256=c.digest(c.WORK / "generation-build-terminal.json"))
    c.publish(receipt, record)
    return record


def verify_build():
    c.verify_prior()
    record = c.load(c.WORK / "generation-build.json")
    c.require(record["sourceHashes"] == source_bindings() and record["binarySHA256"] == c.digest(BINARY)
              and record["source"]["oldSwiftSHA256"] == c.digest(OLD_SOURCE)
              and record["source"]["generatedSwiftSHA256"] == c.digest(SOURCE)
              and SOURCE.read_text() == generated_source()
              and record["instructionsSHA256"] == sha(instructions()) and record["schema"] == SCHEMA
              and record["schemaSHA256"] == sha(SCHEMA) and record["controlsSHA256"] == sha(controls_spec())
              and record["runtime"] == runtime_identity()
              and record["oldBuildSHA256"] == c.digest(OLD_WORK / "generation-build.json")
              and record["reservationSHA256"] == c.digest(c.WORK / "generation-build-reserved.json")
              and record["terminalSHA256"] == c.digest(c.WORK / "generation-build-terminal.json"),
              "frozen v2 build/prompt/schema/runtime changed")
    return record


def control_correct(output, expected):
    if output.get("verdict") != expected["verdict"] or output.get("answer") not in expected["answers"]: return False
    return sorted(output["evidence"], key=lambda r: (r["candidateID"], r["quote"])) == sorted(
        expected["evidence"], key=lambda r: (r["candidateID"], r["quote"]))


def reservations():
    prior = list((OLD_WORK / "generation-reservations").glob("*.json"))
    current = list((c.WORK / "generation-reservations").glob("*.json"))
    return prior, current


def verified_request(spec, build_record):
    request = dict(schemaVersion=1, unit=spec["id"], instructions=instructions(),
                   packet=json.dumps(old.model_packet(spec["packet"]), ensure_ascii=False, sort_keys=True),
                   expectedRuntime=build_record["runtime"])
    c.require(len(c.encoded(request)) <= 32768, "context request too large; no truncation")
    return request


def interpret(raw, spec, runtime):
    terminal, error = None, None
    try:
        terminal = old.parse_terminal(raw, spec["id"], runtime)
        c.require(terminal["status"] == "ok", "native returned execution error")
        host_policy.validate_output(terminal.get("output"), spec["packet"])
    except (ValueError, KeyError, TypeError, AttributeError) as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
    return terminal, error


def verify_unit(spec, build_record):
    binding = c.digest(c.WORK / "generation-build.json")
    unit = spec["id"]
    row = c.read_unit(c.WORK / "generation-units" / (unit + ".json"), binding)
    raw = c.RUN / "generation-raw" / (unit + ".log")
    inp = c.RUN / "generation-inputs" / (unit + ".json")
    reserved = c.WORK / "generation-reservations" / (unit + ".json")
    c.require(c.digest(raw) == row["rawSHA256"] and c.digest(inp) == row["inputSHA256"]
              and c.digest(reserved) == row["reservationSHA256"], "v2 unit raw/input/reservation changed")
    c.require(c.load(inp) == verified_request(spec, build_record), "saved request differs from frozen control")
    reservation = c.load(reserved)
    c.require(reservation["bindingSHA256"] == binding and reservation["inputSHA256"] == c.digest(inp)
              and reservation["frozenSHA256"] == c.digest(c.WORK / "frozen.json")
              and reservation["unit"] == unit and reservation["requestCount"] == 1,
              "v2 reservation binding mismatch")
    parsed, error = interpret(raw.read_text(), spec, build_record["runtime"])
    c.require(parsed == row["terminal"] and row["output"] == (parsed.get("output") if parsed else None),
              "v2 raw interpretation changed")
    c.require(row["executionKnown"] == (parsed is not None) and row["hostProcessExited"] is True,
              "v2 owned process exit/execution identity unconfirmed")
    c.require(row["validationError"] == error and row["requestCount"] == 1 and row["id"] == unit,
              "v2 saved error/count/identity interpretation changed")
    content_passed = row["failure"] is None and error is None and control_correct(row["output"], spec["expected"])
    c.require(row["contentPassed"] == content_passed, "v2 content verdict changed")
    repeat_matched = None
    if spec["repeat"] == 2:
        previous = c.read_unit(c.WORK / "generation-units" / (unit[:-1] + "1.json"), binding)
        repeat_matched = row["output"] == previous["output"]
    c.require(row["repeatMatched"] == repeat_matched
              and row["passed"] == (content_passed and repeat_matched is not False), "v2 repeat verdict changed")
    return row


def request_control(spec, build_record):
    allowlist = {row["id"]: row for row in controls_spec()}
    c.require(spec.get("id") in allowlist and spec == allowlist[spec["id"]],
              "v2 permits only eight frozen fresh controls; no benchmark dispatch")
    c.verify_frozen()
    c.require(build_record == verify_build(), "caller build record differs from frozen v2 build")
    for preceding in controls_spec():
        if preceding["id"] == spec["id"]: break
        path = c.WORK / "generation-units" / (preceding["id"] + ".json")
        c.require(path.exists(), "v2 controls must run in frozen order")
        c.require(verify_unit(preceding, build_record)["passed"], "earlier v2 control failed; no further dispatch")
    unit = spec["id"]
    destination = c.WORK / "generation-units" / (unit + ".json")
    if destination.exists(): return verify_unit(spec, build_record)
    c.boundary()
    prior, current = reservations()
    c.require(len(prior)+len(current) < GLOBAL_LIMIT, "145 cumulative generation reservations exhausted")
    c.require(len(current) < CHECKPOINT_LIMIT, "eight v2 control reservations exhausted")
    reservation = c.WORK / "generation-reservations" / (unit + ".json")
    c.require(not reservation.exists(), "unresolved v2 generation reservation; never retry automatically")
    request = verified_request(spec, build_record)
    request_path = c.RUN / "generation-inputs" / (unit + ".json")
    c.publish(request_path, request)
    binding = c.digest(c.WORK / "generation-build.json")
    c.publish(reservation, dict(unit=unit, bindingSHA256=binding, inputSHA256=c.digest(request_path),
              frozenSHA256=c.digest(c.WORK / "frozen.json"), checkpoint="v2-controls-only", requestCount=1,
              priorReservations=len(prior), cumulativeReservations=len(prior)+len(current)+1,
              startedUnix=time.time()))
    raw = c.checked(c.RUN / "generation-raw" / (unit + ".log"))
    raw.parent.mkdir(parents=True, exist_ok=True)
    process, failure, interrupted = None, None, None
    started = time.monotonic()
    try:
        with raw.open("xb") as stream:
            process = subprocess.Popen([str(BINARY), "--input", str(request_path)],
                        stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            while process.poll() is None:
                time.sleep(.25)
                c.boundary()
                if time.monotonic()-started > HOST_DEADLINE: raise TimeoutError("v2 host generation watchdog")
            c.require(process.returncode == 0, "native process failed")
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        interrupted = error
    finally:
        if process is not None: stop_group(process)
    terminal, output_error = interpret(raw.read_text(), spec, build_record["runtime"])
    content_passed = failure is None and output_error is None and control_correct(terminal["output"], spec["expected"])
    repeat_matched = None
    if spec["repeat"] == 2:
        first = c.read_unit(c.WORK / "generation-units" / (unit[:-1] + "1.json"), binding)
        repeat_matched = first["output"] == (terminal.get("output") if terminal else None)
    passed = content_passed and repeat_matched is not False
    payload = dict(id=unit, passed=passed, contentPassed=content_passed, repeatMatched=repeat_matched,
                   output=terminal.get("output") if terminal else None, terminal=terminal, failure=failure,
                   validationError=output_error, rawSHA256=c.digest(raw), inputSHA256=c.digest(request_path),
                   reservationSHA256=c.digest(reservation), hostProcessExited=process is None or process.poll() is not None,
                   executionKnown=terminal is not None, requestCount=1)
    c.unit(destination, payload, binding)
    if interrupted is not None: raise interrupted
    return payload


def controls(maximum=None, resume=False):
    c.require(maximum is None or type(maximum) is int and maximum > 0, "invalid control limit")
    c.verify_frozen()
    record = verify_build()
    completed, made = [], 0
    for spec in controls_spec():
        c.boundary()
        existed = (c.WORK / "generation-units" / (spec["id"] + ".json")).exists()
        result = request_control(spec, record)
        completed.append(result)
        c.require(result["passed"], f"v2 neutral control failed: {spec['id']}; stop, no tuning/retries")
        if not existed:
            made += 1
            if maximum is not None and made >= maximum: break
    if len(completed) == CHECKPOINT_LIMIT: return verify_controls()
    return dict(completed=len(completed), qualified=False, boundedStop=True, stageBAllowed=False)


def verify_controls():
    c.verify_frozen()
    record = verify_build()
    rows = [verify_unit(spec, record) for spec in controls_spec()]
    c.require(all(row["passed"] for row in rows), "v2 controls failed; qualification denied")
    prior, current = reservations()
    c.require(len(current) == CHECKPOINT_LIMIT and len(prior)+len(current) <= GLOBAL_LIMIT,
              "v2 request count mismatch")
    answers = [row["output"]["answer"] for row in rows if row["output"]["verdict"] == "supported"]
    result = dict(controls=CHECKPOINT_LIMIT, qualified=True, reproduciblePairs=4,
                  generationReservations=len(current), preservedPriorReservations=len(prior),
                  cumulativeReservations=len(prior)+len(current), buildSHA256=c.digest(c.WORK / "generation-build.json"),
                  supportedAnswerLengths=[len(answer) for answer in answers], stageBAllowed=False,
                  benchmarkGenerationAllowed=False)
    c.publish(c.WORK / "controls.json", result)
    return result
