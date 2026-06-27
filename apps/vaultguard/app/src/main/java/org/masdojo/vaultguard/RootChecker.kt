package org.masdojo.vaultguard

import android.os.Build
import java.io.File

/**
 * Client-side root detection.
 *
 * VULNERABILITY (MASVS-RESILIENCE-1): the entire gate is one boolean computed on
 * the device. An attacker who instruments the process can force it to return
 * false. The checks below intentionally flag the emulator as "rooted" (it ships
 * with test-keys and su-like binaries), so the vault stays locked until the
 * learner's Frida hook flips the verdict.
 */
object RootChecker {

    private val SU_PATHS = arrayOf(
        "/system/bin/su",
        "/system/xbin/su",
        "/sbin/su",
        "/su/bin/su",
        "/data/local/tmp/su",
    )

    fun isDeviceRooted(): Boolean {
        return hasTestKeys() || hasSuBinary() || looksLikeEmulator()
    }

    private fun hasTestKeys(): Boolean {
        val tags = Build.TAGS
        return tags != null && tags.contains("test-keys")
    }

    private fun hasSuBinary(): Boolean = SU_PATHS.any { File(it).exists() }

    private fun looksLikeEmulator(): Boolean {
        val fp = Build.FINGERPRINT ?: ""
        return fp.startsWith("generic") ||
            fp.contains("sdk_gphone") ||
            Build.MODEL.contains("Emulator") ||
            Build.MODEL.contains("Android SDK built for") ||
            (Build.BRAND.startsWith("generic") && Build.DEVICE.startsWith("generic"))
    }
}
