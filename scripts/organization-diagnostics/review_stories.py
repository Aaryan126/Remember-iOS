"""Seal authored stories and prepare source-only independent prefix review."""
import argparse
import json

import checkpoint as c
import stories as s


def prepare():
    paths = sorted((c.DATA / "stories").glob("story-*.json"))
    c.require([p.stem for p in paths] == [f"story-{i:02d}" for i in range(1, 13)], "Require all twelve stories")
    packet = {"schemaVersion": 1,
              "reviewPurpose": "Retrospective manual causal audit of intended capture-prefix memberships and every textual dependency; full story and declared scopes visible, not prefix-blind evaluation",
              "stories": []}
    for path in paths:
        story = s.validate(c.read(path))
        c.require(story["id"] == path.stem, "Story identity mismatch")
        shown = {key: story[key] for key in ("id", "title", "threads")}
        shown["captures"] = [{key: item[key] for key in ("id", "modality", "text")} for item in story["captures"]]
        shown["events"] = []
        for event in story["events"]:
            entry = {key: value for key, value in event.items() if key != "memberships"}
            if event["kind"] == "correct":
                entry["userRequestedProjects"] = event["memberships"]
                entry["explicitUserAction"] = True
            shown["events"].append(entry)
        packet["stories"].append(shown)
    c.publish(c.DATA / "packets/stories.json", packet)
    c.publish(c.DATA / "receipts/story-authoring.json", {
        "stories": {path.name: c.digest(path) for path in paths},
        "packetSHA256": c.digest(c.DATA / "packets/stories.json"),
        "contractSHA256": c.digest(c.DATA / "CONTRACT.md"),
        "authoringSpecificationSHA256": c.digest(c.DATA / "STORY_AUTHORING.md"),
        "packetBuilderSHA256": c.digest(c.ROOT / "scripts/organization-diagnostics/review_stories.py"),
        "validatorSHA256": c.digest(c.ROOT / "scripts/organization-diagnostics/stories.py"),
        "authoredMembershipsHidden": True, "declaredProjectScopesShown": True,
    })
    return {"stories": 12, "captures": 144, "packetSHA256": c.digest(c.DATA / "packets/stories.json")}


def validate_review(review, packet):
    c.require(set(review) == {"schemaVersion", "reviewer", "packetSHA256", "stories"}
              and review["schemaVersion"] == 1 and review["reviewer"] == "alpha", "Invalid story review header")
    source = {story["id"]: story for story in packet["stories"]}
    ids = [story["id"] for story in review["stories"]]
    c.require(len(ids) == len(set(ids)) and set(ids) == set(source), "Story review incomplete/duplicate")
    for judgment in review["stories"]:
        c.require(set(judgment) == {"id", "assignments", "findings"}, "Invalid story judgment keys")
        story = source[judgment["id"]]
        assignments = judgment["assignments"]
        ids = [row["capture"] for row in assignments]
        c.require(len(ids) == len(set(ids)) and set(ids) == {row["id"] for row in story["captures"]}, "Capture review incomplete/duplicate")
        for row in assignments:
            c.require(set(row) == {"capture", "memberships", "rationale"}, "Invalid assignment keys")
            s.memberships(row["memberships"], {thread["id"] for thread in story["threads"]})
            c.require(isinstance(row["rationale"], str) and len(row["rationale"].strip()) >= 20, "Assignment needs rationale")
        c.require(isinstance(judgment["findings"], list), "Findings must be a list")
        for finding in judgment["findings"]:
            c.require(set(finding) == {"severity", "eventIds", "captureIds", "issue", "suggestion"}, "Invalid finding keys")
            c.require(finding["severity"] in {"blocker", "note"}, "Invalid finding severity")
            c.require(isinstance(finding["eventIds"], list) and isinstance(finding["captureIds"], list), "Invalid finding evidence")
            c.require(set(finding["eventIds"]) <= {e["id"] for e in story["events"]}
                      and set(finding["captureIds"]) <= set(ids), "Unknown finding references")
            c.require(all(isinstance(finding[k], str) and len(finding[k].strip()) >= 20 for k in ("issue", "suggestion")), "Finding needs explanation")


def seal():
    prepare()  # Same-content publication verifies the original authoring seal.
    path, packet_path = c.DATA / "reviews/alpha-stories.json", c.DATA / "packets/stories.json"
    review, packet = c.read(path), c.read(packet_path)
    validate_review(review, packet)
    c.require(review["packetSHA256"] == c.digest(packet_path), "Story review packet changed")
    receipt = {"reviewer": "alpha", "reviewSHA256": c.digest(path), "packetSHA256": c.digest(packet_path),
               "stories": len(review["stories"]), "assignments": sum(len(s["assignments"]) for s in review["stories"])}
    c.publish(c.DATA / "receipts/alpha-stories.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "seal"))
    args = parser.parse_args()
    print(json.dumps(prepare() if args.command == "prepare" else seal()))


if __name__ == "__main__":
    main()
