package org.masdojo.vaultbank

import android.os.Bundle
import android.util.Log
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * The RASP practice surface: three independent runtime self-protection gates,
 * each guarding its own reward.
 *
 * VULNERABILITY (MASVS-RESILIENCE, tasks 093 / 094 / 096): every gate is a single
 * in-process boolean, so each is defeated by hooking its one decision method:
 *  - AntiTamper.isInstrumented()          (task 091)
 *  - EmulatorDetector.isEmulator()        (task 093)
 *  - DebugDetector.isBeingTraced()        (task 094)
 *  - PlayIntegrityStub.attestationPassed()(task 096)
 *
 * On the training emulator every gate denies by design; the learner's Frida hook
 * flips the guarded method so the matching reward is revealed. Each gate logs a
 * distinct MASDOJO_* marker so a live grader can attribute the unlock.
 */
class RaspLabActivity : AppCompatActivity() {

    private val tag = "VaultBank"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val lines = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 96, 48, 48)
            addView(TextView(this@RaspLabActivity).apply { text = "VaultBank — RASP Lab"; textSize = 22f })
        }
        setContentView(ScrollView(this).apply { addView(lines) })

        gate(
            lines, "Anti-instrumentation (anti-Frida) gate",
            clean = !AntiTamper.isInstrumented(),
            reason = "MASDOJO_DENIED_TAMPER: instrumentation toolkit detected",
            unlock = "MASDOJO_UNLOCK_TAMPER", flag = BuildConfig.TAMPER_FLAG,
        )
        gate(
            lines, "Emulator / sandbox gate",
            clean = !EmulatorDetector.isEmulator(),
            reason = "MASDOJO_DENIED_EMU: emulator/sandbox detected",
            unlock = "MASDOJO_UNLOCK_EMU", flag = BuildConfig.EMU_FLAG,
        )
        gate(
            lines, "Anti-debug (TracerPid) gate",
            clean = !DebugDetector.isBeingTraced(),
            reason = "MASDOJO_DENIED_DBG: tracer attached (TracerPid != 0)",
            unlock = "MASDOJO_UNLOCK_DBG", flag = BuildConfig.DEBUG_FLAG,
        )
        gate(
            lines, "Play-Integrity attestation gate",
            clean = PlayIntegrityStub.attestationPassed(),
            reason = "MASDOJO_DENIED_ATT: attestation verdict failed",
            unlock = "MASDOJO_UNLOCK_ATT", flag = BuildConfig.ATTEST_FLAG,
        )
    }

    private fun gate(root: LinearLayout, title: String, clean: Boolean, reason: String, unlock: String, flag: String) {
        val tv = TextView(this).apply { textSize = 14f }
        if (clean) {
            Log.i(tag, "$unlock:$flag")
            tv.text = "$title: UNLOCKED\n$flag"
        } else {
            Log.w(tag, reason)
            tv.text = "$title: locked"
        }
        root.addView(tv)
    }
}
