# Scale execution and incomplete-workload incident

The unchanged scale configuration `404d9cd587c7ac3470fa703caf850aaed693442b3092001eb978607a79cc7771` ran on the paired iPhone 17, iOS 26.6.1, on 11 September 2026. Its manifest records launch at 12:10:05 Singapore time. Each scenario has a 600-second cooperative limit. The host wrapper was configured with a 2,100-second overall timeout.

| Workload | Observed outcome | Durable completed inputs | Elapsed scenario time | Peak sampled app memory |
| --- | --- | --- | --- | --- |
| 100 | Completed | 100/100 | 46.97 seconds | 95.23 MiB |
| 500 | In-process timeout | 372/500 | 600.07 seconds | 130.61 MiB |
| 1,000 | Host-stopped, incomplete | 200/1,000 | Not available | Not available |

The 500-item result records `CancellationError()`. Its one unavailable-vector observation includes an interrupted in-flight input and is not a language-capability measurement.

For the 1,000-item workload, the last console progress line was `ORGANIZATION_PROGRESS run=scale-1000-embedding-chronological-0 step=238/1000`. The console log stopped changing at 12:24:54 Singapore time. The run remained present at 12:32:28, with no further progress or in-process terminal result. Device checks showed a connected phone with no passcode required and the isolated probe process present. They did **not** prove that the app remained foregrounded or establish the cause of the stall.

At **12:32:38 Singapore time**, only the verified isolated `OrganizationProbe.app/OrganizationProbe` process was terminated by the host. This was a **post-hoc operational stop** after the nominal per-scenario deadline and a grace period, **before** the configured overall 2,100-second host timeout. It is not relabeled as a preregistered in-process timeout. The cause may lie in the workload, diagnostics, OS/service behavior, or lifecycle state; it was not isolated by this execution.

Final collection retained the raw scenario status `running` and its last durable active checkpoint at **200 inputs**. Scale checkpoints are spaced every 50 inputs in this workload, so the 238 logged completed captures and 200 durably checkpointed captures are different evidence. No terminal duration, peak memory, or complete embedding-availability telemetry exists for this scenario; none is inferred from the previous workload. The wrapper exited with status 2 for incomplete/non-success coverage. A subsequent process-list check confirmed the probe was no longer running.

Evidence:

Final scale archive SHA-256: `ce415f9c391795900fc8f0cfb4e537d4869606dece6cf89fcc65b3af0b5f8dda`. Preserved console SHA-256: `b5d9f9f5e0dd2920fa96c68583100ab31f7b310a99c659d7e9da4bebb6ebfd69`.

- [Final collected scale archive](../results/scale-terminal-2026-09-11.json.gz): raw statuses remain unchanged; the filename describes the final collection, not successful terminal status of every scenario.
- [Preserved console log](../results/scale-console-2026-09-11.log): retains the final 238/1,000 progress line and collection summary.
- [Earlier checkpoint](../results/scale-checkpoint-02-2026-09-11.json.gz): retains the completed 100-item workload, 500-item timeout, and then-active 1,000-item attempt.

No production code, workload size, labels, or timeout values were tuned during this run. The personal Remember app and vault were not touched. All 144 core scenarios are independently complete. This incident limits the performance conclusion: the instrumented 1,000-item workload did not complete, and further lifecycle/deadline profiling is needed before attributing its stall to the production grouping algorithm. A future retry must preserve this evidence and use a new output artifact; it must not erase this failure or be presented as the original attempt.
