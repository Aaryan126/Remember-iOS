# Development author corrections after independent review

Original reviewed SHA-256: `098fc314bfdcd99e9c80e63d2554624915345d45a256d4656be6449eeb6e1ad2`.

The initial review remains unchanged. These revisions address its semantic errors, causal-dependency warnings, and selected naturalism problems. No model predictions or scores were inspected. All twelve domains, two project roots per library, twelve events, and four tasks remain intact.

## Semantic adjudications

- `dev06/e08,e12`: the expedition's return/completion is real project history. The return note and its revision now have both expedition and lending memberships; revision text retains the return/completion facts and also records inventory state. The independent sleeve-inspection source remains lending-only.
- `dev01/q4`, `dev02/q2`, `dev08/q1`, `dev09/q4`, `dev10/q1`: keep the broad historical questions and include additional equally relevant source/revision evidence. No question was narrowed merely to force an obsolete citation. `expectedEvidence` is a relevant set, not a requirement to retrieve every alternative at once.
- `dev05/q1`: keep the broad permissions question and include both individual permission records in addition to the joint registrar memo.
- `dev05/q2`: ask which image and permission type the speaker meant. This is a truly unknown referent, unlike asking whether the fragment grants publication rights.
- `dev04/q2`: add the safety-marker condition to the planned Tuesday evidence, rather than imply unconditional excavation authorization.

## Causality and naturalism

Added dependencies only for derived changes, synchronized revisions, observations after decisions, handoff/return progression, and conclusions after evidence. The reverse-ready schedule still differs from chronological order for every library. This is causal reordering, not a late-ingestion stress test.

Removed selected phrases that explicitly told the classifier the intended relationship (for example 'not a second outing' or 'do not split the experiment'). Kept factual separate authorities, specific work orders, real user corrections, conditional approvals, and evidence of obsolete documents. Some sources still contain unusually explicit contrasts; this remains an agent-authored contract screening suite, not representative quality evidence.

Audio/photo/video text that combines extraction and observations is now explicitly marked `Capture annotation:` where edited, with matching locators. Such annotations are fictional observed capture metadata, not model-generated verdicts or raw ASR claims. Neither version evaluates actual media extraction.

## Complete changed locations

Fields below are compared with the original reviewed authoring snapshot; `gold` includes updated citations/rationales or the explicitly noted membership correction.

