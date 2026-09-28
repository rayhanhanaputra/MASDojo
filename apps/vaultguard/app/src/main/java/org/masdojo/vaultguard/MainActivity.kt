package org.masdojo.vaultguard

import android.os.Bundle
import android.util.Log
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private val tag = "VaultGuard"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val status = TextView(this).apply { textSize = 16f }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 96, 48, 48)
            addView(TextView(this@MainActivity).apply {
                text = "VaultGuard"
                textSize = 24f
            })
            addView(status)
        }
        setContentView(root)

        // The single client-side decision that gates the premium vault.
        if (RootChecker.isDeviceRooted()) {
            // MASDOJO_DENIED — the marker the grader checks is absent of unlock.
            Log.w(tag, "MASDOJO_DENIED: rooted device detected, vault locked")
            status.text = "Access denied: this device appears to be rooted."
        } else {
            unlockVault(status)
        }
    }

    private fun unlockVault(status: TextView) {
        val flag = Flags.reveal(BuildConfig.VAULT_FLAG)
        // MASDOJO_UNLOCK:<flag> is logged only on the not-rooted path.
        Log.i(tag, "MASDOJO_UNLOCK:$flag")
        status.text = "Premium vault unlocked.\n$flag"
    }
}
