"""Grader for 093 — Emulator / Sandbox Detection Bypass (frida_assert).

Live on a KVM host the submitted script is injected and its effect asserted; in
dry-run it is statically validated: does the script hook EmulatorDetector's
decision method and force the "not an emulator" verdict? Static validation
genuinely detects whether the learner wrote a correct bypass, so the task is
solvable everywhere.
"""
from __future__ import annotations

from runner.graders import grade_frida_script


def grade(ctx):
    return grade_frida_script(ctx)
