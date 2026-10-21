**Full solution.**

1. Decompile the APK you downloaded from the skill map:
   ```bash
   jadx -d vaultbank_src MASDojo.apk
   ```
2. The app embeds its API key two ways - as a `BuildConfig` field (`API_KEY`) and
   as the `apiKey` constant read in `ApiConfig` (used to build the `Bearer`
   header). Both contain the same value:
   ```
   grep -rn "msd_live_sk_" vaultbank_src/
   ```
3. The recovered key is:
   ```
   msd_live_sk_8f3c1d77a94b42e0b6c5e9f0a1d2c3b4
   ```
   Submit it in the **value** field.

**Why this is a finding.** Per MASVS-STORAGE-1, secrets must not be stored in
the app package. A hardcoded API key can be extracted by anyone with the APK and
used to impersonate the app against the backend. The fix is to keep the secret
server-side and have the backend mint short-lived, scoped tokens for the client.
