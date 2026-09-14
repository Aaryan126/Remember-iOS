#!/usr/bin/env python3
"""Print a small fictional two-run integration fixture for bounded pause/resume."""

from copy import deepcopy
import hashlib
import json


def fixture():
    state = {}
    events = []

    def record(command):
        events.append({**command, "expectedState": deepcopy(state)})

    for index in (1, 2):
        source = f"localc0{index}"
        text = f"Fictional smoke source {index}."
        state[source] = {"memberships": ["t:c01"], "archived": False,
                         "textSHA256": hashlib.sha256(text.encode()).hexdigest(), "revision": 0}
        record({"id": f"capture-{index}", "kind": "capture", "source": {"id": source, "text": text, "modality": "note"},
                "assignments": ["t:c01"]})
    state["localc02"]["memberships"] = ["t:c02"]
    record({"id": "correct", "kind": "correct", "target": "localc02", "assignments": ["t:c02"]})
    revised = "Fictional revised smoke source."
    state["localc01"].update(textSHA256=hashlib.sha256(revised.encode()).hexdigest(), revision=1)
    record({"id": "revise", "kind": "revise", "target": "localc01", "text": revised})
    for archived in (True, False):
        kind = "archive" if archived else "restore"
        state["localc02"]["archived"] = archived
        record({"id": kind, "kind": kind, "target": "localc02"})
    return {"schemaVersion": 1, "runs": [{"id": "smoke-one", "events": events}, {"id": "smoke-two", "events": events}]}


if __name__ == "__main__":
    print(json.dumps(fixture(), sort_keys=True, indent=2))
