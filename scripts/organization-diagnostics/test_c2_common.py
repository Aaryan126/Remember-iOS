"""Cross-process worker lifecycle checks on temporary synthetic work units."""

import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import unittest

import c2_common as c


SCRIPTS = Path(__file__).resolve().parent
WORKER_FIXTURE = r'''
import json
from pathlib import Path
import sys
import c2_common as c

c.RUN = Path(sys.argv[1])
# Resource limits have separate operational checks; this fixture isolates control.
c.space = lambda planned=0: {"plannedBytes": planned}
mode = sys.argv[2]
try:
    if mode == "pause":
        print(json.dumps(c.request_pause()), flush=True)
    else:
        with c.worker(resume=mode == "resume"):
            first = c.RUN / "units/first.json"
            if first.exists():
                payload = c.read_unit(first)
                assert payload == {"id": "first", "value": 42}
                reused = True
            else:
                c.unit(first, {"id": "first", "value": 42})
                reused = False
            print(json.dumps({"state": "first-saved", "reused": reused,
                              "sha256": c.digest(first)}), flush=True)
            if mode != "resume":
                assert sys.stdin.readline().strip() == "boundary"
            c.boundary("after-first-unit")
            c.unit(c.RUN / "units/second.json", {"id": "second", "value": 84})
            print(json.dumps({"state": "complete", "firstSHA256": c.digest(first)}), flush=True)
except c.Paused as error:
    print(json.dumps({"state": "paused", "phase": str(error)}), flush=True)
except RuntimeError as error:
    print(json.dumps({"state": "rejected", "error": str(error)}), flush=True)
    sys.exit(3)
'''


class CommonTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="c2-control-test-")
        self.addCleanup(self.temporary.cleanup)
        self.run_path = Path(self.temporary.name) / "isolated-run"

    def start(self, mode):
        process = subprocess.Popen([sys.executable, "-c", WORKER_FIXTURE, str(self.run_path), mode],
                                   cwd=SCRIPTS, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, bufsize=1)
        self.addCleanup(self.stop, process)
        return process

    @staticmethod
    def stop(process):
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)

    def line(self, process):
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            self.assertTrue(selector.select(timeout=5), "Worker did not reach expected bounded unit")
        line = process.stdout.readline()
        self.assertTrue(line, "Worker exited before emitting expected state")
        return json.loads(line)

    def finish(self, process, command=None):
        stdout, stderr = process.communicate(input=command, timeout=5)
        self.assertEqual(stderr, "")
        return [json.loads(line) for line in stdout.splitlines() if line]

    def test_cross_process_pause_resume_preserves_saved_unit(self):
        worker = self.start("start")
        first = self.line(worker)
        self.assertFalse(first["reused"])
        saved = self.run_path / "units/first.json"
        first_bytes = saved.read_bytes()
        first_mtime = saved.stat().st_mtime_ns
        controller = self.start("pause")
        requested = self.finish(controller)
        self.assertEqual(controller.returncode, 0)
        self.assertEqual(requested, [{"pauseRequested": True, "safeToClose": False}])
        marker = self.run_path / "control/pause-requested.json"
        pause_hash = c.digest(marker)
        paused = self.finish(worker, "boundary\n")
        self.assertEqual(worker.returncode, 0)
        self.assertEqual(paused, [{"state": "paused", "phase": "after-first-unit"}])
        self.assertFalse((self.run_path / "units/second.json").exists())
        checkpoints = list((self.run_path / "pauses").glob("*.json"))
        self.assertEqual(len(checkpoints), 1)
        self.assertEqual(c.read(checkpoints[0]), {"phase": "after-first-unit", "state": "saved-boundary"})

        resumed = self.start("resume")
        receipts = self.finish(resumed)
        self.assertEqual(resumed.returncode, 0)
        self.assertEqual(receipts[0], {"state": "first-saved", "reused": True, "sha256": first["sha256"]})
        self.assertEqual(receipts[1], {"state": "complete", "firstSHA256": first["sha256"]})
        self.assertEqual(saved.read_bytes(), first_bytes)
        self.assertEqual(saved.stat().st_mtime_ns, first_mtime)
        self.assertEqual(c.read_unit(self.run_path / "units/second.json"), {"id": "second", "value": 84})
        self.assertFalse(marker.exists())
        resumptions = list((self.run_path / "resumptions").glob("*.json"))
        self.assertEqual(len(resumptions), 1)
        self.assertEqual(c.read(resumptions[0]), {"pauseRequestSHA256": pause_hash})

    def test_exclusive_worker_rejects_concurrent_process(self):
        first_worker = self.start("start")
        self.line(first_worker)
        duplicate = self.start("resume")
        rejected = self.finish(duplicate)
        self.assertEqual(duplicate.returncode, 3)
        self.assertEqual(rejected[0]["state"], "rejected")
        self.assertIn("Another C2 worker is active", rejected[0]["error"])
        self.assertFalse((self.run_path / "units/second.json").exists())
        self.assertEqual(self.finish(first_worker, "boundary\n")[-1]["state"], "complete")
        self.assertEqual(first_worker.returncode, 0)

    def test_sigterm_defers_stop_until_saved_boundary(self):
        worker = self.start("start")
        first = self.line(worker)
        worker.send_signal(signal.SIGTERM)
        paused = self.finish(worker, "boundary\n")
        self.assertEqual(worker.returncode, 0)
        self.assertEqual(paused, [{"state": "paused", "phase": "after-first-unit"}])
        self.assertEqual(c.digest(self.run_path / "units/first.json"), first["sha256"])
        self.assertFalse((self.run_path / "units/second.json").exists())
        resumed = self.start("resume")
        self.assertEqual(self.finish(resumed)[-1]["state"], "complete")
        self.assertEqual(resumed.returncode, 0)

    def test_corrupt_unit_rejected_before_resume_skip(self):
        path = self.run_path / "units/first.json"
        c.unit(path, {"id": "first", "value": 42})
        # Deliberately corrupt a test-owned work unit; production units stay immutable.
        saved = c.read(path)
        saved["payload"]["value"] = 99
        path.write_text(json.dumps(saved))
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            c.read_unit(path)
        resumed = self.start("resume")
        stdout, stderr = resumed.communicate(timeout=5)
        self.assertNotEqual(resumed.returncode, 0)
        self.assertEqual(stdout, "")
        self.assertIn("Work-unit checksum mismatch", stderr)
        self.assertFalse((self.run_path / "units/second.json").exists())

    def test_conflicting_publication_rejected_identical_retry_preserved(self):
        path = self.run_path / "units/example.json"
        c.unit(path, {"value": 1})
        original = path.read_bytes()
        original_mtime = path.stat().st_mtime_ns
        c.unit(path, {"value": 1})
        self.assertEqual(path.stat().st_mtime_ns, original_mtime)
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            c.unit(path, {"value": 2})
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(c.read_unit(path), {"value": 1})


if __name__ == "__main__":
    unittest.main()