- `dev01/e02`: `text`.
- `dev01/e04`: `text`.
- `dev01/e05`: `text`.
- `dev01/e07`: `dependsOn`.
- `dev01/e12`: `dependsOn`, `text`, `locator`, `gold`.
- `dev01/q4`: `expectedEvidence`, `rationale`.
- `dev02/e01`: `text`.
- `dev02/e05`: `text`, `locator`.
- `dev02/e09`: `text`.
- `dev02/e11`: `dependsOn`.
- `dev02/q2`: `expectedEvidence`, `rationale`.
- `dev03/e03`: `text`.
- `dev03/e04`: `text`, `locator`.
- `dev03/e05`: `text`.
- `dev03/e07`: `text`, `locator`.
- `dev03/e10`: `dependsOn`, `text`.
- `dev03/e12`: `dependsOn`, `text`.
- `dev04/e01`: `text`.
- `dev04/e02`: `text`.
- `dev04/e03`: `text`, `locator`.
- `dev04/e07`: `text`.
- `dev04/e12`: `dependsOn`, `text`.
- `dev04/q2`: `expectedEvidence`, `rationale`.
- `dev05/e04`: `text`.
- `dev05/e05`: `dependsOn`, `text`.
- `dev05/e07`: `text`, `locator`.
- `dev05/e09`: `text`, `gold`.
- `dev05/e10`: `dependsOn`.
- `dev05/e12`: `dependsOn`, `text`, `locator`.
- `dev05/q1`: `expectedEvidence`, `rationale`.
- `dev05/q2`: `question`, `rationale`.
- `dev06/e02`: `text`.
- `dev06/e04`: `text`, `gold`.
- `dev06/e05`: `dependsOn`.
- `dev06/e06`: `dependsOn`, `text`.
- `dev06/e07`: `dependsOn`, `text`, `locator`.
- `dev06/e08`: `dependsOn`, `text`, `gold`.
- `dev06/e09`: `text`, `locator`.
- `dev06/e10`: `dependsOn`.
- `dev06/e12`: `dependsOn`, `text`, `gold`.
- `dev07/e02`: `text`.
- `dev07/e04`: `dependsOn`, `text`.
- `dev07/e06`: `text`.
- `dev07/e08`: `text`.
- `dev07/e10`: `text`, `locator`, `gold`.
- `dev07/e12`: `dependsOn`.
- `dev08/e02`: `text`.
- `dev08/e03`: `text`.
- `dev08/e05`: `text`.
- `dev08/e08`: `text`, `locator`.
- `dev08/e10`: `dependsOn`.
- `dev08/e12`: `dependsOn`, `text`, `locator`.
- `dev08/q1`: `expectedEvidence`, `rationale`.
- `dev09/e01`: `text`.
- `dev09/e03`: `text`.
- `dev09/e05`: `dependsOn`.
- `dev09/e06`: `text`, `locator`, `gold`.
- `dev09/e09`: `text`.
- `dev09/e10`: `dependsOn`, `text`.
- `dev09/e12`: `dependsOn`.
- `dev09/q4`: `expectedEvidence`, `rationale`.
- `dev10/e01`: `text`.
- `dev10/e03`: `text`.
- `dev10/e07`: `dependsOn`, `text`, `locator`.
- `dev10/e09`: `text`, `locator`.
- `dev10/e11`: `text`, `gold`.
- `dev10/q1`: `expectedEvidence`, `rationale`.
- `dev11/e03`: `text`, `locator`.
- `dev11/e04`: `dependsOn`, `text`.
- `dev11/e05`: `dependsOn`, `text`.
- `dev11/e06`: `dependsOn`.
- `dev11/e07`: `dependsOn`, `text`.
- `dev11/e12`: `dependsOn`, `text`.
- `dev12/e01`: `text`.
- `dev12/e03`: `text`, `gold`.
- `dev12/e04`: `dependsOn`.
- `dev12/e05`: `text`.
- `dev12/e06`: `dependsOn`, `text`, `gold`.
- `dev12/e08`: `text`, `locator`.
- `dev12/e10`: `dependsOn`, `text`, `locator`.
- `dev12/e12`: `dependsOn`, `text`.

## Verification

### Second independent review: three bounded corrections

Reviewed input SHA-256: `09992feb5dccf0ab6e3d51498f53a9281900a5aa28ceab788d0099c0c49d7dd2`; retained review: `reviews/development.rereview.json`.

- `dev06/e02 text`: restored a general gear-lending inventory/service root. Removed the newly introduced expedition reservation transaction; the concrete GR-9 checkout stays at `e06`, where both project memberships are represented. Root gold and its exact quoted mandate are unchanged.
- `dev06/e11 dependsOn`: added `e08` so a correction referring to the completed expedition follows its return/completion record.
- `dev09/e08 dependsOn`: added `e03` so the protocol revision preserving earlier observations follows those observations.

No other fixture text, labels, tasks, or dependencies changed in this second correction pass. Structural validation and all twelve nontrivial alternative schedules passed again; independent final review remains required.

Additional reverse-schedule audit: `dev02/e09` now follows the red-marker trial `e06`; `dev03/e05` follows the electrician visit plan `e03`; `dev04/e10` clearance follows the pre-intervention flood observation `e03`; `dev06/e04` weather contingency follows the bulletin `e03`; and `dev10/e11`, explicitly a purchase after the outreach visit, follows that visit `e03`. These add `dependsOn` changes to the location list above and avoid representing later-world continuations as independent late arrivals.

`PYTHONDONTWRITEBYTECODE=1 python3` with `fixtures.validate_split(fixtures.load(...))` passed after the corrections. Exact quotations, observed revisions, source/project dependencies, prefix task validity, source-state retention, and minimum coverage were checked. Reverse-ready schedules were inspected and remain nontrivial. Independent semantic re-review is still required; structural validation is not semantic approval.
