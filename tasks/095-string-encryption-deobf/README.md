# 095-string-encryption-deobf — Defeat String Encryption (Anti-Static-Analysis)

**Grader type:** `static_assert` (seeded) · **MASVS:** MASVS-RESILIENCE-3 · **MASTG:** MASTG-TECH-0023 · status: **implemented**

## The vulnerability
`org.masdojo.vaultbank.StringVault` (in `apps/vaultbank`) stores sensitive
constants XOR-encrypted so they don't surface in a `strings` dump, decoding them
at runtime. This is an anti-static-analysis speed bump, not a control: the
`XOR_KEY` and the ciphertext both ship in the binary, so the plaintext is
recoverable offline by replaying the same XOR.

## How the grader proves it
The challenge is seeded per-learner (`challenge/generate.py`): the learner
downloads a decompiled `StringVault` with a per-seed key and encrypted table.
`grader/grade.py` (`grade_seeded_recovered`) regenerates that learner's answer
from their seed and constant-time compares. The plaintext reward never appears
verbatim in the challenge files — recovering it *is* proof the learner reversed
the obfuscation, and a value from another learner won't pass.

This is the RASP curriculum's static-analysis task (no device needed), rounding
out the technique tour alongside the runtime-hook gates (093/094/096).
