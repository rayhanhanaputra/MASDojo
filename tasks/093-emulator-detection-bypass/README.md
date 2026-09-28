# 093-emulator-detection-bypass — Emulator / Sandbox Detection Bypass

**Grader type:** `frida_assert` · **MASVS:** MASVS-RESILIENCE-1 · **MASTG:** MASTG-TECH-0043 · status: **implemented**

## The vulnerability
`org.masdojo.vaultbank.EmulatorDetector.isEmulator()` (in `apps/vaultbank`) tries
to "validate the integrity of the platform" by refusing to run on an emulator /
analysis sandbox. The verdict is a single in-process boolean built from the
classic QEMU/generic-hardware tells, so it is fully attacker-controlled at
runtime. `RaspLabActivity` gates its emulator reward on it.

## How the grader proves it
`grader/grade.py` uses `grade_frida_script`. In dry-run the submitted script is
statically validated (does it hook `EmulatorDetector.isEmulator()` and force
`false`?). On a KVM host, launch `.RaspLabActivity` and confirm the emulator
gate logs `MASDOJO_UNLOCK_EMU:<flag>` only after the hook — the baseline run logs
`MASDOJO_DENIED_EMU`.

Per the derive-the-answer principle the decompiled artifact shows only the
decision structure, never a flag; the reward is `EMU_FLAG`, revealed only when
the check is defeated at runtime.

## Rebuilding the target
```bash
infra/build-apps.sh vaultbank   # EmulatorDetector + RaspLabActivity ship in the APK
```
