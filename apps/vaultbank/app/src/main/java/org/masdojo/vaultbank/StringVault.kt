package org.masdojo.vaultbank

/**
 * String-encryption as an anti-static-analysis layer (RASP technique).
 *
 * VULNERABILITY (MASVS-RESILIENCE-3, task 095): to keep sensitive constants out
 * of a `strings` dump or a casual jadx read, the app stores them XOR-encrypted
 * and decodes them at runtime. This *raises the bar* for static analysis but is
 * not a secret: the key and the ciphertext both ship in the binary, so anyone who
 * reads the decompiled `decode()` can reconstruct the plaintext offline. This is
 * exactly why obfuscation is a speed bump, not a control — the learner recovers
 * the value by replaying the same XOR, never by finding it in cleartext.
 *
 * (The graded challenge is seeded per-learner with its own key/ciphertext; the
 * table below is a representative in-app example so the technique is grounded in
 * a real, shipped decode routine.)
 */
object StringVault {

    // XOR key baked into the binary alongside the ciphertext (hence recoverable).
    private const val XOR_KEY: Int = 0x5a

    // Encrypted entries as hex. Decoded lazily at first use.
    private val TABLE: Map<String, String> = mapOf(
        // "reward-endpoint" -> the internal reward route (obfuscated, not secret)
        "reward" to "281f1f1c351f24243f38393a34343f3f",
    )

    private fun hexToBytes(hex: String): ByteArray =
        ByteArray(hex.length / 2) { ((Character.digit(hex[it * 2], 16) shl 4) +
            Character.digit(hex[it * 2 + 1], 16)).toByte() }

    /** Reconstruct a stored string by XOR-decoding it with the baked key. */
    fun decode(name: String): String {
        val enc = TABLE[name] ?: return ""
        val bytes = hexToBytes(enc)
        for (i in bytes.indices) bytes[i] = (bytes[i].toInt() xor XOR_KEY).toByte()
        return String(bytes)
    }
}
