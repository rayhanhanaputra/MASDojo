# 094-anti-debug-tracerpid — Anti-Debug (TracerPid) Bypass

**Grader type:** `frida_assert` · **MASVS:** MASVS-RESILIENCE-4 · **MASTG:** MASTG-TECH-0043 · status: **implemented**

## The vulnerability
`org.masdojo.vaultbank.DebugDetector.isBeingTraced()` (in `apps/vaultbank`)
implements anti-dynamic-analysis by reading `TracerPid` from
`/proc/self/status`. This is stronger than `Debug.isDebuggerConnected()` — it
catches any ptrace-based tracer (native debugger, `strace`, a Frida ptrace
attach), not just a JDWP debugger — but it is still a single in-process boolean
and is defeated by hooking that one method.

## How the grader proves it
`grader/grade.py` uses `grade_frida_script`. Dry-run statically validates that
the script hooks `DebugDetector.isBeingTraced()` and forces `false`. On a KVM
host, launch `.RaspLabActivity` and confirm `MASDOJO_UNLOCK_DBG:<flag>` appears
only after the hook (baseline: `MASDOJO_DENIED_DBG`).

The decompiled artifact shows the decision structure only; the reward
(`DEBUG_FLAG`) is never in a learner-visible file.

## Rebuilding the target
```bash
infra/build-apps.sh vaultbank
```
