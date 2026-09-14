#!/usr/bin/env python3
"""Clean source freeze after a preparation-only test snapshot mismatch."""
from contextlib import contextmanager

import screening2_headroom as driver

ATTEMPT = "checkpoint-headroom-attempt-02"
PLAN = driver.common.SCREENING / "CHECKPOINT_HEADROOM_RETRY.md"
SOURCES = (*driver.SOURCES, "screening2_headroom_v2.py", "test_screening2_headroom_v2.py")


@contextmanager
def configured_attempt():
    prior = driver.ATTEMPT, driver.PLAN, driver.SOURCES, driver.source_bindings
    original_bindings = driver.source_bindings

    def bindings():
        result = original_bindings()
        failed = driver.common.SCREENING / "runs/screen-attempt-01/runtime-continuations/checkpoint-headroom-attempt-01"
        driver.common.require((failed / "manifest.json").exists(), "missing preserved preparation attempt")
        return result | {str((failed / name).relative_to(driver.common.ROOT)): digest
                         for name, digest in driver.common.files_in(failed).items()}

    driver.ATTEMPT, driver.PLAN, driver.SOURCES, driver.source_bindings = ATTEMPT, PLAN, SOURCES, bindings
    try:
        yield
    finally:
        driver.ATTEMPT, driver.PLAN, driver.SOURCES, driver.source_bindings = prior


if __name__ == "__main__":
    with configured_attempt():
        driver.main()
