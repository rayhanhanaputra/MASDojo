"""Reusable grader helpers so a task's grade.py is a one-liner for the common
comparison cases.

A `flag` or `static_assert` task usually just needs: read the expected value
from the task's server-side `grader/expected.json`, constant-time compare it
against the learner's submission, and return a single Check. These helpers
provide exactly that, so authoring a new comparison task is:

    from runner.graders import grade_flag
    def grade(ctx):
        return grade_flag(ctx)

These run fully in dry-run (no device): they only touch ctx.submission and the
task's expected values.
"""

from __future__ import annotations

from runner.grader_api import Check, GradeResult, GradingContext, constant_time_equals

# Submission fields we accept, in priority order, for a comparison grader.
_SUBMIT_FIELDS = ("flag", "value", "secret")


def _submitted(ctx: GradingContext) -> str:
    for field in _SUBMIT_FIELDS:
        val = ctx.submission.get(field)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _expected(ctx: GradingContext, fields: tuple[str, ...]) -> str:
    data = ctx.artifacts.expected()
    for field in fields:
        val = data.get(field)
        if isinstance(val, str) and val:
            return val
    return ""


def grade_comparison(
    ctx: GradingContext,
    *,
    expected_fields: tuple[str, ...],
    check_name: str,
) -> GradeResult:
    """Constant-time compare the submission against the task's expected value."""
    expected = _expected(ctx, expected_fields)
    submitted = _submitted(ctx)
    if not expected:
        return GradeResult(
            passed=False,
            evidence="Task misconfigured: no expected value in grader/expected.json.",
            checks=[Check(check_name, False, "grader/expected.json is missing the expected value")],
        )
    ok = constant_time_equals(submitted, expected)
    return GradeResult.from_checks(
        [Check(check_name, ok, "exact match" if ok else "submitted value did not match")],
        "Accepted." if ok else "Rejected: the submitted value is not correct.",
    )


def grade_flag(ctx: GradingContext) -> GradeResult:
    """Grade a `flag` task against `flag` (or `value`) in expected.json."""
    return grade_comparison(ctx, expected_fields=("flag", "value"), check_name="flag matches expected")


def grade_static(ctx: GradingContext) -> GradeResult:
    """Grade a `static_assert` task against `secret`/`value` in expected.json."""
    return grade_comparison(
        ctx, expected_fields=("secret", "value", "flag"), check_name="recovered value is correct"
    )


def grade_recovered(ctx: GradingContext) -> GradeResult:
    """Grade a value the learner recovered by applying a technique.

    The payload-detection contract: the submitted value must (1) match the
    expected value exactly, and (2) where `present_in` lists committed artifact
    files, genuinely appear inside them — so the format alone can't be guessed
    and the learner must have actually analysed the target. Crypto tasks omit
    `present_in`: the plaintext can't be guessed, so a correct value *is* proof
    the learner performed the decryption.

    expected.json:
        {"value": "<answer>", "present_in": ["artifacts/res/values/strings.xml"]}
    """
    data = ctx.artifacts.expected()
    expected = _expected(ctx, ("value", "flag", "secret"))
    submitted = _submitted(ctx)

    if not expected:
        return GradeResult(
            passed=False,
            evidence="Task misconfigured: no expected value in grader/expected.json.",
            checks=[Check("configured", False, "grader/expected.json is missing the expected value")],
        )

    matches = constant_time_equals(submitted, expected)
    checks = [
        Check(
            "recovered value is correct",
            matches,
            "exact match" if matches else "submitted value did not match the expected answer",
        )
    ]

    for rel in data.get("present_in", []) or []:
        path = ctx.package_dir / rel
        present = path.is_file() and expected.encode() in path.read_bytes()
        checks.append(
            Check(
                f"value genuinely present in {rel}",
                present,
                f"found in {rel}" if present else f"not found in {rel}",
            )
        )

    passed = all(c.passed for c in checks)
    return GradeResult.from_checks(
        checks,
        "Technique applied: the recovered value is correct."
        if passed
        else "The submitted value is not the correct answer for this task.",
    )


