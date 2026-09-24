# Answer support v1 — proposed experimental contract

19 September 2026. Planning only; not a shipped feature or a completed evaluation.
This supplements, but never replaces or relabels, the frozen relationship and
history-recovery experiments. Execution requires approval of [PLAN.md](PLAN.md).

## Product boundary

**Save anything. Recover the right context. See how your projects developed—with
evidence.** Finding a possibly relevant source and establishing an answer are
different operations. A verifier may withhold an answer, but must not remove the
retrieved sources from the browsing result. It never assigns, separates or merges
projects, modifies a memory, or invents missing history.

| State | Meaning | Proposed presentation, not implemented UI |
| --- | --- | --- |
| `supported` | Supplied evidence explicitly answers the requested fact, for the right entity and time, without an unresolved conflict in the packet | Short source extract, citation, and current/historical badge; no claim of external truth |
| `explicit_missing` | Evidence explicitly says the requested fact was not recorded, measured or identified | “This source says the detail wasn’t recorded,” with the exact passage |
| `conflicting` | Eligible evidence gives incompatible answers to the same requested fact, with no supported resolution | “These sources disagree,” showing both passages |
| `not_established` | The supplied passages do not establish an answer, or the relationship is ambiguous | “I couldn’t establish this from these sources”; keep sources available |
| execution error | Unavailable model, timeout, malformed or invalid evidence output | “Answer check unavailable”; keep sources available; do not count as successful abstention |

“Potentially related sources” is the independent retrieval layer, not a model
assertion that each source answers the question. Absence from the top-three packet
does not establish absence from the entire library. `explicit_missing` describes
what the cited source says, not what all memories or the real world contain.

## What qualifies as an answer

Judge the exact question against its eligible evidence at its event boundary:

- “Which tool number was recorded?” + “No tool number was recorded” is
  `explicit_missing`, not an answer containing a tool number.
- “Was a tool number recorded?” + the same source supports the negative answer.
  Do not implement a generic “contains no/not => abstain” shortcut.
- A deadline for another commission is not support for this commission, even if
  dates and vocabulary match. A suggested date is not an approved date.
- A newer unrelated mention does not supersede an older fact. An explicit revision
  can establish a change; current and historical requests use the specified scope.
- Two sources agreeing do not by themselves create a conflict. Two different
  answers about different times/entities do not necessarily conflict either.
- A missing measurement cannot be supplied from general knowledge or derived from
  incomplete inputs. This first screen excludes arithmetic and multi-hop synthesis.

## Input and output boundary

The input is a question, explicit `current`/`includeHistory` scope and up to three
unchanged native source-text chunks. Each chunk has a stable candidate ID,
source/revision, version/snapshot ID, locator and current/archive status. No
answerability label, expected answer, task category, ideal project assignment,
future event or model score enters the verifier prompt. Display order is fixed
by the retriever, never rearranged using gold labels.

The proposed structured output contains a verdict, an optional short **verbatim
answer span**, and up to three evidence references. Each reference identifies a
supplied candidate and supplies a verbatim supporting passage. No open-ended
answer synthesis, confidence percentage, web tool or external model call.

Host-side validation is separate from semantic scoring:

1. Validate the enum, known candidate IDs, lengths, cardinality and complete output.
2. Require exact supporting passages within their cited original chunks. For
   `supported`, the answer span must occur inside a supporting passage. Preserve
   negation, units, entity and temporal qualifiers; do not silently repair output.
3. Require evidence for `supported` and `explicit_missing`; `conflicting` needs
   two distinct, supplied supporting passages. `not_established` has no answer span.
4. Attach immutable provenance from the host index, not model-generated IDs or
   locators. Recheck scope/revision/event eligibility before displaying anything.
5. Reject invalid output as a recorded error. Never turn it into a correct abstention
   for the quality score. A valid quote alone **does not prove semantic support**.

Freeze concrete field/size constraints and one prompt before benchmark inference.
The first screen bounds each native chunk to the existing 800-character chunking
contract and uses at most three chunks. Never silently truncate an oversized packet
or drop qualifying evidence to make the prompt fit; record a context error instead.

Source text is untrusted data, including embedded instructions. The model has no
tools and cannot perform actions. Quoted instructions are never authority to change
the task. A factual-looking injected answer remains wrong if it does not support
the requested fact under the independently reviewed labels.

## Gold labels and semantic scoring

New fixtures receive separate **corpus-level** and **retrieved-packet-level** labels.
Corpus labels establish whether eligible stored evidence answers the question.
Packet labels establish what the fixed retriever actually supplied. This separates
retrieval misses from verifier errors without erasing either from end-to-end recall.

Reviewers annotate acceptable minimal answer spans/variants, all supporting
passages, missing-information passages and conflicting evidence as applicable.
Multiple genuinely supporting passages may receive credit; we do not impose one
gold source when several are valid. Review covers every eligible passage, not just
the source the author intended. Extra answer-bearing text must be included in gold
or removed before freeze, without reference to model predictions.

An exact but irrelevant span is incorrect. A long quoted passage that never
answers the question is incorrect. No model-under-test self-grading and no fuzzy
LLM judge in the primary metric. Use pre-reviewed accepted spans/variants and
evidence identities. Unexpected plausible variants are logged for later review;
do not edit the frozen primary score after seeing predictions.

Errors, unsupported answers, wrong answers, false “missing” claims and invented
conflicts remain distinct outcomes. Always report all denominators and source-only
fallback availability. Abstaining on every question cannot qualify.

## Relationship to existing code and results

`Remember/Remember/LocalAI.swift` already checks verbatim quote existence, and
`AskRememberView.swift` already distinguishes sources-only responses. These are
reuse candidates, not proof that this semantic contract is implemented. Inspect
the current pipeline before any later integration; do not assume an existing
assistant service is local-only just because its type name says “LocalAI”.

The previous B/C no-go remains unchanged. This new task cannot qualify automatic
membership, outside-River suggestions, or the old recovery gates by changing their
meaning. It tests an additional answer layer over a still-visible source list.
