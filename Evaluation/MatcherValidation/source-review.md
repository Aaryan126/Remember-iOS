# P1 source-level review before model fitting

The root agent inspected all24 highest cross-split three-token-shingle overlaps from `runs/p1-01/source-audit.json`, with both source texts visible. This supplements automated checks; it is not an independent semantic-duplicate audit.

The largest overlap,0.154, is the generic phrase “keep the receipt until” in a rail refund and an unidentified receipt fragment. Other top matches contain ordinary administrative wording, spatial phrases, and two relay-entry corrections in different sporting stories. No inspected pair is an entity-renamed copy of a complete story or source. These recurring task motifs remain a limitation: declared story-family separation does **not** establish that every task type, topic or linguistic template is unseen at evaluation.

The old train/development plus P0-pilot screen covers520 previously inspected sources. No exact or>=0.85 shingle duplicate was found; the largest old/new overlap was0.056. Old test sources/labels were not parsed. Low lexical overlap does not prove semantic independence.

Authored thread counts vary: five libraries have three threads,22 have four,18 have five and three have six. There are nine longer100–160-word notes, distributed three per split. Most memories remain short: mean lengths are about20–25 words. This is primarily a short-memory-text benchmark, not a long-document, real OCR/ASR, multilingual or full-media benchmark.

Thread granularity is **concrete objectives/deliverables**, not automatically one thread per broad event or domain. A book's catalogue correction and its shipping task can be related without being the same objective. This is an agent-defined product policy; a real user might prefer broader grouping. Agent cross-review checks consistency with this policy but cannot establish real-user preference.

Related-but-separate cases are deliberately plentiful. Their engineered prevalence must not be presented as an estimate of production prevalence or used to compare raw old/new accuracy without a contemporaneous baseline. The primary later comparison will refit both the control and hybrid using the new fixed splits.

Pair-first/context reviews and adjudication remain separate evidence. Context can resolve a source's history membership without resolving every two-source comparison. Any adjudicated pair-only uncertainty override must be explicit and preserved alongside the contextual gold, never a silent rewrite of an authored narrative or a change made after model results.

## Final adjudication

All 131 recorded discrepancies received individual root-agent dispositions: seven source memberships, 23 thread-link sets and 101 sampled pair judgments. Seven fragments become identifiable in full-library context. Root inspection also removed one author/reviewer-consensus link: the dishwasher warranty case and new oven registration shared only a broad topic, not an appliance, claim or transaction. This additional correction is recorded separately; the original issue report and all author/reviewer evidence remain unchanged.

The resulting link sets differ from the authors' proposals in 22 libraries. The policy recognizes a supported common initiative, event, physical setup or material without merging its concrete objectives. Merely sharing a person, organization or broad field is insufficient. These contextual relatedness annotations remain judgment calls, not a verified ontology or proof that every omitted edge is semantically unrelated. In particular, a pair can be clearly **not the same objective** even when its related-versus-unrelated subtype needs the full library. Later false-related/false-unrelated breakdowns must retain this caveat.

All 35 sampled pairs whose contextual class changed were re-read against the final assignments and links, including seven that were not in the original pair-disagreement list. Eight pair-only uncertainty overrides preserve cases where even same-versus-not-same is not reliably identifiable from the two texts: four original disagreements plus four newly resolved-fragment comparisons. Their contextual memberships remain available for history fixtures. The remaining generated pairs do not receive this exhaustive pair-only sufficiency review; context-defined labels may still contain difficult or ambiguous pair-only targets.

The final pair labels differ from the authored projection on 630 of 9,120 pairs, mostly related/unrelated subtype corrections propagated from explicit link changes. None of these decisions uses a model score. The release retains both contextual gold and the pair-only overrides, so neither uncertainty handling nor author/reviewer disagreements are hidden.

The 48 history fixtures exercise a pure reference replay of memberships, revisions, explicit renames where present, and hypothetical incorrect-link/undo corrections. They do **not** test Remember's production persistence, clustering, UI or actual merge/undo implementation. This stage qualifies dataset readiness for the next experiment, not product or model readiness.
