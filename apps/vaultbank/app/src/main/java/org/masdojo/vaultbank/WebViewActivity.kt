package org.masdojo.vaultbank

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebView
import androidx.appcompat.app.AppCompatActivity

/**
 * In-app support chat rendered in a WebView.
 *
 * VULNERABILITY (MASVS-PLATFORM-2, task 082): JavaScript is enabled and a Java
 * object is bridged into the page via @JavascriptInterface. Any JS the WebView
 * runs — including content injected by a MITM over the cleartext channel — can
 * call SupportBridge.getSessionSecret() and exfiltrate it.
 */
class WebViewActivity : AppCompatActivity() {

    @SuppressLint("SetJavaScriptEnabled", "AddJavascriptInterface")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.addJavascriptInterface(SupportBridge(), "SupportBridge")
        setContentView(web)

        val html = """
            <html><body style="font-family:sans-serif;padding:24px">
            <h3>VaultBank Support</h3>
            <p id="out">Connecting…</p>
            <script>
              // A hostile page would do exactly this:
              document.getElementById('out').innerText =
                'session: ' + SupportBridge.getSessionSecret();
            </script>
            </body></html>
        """.trimIndent()
        web.loadDataWithBaseURL("https://api.vaultbank.example/", html, "text/html", "UTF-8", null)
    }

    class SupportBridge {
        /** Exposed to untrusted JS — returns a secret it should never hand out. */
        @JavascriptInterface
        fun getSessionSecret(): String = Flags.reveal("1c161b1d2130290538286b3e3d690536696e31290529693928692e27")
    }
}
