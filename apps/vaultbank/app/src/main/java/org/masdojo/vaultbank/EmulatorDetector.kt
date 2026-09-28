package org.masdojo.vaultbank

import android.os.Build
import java.io.File

/**
 * Client-side emulator / sandbox detection (RASP technique).
 *
 * VULNERABILITY (MASVS-RESILIENCE-1, task 093): the app tries to "validate the
 * integrity of the platform" by refusing to run on an emulator/sandbox — but the
 * whole verdict is one in-process boolean. An attacker who instruments the
 * process forces `isEmulator()` to return false, so the environment check is
 * worthless. The training AVD trips every signal by design, so the gated feature
 * stays locked until the learner's Frida hook flips the verdict.
 *
 * These are the canonical emulator tells (QEMU build fingerprints, generic
 * hardware, the qemu pipe/driver nodes) — the same family MASTG lists for
 * anti-emulation. None of them is authoritative on its own, which is exactly why
 * a purely client-side environment gate is defeatable.
 */
object EmulatorDetector {

    private val QEMU_NODES = arrayOf(
        "/dev/socket/qemud",
        "/dev/qemu_pipe",
        "/system/lib/libc_malloc_debug_qemu.so",
        "/sys/qemu_trace",
        "/dev/goldfish_pipe",
    )

    /** True if this looks like an emulator / analysis sandbox. */
    fun isEmulator(): Boolean =
        hasQemuBuildProps() || hasGenericHardware() || hasQemuNodes()

    private fun hasQemuBuildProps(): Boolean {
        val fp = Build.FINGERPRINT ?: ""
        return fp.startsWith("generic") ||
            fp.startsWith("unknown") ||
            fp.contains("sdk_gphone") ||
            fp.contains("emulator") ||
            fp.contains("vbox") ||
            Build.PRODUCT.contains("sdk") ||
            Build.PRODUCT.contains("emulator") ||
            Build.HARDWARE.contains("goldfish") ||
            Build.HARDWARE.contains("ranchu")
    }

    private fun hasGenericHardware(): Boolean =
        (Build.BRAND.startsWith("generic") && Build.DEVICE.startsWith("generic")) ||
            Build.MANUFACTURER.contains("Genymotion") ||
            Build.MODEL.contains("Emulator") ||
            Build.MODEL.contains("Android SDK built for")

    private fun hasQemuNodes(): Boolean = QEMU_NODES.any { File(it).exists() }
}
