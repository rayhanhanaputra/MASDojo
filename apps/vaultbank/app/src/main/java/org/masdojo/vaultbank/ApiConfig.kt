package org.masdojo.vaultbank

import android.content.Context
import android.content.pm.PackageManager
import android.util.Log
import okhttp3.CertificatePinner
import okhttp3.OkHttpClient
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.security.cert.Certificate
import java.security.cert.CertificateFactory

/**
 * Networking + embedded secrets.
 *
 * Vulnerabilities:
 *  - MASVS-STORAGE-1 (task 001): API_KEY is a hardcoded constant in the binary.
 *  - MASVS-CODE (task 011): ADMIN_ENDPOINT is a privileged route present only in
 *    the compiled strings, never surfaced in the UI.
 *  - MASVS-NETWORK-1 (task 051): loginCleartext talks plain HTTP.
 *  - MASVS-NETWORK-2 (task 061): pinnedClient() pins the API cert via OkHttp's
 *    CertificatePinner — the bypass target.
 */
object ApiConfig {

    private const val TAG = "VaultBank"

    // Hardcoded secret (recoverable from BuildConfig or smali).
    val apiKey: String = BuildConfig.API_KEY

    // Hidden privileged endpoint — string-only, no UI path reaches it.
    val adminEndpoint: String = BuildConfig.ADMIN_ENDPOINT

    // Cleartext login base (intentionally http://).
    private const val LOGIN_URL = "http://api.vaultbank.example/v1/login"

    fun authorizationHeader(): String = "Bearer $apiKey"

    /**
     * VULNERABILITY (MASVS-NETWORK-1): sends username/password over plain HTTP.
     * Returns a pretend session token; the point is that the request body is
     * observable on any proxy in the path.
     */
    fun loginCleartext(username: String, password: String): String {
        val body = buildString {
            append("username=").append(URLEncoder.encode(username, "UTF-8"))
            append("&password=").append(URLEncoder.encode(password, "UTF-8"))
        }
        try {
            val conn = (URL(LOGIN_URL).openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                doOutput = true
                connectTimeout = 4000
                readTimeout = 4000
                setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
                setRequestProperty("Authorization", authorizationHeader())
            }
            conn.outputStream.use { os: OutputStream -> os.write(body.toByteArray()) }
            Log.i(TAG, "login POST -> ${conn.responseCode}")
            conn.disconnect()
        } catch (e: Exception) {
            // The request already left the device and is interceptable.
            Log.w(TAG, "login send failed: ${e.message}")
        }
        return "sess_" + Integer.toHexString((username + password).hashCode())
    }

    /**
     * VULNERABILITY (MASVS-NETWORK-2): an OkHttp client that pins the API host.
     * Learners bypass this by hooking CertificatePinner.check with Frida
     * (task 061) so their proxy CA is accepted.
     */
    fun pinnedClient(): OkHttpClient {
        val pinner = CertificatePinner.Builder()
            .add("api.vaultbank.example", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
            .build()
        return OkHttpClient.Builder().certificatePinner(pinner).build()
    }

    /**
     * VULNERABILITY (MASVS-NETWORK-2, task 061): runs the client-side certificate
     * pin as an in-process check. The configured pin is a placeholder that the
     * presented certificate can never match, so `CertificatePinner.check()` throws
     * and the "connection" is refused (gate denies). Hooking
     * `okhttp3.CertificatePinner.check` with Frida so it no longer throws defeats
     * the pinning entirely — the app then trusts any certificate (e.g. a proxy's),
     * which is the whole point of an SSL-pinning bypass.
     *
     * Returns true only if the pin check passes (i.e. was bypassed).
     */
    fun pinnedConnectionTrusted(ctx: Context): Boolean {
        return try {
            @Suppress("DEPRECATION", "PackageManagerGetSignatures")
            val sigs = ctx.packageManager
                .getPackageInfo(ctx.packageName, PackageManager.GET_SIGNATURES)
                .signatures ?: return false
            val cf = CertificateFactory.getInstance("X.509")
            val chain: List<Certificate> =
                sigs.map { cf.generateCertificate(it.toByteArray().inputStream()) }
            val pinner = CertificatePinner.Builder()
                .add("api.vaultbank.example", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
                .build()
            // Throws CertificatePinner.check failure unless the pin matches (it
            // won't) — or unless a Frida hook neutralises check().
            pinner.check("api.vaultbank.example", chain)
            true
        } catch (e: Exception) {
            Log.w(TAG, "pin check rejected the connection: ${e.javaClass.simpleName}")
            false
        }
    }
}
