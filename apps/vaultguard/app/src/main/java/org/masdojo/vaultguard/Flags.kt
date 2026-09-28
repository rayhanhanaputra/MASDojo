package org.masdojo.vaultguard

/**
 * Reward-flag obfuscation: the premium-vault FLAG{...} is stored XOR-encrypted
 * (hex) so a naive `strings` over the APK reveals nothing; it is decoded at
 * runtime only on the not-rooted (unlocked) path. Light anti-static-analysis —
 * the key ships in the binary — its job is only to keep the reward out of a
 * `strings apk | grep FLAG` dump.
 */
internal object Flags {
    private const val KEY = 0x5A

    fun reveal(hex: String): String {
        val out = StringBuilder(hex.length / 2)
        var i = 0
        while (i + 1 < hex.length) {
            out.append(((hex.substring(i, i + 2).toInt(16)) xor KEY).toChar())
            i += 2
        }
        return out.toString()
    }
}
