package org.masdojo.vaultbank

import android.os.Build
import java.io.File

/**
 * A local Play-Integrity / SafetyNet-style attestation *stub* (RASP technique).
 *
 * This is a self-contained TRAINING stub: it makes NO network call to Google and
 * performs NO real remote attestation. It only mimics the shape of an integrity
 * verdict (device-integrity / basic-integrity / CTS-profile fields) so learners
 * can practise the bypass without any external service.
 *
 * VULNERABILITY (MASVS-RESILIENCE-1, task 096): a real integrity API returns a
 * *server-signed* verdict, but this app trusts a verdict it computes locally and
 * gates on a single boolean, `attestationPassed()`. Because the decision never
 * leaves the device, hooking `attestationPassed()` to return true (or forcing
 * the verdict fields) forges a "genuine, unrooted device" result. That is the
 * canonical failure of client-side attestation: trusting a locally-produced
 * verdict instead of verifying a signed token server-side.
 */
object PlayIntegrityStub {

    /** Mimics an integrity verdict token's fields (locally computed — not signed). */
    data class Verdict(
        val deviceIntegrity: Boolean,
        val basicIntegrity: Boolean,
        val ctsProfileMatch: Boolean,
    )

    private fun localVerdict(): Verdict {
        val emulated = EmulatorDetector.isEmulator()
        val rooted = RootDetector.isCompromised()
        val debug = File("/system/bin/su").exists() || Build.TAGS?.contains("test-keys") == true
        val clean = !emulated && !rooted && !debug
        return Verdict(deviceIntegrity = clean, basicIntegrity = clean, ctsProfileMatch = !emulated)
    }

    /**
     * The single gate the rest of the app trusts. VULNERABLE: the verdict is
     * produced and evaluated in-process, so it is fully attacker-controlled.
     */
    fun attestationPassed(): Boolean {
        val v = localVerdict()
        return v.deviceIntegrity && v.basicIntegrity && v.ctsProfileMatch
    }
}
