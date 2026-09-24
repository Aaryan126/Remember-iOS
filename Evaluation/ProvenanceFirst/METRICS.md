# Frozen measurement definitions

Checkpoint 1 measures representation and replay only. The following definitions
prevent reinterpretation of checkpoint-2 metrics after seeing evaluation outputs.

- Query gold is a set of eligible `(sourceId, revision)` evidence identities; multiple
  quotes from the same identity do not multiply its weight. Expected evidence need
  not all be required together to formulate an answer: this is retrieval coverage,
  not a generative answering or minimal-support-set benchmark.
- Precision@3 is relevant returned identities / returned identities among at most
  three unique results. An empty list has undefined precision, not 100%. Report
  aggregate returned counts, query-level coverage and the distribution of zero/one/
  two/three results so abstention cannot conceal low usefulness.
- Recall@3 is relevant returned identities / all eligible identities for answerable
  queries. An empty list scores zero. Unanswerable queries are excluded from recall
  and separately score whether the system asserts unsupported relevance.
- Report macro recall by library and task mode, along with pooled counts. Histories
  and alternative orders are correlated, not independent new libraries. A historical
  task asks about a past state or explicitly requests an old source/version. Current
  revisions can be eligible when they directly evidence the requested past state;
  report genuinely version-specific tasks separately. Current tasks cannot silently
  receive credit for a stale revision or archived source.
- An automatic attachment is evaluated as a source-to-project membership edge.
  A multi-project source can have two correct edges; one right edge does not excuse
  a wrong one. Also report exact membership-set recovery and shared-source success.
- Automatic precision includes unsupported edges on unresolved sources as errors.
  Correct-attachment retention compares candidate correct edges with reference A's
  correct edges on the same prefixes; show absolute counts and missed edges too.
- Unsupported-decision rate is the fraction of unresolved capture opportunities
  receiving any automatic membership assertion. Keeping a singleton is not a
  same-project or separate-project semantic assertion.
- Classifier scores are ranking/eligibility scores, not calibrated probabilities.
  Dev threshold selection has three prespecified candidates only. If precision
  ties on coverage, choose the stricter threshold. No threshold changes on evaluation.
- New automatic candidate evaluation also requires at least 20 observed automatic
  attachments; fewer is inconclusive, never a precision pass. Query/edge correlations
  must be disclosed; point targets alone do not constitute release qualification.

All task source content and corrections are observed-prefix limited. Future
clarifications, gold project titles/memberships, rationale, dependency metadata,
review verdicts and expected evidence must not enter scorer/retriever packets.
