package org.masdojo.vaultbank

import java.io.File

/**
 * Client-side debugger detection via the kernel's TracerPid (RASP technique).
 *
 * VULNERABILITY (MASVS-RESILIENCE-4, task 094): unlike the naive
 * `Debug.isDebuggerConnected()` (which only sees a Java/JDWP debugger), this
 * reads `TracerPid` from `/proc/self/status`. Any ptrace-based tracer — a native
 * debugger, `strace`, or Frida's own ptrace attach — makes TracerPid non-zero,
 * so the app bails. It is still just one in-process boolean, though: hooking
 * `isBeingTraced()` to return false (or making the reader see TracerPid 0)
 * defeats it. This is the ptrace/TracerPid anti-debug check MASTG documents, and
 * it is defeated the same way every client-side RASP check is.
 */
object DebugDetector {

    init {
        // libguard.so forks a child that ptrace-SEIZEs this process on load, so
        // TracerPid becomes non-zero and the check below actually fires. Wrapped
        // so the gate still works if the native lib is unavailable.
        try {
            System.loadLibrary("guard")
        } catch (_: Throwable) {
        }
    }

    /**
     * True if a tracer is attached. Reads the `TracerPid:` line of
     * `/proc/self/status`; a value other than 0 means some process is ptrace'ing
     * us (native debugger, strace, or a Frida ptrace attach).
     */
    fun isBeingTraced(): Boolean {
        return try {
            val status = File("/proc/self/status").readText()
            val line = status.lineSequence().firstOrNull { it.startsWith("TracerPid:") }
                ?: return false
            val tracer = line.substringAfter("TracerPid:").trim().toIntOrNull() ?: 0
            tracer != 0
        } catch (_: Exception) {
            false
        }
    }
}
