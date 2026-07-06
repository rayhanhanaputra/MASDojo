package org.masdojo.vaultbank

import android.content.Context

/**
 * Persists "convenience" data on the device.
 *
 * VULNERABILITY (MASVS-STORAGE-1, tasks 021 / 023): everything is written to a
 * world-readable-by-backup SharedPreferences XML in the clear — the session
 * token, the user's card PIN, and the symmetric key used by CryptoVault. An
 * `adb backup` or a read of /data/data/<pkg>/shared_prefs/vault.xml recovers
 * all of it.
 */
object SecretsManager {

    private const val PREFS = "vault"

    // Hardcoded key material — never do this in production (MASVS-CRYPTO-1).
    const val ENCRYPTION_KEY = "masdojo_ecb_key!"

    fun saveSession(ctx: Context, username: String, token: String) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().apply {
            putString("username", username)
            // Stored in plaintext (task 021).
            putString("session_token", token)
            putString("card_pin", "4921")
            putString("enc_key", ENCRYPTION_KEY)
            apply()
        }
    }

    fun sessionToken(ctx: Context): String? =
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString("session_token", null)
}
