# Exposed regression cases — not fresh evaluation

Keep the existing C5/C6 and iOS 27 quality-continuation artifacts unchanged. In
checkpoint 2, report their results separately from the new development/evaluation
libraries; do not mix their denominators or call them held out.

Named behaviors retained in checkpoint-1 validator tests:

- **Shared rota / bridge:** a source can be assigned to both projects without
  merging project identities (`test_archive_does_not_revise_source` checks retained
  dual membership; native replay checks actual cluster projections).
- **Unresolved referent before correction:** uncertainty keeps a singleton without
  inferring a new project, then an explicit correction resolves it
  (`test_unresolved_retains_singleton_not_project`).
- **Reference before/after:** no future revision/correction may enter an earlier
  packet (`test_exact_future_quote_rejected`, `test_prefix_packet_has_no_future_or_labels`).
- **Corrections survive later events:** pinned authority is not lost during revision
  or archive (`test_correction_authority_survives_later_event` plus native invariants).

These are deterministic representation regressions, not reruns of old semantic
model predictions. Original exposed source evidence is in
`Evaluation/OrganizationDiagnostics/c5/authored-families.json` and the saved
`Evaluation/iOS27/quality-continuation/` report/predictions. The old harbour-radio
ambiguity was identified during review and excluded from the fresh evaluation
split by replacing its entire scenario family before freezing.
