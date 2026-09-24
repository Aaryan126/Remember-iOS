# Approved simulator cleanup — 24 September 2026

The user approved the exact five directories and the stated diagnostic loss:

- `Evaluation/ProvenanceFirst/runs/unified-search/build`
- `Evaluation/ProvenanceFirst/runs/source-browser-ui/build/Build/Products/Debug-iphonesimulator`
- `Evaluation/ProvenanceFirst/runs/source-browser-media/build/Build/Products/Debug-iphonesimulator`
- `Evaluation/ProvenanceFirst/runs/source-browser-ui/1789818419334524000.xcresult`
- `Evaluation/ProvenanceFirst/runs/source-browser-ui/1789824035287035000.xcresult`

All five `rm -r` deletions succeeded. Available space rose from 11,358,760 KiB to
12,267,448 KiB: about 887 MiB net (0.87 GiB), versus measured directory allocation
of about 1.05 GiB. Shared APFS blocks and unrelated filesystem activity can make
the net change differ from directory totals.

The three simulator build directories are regenerable, including their copied
model assets. The two old failed/interrupted test-result bundles are permanently
removed, not in Trash; their original diagnostic attachments cannot be recovered
from this project. Their text logs/reports and recent passing results remain.

Original model assets, app source, datasets, private phone backups, signed iPhone
products and reused device module cache were retained. No outside-project paths,
Git metadata or other folders were deleted. This approval is exhausted. Future
simulator checks must rebuild the removed shared simulator cache.
