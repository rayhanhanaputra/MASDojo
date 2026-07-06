// Decompiled with jadx — com.vaultbank.crypto.CryptoUtil
// The vault uses AES in ECB mode with a *hardcoded* key (both are the weakness:
// ECB has no IV and leaks block structure; a baked-in key means anyone with the
// APK can decrypt). The key bytes are XOR-obfuscated in the binary.
class CryptoUtil {
    private static final String K_ENC = "313d2f3833363303393f3e033739257d";   // hex
    private static final int    K_XOR = 0x5c;

    static byte[] key() {
        byte[] k = hexToBytes(K_ENC);
        for (int i = 0; i < k.length; i++) k[i] ^= K_XOR;   // -> the 16-byte AES key
        return k;
    }

    static String open(byte[] ciphertext) {
        Cipher c = Cipher.getInstance("AES/ECB/PKCS5Padding");   // ECB, no IV
        c.init(Cipher.DECRYPT_MODE, new SecretKeySpec(key(), "AES"));
        return new String(c.doFinal(ciphertext));
    }
}
// The encrypted blob ships as base64 in weak.enc.
