import unittest
import hashlib
from pathlib import Path
import tempfile
from unittest.mock import patch

import as_approved as a


class ResourceAmendment(unittest.TestCase):
    def test_21_gib_limit_and_original_19_gib_controller(self):
        self.assertEqual(a.accounting(11*a.c.GIB,31*a.c.GIB,0,0)["conservativeGrowthBytes"],20*a.c.GIB)
        with self.assertRaises(ValueError):a.c.accounting(11*a.c.GIB,31*a.c.GIB,0,0)
        with self.assertRaisesRegex(ValueError,"21 GiB"):a.accounting(11*a.c.GIB,33*a.c.GIB,0,0)

    def test_reserve_and_scoped_growth_still_enforced(self):
        for args in ((9*a.c.GIB,9*a.c.GIB,0,0),(30*a.c.GIB,30*a.c.GIB,22*a.c.GIB,0),(-1,0,0,0)):
            with self.assertRaises(ValueError):a.accounting(*args)

    def test_callback_restored_even_on_failure(self):
        original=a.c.resources
        with patch.object(a,"verify_amendment"):
            with self.assertRaises(RuntimeError):
                with a.activate():
                    self.assertIs(a.c.resources,a.resources)
                    raise RuntimeError("interrupted")
        self.assertIs(a.c.resources,original)

    def test_failed_binding_never_changes_controller(self):
        original=a.c.resources
        with patch.object(a,"verify_amendment",side_effect=ValueError("changed")):
            with self.assertRaises(ValueError):
                with a.activate():self.fail("must not activate")
        self.assertIs(a.c.resources,original)

    def test_live_status_can_advance_but_historical_bytes_are_verified(self):
        original='{"status":"paused","completed":"3"}'
        expected=hashlib.sha256(original.encode()).hexdigest()
        with tempfile.TemporaryDirectory() as folder,patch.object(a.c,"RUN",Path(folder)):
            status=Path(folder)/"native-output/status.json"
            status.parent.mkdir();status.write_text('{"status":"complete","completed":"16"}')
            a.verify_hold_artifact(status,expected,original)
            with self.assertRaises(ValueError):a.verify_hold_artifact(status,expected,"changed")

    def test_other_artifact_cannot_use_mutable_exception(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(a.c,"RUN",Path(folder)):
            path=Path(folder)/"result.json";path.write_text("original")
            expected=a.c.digest(path);path.write_text("modified")
            with self.assertRaises(ValueError):a.verify_hold_artifact(path,expected,"original")
