# Scope prototype provenance and applicability

The `c6_scope_prototype` coding agent implemented this control using only root AGENTS.md,
the review contract and its own invented fixtures. It was instructed not to open C5/C6
packets, authored text, labels, reviews or results. It returned these hashes before any
model execution:

- `c6_scope.py`: `3c83ebcf3b86386cdf675a5f4a8d068eeaafb2e1e66cf9d4bc12805d6b33f5da`
- `test_c6_scope.py`: `6a95a02fbfc56588fdb37ca3ccd4aa1eb5daed30b5a5a2becb137d43539cb458`

This is a controlled-English grammar feasibility control, not a natural-language
reasoner or an on-device neural verifier. It requires explicit source-to-project
bindings and direct project relations; any unsupported sentence triggers abstention.
Quoted names alone are insufficient, and exclusive memberships are required for
separation. It should not be broadened after corpus results are visible.

These restrictions may yield zero coverage on natural prose. If so, report it as an
inapplicable text-understanding prototype, not as perfect precision, a model regression,
or evidence that project-conflict detection itself is impossible. A future semantic
extractor would be a materially different candidate requiring a new frozen comparison.

The independent reference reviewers are annotators, not the implementation or runtime
of this control. No claim of local-device execution of the review agents is made.
Shared model-family/systematic annotation limitations remain despite separate agents.
