"""Grader for 094 — Anti-Debug (TracerPid) Bypass (frida_assert).

Live on a KVM host the submitted script is injected and its effect asserted; in
dry-run it is statically validated: does the script hook the TracerPid-based
decision method and force the "not being traced" verdict?
"""
from __future__ import annotations

from runner.graders import grade_frida_script


def grade(ctx):
    return grade_frida_script(ctx)
