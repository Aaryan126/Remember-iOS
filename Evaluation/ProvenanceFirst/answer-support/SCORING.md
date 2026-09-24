# Primary scoring and limitations

Recorded before any verifier generations. This supplements the frozen contract;
it does not change corpus labels, accepted answer spans, retrieval, or pilot gates.

Primary correctness is **reviewed-span correctness**, a conservative measure:
the verdict must match, each citation must contain an independently reviewed
support passage from the correct source/revision, and the answer must match an
accepted verbatim span in at least one cited passage. Additional valid citations
may express that same fact differently; they need not repeat the answer wording.

A shorter quote can genuinely support an answer but fail this strict passage
check. For example, a source sentence approving a 5 cm allowance can support a
shorter quotation naming that allowance. Without separately reviewed evidence
spans, we cannot automatically distinguish this from dropping an important
negation, entity or time qualifier. Such supported-answer cases receive the
diagnostic `unreviewed_support_span` when their evidence identity and accepted
answer match but the quotation is only a substring of a reviewed passage.
They remain failures in the primary denominator and gates, not automatic credit.
This diagnostic is not a finding that the shorter quotation is semantically valid.
Report these separately from established wrong-answer or reasoning errors.
Later review may explain a failure; it must not retroactively promote this screen.

If retrieval supplies only one side of a corpus-level disagreement, the packet
label can be `supported` while the corpus remains `conflicting`. A resulting
answer fails the end-to-end corpus metric. This does not establish that the
underlying disagreement has been resolved.

Stage A tests this scoring machinery and technical readiness only. Full raw-model
versus host-validated comparisons, R1 diagnostics and benchmark latency/memory
summaries belong to the separately approved Stage B and are not yet measured.
