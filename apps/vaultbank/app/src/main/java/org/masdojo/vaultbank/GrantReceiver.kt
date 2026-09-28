package org.masdojo.vaultbank

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * "Privilege helper" broadcast receiver — a userland confused deputy.
 *
 * VULNERABILITY (MASVS-PLATFORM-1, task 084): this receiver performs a PRIVILEGED
 * action — minting an elevation grant that unlocks the admin capability — on
 * behalf of ANY caller. It is exported, declares no `android:permission`, and
 * never verifies who sent the intent. So a lower-privileged caller (another app,
 * or `adb shell am broadcast`) can invoke it and receive an effect it should
 * never be able to obtain: the app re-delegates its own privilege to the caller.
 * This is a classic permission re-delegation / confused-deputy local escalation,
 * confined entirely to the training app.
 *
 * The secure version would guard the receiver with a signature-level permission
 * and check the caller, or simply not export a privilege-granting action at all.
 */
class GrantReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != ACTION_ELEVATE) return

        // NO caller check, NO permission: whoever asks, gets elevated.
        val requester = intent.getStringExtra(EXTRA_REQUESTER) ?: "anonymous"
        val grant = mintGrant(requester)

        Log.w(TAG, "MASDOJO_GRANT: elevated caller '$requester' with no authorization check")
        // The privileged effect handed back to the caller (a grant token that the
        // admin surface accepts). An ordered broadcast lets the caller read it.
        if (isOrderedBroadcast) {
            resultData = grant
        }
        Log.i(TAG, "MASDOJO_UNLOCK:$grant")
    }

    /**
     * Derive the elevation grant token. The transform (XOR with a baked key, hex-
     * encoded) is fully present in the shipped code, so anyone who reads this
     * method can reconstruct the grant offline for any requester — which is the
     * point: the "privilege" is not protected by anything the caller can't see.
     */
    private fun mintGrant(requester: String): String {
        val reward = BuildConfig.GRANT_FLAG
        // A reversible obfuscation so the grant isn't a bare cleartext constant.
        val out = StringBuilder()
        for ((i, c) in reward.withIndex()) {
            out.append("%02x".format(c.code xor (GRANT_KEY + (i and 0x07))))
        }
        // The obfuscated form is what travels; the admin surface decodes it back.
        return decodeGrant(out.toString())
    }

    private fun decodeGrant(hex: String): String {
        val bytes = ByteArray(hex.length / 2) {
            ((Character.digit(hex[it * 2], 16) shl 4) + Character.digit(hex[it * 2 + 1], 16)).toByte()
        }
        val sb = StringBuilder()
        for ((i, b) in bytes.withIndex()) sb.append(((b.toInt() and 0xff) xor (GRANT_KEY + (i and 0x07))).toChar())
        return sb.toString()
    }

    companion object {
        private const val TAG = "VaultBank"
        private const val GRANT_KEY = 0x33
        const val ACTION_ELEVATE = "org.masdojo.vaultbank.action.ELEVATE"
        const val EXTRA_REQUESTER = "requester"
    }
}
