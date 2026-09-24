# Evaluation author corrections after initial review

Author: `/root/pf_author_eval`. Date: 17 September 2026.

Reviewed input: `reviews/evaluation.initial.json`, input SHA256
`f51bff0d02c06100afb21a46d525cfccd1a538773efc6f93e1cfcba81e9238a9`.
This records author changes, not independent approval. The root retained the
reviewed original. No development fixtures, model outputs or predictions were read.

## Substantive corrections requiring independent re-review

- Replaced **eval05** completely. The exposed oral-history/bulletin mechanism is
  removed from the prospective evaluation set. Its replacement distinguishes
  **French carton artwork localization** from **shipping-carton barcode
  certification**: one physical carton and edition handoff support separate
  deliverables and acceptance authorities. Version-three language acceptance does
  not inherit version-two physical-sample certification. The replacement has twelve
  events, four tasks, explicit dependencies, exact evidence and prefix-limited
  ambiguity; no old harbour dialogue remains.
- **eval07:** physical-object custody transfer is now explicitly distinct from
  unfinished caption proofreading and documentation delivery. The exhibition label
  no longer implies those restoration tasks are complete. Updated the handoff
  evidence/task wording and added the documentation precursor dependency.
- **eval08/e11:** the signed-receipt continuation now depends on e03, which first
  records the outstanding receipt.
- **eval10/q2:** added the later approved side-by-side proof as eligible current
  evidence alongside the revised layout instruction. **q3** now explicitly asks
  for the original superseded instruction artifact, not any retrospective account.
- **eval11/q2:** added the later prototype-context confirmation as eligible current
  evidence. **q3** explicitly requests the original packing-note revision. The
  base-game ferry nickname is established in e02, before the ambiguous forwarded
  memo, and that memo depends on this precursor.
- **eval12/q2:** added the still-valid checked sign proof alongside the later
  coordinator confirmation. **e09** now depends on both that proof and the older
  brochure to which it responds.

## Cue and provenance-quality improvements

- Rewrote ambiguous capture text across eval01–04 and eval06–12 so voices sound
  like actual clipped messages instead of narrating an analyst's uncertainty
  verdict. Missing identifiers remain missing; no later clarification is imported
  into an earlier prefix. Exact quotation evidence was refreshed accordingly.
- OCR crops explicitly identify capture-author annotations rather than implying
  crop-quality commentary appeared on the photographed document. Locator labels
  distinguish speech, observed frames, OCR and author ASR-quality annotations.
- Retained factual commissioning boundaries and approvals where they establish
  actual project identity. The aim is not to erase legitimate source evidence.

## Remaining limitations

These are agent-authored fictional contract fixtures. They still have a controlled
four-task mix and many explicit project codes/commission boundaries; they are not
representative unannotated personal libraries. Revised ambiguous wording and
eligible evidence sets require independent re-review. Passing the ideal-label
replay proves representation only, not inference quality, calibrated confidence,
actual OCR/ASR performance, or real-user preference alignment.

## Author validation

- JSON parsing succeeds.
- `fixtures.validate_split(load(Path("Evaluation/ProvenanceFirst/authored/evaluation.json")))`
  succeeds for twelve libraries, 144 events and 48 tasks.
- No inference, downloads, paid APIs, personal data or Git mutations performed.
