#!/usr/bin/env python3
"""Execute the nine-path cleanup approved on 24 September, once only."""
import importlib.util
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location("inventory", Path(__file__).with_name("inspect-cleanup.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def main():
    os.umask(0o077)
    names = audit.GENERATED + audit.OLDER_BACKUPS
    proposal = audit.ROOT / "Evaluation/ProvenanceFirst/search-handoff/CLEANUP-PROPOSAL.md"
    listed = re.findall(r"^\| `(Evaluation/ProvenanceFirst/runs/[^`]+)` \|", proposal.read_text(), re.M)
    if listed != [str((audit.RUN / name).relative_to(audit.ROOT)) for name in names]:
        raise ValueError("Proposal differs from approved targets")
    inventories = [audit.inventory(name) for name in names]
    reference = None
    verified = {}
    for name in audit.PROTECTED + audit.OLDER_BACKUPS:
        count, originals = audit.verify_backup(name)
        if reference is not None and originals != reference:
            raise ValueError("Original files differ; cleanup stopped")
        reference = originals
        verified[name] = count
    receipt = audit.RUN / "search-handoff/cleanup-approved.json"
    state = {"startedUTC": datetime.now(timezone.utc).isoformat(), "complete": False,
             "targets": inventories, "verifiedBefore": verified, "deleted": [],
             "freeBytesBefore": shutil.disk_usage(audit.ROOT).free}
    with receipt.open("x") as stream:
        json.dump(state, stream, indent=2)
    try:
        for name in names:
            audit.inventory(name)  # Revalidate exact literal target immediately before removal.
            shutil.rmtree(audit.RUN / name)
            state["deleted"].append(name)
            receipt.write_text(json.dumps(state, indent=2) + "\n")
        state["verifiedAfter"] = {}
        for name in audit.PROTECTED:
            count, originals = audit.verify_backup(name)
            if originals != reference:
                raise ValueError("Protected originals changed")
            state["verifiedAfter"][name] = count
        state["complete"] = True
    finally:
        state["freeBytesAfter"] = shutil.disk_usage(audit.ROOT).free
        state["netFreeBytesRecovered"] = state["freeBytesAfter"] - state["freeBytesBefore"]
        receipt.write_text(json.dumps(state, indent=2) + "\n")
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
