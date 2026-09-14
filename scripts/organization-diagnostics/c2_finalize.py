#!/usr/bin/env python3
"""Post-run evidence verification/curation; cannot execute or change model policies.

Added after the prospective scoring freeze. Its own source and curated outputs are
bound by the final completion receipt; the original experiment manifest stays intact.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

import c2_common as c
from c2_report import verify_predictions
from c2_run import verify_parity_receipt


def evidence():
    import finalize
    finalize.verify()
    c.verify_bindings()
    verify_parity_receipt()
    predictions = verify_predictions()
    metric = c.read(c.RUN / "metrics-complete.json")
    c.require(metric["summarySHA256"] == c.digest(c.RUN / "metrics-summary.json")
              and metric["errorsSHA256"] == c.digest(c.RUN / "errors.json")
              and metric["predictionReceiptSHA256"] == c.digest(c.RUN / "predictions-complete.json")
              and metric["prefixes"] == 4632, "Metric receipt mismatch")
    replay = c.read(c.RUN / "ledger/replay-summary.json")
    status = c.read(c.RUN / "ledger/results/status.json")
    c.require(status["status"] == "complete" and int(status["completed"]) == 288, "Ledger incomplete")
    c.require(status["batchSHA256"] == replay["inputSHA256"] == c.digest(c.RUN / "ledger-input.json"), "Ledger input mismatch")
    c.require(status["bindingsSHA256"] == replay["bindingsSHA256"] == c.read(c.RUN / "manifest.json")["ledgerBindingSHA256"],
              "Ledger binding mismatch")
    expected = {c.read_unit(c.RUN / name)["id"]: c.read_unit(c.RUN / name) for name in predictions["traces"]}
    observed = set()
    prefixes = historical = restarted = 0
    for name, sha in replay["receiptHashes"].items():
        path = (c.RUN / name).resolve()
        c.require(path.is_relative_to(c.RUN / "ledger/results") and c.digest(path) == sha, "Ledger receipt changed")
        receipt = c.read(path)
        identifier = receipt["id"]
        c.require(identifier in expected and identifier not in observed, "Unexpected/duplicate ledger run")
        observed.add(identifier)
        c.require(receipt["batchSHA256"] == status["batchSHA256"] and receipt["bindingsSHA256"] == status["bindingsSHA256"],
                  "Run binding mismatch")
        c.require([p["id"] for p in receipt["prefixes"]] == [e["id"] for e in expected[identifier]["events"]],
                  "Ledger prefix identity mismatch")
        count = len(expected[identifier]["events"])
        c.require(receipt["prefixCount"] == receipt["historicalPrefixesVerified"] == count
                  and receipt["restartVerified"] is True, "Run checks incomplete")
        ledger = (c.RUN / "ledger/results" / receipt["attempt"] / "ledger.json").resolve()
        c.require(ledger.is_relative_to(c.RUN / "ledger/results") and c.digest(ledger) == receipt["ledgerSHA256"],
                  "Saved ledger changed")
        c.require(len(c.read(ledger)) == receipt["ledgerCount"], "Ledger event count mismatch")
        prefixes += count
        historical += receipt["historicalPrefixesVerified"]
        restarted += 1
    c.require(observed == set(expected) and len(observed) == 288 and prefixes == historical == 4632 and restarted == 288,
              "Replay coverage incomplete")
    c.require(replay["firstReceiptSHA256Before"] == replay["firstReceiptSHA256After"], "Resume changed saved evidence")
    c.require(c.digest(c.RUN / replay["explicitInvariantReceipt"]) == replay["explicitInvariantReceiptSHA256"]
              and replay["explicitInvariantChecks"] == 31, "Invariant evidence changed")
    ready = c.read(c.RUN / "ledger/ready.json")
    app = c.RUN / ready["buildAppPath"]
    c.require(c.digest(app / "OrganizationLedgerProbe") == ready["appbinarySHA256"]
              and c.digest(app / "OrganizationLedgerProbe.debug.dylib") == ready["appDebugDylibSHA256"], "Built harness changed")
    return replay


def test_receipts():
    path = c.RUN / "validation/tests.json"
    commands = [[sys.executable, "-m", "unittest", "discover", "-s", folder, "-p", "test_*.py"]
                for folder in ("scripts/organization-diagnostics", "scripts/organization-diagnostics/ledger")]
    if path.exists():
        saved = c.read(path)
        c.require([row["command"] for row in saved["checks"]] == commands
                  and all(row["returnCode"] == 0 for row in saved["checks"]), "Test receipt mismatch")
        return
    checks = []
    for command in commands:
        result = subprocess.run(command, cwd=c.ROOT, capture_output=True, text=True, timeout=60,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        checks.append({"command": command, "returnCode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        c.require(result.returncode == 0 and "skipped=" not in result.stderr, "Tests failed or skipped: " + result.stderr)
    c.publish(path, {"checks": checks, "runtime": c.runtime()})


def complete():
    if (c.CURATED / "complete.json").exists():
        return {**verify(), "complete": True}
    replay = evidence()
    test_receipts()
    summary = c.read(c.RUN / "metrics-summary.json")
    compact = {"diagnosticOnly": True, "agentReviewedNotHumanReviewed": True,
               "stories": 12, "ordersPerStory": 3, "policyStreams": 288, "prefixes": 4632,
               "policy": {key: {"allOrders": value["allOrders"],
                                 "orderSensitivity": value["orderSensitivity"]["macroPairDisagreement"]}
                          for key, value in summary["policy"].items()}}
    c.publish(c.CURATED / "summary.json", compact)
    c.publish(c.CURATED / "ledger-summary.json", {key: replay[key] for key in
        ("prefixes", "historicalPrefixesVerified", "explicitInvariantChecks", "policyRuns", "ledgerEvents", "ledgerKinds",
         "elapsedSeconds", "peakMeasuredDiagnosticBytes", "peakMeasuredSimulatorNewBytes", "minimumMeasuredFreeBytes")})
    c.publish(c.CURATED / "model-parity.json", {str(seed): c.read(c.RUN / f"parity/seed-{seed}.json") for seed in (17, 29, 41)})
    c.publish(c.CURATED / "tests.json", c.read(c.RUN / "validation/tests.json"))
    raw_paths = [c.RUN / name for name in ("manifest.json", "predictions-complete.json", "metrics-complete.json", "metrics-summary.json",
                                         "ledger/replay-summary.json", "ledger/replay-commands.json", "ledger/input-transfer.json",
                                         "ledger/first-run-checkpoint.json", "ledger-input.json", "validation/tests.json")]
    paths = raw_paths + list(c.CURATED.glob("*.md")) + [c.CURATED / name for name in
              ("summary.json", "ledger-summary.json", "model-parity.json", "tests.json")] + [Path(__file__).resolve()]
    c.require((c.CURATED / "REPORT.md").exists(), "Write the diagnostic recommendation before completing")
    receipt = {"complete": True, "checkpoint": 2, "stopForUserReview": True, "productionQualified": False,
               "checkpoint1SHA256": c.digest(c.DATA / "complete.json"), "manifestSHA256": c.digest(c.RUN / "manifest.json"),
               "sources": {str(path.relative_to(c.ROOT)): c.digest(path) for path in paths},
               "runs": 288, "prefixes": 4632, "historicalPrefixes": 4632, "restartChecks": 288,
               "resourceAtFinalization": c.space(), "nextExperimentStarted": False}
    c.publish(c.CURATED / "complete.json", receipt)
    return {"complete": True, "stopForUserReview": True, "completeSHA256": c.digest(c.CURATED / "complete.json")}


def verify():
    receipt = c.read(c.CURATED / "complete.json")
    c.require(receipt["complete"] is True and receipt["productionQualified"] is False
              and receipt["nextExperimentStarted"] is False, "Invalid completion status")
    for name, sha in receipt["sources"].items():
        path = (c.ROOT / name).resolve()
        c.require(path.is_relative_to(c.ROOT) and c.digest(path) == sha, "Completed evidence changed: " + name)
    evidence()
    return {"verified": True, "stopForUserReview": True, "completeSHA256": c.digest(c.CURATED / "complete.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("complete", "verify"))
    args = parser.parse_args()
    with c.worker():
        c.boundary("finalize")
        c.log("finalize", **({"complete": complete, "verify": verify}[args.phase]()))
