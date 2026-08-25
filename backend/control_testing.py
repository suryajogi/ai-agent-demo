"""Pluggable control-test connectors (NR-016).

A control with no connector configured falls back to the original demo
behavior (random Pass/Fail) — no regression for controls that don't target a
real system. A control with `test_connector_type="http_health_check"` is
tested against a real URL.
"""

import random
from typing import Optional

import httpx

import models


def run_test(control: "models.Control") -> tuple[str, str]:
    """Returns (result, detail) where result is 'Pass' or 'Fail'."""
    connector = control.test_connector_type
    config = control.test_connector_config or {}

    if connector == "http_health_check":
        url = config.get("url")
        expect_status = config.get("expect_status", 200)
        if not url:
            return "Fail", "http_health_check configured with no url"
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == expect_status:
                return "Pass", f"GET {url} -> {response.status_code} (expected {expect_status})"
            return "Fail", f"GET {url} -> {response.status_code} (expected {expect_status})"
        except httpx.HTTPError as e:
            return "Fail", f"GET {url} failed: {e}"

    # No connector configured — preserve original demo behavior.
    outcome = random.choice(["Pass", "Fail"])
    return outcome, "Simulated result (no connector configured)"
