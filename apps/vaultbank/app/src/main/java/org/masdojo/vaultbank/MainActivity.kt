package org.masdojo.vaultbank

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import kotlin.concurrent.thread

/**
 * VaultBank login screen — the entry point of the all-in-one target.
 *
 * Vulnerabilities exercised here:
 *  - MASVS-NETWORK-1 (task 051): the login request is sent over cleartext HTTP.
 *  - MASVS-STORAGE-2 (task 022): the raw username and password are written to
 *    logcat on every attempt.
 *  - MASVS-STORAGE-1 (task 021): the returned session token is persisted to
 *    SharedPreferences in plaintext.
 */
class MainActivity : AppCompatActivity() {

    private val tag = "VaultBank"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val user = EditText(this).apply { hint = "username" }
        val pass = EditText(this).apply { hint = "password" }
        val status = TextView(this).apply { textSize = 13f }
        val signIn = Button(this).apply { text = "Sign in" }

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 96, 48, 48)
            addView(TextView(this@MainActivity).apply { text = "VaultBank"; textSize = 26f })
            addView(TextView(this@MainActivity).apply { text = "Secure mobile banking"; textSize = 13f })
            addView(user)
            addView(pass)
            addView(signIn)
            addView(status)
        }
        setContentView(root)

        signIn.setOnClickListener {
            val u = user.text.toString().ifBlank { "demo" }
            val p = pass.text.toString().ifBlank { "demo" }

            // VULNERABILITY (MASVS-STORAGE-2): credentials leaked to logcat.
            Log.d(tag, "login attempt username=$u password=$p")

            status.text = "Signing in…"
            thread(name = "login") {
                // VULNERABILITY (MASVS-NETWORK-1): cleartext login over HTTP.
                val token = ApiConfig.loginCleartext(u, p)

                // VULNERABILITY (MASVS-STORAGE-1): session token stored in the
                // clear in shared_prefs, alongside the user's PIN.
                SecretsManager.saveSession(this, u, token)

                runOnUiThread {
                    status.text = "Signed in. Opening dashboard…"
                    startActivity(Intent(this, DashboardActivity::class.java))
                }
            }
        }
    }
}
