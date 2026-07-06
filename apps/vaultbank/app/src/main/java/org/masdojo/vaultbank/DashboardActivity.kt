package org.masdojo.vaultbank

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Account dashboard.
 *
 * Vulnerabilities:
 *  - MASVS-RESILIENCE-1 (task 042/012): the "premium" ledger is gated by a
 *    single client-side boolean, isPremiumUser(). Flip it (Frida hook or a
 *    smali patch) and the premium flag is revealed.
 *  - MASVS-RESILIENCE-1 (task 041): computeReward() returns a flag at runtime
 *    that never renders in the UI unless you hook it and read the return value.
 *  - MASVS-RESILIENCE-1/2 (task 009/091): the transfer feature is behind a
 *    root/anti-frida check; defeat the detector to unlock VAULT_FLAG.
 */
class DashboardActivity : AppCompatActivity() {

    private val tag = "VaultBank"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val status = TextView(this).apply { textSize = 13f }
        val premiumBtn = Button(this).apply { text = "Open premium ledger" }
        val transferBtn = Button(this).apply { text = "Transfer funds" }
        val webBtn = Button(this).apply { text = "Support chat" }

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 96, 48, 48)
            addView(TextView(this@DashboardActivity).apply { text = "Dashboard"; textSize = 22f })
            addView(TextView(this@DashboardActivity).apply {
                text = "Balance: \$4,921.00"; textSize = 16f
            })
            addView(premiumBtn)
            addView(transferBtn)
            addView(webBtn)
            addView(status)
        }
        setContentView(root)

        // A reward is computed but never shown — only a runtime hook sees it.
        Log.d(tag, "reward token issued (length=${computeReward().length})")

        premiumBtn.setOnClickListener {
            if (isPremiumUser()) {
                status.text = "Premium ledger unlocked.\n${BuildConfig.PREMIUM_FLAG}"
                Log.i(tag, "MASDOJO_PREMIUM:${BuildConfig.PREMIUM_FLAG}")
            } else {
                status.text = "Premium membership required."
            }
        }

        transferBtn.setOnClickListener {
            // Client-side root/anti-instrumentation gate (task 009/091).
            if (RootDetector.isCompromised()) {
                status.text = "Transfers disabled on a compromised device."
                Log.w(tag, "MASDOJO_DENIED: compromised device")
            } else {
                status.text = "Transfer authorised.\n${BuildConfig.VAULT_FLAG}"
                Log.i(tag, "MASDOJO_UNLOCK:${BuildConfig.VAULT_FLAG}")
            }
        }

        webBtn.setOnClickListener {
            startActivity(Intent(this, WebViewActivity::class.java))
        }
    }

    /** VULNERABILITY (task 042): the entire premium gate is this boolean. */
    private fun isPremiumUser(): Boolean = false

    /** VULNERABILITY (task 041): flag computed at runtime, never rendered. */
    private fun computeReward(): String = BuildConfig.REWARD_FLAG

    /** Deep link into the exported admin console (task 081). */
    @Suppress("unused")
    fun openAdminViaDeepLink() {
        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("vaultbank://admin")))
    }
}
