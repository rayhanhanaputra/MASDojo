package org.masdojo.pulse

import android.util.Log
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

/**
 * Sends a startup "heartbeat" to the telemetry endpoint.
 *
 * VULNERABILITY (MASVS-NETWORK-1): the request goes over plain HTTP with no
 * certificate pinning, and it carries a long-lived device token in the body.
 * Anyone intercepting the traffic recovers the token.
 */
object TelemetryClient {

    private const val TAG = "Pulse"

    fun sendHeartbeat() {
        val body = buildString {
            append("device_id=").append(URLEncoder.encode("pulse-emulator", "UTF-8"))
            append("&device_token=").append(URLEncoder.encode(BuildConfig.DEVICE_TOKEN, "UTF-8"))
        }

        val url = URL(BuildConfig.TELEMETRY_URL)
        val conn = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            doOutput = true
            connectTimeout = 5000
            readTimeout = 5000
            setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
        }
        try {
            conn.outputStream.use { os: OutputStream -> os.write(body.toByteArray()) }
            val code = conn.responseCode
            Log.i(TAG, "telemetry sent, server responded $code")
        } catch (e: Exception) {
            // Even if the upstream is unreachable, the request already left the
            // device and is observable on the proxy.
            Log.w(TAG, "telemetry send failed: ${e.message}")
        } finally {
            conn.disconnect()
        }
    }
}
