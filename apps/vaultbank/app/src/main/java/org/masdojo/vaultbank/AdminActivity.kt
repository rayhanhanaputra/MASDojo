package org.masdojo.vaultbank

import android.os.Bundle
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Internal admin console.
 *
 * VULNERABILITY (MASVS-PLATFORM-1, task 081): this activity is exported with a
 * `vaultbank://admin` deep link and no authentication check, so it can be
 * launched directly — bypassing login entirely — via:
 *   adb shell am start -W -a android.intent.action.VIEW -d "vaultbank://admin"
 * It then discloses the hidden admin ledger endpoint and a flag.
 */
class AdminActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 96, 48, 48)
            addView(TextView(this@AdminActivity).apply { text = "Admin Console"; textSize = 22f })
            addView(TextView(this@AdminActivity).apply {
                // No auth was required to reach this screen.
                text = "${Flags.reveal("1c161b1d213f222a6a282e693e053b3e376b34053435053b2f2e3227")}\n\nLedger API: ${ApiConfig.adminEndpoint}"
                textSize = 13f
            })
        }
        setContentView(root)
    }
}
