package org.masdojo.securenotes

import android.os.Bundle
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 96, 48, 48)
        }
        root.addView(TextView(this).apply {
            text = "SecureNotes"
            textSize = 24f
        })
        root.addView(TextView(this).apply {
            text = "Your notes are synced securely.\nAPI key: ${ApiClient.maskedKey()}"
            textSize = 14f
        })
        setContentView(root)

        // The app uses the embedded key to authorize — the raw value lives in the
        // compiled binary even though the UI only shows a masked form.
        check(ApiClient.authorizationHeader().startsWith("Bearer "))
    }
}
