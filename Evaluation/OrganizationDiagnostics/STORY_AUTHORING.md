# Fictional chronological fixtures — authoring specification

Read CONTRACT.md. Author 12 distinct stories, 12 captures each, in `stories/story-01.json`
through `stories/story-12.json`. These are diagnostic fixtures, not train/test splits.
Use realistic short English notes, fictional OCR/transcripts and file/video descriptions;
all modalities are text, not actual media extraction. No personal data or old datasets.
Vary domains, wording, project topology, ambiguity and chronology. Avoid twelve renamed
copies of one template. Each story must have at least two related-but-distinct projects,
multiple phases of one project, and at least one genuinely unrelated capture. Across the
set include independent experiments, recurring events, shared suppliers, explicit bridges,
short fragments, delayed clarification, and project scope boundaries.

JSON shape (all keys required):

```
{
  "schemaVersion": 1, "id": "story-01", "title": "...",
  "threads": [{"id":"p1","title":"...","scope":"..."}],
  "captures": [{"id":"c01","modality":"note","text":"...",
                "memberships":["p1"],"rationale":"..."}],
  "events": [{"id":"e01","kind":"capture","capture":"c01","dependsOn":[]}],
  "challenges": ["..."], "authorNotes": "..."
}
```

Use local capture IDs c01–c12 and event IDs e01, e02, ... in intended chronology.
Modalities: note, image, voice, file, video. Thread IDs are gold-only, never model input.
Each capture appears exactly once in a capture event. Empty memberships mean uncertain,
not unrelated; genuinely unrelated captures get their own thread. Every thread needs a
clear narrow continuing-project scope, and at least one initial member.

Each story also includes all four explicit event kinds below, besides its 12 captures:

- `revise`: id, kind, target (capture ID), text (replacement), dependsOn. This models
  an edit to an existing memory, NOT a newly imported item; keep project identity.
- `correct`: id, kind, target, memberships (new gold thread IDs), reason, dependsOn.
  An explicit user decision, e.g. resolving an uncertain fragment. It must have a
  supported reason; do not manufacture unrelated membership changes just for coverage.
- `archive` and `restore`: id, kind, target, dependsOn. Restore must follow archive.
  Captures retain content and memberships while archived.

Use dependency IDs to ensure each mutation follows its target capture and earlier
mutations of that same target. Capture follow-ups/revisions referring to earlier
captures must depend on their capture event. Corrections relying on a clarification
must also depend on that clarification's capture event. Avoid ordering every event:
leave independent work reorderable. All dependencies point backward in the author
chronology. Author no expected-prefix outputs: the validator will derive them and a
different agent will review the stories and their causal assumptions. Do not access
P2 predictions, selection strata, old gold, or other agents' reviews.
