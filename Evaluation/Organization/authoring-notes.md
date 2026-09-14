# Original synthetic organization corpus: author notes

These notes, `author_corpus.py`, and `author-labels.json` contain author knowledge and must not be supplied to a blind reviewer or the production runner. Reviewers receive only `inputs.json` and `CONTRACT.md` (plus applicable repository instructions). The author read the contract and repository rules, and did not inspect production clustering code, policy thresholds, old fixtures, model predictions, or reviewer decisions.

The corpus comprises 360 manually composed fictional text memories, serialized as twelve independent libraries of thirty. No private vault data, real contact information, copied public passages, or external corpus text was used. The author is an AI agent; its exact runtime model identifier was not available to the author. Candidate labels are author judgments, not independent review or human validation.

| Library | Split | Language slice | Distinct setting |
| --- | --- | --- | --- |
| l01 | development | English | Neighborhood infrastructure proposals and volunteer work |
| l02 | development | English | Six separate university assignments |
| l03 | development | English | Six distinct personal trips |
| l04 | development | English | Independent arts commissions, editions, and events |
| l05 | development | English | Small software prototypes |
| l06 | heldout | English | Museum conservation, object records, and loan preparation |
| l07 | heldout | English | Agricultural experiments and field operations |
| l08 | heldout | English | Harbor surveys, vessel maintenance, and operational exercises |
| l09 | heldout | English | Distinct community sports instruction programs and events |
| l10 | heldout | English | Observatory measurements and instrument tasks |
| l11 | development | Multilingual: Spanish and English | Culinary teaching, food service, and bilingual recipe editing |
| l12 | heldout | Multilingual: French and English | Archaeological field investigations and contextual archiving |

Every library has six primary contexts with 2, 3, 3, 4, 5, and 7 single-membership sources, respectively; three explicit bridge sources with two memberships apiece; and three unrelated singleton notes. The resulting nine candidate threads must remain separate even where a source belongs to two. Bridges document a real shared resource, comparison, or scheduling dependency; they do not imply a merged project. Positive relationship labels use those bridge sources as evidence. Other candidate relationship pairs are explicitly negative at the specific continuing-context granularity. Reviewers may challenge these judgments from the text.

Items include plans, receipts and costs, design choices, meeting decisions, revised dates, erroneous initial interpretations, negative results, and naturally described duplicate reminders. Later corrections retain earlier observations as part of the same project. Closely named but distinct contexts include two Mere visits, two Brisa workshops, two Valon trenches, and similarly named prototype or artwork projects. Non-project singleton metaphors reuse vocabulary such as repair, harbor, running, stars, and wells without providing evidence of project membership. Several follow-up notes identify their context through concrete referents rather than repeating its full title.

Each development and heldout library uses different specific projects and source passages. No original, paraphrase, revision, duplicate reminder, or media family crosses the split. Recurring challenge types and general note forms are deliberate benchmark motifs, not claims of stylistic independence. The prose is relatively polished and consistently short; this is a limitation compared with messy real-world memories. Text-only and multilingual performance should be reported separately, and agent agreement should not be described as human validation.

Opaque item IDs are assigned after deterministic per-library shuffling. Inputs expose only required library split/slice metadata and item ID, text, kind, and timestamp. Natural project names occur inside the memories as ordinary evidence; hidden memberships and rationales never appear in input metadata. Synthetic epoch timestamps preserve each authored context's revision order and are independent of shuffled input order; they are fictional sequence anchors, not claims about real-world event dates. The corpus is not a forecast or a historical dataset.

Author rationales quote the opening source sentence as a concise evidence anchor. They are intentionally not hidden chains of reasoning. There are no author-marked ambiguous base items, because the author intended enough evidence to support the proposed boundaries; independent reviewers must still flag genuine uncertainty rather than defer to that intention.

The generator performs serialization only: its 360 source passages were manually authored. Regeneration is `python3 Evaluation/Organization/author_corpus.py`. It asserts twelve libraries, exact primary-context sizes, three bridges and three singletons per library, and a 20–65-word range. The completed corpus contains 11,255 whitespace-delimited words, with individual memories spanning 27–37 words. These counts are not a measure of linguistic difficulty or review completeness.

The author also checked complete and unique IDs, allowlisted input keys, epoch integer timestamps, split/slice counts, label coverage, exact membership counts, complete relationship pairs, valid evidence references, and unique source text. These are structural checks only. Semantic approval belongs to the independent review/adjudication workflow described in the contract. No application predictions were executed by the author.
