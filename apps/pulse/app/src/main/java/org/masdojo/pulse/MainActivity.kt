package org.masdojo.pulse

import android.os.Bundle
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 96, 48, 48)
        }
        root.addView(TextView(this).apply {
            text = "Pulse"
            textSize = 24f
        })
        root.addView(TextView(this).apply {
            text = "Syncing telemetry…"
            textSize = 14f
        })
        setContentView(root)

        // Phone home on startup. Network must run off the main thread.
        thread(name = "telemetry") {
            TelemetryClient.sendHeartbeat()
        }
    }
}
