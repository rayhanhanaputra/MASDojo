package org.masdojo.vaultbank

import android.os.Build
import android.os.Debug
import java.io.File

/**
 * Client-side root / instrumentation / debugger detection.
 *
 * VULNERABILITY (MASVS-RESILIENCE-1/2/3, tasks 009 / 091): every protection is
 * a boolean computed in-process, so a Frida hook on isCompromised() (or on any
 * of the helpers) forces a "clean" verdict. The emulator trips these checks by
 * design, so the gated feature stays locked until the learner defeats them.
 */
object RootDetector {

    private val SU_PATHS = arrayOf(
        "/system/bin/su", "/system/xbin/su", "/sbin/su", "/su/bin/su", "/data/local/tmp/su",
    )

    fun isCompromised(): Boolean =
        hasSuBinary() || looksLikeEmulator() || isDebuggerAttached() || isFridaPresent()

    private fun hasSuBinary(): Boolean = SU_PATHS.any { File(it).exists() }

    private fun looksLikeEmulator(): Boolean {
        val fp = Build.FINGERPRINT ?: ""
        return fp.startsWith("generic") || fp.contains("sdk_gphone") ||
            Build.MODEL.contains("Emulator") || Build.MODEL.contains("Android SDK built for")
    }

    private fun isDebuggerAttached(): Boolean = Debug.isDebuggerConnected()

    /** Look for the frida-server default port / library markers. */
    private fun isFridaPresent(): Boolean {
        return try {
            File("/proc/self/maps").readLines().any {
                it.contains("frida") || it.contains("gum-js-loop") || it.contains("gadget")
            }
        } catch (_: Exception) {
            false
        }
    }
}
