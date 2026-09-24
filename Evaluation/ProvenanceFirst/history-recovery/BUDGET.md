# Resource amendment — approved 19 September 2026

User approved **18 GiB conservative growth**, keeping the original shared
`Evaluation/ProvenanceFirst/resources.json` baseline and **10 GiB free reserve**.
Approval reply: “Yes approved”. Applies to the history-recovery checkpoint only.
Historical 4/5/8 GiB stop receipts and frozen experiments remain unchanged.

At the preceding blocked preflight: 28,394,385,408 bytes free;
16,568,582,144 bytes conservative growth; 447,193,088 bytes scoped files;
2,432,847,872 bytes registered simulator growth. The conservative measure includes
whole-Mac free-space decline; it is not attribution of all usage to this experiment.

Do not reset the baseline or delete files automatically. New code/artifacts remain
under the existing accounted `scripts/provenance-first` and
`Evaluation/ProvenanceFirst` trees. Use the already registered isolated simulator.
