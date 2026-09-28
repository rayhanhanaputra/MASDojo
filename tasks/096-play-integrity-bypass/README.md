# 096-play-integrity-bypass — Forge a Play-Integrity / Attestation Verdict

**Grader type:** `frida_assert` · **MASVS:** MASVS-RESILIENCE-1 · **MASTG:** MASTG-TECH-0043 · status: **implemented**

## The vulnerability
`org.masdojo.vaultbank.PlayIntegrityStub` (in `apps/vaultbank`) is a self-contained
**training stub** for a Play-Integrity / SafetyNet-style attestation. It makes no
network call and performs no real remote attestation; it only mimics the shape of
an integrity verdict. The modelled flaw is real: the app trusts a verdict it
computes *locally* (`attestationPassed()`) instead of verifying a server-signed
token, so the "genuine device" decision is fully attacker-controlled. This gate
unlocks on a **passing** verdict, so the bypass forces `attestationPassed()` to
return `true`.

## How the grader proves it
`grader/grade.py` uses `grade_frida_script`. Dry-run statically validates that the
script hooks `PlayIntegrityStub.attestationPassed()` and forces `true`. On a KVM
host, launch `.RaspLabActivity` and confirm `MASDOJO_UNLOCK_ATT:<flag>` appears
only after the hook (baseline: `MASDOJO_DENIED_ATT`).

The reward (`ATTEST_FLAG`) is never in a learner-visible file.

## Rebuilding the target
```bash
infra/build-apps.sh vaultbank
```
