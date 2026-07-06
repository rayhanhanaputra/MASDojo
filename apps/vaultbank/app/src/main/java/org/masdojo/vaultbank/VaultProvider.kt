package org.masdojo.vaultbank

import android.content.ContentProvider
import android.content.ContentValues
import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri

/**
 * Exposes account rows to other apps.
 *
 * VULNERABILITY (MASVS-PLATFORM-3, task 083): the provider is exported with no
 * read permission, so any app on the device can dump the account ledger:
 *   adb shell content query --uri content://org.masdojo.vaultbank.provider/accounts
 * The dump includes account numbers, balances, and a flag row.
 */
class VaultProvider : ContentProvider() {

    override fun onCreate(): Boolean = true

    override fun query(
        uri: Uri,
        projection: Array<out String>?,
        selection: String?,
        selectionArgs: Array<out String>?,
        sortOrder: String?,
    ): Cursor {
        val cursor = MatrixCursor(arrayOf("_id", "account", "holder", "balance"))
        cursor.addRow(arrayOf(1, "IBAN-0001", "demo user", "4921.00"))
        cursor.addRow(arrayOf(2, "IBAN-0002", "j. doe", "88120.55"))
        // A row that should never be readable by other apps.
        cursor.addRow(arrayOf(3, "FLAG{l34ky_c0nt3nt_pr0v1d3r}", "admin", "0.00"))
        return cursor
    }

    override fun getType(uri: Uri): String = "vnd.android.cursor.dir/vnd.vaultbank.accounts"

    override fun insert(uri: Uri, values: ContentValues?): Uri? = null
    override fun update(uri: Uri, values: ContentValues?, s: String?, a: Array<out String>?): Int = 0
    override fun delete(uri: Uri, s: String?, a: Array<out String>?): Int = 0
}
