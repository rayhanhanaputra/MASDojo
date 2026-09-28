package org.masdojo.vaultbank

/**
 * Reward-flag obfuscation.
 *
 * Every reward FLAG{...} is stored XOR-encrypted (as hex) in BuildConfig / code,
 * so a naive `strings` or grep over the APK's classes.dex reveals nothing — the
 * flag only materializes at runtime once the guarded path is actually reached.
 * This is a deliberately light anti-static-analysis layer (the key ships in the
 * binary, so a decompiler still recovers the flags); its job is simply to stop
 * the reward being handed to `strings apk | grep FLAG`. It is the same idea the
 * learner defeats in task 095 (StringVault).
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
