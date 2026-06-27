package org.masdojo.securenotes

/**
 * Talks to the SecureNotes backend.
 *
 * VULNERABILITY (MASVS-STORAGE-1): the API key is a hardcoded constant. It is
 * duplicated from BuildConfig.API_KEY so the secret is recoverable whether the
 * learner reads BuildConfig or this class. In a real app the key would be minted
 * server-side and never embedded in the client.
 */
object ApiClient {

    // Hardcoded secret — do not do this in production.
    private const val API_KEY = "msd_live_sk_8f3c1d77a94b42e0b6c5e9f0a1d2c3b4"

    const val BASE_URL = "https://api.securenotes.example/v1"

    fun authorizationHeader(): String = "Bearer $API_KEY"

    /** Returns a masked form for display so the UI doesn't print the raw key. */
    fun maskedKey(): String = API_KEY.take(11) + "…" + API_KEY.takeLast(4)
}