def grade_frida_script(ctx: GradingContext) -> GradeResult:
    """Grade a submitted Frida script.

    On a live device (KVM host) the script is injected and its runtime effect is
    asserted — the strongest check. In dry-run it is statically validated: does
    the script hook the required class + method and enforce the required
    behaviour? Static validation genuinely detects whether the learner wrote a
    correct bypass, so the technique is checkable everywhere.

    expected.json:
        {"frida": {"class": "...", "method": "...", "returns": "false",
                   "must_contain": ["..."],
                   "package": "...", "unlock_marker": "MASDOJO_UNLOCK",
                   "denied_marker": "MASDOJO_DENIED", "flag": "FLAG{...}"}}
    """
    spec = (ctx.artifacts.expected().get("frida") or {})
    script = str(ctx.submission.get("script", "")).strip()

    if not script:
        return GradeResult(
            passed=False,
            evidence="No Frida script was submitted.",
            checks=[Check("script provided", False, "submission did not include a script")],
        )

    live = type(ctx.frida).__name__ != "_NullDevice"
    if live and spec.get("package") and spec.get("unlock_marker"):
        return _grade_frida_live(ctx, spec, script)
    return _grade_frida_static(spec, script)


def _grade_frida_static(spec: dict, script: str) -> GradeResult:
    checks: list[Check] = []
    cls = spec.get("class", "")
    method = spec.get("method", "")
    returns = spec.get("returns")

    if cls:
        hit = cls in script
        checks.append(Check(f"hooks the target class {cls}", hit,
                            "class referenced" if hit else "target class not hooked"))
    if method:
        # accept `.<method>.implementation` (allowing overload().implementation)
        hit = f".{method}" in script and "implementation" in script
        checks.append(Check(f"overrides {method}()", hit,
                            "implementation override present" if hit else "method not overridden"))
    if returns is not None:
        hit = f"return {returns}" in script.replace(";", " ")
        checks.append(Check(f"forces the return value to {returns}", hit,
                            "correct return" if hit else f"does not return {returns}"))
    for needle in spec.get("must_contain", []) or []:
        hit = needle in script
        checks.append(Check(f"uses `{needle}`", hit, "present" if hit else "missing"))

    if not checks:  # no spec — accept any non-empty script (author should add a spec)
        checks.append(Check("script provided", True, "no static spec configured"))

    passed = all(c.passed for c in checks)
    return GradeResult.from_checks(
        checks,
        "Frida script statically validated — it hooks the right method and enforces the "
        "required behaviour. (Run on a KVM host for full live verification.)"
        if passed
        else "The Frida script does not correctly implement the required hook.",
    )


def _grade_frida_live(ctx: GradingContext, spec: dict, script: str) -> GradeResult:
    """Inject the script and assert its runtime effect via a logcat marker."""
    package = spec["package"]
    unlock_marker = spec["unlock_marker"]
    denied_marker = spec.get("denied_marker", "")
    flag = spec.get("flag", "")

    ctx.emit("clearing logcat and injecting the submitted script", phase="frida")
    ctx.adb.clear_logcat()
    session, _pid = ctx.frida.spawn_and_inject(package, script)
    try:
        session.wait(6)
        logcat = ctx.adb.logcat_dump()
    finally:
        session.unload()

    unlocked = unlock_marker in logcat
    denied = bool(denied_marker) and denied_marker in logcat
    checks = [Check("hook flipped the guarded behaviour", unlocked and not denied,
                   "unlock marker observed" if unlocked else "the guard was not bypassed")]
    if flag:
        got = any(unlock_marker in ln and flag in ln for ln in logcat.splitlines())
        checks.append(Check("expected flag revealed", got,
                            "flag recovered" if got else "expected flag not observed"))
    passed = all(c.passed for c in checks)
    return GradeResult.from_checks(
        checks,
        "Bypass verified live on the emulator." if passed else "The bypass did not take effect on the device.",
    )
