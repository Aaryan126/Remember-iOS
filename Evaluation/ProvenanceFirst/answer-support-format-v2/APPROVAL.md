# Approved v2 preparation and technical-control checkpoint

19 September 2026. The user agreed to the recommendation and further implementation
after the explicit proposal for independently reviewed answer forms, scorer tests,
and at most eight fresh local checks. The cumulative request ceiling is 145,
including the preserved v1 request. This checkpoint permits only eight new controls;
Stage B still requires separate approval.

Preserve v1 code, data, labels, raw outputs and failed score. Use separate v2 code,
artifacts and reservations. Keep the original disk baseline, approved 21 GiB growth
allowance and 10 GiB reserve. No paid API, phone test, downloads, model/prompt search,
production integration, cleanup or Git-state changes. Stop at the first failed
control or after all eight checks, then report for user review. Pause/resume required.

Change only answer granularity in the prompt and corresponding generated-schema
description: concise verbatim extract rather than mandatory minimal span. Fields,
limits, evidence criteria, model and decoding remain unchanged. If the old binary's
schema description still requires minimality, build an isolated copy with that
description updated rather than silently leaving conflicting instructions.
