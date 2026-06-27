# 009 — Root Detection Bypass  ⭐ reference task

**Grader type:** `frida_assert` · **MASVS:** MASVS-RESILIENCE-1

## The vulnerability
`apps/vaultguard` gates its "premium vault" behind a client-side root check
(`RootChecker.isDeviceRooted()`). On the emulator the check returns `true`
(it detects test-keys / the emulator fingerprint), so the vault stays locked and
the app logs `VaultGuard: MASDOJO_DENIED`. The check is a single boolean
choke-point that an attacker can flip at runtime.

## How the grader proves it
1. The runner clears logcat and spawns the app with the learner's Frida script
   injected at startup.
2. VaultGuard logs `MASDOJO_UNLOCK:<flag>` **only** when `isDeviceRooted()`
   returns false. Because the emulator is "rooted", that marker can only appear
   if the learner's hook flipped the return value.
3. `grader/grade.py` reads logcat and asserts the unlock marker is present (and
   the denied marker is not), then verifies the revealed flag.

The reference hook lives in `frida/reference_bypass.js` (never shown to the
learner).

## Rebuilding the target
```bash
infra/build-apps.sh vaultguard
# produces tasks/009-root-detection-bypass/app/target.apk
```
