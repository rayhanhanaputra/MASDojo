package org.masdojo.vaultbank

import android.util.Log
import okhttp3.CertificatePinner
import okhttp3.OkHttpClient
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

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
}
