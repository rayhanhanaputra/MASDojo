"""Grader for 005 — Intercept & Capture the API Call (network_assert).

The runner proxies the emulator's traffic through mitmproxy and triggers the
app, then hands us the captured flows. We verify:
  1. the telemetry request was actually made (proof the app phoned home and the
     proxy captured it), and
  2. the learner submitted the same device_token that the request carried (proof
     they actually read the intercepted value, not just guessed the endpoint).
"""

from __future__ import annotations

import json
from urllib.parse import parse_qs

from runner.grader_api import Check, GradeResult, GradingContext, constant_time_equals


def _extract_token(body: str, query: dict, param: str) -> str:
    """Pull the device token out of a captured request (form, JSON, or query)."""
    if param in query and query[param]:
        return query[param][0]
    if body:
        # urlencoded form body
        parsed = parse_qs(body)
        if param in parsed and parsed[param]:
            return parsed[param][0]
        # JSON body
        try:
            data = json.loads(body)
            if isinstance(data, dict) and param in data:
                return str(data[param])
        except (ValueError, TypeError):
            pass
    return ""


def grade(ctx: GradingContext) -> GradeResult:
    expected = ctx.artifacts.expected()
    endpoint = expected.get("endpoint_path", "/api/v1/telemetry")
    param = expected.get("param_name", "device_token")
    expected_token = expected.get("device_token", "")
    submitted = str(ctx.submission.get("value", "")).strip()

    checks: list[Check] = []

    matching_flows = ctx.network.to(endpoint)
    captured = bool(matching_flows)
    checks.append(
        Check(
            name=f"telemetry request to {endpoint} was intercepted",
            passed=captured,
            detail=f"captured {len(matching_flows)} request(s) to the endpoint"
            if captured
            else "no request to the telemetry endpoint was seen on the wire",
        )
    )

    captured_token = ""
    for flow in matching_flows:
        captured_token = _extract_token(flow.request_body, flow.query, param)
        if captured_token:
            break

    token_correct = bool(captured_token) and constant_time_equals(captured_token, expected_token)
    checks.append(
        Check(
            name="intercepted request carried the expected device token",
            passed=token_correct,
            detail="device_token in the captured request matched the target value"
            if token_correct
            else "did not find the expected device_token in any captured request",
        )
    )

    submission_matches = (
        bool(submitted)
        and constant_time_equals(submitted, expected_token)
        and constant_time_equals(submitted, captured_token or "")
    )
    checks.append(
        Check(
            name="submitted value matches the token you intercepted",
            passed=submission_matches,
            detail="your submission matches the captured device_token"
            if submission_matches
            else "your submission did not match the value the app actually sent",
        )
    )

    passed = all(c.passed for c in checks)
    evidence = (
        "Telemetry request intercepted and the captured device token verified."
        if passed
        else "Could not confirm you intercepted the telemetry request and its device token."
    )
    return GradeResult.from_checks(checks, evidence)
