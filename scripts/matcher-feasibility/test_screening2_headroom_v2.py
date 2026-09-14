import unittest
from unittest.mock import patch

import screening2_headroom_v2 as retry


class HeadroomRetryTests(unittest.TestCase):
    def test_attempt_configures_and_restores_without_changing_execution(self):
        driver = retry.driver
        before = driver.ATTEMPT, driver.PLAN, driver.SOURCES, driver.source_bindings
        execute, guard = driver.original.execute, driver.StorageGuard
        with self.assertRaisesRegex(RuntimeError, "test"):
            with retry.configured_attempt():
                self.assertEqual(driver.ATTEMPT, retry.ATTEMPT)
                self.assertEqual(driver.PLAN, retry.PLAN)
                self.assertEqual(driver.SOURCES, retry.SOURCES)
                self.assertIs(driver.original.execute, execute)
                self.assertIs(driver.StorageGuard, guard)
                raise RuntimeError("test")
        self.assertEqual((driver.ATTEMPT, driver.PLAN, driver.SOURCES, driver.source_bindings), before)

    def test_freeze_includes_failed_preparation_artifacts(self):
        driver = retry.driver
        with patch.object(driver, "source_bindings", return_value={"source": "digest"}), \
             patch.object(driver.common, "files_in", return_value={"manifest.json": "old-digest"}), \
             patch("pathlib.Path.exists", return_value=True):
            with retry.configured_attempt():
                values = driver.source_bindings()
        self.assertEqual(values["source"], "digest")
        self.assertTrue(any(k.endswith("checkpoint-headroom-attempt-01/manifest.json") and v == "old-digest"
                            for k, v in values.items()))


if __name__ == "__main__":
    unittest.main()
