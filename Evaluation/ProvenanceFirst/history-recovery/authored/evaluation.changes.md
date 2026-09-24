# Evaluation review corrections

Author: /root/history_author_eval. Date: 19 September 2026.

Initial independently reviewed JSON SHA256:
`e581d28380ef3ca9773782e70da09f618bcd635df2df95f0453ac53d61fabf66`.

Corrected JSON SHA256:
`c586e946b72bac762fdda3c25690f53411d3f8bf66cd5ef26eb82bc1aae484fb`.

The review in `../reviews/evaluation.initial.json` is preserved unchanged.
These corrections address authoring and evidence-contract findings only; no
model outputs, predictions or performance information were available.

- Replaced contradictory generic unresolved-capture rationales in eval01–05,
  eval08–09 and eval11 with the specific missing identifying context. Their
  dispositions, empty evidence and later explicit corrections are unchanged.
- Reworded uncertain questions in eval02, eval05, eval07 and eval08 to request
  unavailable physical values (humidity, concentration, route length and join
  angle), avoiding questions whose premises are refuted by explicit statements
  that a reading or assignment does not exist.
- Replaced eval04's prospective receipt-signer question with the unavailable
  bassoon-case serial number. Replaced eval10's explicitly unspecified hold
  duration question with the unavailable train B housing bore diameter. The
  six changed questions retain empty evidence and current scope.
- Added eval08/e09's dependency on e03, whose C27 identifier is required by the
  anatomy-chart annotation.
- Redesigned eval12 after cross-split adjudication. An initial whole-batch
  booking now encounters a cassette compatibility manifest, and a single
  amendment splits the batch into compact-insert and long-insert handoff groups.
  The grouping has its own document-wallet continuation. There is no stale
  calendar quotation and no second schedule amendment. The other seed batch has
  a distinct carrier insert while genuinely sharing the trolley. The original
  note remains superseded and active; the historical question explicitly asks
  for its original whole-batch booking. This avoids treating the unchanged
  Tuesday time for only part of the batch as equivalent original evidence.

Validation rerun successfully: existing `validate_split` and read-only
`validate_library` snapshot assertions for mode coverage, explicit scopes,
unanswerable empty evidence, six archived unrevised historical targets, and six
superseded active-note targets. All 12 libraries still have 12 events and four
tasks. eval12 now has 11 captures and one revision. Existing split-wide coverage
minimums still pass. Independent re-review is required before sealing.
