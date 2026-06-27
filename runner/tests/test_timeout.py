"""Tests for the hard job timeout."""

from __future__ import annotations

import time

import pytest

from runner.timeout import JobTimeout, hard_timeout


def test_hard_timeout_interrupts_long_work():
    with pytest.raises(JobTimeout):
        with hard_timeout(1):
            time.sleep(5)


def test_hard_timeout_allows_fast_work():
    with hard_timeout(5):
        result = sum(range(1000))
    assert result == 499500
