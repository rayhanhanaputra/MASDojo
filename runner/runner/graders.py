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

import json

from runner.grader_api import (
    Check,
    EvidenceItem,
    GradeResult,
    GradingContext,
    constant_time_equals,
)

# A no-op Frida payload used for the baseline run: it spawns the app but hooks
# nothing, so the app exhibits its natural (gated) behaviour.
_NOOP_SCRIPT = "Java.perform(function(){});"


def _tail(text: str, lines: int = 40) -> str:
    """Keep the last N non-empty log lines so the evidence bundle stays compact."""
    kept = [ln for ln in text.splitlines() if ln.strip()]
    return "\n".join(kept[-lines:])

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
    note = EvidenceItem(
        "static analysis (no device)",
        "note",
        "Graded without an emulator: the script was checked for the required hook. "
        "Run on a KVM host for the behavioral proof (baseline-locked → hook → unlocked).",
    )
    return GradeResult.from_checks(
        checks,
        "Frida script statically validated — it hooks the right method and enforces the "
        "required behaviour. (Run on a KVM host for full live verification.)"
        if passed
        else "The Frida script does not correctly implement the required hook.",
        evidence_items=[note],
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


def grade_frida_behavioral(ctx: GradingContext) -> GradeResult:
    """Behavioral (proof-of-technique) grader for a runtime-hook task.

    This is the strongest grader in the platform. Rather than checking that a
    success marker merely appears, it proves the learner's hook *caused* the
    state change, by running the app twice:

      1. **Baseline** — spawn the app with no hook and confirm the guard is
         actually engaged (the app denies access on this device). This rules out
         a false pass where the environment wasn't gating in the first place.
      2. **Hooked** — spawn again with the learner's script and confirm the guard
         is now defeated (access unlocked, the expected flag revealed).

    A pass therefore means: locked at baseline → unlocked after your hook → the
    bypass is *attributable to your script*. Every run is captured into a
    structured evidence bundle (baseline logcat, post-hook logcat, Frida message
    trace, timeline) that backs the verdict and is signed by the Proof-of-Pwn
    certificate.

    In dry-run (no device) it degrades to static validation of the script so the
    task stays solvable for self-study; the behavioral proof needs a KVM host.

    expected.json:
        {"flag": "FLAG{...}",
         "frida": {"package": "...", "class": "...", "method": "...",
                   "returns": "false", "must_contain": ["..."],
                   "unlock_marker": "MASDOJO_UNLOCK",
                   "denied_marker": "MASDOJO_DENIED"}}
    """
    expected = ctx.artifacts.expected()
    spec = expected.get("frida") or {}
    script = str(ctx.submission.get("script", "")).strip()

    if not script:
        return GradeResult(
            passed=False,
            evidence="No Frida script was submitted.",
            checks=[Check("script provided", False, "submission did not include a script")],
        )

    live = type(ctx.frida).__name__ != "_NullDevice" and spec.get("package") and spec.get("unlock_marker")
    if not live:
        return _grade_frida_static(spec, script)
    return _grade_frida_delta(ctx, spec, expected, script)


def _grade_frida_delta(ctx: GradingContext, spec: dict, expected: dict, script: str) -> GradeResult:
    package = spec["package"]
    unlock = spec["unlock_marker"]
    denied = spec.get("denied_marker", "")
    flag = spec.get("flag") or expected.get("flag", "")

    def _run(source: str, note: str) -> tuple[str, list]:
        ctx.emit(note, phase="frida")
        ctx.adb.clear_logcat()
        session, _pid = ctx.frida.spawn_and_inject(package, source)
        try:
            session.wait(6)
            log = ctx.adb.logcat_dump()
            payloads = session.payloads() if hasattr(session, "payloads") else []
        finally:
            session.unload()
        return log, payloads

    baseline_log, _ = _run(_NOOP_SCRIPT, "baseline run — launching the app unmodified to confirm it gates")
    hooked_log, frida_msgs = _run(script, "injecting your Frida script and re-running")

    baseline_gated = (denied in baseline_log if denied else True) and unlock not in baseline_log
    hooked_unlocked = unlock in hooked_log and (denied not in hooked_log if denied else True)
    flag_ok = bool(flag) and any(unlock in ln and flag in ln for ln in hooked_log.splitlines())

    checks = [
        Check(
            "target genuinely gates on this device (baseline locked)",
            baseline_gated,
            "the app denied access before your hook — the guard is real"
            if baseline_gated
            else "the app did not gate at baseline, so a pass cannot be attributed to your hook",
        ),
        Check(
            "your hook flipped the guard at runtime (locked → unlocked)",
            hooked_unlocked,
            "the unlock marker appeared only after your hook was injected"
            if hooked_unlocked
            else "the guard was not bypassed by your hook",
        ),
    ]
    if flag:
        checks.append(
            Check(
                "unlocked path revealed the expected flag",
                flag_ok,
                "flag recovered at runtime" if flag_ok else "expected flag not observed",
            )
        )

    passed = all(c.passed for c in checks)
    timeline = (
        f"baseline (no hook): {'DENIED / locked' if baseline_gated else 'not gated'}\n"
        f"after your hook:    {'UNLOCKED' if hooked_unlocked else 'still locked'}\n"
        f"flag revealed:      {'yes' if flag_ok else 'no'}"
    )
    items = [
        EvidenceItem("baseline logcat (no hook)", "log", _tail(baseline_log) or "(empty)"),
        EvidenceItem("logcat after your hook", "log", _tail(hooked_log) or "(empty)"),
        EvidenceItem("frida send() messages", "trace", json.dumps(frida_msgs, indent=2) if frida_msgs else "(none)"),
        EvidenceItem("timeline", "timeline", timeline),
    ]
    evidence = (
        "Behavioral proof: the target was locked at baseline and your hook unlocked it at "
        "runtime — the bypass is attributable to your script."
        if passed
        else "Not verified: "
        + (
            "the app was not gating at baseline (cannot attribute a bypass to your hook). "
            if not baseline_gated
            else "your hook did not defeat the guard. "
        )
    )
    return GradeResult.from_checks(checks, evidence, evidence_items=items)
