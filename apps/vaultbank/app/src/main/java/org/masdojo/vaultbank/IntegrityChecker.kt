package org.masdojo.vaultbank

import android.content.Context
import android.content.pm.PackageManager
import java.security.MessageDigest

/**
 * Verifies the APK hasn't been re-signed after tampering.
 *
 * VULNERABILITY (MASVS-RESILIENCE-4, task 092): the integrity decision is a
 * single in-process comparison against a hardcoded signature digest. After a
 * learner patches and re-signs the APK the digest changes, but hooking
 * isValidSignature() to return true (or patching the comparison in smali)
 * defeats the check.
 */
object IntegrityChecker {

    // Digest the app "expects" its own signing cert to have.
    private const val EXPECTED_SHA256 = "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"

    @Suppress("DEPRECATION", "PackageManagerGetSignatures")
    fun isValidSignature(ctx: Context): Boolean {
        return try {
            val sigs = ctx.packageManager
                .getPackageInfo(ctx.packageName, PackageManager.GET_SIGNATURES)
                .signatures ?: return false
            val md = MessageDigest.getInstance("SHA-256")
            val actual = md.digest(sigs[0].toByteArray()).joinToString("") { "%02x".format(it) }
            actual == EXPECTED_SHA256
        } catch (_: Exception) {
            false
        }
    }
}
