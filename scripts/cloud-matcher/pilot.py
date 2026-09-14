#!/usr/bin/env python3
"""Bounded, resumable GPT-5.4 diagnostic. No production or historical-run writes."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import statistics
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HELPERS = ROOT / "scripts/organization-diagnostics"
sys.path.insert(0, str(HELPERS))
import c2_common as c
import c7_run as historical

RUN = ROOT / "Evaluation/CloudMatcher/pilot-01"
MODEL = "gpt-5.4-2026-03-05"
MAX_CALLS = 120
MAX_INPUT = 4000
MAX_OUTPUT = 2000
CAP_NANO = 5_000_000_000
RESERVE_NANO = MAX_INPUT * 2500 + MAX_OUTPUT * 15000
PAUSED = False
SCHEMA = {"type": "object", "additionalProperties": False,
    "properties": {
        "evidence": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {"sourceID": {"type": "string"}, "quote": {"type": "string"}},
            "required": ["sourceID", "quote"]}},
        "verdict": {"type": "string", "enum": ["same_project", "separate_projects", "abstain"]},
        "rationale": {"type": "string"}}, "required": ["evidence", "verdict", "rationale"]}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def log(**fields):
    print(json.dumps(fields, sort_keys=True), flush=True)


def credentials():
    """Read only the configured key; never publish credentials or environment contents."""
    value = os.environ.get("OPENAI_API_KEY", "").strip()
    if not value and (ROOT / ".env").is_file():
        for line in (ROOT / ".env").read_text().splitlines():
            name, separator, candidate = line.strip().partition("=")
            if separator and name.strip() == "OPENAI_API_KEY":
                value = candidate.strip().strip('"').strip("'")
    c.require(bool(value) and "\n" not in value and "\r" not in value, "API credential missing or invalid")
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def transport(method, path, payload=None):
    c.require(path in {"/responses", "/models/" + MODEL}, "Unapproved API path")
    request = urllib.request.Request("https://api.openai.com/v1" + path,
        data=canonical(payload).encode() if payload is not None else None,
        headers={"Authorization": "Bearer " + credentials(), "Content-Type": "application/json"}, method=method)
    # No SDK retries, redirects, proxy-model overrides, tools or asynchronous jobs.
    opener = urllib.request.build_opener(NoRedirect())
    started = time.monotonic()
    try:
        with opener.open(request, timeout=55) as response:
            data = response.read(1_000_001)
            if len(data) > 1_000_000:
                return {"httpStatus": response.status, "errorKind": "oversized-response", "elapsedSeconds": time.monotonic() - started}
            try:
                body = json.loads(data)
            except (ValueError, UnicodeError):
                return {"httpStatus": response.status, "errorKind": "invalid-json", "elapsedSeconds": time.monotonic() - started}
            return {"httpStatus": response.status, "body": body, "elapsedSeconds": time.monotonic() - started}
    except urllib.error.HTTPError as error:
        # An upstream error can echo request details; never print/store its raw body.
        return {"httpStatus": error.code, "errorKind": "http-error", "elapsedSeconds": time.monotonic() - started}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"httpStatus": None, "errorKind": "transport-error", "elapsedSeconds": time.monotonic() - started}


def request(packet):
    visible = historical.visible(packet)
    body = {"model": MODEL, "instructions": historical.PROMPT.read_text(), "input": canonical(visible),
        "reasoning": {"effort": "low"}, "max_output_tokens": MAX_OUTPUT,
        "service_tier": "default", "store": False, "tools": [], "truncation": "disabled",
        "text": {"format": {"type": "json_schema", "name": "project_relationship", "strict": True, "schema": SCHEMA}}}
    # UTF-8 byte count is a deliberately generous token bound; additional allowance
    # covers message/schema framing. Never truncate evidence to fit the budget.
    upper = len(canonical(body).encode()) + 512
    c.require(upper <= MAX_INPUT, "Input bound exceeded; stop rather than truncate")
    return body


def usage_cost(body):
    usage = body.get("usage") if isinstance(body, dict) else None
    if not isinstance(usage, dict):
        return None
    inp, out = usage.get("input_tokens"), usage.get("output_tokens")
    cached = usage.get("input_tokens_details", {}).get("cached_tokens", 0)
    c.require(all(type(v) is int and v >= 0 for v in (inp, out, cached)) and cached <= inp, "Invalid usage counts")
    c.require(inp <= MAX_INPUT and out <= MAX_OUTPUT, "Usage exceeded reserved bounds; stop")
    return (inp - cached) * 2500 + cached * 250 + out * 15000


def interpret(packet, wire):
    error = wire.get("errorKind")
    body = wire.get("body", {})
    if error or wire.get("httpStatus") != 200:
        return {"status": "error", "errorKind": error or "http-error", "prediction": None}
    try:
        c.require(body.get("model") == MODEL, "Unexpected model")
        c.require(body.get("service_tier") == "default", "Unexpected billing tier")
        c.require(body.get("status") == "completed", "Incomplete/refused response")
        c.require(body.get("store") is False, "Unexpected response storage")
        messages = [item for item in body["output"] if item.get("type") == "message"]
        content = [part for item in messages for part in item.get("content", [])]
        c.require(len(content) == 1 and content[0].get("type") == "output_text", "Missing text or refusal")
        prediction = historical.validate_output(packet, json.loads(content[0]["text"]))
        return {"status": "ok", "prediction": prediction}
    except (ValueError, KeyError, TypeError, AttributeError):
        return {"status": "error", "errorKind": "invalid-output", "prediction": None}


def verify():
    manifest = c.read(RUN / "manifest.json")
    for relative, digest in manifest["files"].items():
        path = ROOT / relative
        c.require(path.resolve().is_relative_to(ROOT) and c.digest(path) == digest, "Frozen source changed: " + relative)
    return manifest


def freeze():
    if (RUN / "manifest.json").exists():
        verify()
        return {"frozen": True}
    # Read/check completed historical receipts, but do not invoke their write-capable audit commands.
    for receipt in (historical.CURATED / "complete.json", historical.c6_run.CURATED / "complete.json"):
        for relative, digest in c.read(receipt)["sources"].items():
            c.require(c.digest(ROOT / relative) == digest, "Historical receipt mismatch: " + relative)
    catalogue = historical.catalogue()
    c.require(len(catalogue["contexts"]) == 112 and len(catalogue["mapping"]) == 160, "Changed dataset")
    for packet in catalogue["contexts"].values():
        request(packet)
    c.publish(RUN / "catalogue.json", catalogue)
    paths = list(Path(__file__).parent.glob("*.py")) + [RUN / "PROTOCOL.md", RUN / "catalogue.json", historical.PROMPT,
        historical.c6_run.RUN / "adjudicated-gold.json", historical.c5_run.RUN / "release/inputs.json",
        historical.c6_run.RUN / "predictions/baseline.json", historical.c6_run.RUN / "predictions/29.json",
        ROOT / "Evaluation/AppMatcher/inputs.json", ROOT / "Remember/Remember/D3OrganizationPolicy.swift"]
    paths += list(HELPERS.glob("*.py"))
    c.publish(RUN / "manifest.json", {"model": MODEL, "maximumCalls": MAX_CALLS,
        "inputBoundTokens": MAX_INPUT, "maximumOutputTokens": MAX_OUTPUT,
        "capNanoUSD": CAP_NANO, "reservationNanoUSD": RESERVE_NANO,
        "inputNanoUSDPerToken": 2500, "cachedInputNanoUSDPerToken": 250, "outputNanoUSDPerToken": 15000,
        "files": {str(p.relative_to(ROOT)): c.digest(p) for p in sorted(set(paths))},
        "createdAtUnix": time.time(), "exposedDiagnostic": True, "productionQualified": False})
    return {"frozen": True, "uniqueInputs": 112, "maximumRequestBytesPlusFraming": max(len(canonical(request(p)).encode()) + 512 for p in catalogue["contexts"].values())}


def budget():
    receipts = sorted((RUN / "attempts").glob("*/reservation.json"))
    accounted, measured, unresolved = 0, 0, 0
    for path in receipts:
        reserved = c.read(path)
        c.require(reserved["reservedNanoUSD"] == RESERVE_NANO, "Invalid reservation")
        outcome = path.with_name("result.json")
        if outcome.exists():
            cost = usage_cost(c.read_unit(outcome).get("wire", {}).get("body", {}))
        else:
            cost = None
        accounted += RESERVE_NANO if cost is None else cost
        measured += cost or 0
        unresolved += int(cost is None)
    return {"calls": len(receipts), "accountedNanoUSD": accounted, "measuredNanoUSD": measured, "unresolvedCalls": unresolved}


def reserve(key, body):
    current = budget()
    c.require(current["calls"] < MAX_CALLS and current["accountedNanoUSD"] + RESERVE_NANO <= CAP_NANO, "API budget exhausted")
    directory = RUN / "attempts" / f"{current['calls'] + 1:03d}"
    c.publish(directory / "reservation.json", {"key": key, "requestSHA256": c.text_sha(canonical(body)),
        "reservedNanoUSD": RESERVE_NANO, "createdAtUnix": time.time()})
    return directory


def boundary():
    stats = os.statvfs(ROOT)
    c.require(stats.f_bavail * stats.f_frsize > 10 * 1024**3 + 4 * 1024**2, "10 GiB free-space reserve reached")
    if PAUSED or (RUN / "pause.request").exists():
        raise c.Paused("saved-request-boundary")


@contextmanager
def worker(resume=False):
    RUN.mkdir(parents=True, exist_ok=True)
    with (RUN / "worker.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if resume and (RUN / "pause.request").exists():
            c.publish(RUN / f"resumes/{time.time_ns()}.json", {"pauseSHA256": c.digest(RUN / "pause.request")})
            (RUN / "pause.request").unlink()  # Only this runner's saved control marker.
        def stop(signum, frame):
            global PAUSED
            PAUSED = True
        previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGINT, signal.SIGTERM)}
        try:
            yield
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)


def preflight():
    verify()
    boundary()
    result = transport("GET", "/models/" + MODEL)
    available = result.get("httpStatus") == 200 and result.get("body", {}).get("id") == MODEL
    c.publish(RUN / f"access/{time.time_ns()}.json", {"available": available, "httpStatus": result.get("httpStatus"), "model": MODEL})
    c.require(available, "GPT-5.4 access check failed; no model substitution")
    return {"modelAvailable": True, "inferenceCalls": 0}


def predict(limit=None):
    verify()
    catalogue = c.read(RUN / "catalogue.json")
    pending = {}
    for path in sorted((RUN / "attempts").glob("*/reservation.json")):
        key = c.read(path)["key"]
        c.require(key not in pending, "Duplicate reserved input; investigate before running")
        pending[key] = path.parent
    created, errors = 0, 0
    for key, packet in catalogue["contexts"].items():
        boundary()
        unit_path = RUN / f"units/{key}.json"
        body = request(packet)
        if unit_path.exists():
            c.read_unit(unit_path)
            continue
        if key in pending:
            directory = pending[key]
            c.require(c.read(directory / "reservation.json")["requestSHA256"] == c.text_sha(canonical(body)), "Changed reserved request")
            if (directory / "result.json").exists():
                unit = c.read_unit(directory / "result.json")
            else:
                # A crash may occur after the provider accepted a request. Never resend blindly.
                unit = {"wire": {"errorKind": "interrupted-unknown-billing", "httpStatus": None},
                        "outcome": {"status": "error", "errorKind": "interrupted-unknown-billing", "prediction": None}}
        else:
            directory = reserve(key, body)  # Durable write before any paid network activity.
            wire = transport("POST", "/responses", body)
            unit = {"wire": wire, "outcome": interpret(packet, wire)}
            c.unit(directory / "result.json", unit)
            created += 1
        c.unit(unit_path, unit)
        current = budget()
        log(saved=len(list((RUN / "units").glob("*.json"))), total=112,
            status=unit["outcome"]["status"], accountedUSD=current["accountedNanoUSD"] / 1e9,
            seconds=unit["wire"].get("elapsedSeconds"))
        errors = errors + 1 if unit["outcome"]["status"] == "error" else 0
        if unit["wire"].get("httpStatus") == 200:
            envelope = unit["wire"].get("body", {})
            c.require(envelope.get("model") == MODEL and envelope.get("service_tier") == "default",
                      "Provider model/tier mismatch; stop immediately")
        if errors >= 3 or unit["wire"].get("httpStatus") in {401, 403, 429}:
            raise c.Paused("provider-errors; inspect without prompt tuning or automatic retries")
        if limit is not None and created >= limit:
            return {"boundedStop": True, "safeToClose": True, **budget()}
    c.publish(RUN / "outcomes-complete.json", {"manifestSHA256": c.digest(RUN / "manifest.json"),
        "files": {str(p.relative_to(RUN)): c.digest(p) for p in sorted((RUN / "units").glob("*.json"))}})
    return {"complete": True, **budget()}


def assemble():
    verify()
    catalogue = c.read(RUN / "catalogue.json")
    c.require(len(list((RUN / "units").glob("*.json"))) == 112, "Incomplete outcomes; no partial quality claims")
    outputs = {name: [] for name in ("baseline", "d3", "gpt54", "d3-veto", "d3-confirm")}
    old = {name: {r["queryID"]: r for r in c.read_unit(historical.c6_run.RUN / f"predictions/{seed}.json")}
           for name, seed in (("baseline", "baseline"), ("d3", "29"))}
    for packet in historical.packets():
        key = catalogue["mapping"][packet["queryID"]]
        unit = c.read_unit(RUN / f"units/{key}.json")
        c.require(unit["outcome"] == interpret(catalogue["contexts"][key], unit["wire"]), "Saved response replay differs")
        cloud = dict(unit["outcome"])
        if cloud["status"] == "ok":
            cloud["prediction"] = {**cloud["prediction"], "queryID": packet["queryID"]}
        outputs["gpt54"].append({"queryID": packet["queryID"], **cloud})
        for name in ("baseline", "d3"):
            outputs[name].append({"queryID": packet["queryID"], "status": "ok", "prediction": old[name][packet["queryID"]]})
        for mode in ("veto", "confirm"):
            outputs["d3-" + mode].append({"queryID": packet["queryID"], **historical.combine(old["d3"][packet["queryID"]], cloud, mode)})
    return outputs


def evaluate():
    outputs = assemble()
    labels = c.read(historical.c6_run.RUN / "adjudicated-gold.json")["labels"]
    packets = historical.packets()
    summary = {name: historical.metrics(packets, labels, rows) for name, rows in outputs.items()}
    for name, rows in outputs.items():
        c.unit(RUN / f"predictions/{name}.json", rows)
    units = [c.read_unit(p) for p in sorted((RUN / "units").glob("*.json"))]
    elapsed = sorted(u["wire"]["elapsedSeconds"] for u in units if "elapsedSeconds" in u["wire"])
    gold = {r["queryID"]: r["verdict"] for r in labels}
    transitions = {}
    for name in ("gpt54", "d3-veto", "d3-confirm"):
        for view in ("pair", "context"):
            selected = {p["queryID"] for p in packets if p["view"] == view}
            rows = []
            for baseline, new in zip(outputs["d3"], outputs[name]):
                key = baseline["queryID"]
                if key not in selected:
                    continue
                before = baseline["prediction"]["verdict"]
                after = new["prediction"]["verdict"] if new["status"] == "ok" else "error"
                rows.append({"queryID": key, "gold": gold[key], "before": before, "after": after})
            transitions[name + ":" + view] = {"fixed": sum(r["before"] != r["gold"] and r["after"] == r["gold"] for r in rows),
                "damaged": sum(r["before"] == r["gold"] and r["after"] != r["gold"] for r in rows), "rows": rows}
    result = {"metrics": summary, "transitions": transitions,
        "explorationGate": historical.exploration_gate(summary["gpt54"]),
        "budget": budget(), "uniqueRequests": len(units), "expandedPackets": len(packets),
        "latencySeconds": {"p50": statistics.median(elapsed) if elapsed else None,
            "p95": elapsed[max(0, int(len(elapsed) * .95 + .999) - 1)] if elapsed else None},
        "productionQualified": False, "exposedDiagnostic": True}
    c.publish(RUN / "summary.json", result)
    return {"evaluated": True, "sameResultsOnReplay": True, **budget()}


def status():
    return {"savedUnits": len(list((RUN / "units").glob("*.json"))), "total": 112,
        "pauseRequested": (RUN / "pause.request").exists(), **budget()}


def proof():
    path = RUN / "resume-before.json"
    if not path.exists():
        files = sorted((RUN / "units").glob("*.json"))
        c.require(len(files) == 2, "Pause proof requires exactly two completed inputs")
        c.publish(path, {str(p.relative_to(RUN)): {"SHA256": c.digest(p), "mtimeNS": p.stat().st_mtime_ns} for p in files})
        return {"savedResumeProof": True}
    for relative, metadata in c.read(path).items():
        unit = RUN / relative
        c.require(c.digest(unit) == metadata["SHA256"] and unit.stat().st_mtime_ns == metadata["mtimeNS"], "Completed input was rewritten")
    c.publish(RUN / "resume-after.json", {"passed": True, "beforeSHA256": c.digest(path), "unchangedCompletedInputs": 2})
    return {"resumeProofPassed": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "preflight", "predict", "evaluate", "status", "pause", "proof"))
    parser.add_argument("--max-units", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.max_units is not None and args.max_units <= 0:
        parser.error("--max-units must be positive")
    try:
        if args.phase == "pause":
            if not (RUN / "pause.request").exists():
                c.publish(RUN / "pause.request", {"requestedAtUnix": time.time()})
            log(pauseRequested=True, safeToClose=False)
        elif args.phase == "status":
            log(**status())
        else:
            with worker(args.resume):
                boundary()
                action = {"freeze": freeze, "preflight": preflight,
                    "predict": lambda: predict(args.max_units), "evaluate": evaluate, "proof": proof}[args.phase]
                log(**action())
    except c.Paused as error:
        log(paused=True, reason=str(error), safeToClose=True)
        sys.exit(75)
    except (ValueError, OSError) as error:
        # Only controlled errors reach here; never serialize request headers or credentials.
        log(stopped=True, errorType=type(error).__name__, reason=str(error) if isinstance(error, ValueError) else "I/O failure")
        sys.exit(1)
