package org.masdojo.vaultbank

import android.util.Base64
import javax.crypto.Cipher
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * "Encrypts" card data before it leaves the app.
 *
 * Vulnerabilities:
 *  - MASVS-CRYPTO-1/2 (task 032): AES in ECB mode with a hardcoded key. ECB
 *    leaks structure (identical plaintext blocks -> identical ciphertext) and
 *    the static key means anyone with the APK can decrypt.
 *  - MASVS-CRYPTO-1 (task 031): AES-CBC where the IV is prepended to the
 *    ciphertext and the key is the same recoverable constant.
 */
object CryptoVault {

    private val ecbKey = SecretKeySpec(SecretsManager.ENCRYPTION_KEY.toByteArray(), "AES")
    // 16-byte key, hex-encoded elsewhere in the curriculum artifacts.
    private val cbcKey = SecretKeySpec(
        byteArrayOf(
            0x8f.toByte(), 0x3c, 0x1d, 0x77, 0xa9.toByte(), 0x4b, 0x42, 0xe0.toByte(),
            0xb6.toByte(), 0xc5.toByte(), 0xe9.toByte(), 0xf0.toByte(), 0xa1.toByte(), 0xd2.toByte(), 0xc3.toByte(), 0xb4.toByte(),
        ),
        "AES",
    )

    /** ECB — no IV, deterministic (task 032). */
    fun encryptEcb(plaintext: String): String {
        val c = Cipher.getInstance("AES/ECB/PKCS5Padding")
        c.init(Cipher.ENCRYPT_MODE, ecbKey)
        return Base64.encodeToString(c.doFinal(plaintext.toByteArray()), Base64.NO_WRAP)
    }

    /** CBC with the IV prepended to the ciphertext (task 031). */
    fun encryptCbc(plaintext: String, iv: ByteArray): String {
        val c = Cipher.getInstance("AES/CBC/PKCS5Padding")
        c.init(Cipher.ENCRYPT_MODE, cbcKey, IvParameterSpec(iv))
        val ct = c.doFinal(plaintext.toByteArray())
        return Base64.encodeToString(iv + ct, Base64.NO_WRAP)
    }
}
