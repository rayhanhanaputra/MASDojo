"""Grader for 096 — Forge a Play-Integrity / Attestation Verdict (frida_assert).

Live on a KVM host the submitted script is injected and its effect asserted; in
dry-run it is statically validated: does the script hook the attestation gate and
force a passing verdict? The attestation is a self-contained local stub — no
network / no real Google Play Integrity call is involved.
"""
from __future__ import annotations

from runner.graders import grade_frida_script


def grade(ctx):
    return grade_frida_script(ctx)
