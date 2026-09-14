# C7 report correction

The frozen REPORT.md states a median native request time of **2.63 seconds**. The
standard even-sample median, averaging observations 56 and 57 of 112 sorted timings,
is **2.6131240835 seconds**, which rounds to **2.61 seconds**.

Those observations are 2.5903920829 and 2.6358560841 seconds. The original report was
already bound by completion receipt
`ba2bb8124f80566ffcce228812430fda9c69b250348a570b8a409e2715dcec02`, so it is preserved
unchanged and this correction is recorded separately. Mean, p95, maximum, predictions,
quality metrics and the no-go decision are unchanged. No inference was repeated.
