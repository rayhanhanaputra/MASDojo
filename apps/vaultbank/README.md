# VaultBank — the all-in-one vulnerable target

`vaultbank` is a single intentionally-insecure Android banking app that bundles
every vulnerability class the MASDojo curriculum teaches into one installable
APK, in the spirit of Damn Vulnerable Bank / DVIA. It holds no real data and
targets no real backend — every "secret" is a training flag.

Install it on the emulator and practice the whole syllabus against one target:

```bash
adb install -r MASDojo.apk
```

## Vulnerability map

| Area | MASVS | Task | Where | How to exploit |
|------|-------|------|-------|----------------|
| Hardcoded API key | STORAGE-1 | 001 | `ApiConfig.apiKey` / `BuildConfig.API_KEY` | Decompile, read the constant |
| Hidden admin endpoint | CODE | 011 | `BuildConfig.ADMIN_ENDPOINT` | grep decompiled strings for the URL |
| Patch/flip premium gate | RESILIENCE-1 | 012 / 042 | `DashboardActivity.isPremiumUser()` | Hook/patch the boolean → `FLAG{pr3m1um_g4t3_fl1pp3d}` |
| Secrets in shared_prefs | STORAGE-1 | 021 | `SecretsManager.saveSession` → `shared_prefs/vault.xml` | Read the plaintext token/PIN/key |
| Credentials in logs | STORAGE-2 | 022 | `MainActivity` / `ApiConfig` `Log.*` | `adb logcat` during login |
| adb backup extraction | STORAGE-1/2 | 023 | `allowBackup=true` | `adb backup` → unpack `vault.xml` |
| Weak crypto (ECB) | CRYPTO-1/2 | 032 | `CryptoVault.encryptEcb`, key `masdojo_ecb_key!` | Decrypt with the static key |
| Recovered-key decrypt (CBC) | CRYPTO-1 | 031 | `CryptoVault.encryptCbc` (IV prepended) | Reuse the recovered key + split IV |
| Runtime reward flag | RESILIENCE-1 | 041 | `DashboardActivity.computeReward()` | Frida-hook the return → `FLAG{runt1m3_r3w4rd_h00k3d}` |
| Cleartext login | NETWORK-1 | 051 | `ApiConfig.loginCleartext` (`http://`) | Intercept the POST body on a proxy |
| SSL pinning bypass | NETWORK-2 | 061 | `ApiConfig.pinnedClient()` (OkHttp `CertificatePinner`) + `network_security_config.xml` | Hook `CertificatePinner.check` |
| Exported activity / deep link | PLATFORM-1 | 081 | `AdminActivity` (`vaultbank://admin`) | `am start -d vaultbank://admin` → `FLAG{exp0rt3d_adm1n_no_auth}` |
| WebView JS bridge | PLATFORM-2 | 082 | `WebViewActivity.SupportBridge` (`@JavascriptInterface`) | Call `getSessionSecret()` → `FLAG{js_br1dg3_l34ks_s3cr3t}` |
| Leaky content provider | PLATFORM-3 | 083 | `VaultProvider` (exported) | `content query --uri content://org.masdojo.vaultbank.provider/accounts` → `FLAG{l34ky_c0nt3nt_pr0v1d3r}` |
| Root / anti-Frida bypass | RESILIENCE-1/2/3 | 009 / 091 | `RootDetector.isCompromised()` | Force it false → `FLAG{r00t_ch3ck_bypass3d}` |
| Integrity/signature check | RESILIENCE-4 | 092 | `IntegrityChecker.isValidSignature` | Hook/patch to always-valid |

IDOR and JWT forgery (tasks 071 / 072) are server-side and exercised against the
MASDojo backend, not this client.

## Building

```bash
infra/build-apps.sh vaultbank      # -> apps/vaultbank/MASDojo.apk (+ served for download)
```

The build needs a JDK 17 + Android SDK; the `mingc/android-build-box` image (used
by `make apps`) has both. The resulting APK is copied to `apps/vaultbank/MASDojo.apk`
and picked up by the backend's `/download/target-apk` route so learners can grab
it from the platform.
