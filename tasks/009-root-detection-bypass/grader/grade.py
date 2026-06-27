"""Grader for 009 — Root Detection Bypass (frida_assert).

The learner submits a Frida script. The runner spawns the target app with the
script injected at startup. VaultGuard only logs its unlock marker + flag when
`RootChecker.isDeviceRooted()` returns false; on the emulator that method
returns true unless the learner's hook flips it. So the unlock marker appearing
in logcat is proof that the learner's hook fired and the guarded return was
flipped.
"""

from __future__ import annotations

from runner.grader_api import Check, GradeResult, GradingContext, constant_time_equals


def grade(ctx: GradingContext) -> GradeResult:
    expected = ctx.artifacts.expected()
    flag = expected.get("flag", "")
    unlock_marker = expected.get("unlock_marker", "MASDOJO_UNLOCK")
    denied_marker = expected.get("denied_marker", "MASDOJO_DENIED")
    package = "org.masdojo.vaultguard"

    script = str(ctx.submission.get("script", "")).strip()
    checks: list[Check] = []

    if not script:
        return GradeResult(
            passed=False,
            evidence="No Frida script was submitted.",
            checks=[Check("script provided", False, "submission did not include a script")],
        )

    # Start from a clean log, inject the learner's script at spawn, let the app
    # run its startup root check, then read the logcat for the outcome markers.
    ctx.adb.clear_logcat()
    session, _pid = ctx.frida.spawn_and_inject(package, script)
    try:
        session.wait(6)
        logcat = ctx.adb.logcat_dump()
    finally:
        session.unload()

    unlocked = unlock_marker in logcat
    denied = denied_marker in logcat

    checks.append(
        Check(
            name="root check was bypassed (vault unlocked)",
            passed=unlocked and not denied,
            detail="VaultGuard logged its unlock marker"
            if unlocked
            else "the app still treated the device as rooted",
        )
    )

    # Confirm the unlocked flag matches — guards against an app build mismatch.
    flag_ok = False
    if unlocked and flag:
        for line in logcat.splitlines():
            if unlock_marker in line and constant_time_equals(line.split(unlock_marker + ":", 1)[-1], flag):
                flag_ok = True
                break
    checks.append(
        Check(
            name="unlocked vault revealed the expected flag",
            passed=flag_ok,
            detail="flag recovered from the unlocked vault" if flag_ok else "expected flag not observed",
        )
    )

    passed = all(c.passed for c in checks)
    evidence = (
        "Root detection bypassed: the Frida hook flipped the check and the vault unlocked."
        if passed
        else "The root check was not defeated; the gated vault stayed locked."
    )
    return GradeResult.from_checks(checks, evidence)
