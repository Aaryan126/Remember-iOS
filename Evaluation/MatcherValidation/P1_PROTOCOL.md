# P1 corpus authoring and review protocol

This implements the frozen P0 plan without changing it. P1 only; no training, embeddings, phone, downloads, prior-test access or production work. Root AGENTS.md applies. Prior source freezes must stay valid.

## Preassigned families

`families.json` fixes 24 families, two libraries each, 24/12/12 train/calibration/evaluation libraries. Each of three authors receives four training, two calibration and two evaluation families, avoiding author identity as a split confound. No source narratives exist when assignments are first frozen. Family IDs and library IDs are host metadata, never text features.

Authors write only their own `authoring/<library>.json` files with apply_patch and save each library promptly. Use fictional, original English memory text, not copied prior examples. Two libraries in a family must be different stories, not renamed versions. Do not inspect other authors or prior corpora while authoring. Authoring evaluation data is permitted; model evaluation and tuning on it are not.

## Library schema

Each file is one library object compatible with `prepare.validate_corpus`:

```
id, split, storyFamily, templateFamily,
threads: [local thread IDs],
threadDescriptions: {thread ID: short objective},
relatedThreads: [[threadA,threadB],...],
challenges: [host-side challenge tags],
items: [{id,text,modality,memberships,rationale}, ...20],
historyChecks: {
  bridge: {item, threads:[threadA,threadB]},
  revision: {earlier,later,thread},
  rename: {thread,from,to,evidenceItem} or null,
  undo: {item,wrongThread,reason} or null
}
```

Use item IDs `<library>-i01` through `-i20`, ordered chronologically; never put these synthetic IDs in source text. Modalities: note/image/voice/video/file, with text transcriptions only. Provide at least three modalities per library, without making modality predict the label. Thread IDs/labels are local and descriptive, not A/B/C template slots. Memberships refer to thread IDs. Empty memberships mean genuinely uncertain, not known unrelated singleton threads.

Every library needs same-thread positives, related-but-different negatives, unrelated negatives, 1–3 uncertain sources and a substantive multi-thread bridge. Use 3–6 threads with **varied** source counts/topology; do not make every library share one membership pattern or source order. Include short realistic fragments, ordinary notes, paraphrases, repeated names/identifiers, corrections, occasional longer notes and distinct deliverables. Do not force every source to repeat an identifier or an explicit “separate task” cue. Known labels must have visible evidence, not author-only intent. Mentioning another thread in passing is not automatically membership in it.

Each `revision` identifies an earlier/later source in the same thread containing a genuine correction/update. The earlier source remains in provenance. A `rename` must be explicit in its evidence source; null is fine when revision already provides the required history change. An `undo` is an explicitly hypothetical operator correction for a wrong association, not a model decision or a fabricated event in the source text. History checks stay host-side and never alter pair labels.

## Review stages

1. Source projection: publish inputs without author memberships/rationales; freeze source hashes. Select 12 pairs per library before reviewer access: four most lexically overlapping pairs (three-token shingles), then eight deterministically hash-ranked remaining pairs. This is a targeted diagnostic sample, not exhaustive independent pair adjudication.
2. Pair-first: an author reviews another author's batch, with no access to that batch's proposed labels or full-library context yet. For each sampled pair record same/related/unrelated/uncertain, sufficient/needs-context, and a short evidence explanation. Commit the immutable review file before context-stage access. Reviewers know the task and selection method, not class quotas; there are none.
3. Context review: expose all source text plus thread definitions, not proposed memberships/rationales. Reviewer independently proposes each source's memberships, related-thread links and notes contradictions/insufficient evidence. Also inspect the supplied history expectations against source evidence; history checks expose a small subset of author's intended associations, so this phase is context-informed, not fully blind. Preserve pair-first responses unchanged.
4. Main-agent adjudication: compare author/reviewer memberships, pair judgments and evidence. Record every disagreement and disposition; do not silently overwrite authored data. Publish amendments and final labels as separate artifacts. Source changes require a new source projection and fresh affected reviews. A context-only match may remain a disclosed hard case when full pair evidence is insufficient; avoid claiming it is an unambiguous pair-only target.
5. Validate final structure, cross-split and historical train/development overlap, source IDs, memberships and history invariants. Freeze the release, review receipts, adjudications, scripts and split manifest. No automated structural check alone grants qualification.

A reviewer must not review their own authored libraries. This is separate-agent review, not human review or proof of independent error distributions; agents share model capabilities and instructions. Only 576 of 9,120 pairs get direct pair-first review, although all 960 source memberships get a second context pass. Report that coverage honestly. Root may request an additional bounded adjudication on disputed cases.

## Checkpointing

Each authored library and each review phase is saved separately. Pause on user request at the next small boundary; no training state exists in P1. Preserve partial work and report exactly what remains. Before projecting/releasing, require at least 10 GiB free and less than the 4 GiB new-experiment cap. No deletion of prior artifacts.
