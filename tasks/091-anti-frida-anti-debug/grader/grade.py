"""Grader for 091-anti-frida-anti-debug — payload detection (Frida script).

Live on a KVM host the script is injected and its effect asserted; in dry-run it
is statically validated (does it hook the right method and enforce the required
behaviour?).
"""
from __future__ import annotations

from runner.graders import grade_frida_script


def grade(ctx):
    return grade_frida_script(ctx)
