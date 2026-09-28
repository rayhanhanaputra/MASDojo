plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// VaultBank — an intentionally-vulnerable "banking" app that bundles every
// vulnerability class the MASDojo curriculum teaches into one installable APK,
// in the spirit of Damn Vulnerable Bank / DVIA. It targets no real backend and
// holds no real data. Each weakness is tagged with its MASVS control and the
// task it backs; see apps/vaultbank/README.md for the full map.
android {
    namespace = "org.masdojo.vaultbank"
    compileSdk = 34

    defaultConfig {
        applicationId = "org.masdojo.vaultbank"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        // Native self-ptrace anti-debug guard (task 094): src/main/jniLibs/*/
        // libguard.so sets this process's TracerPid non-zero on load so the
        // anti-debug gate actually engages. Prebuilt (see cpp/guard.c) and
        // shipped for the emulator + device ABIs the dojo runs on.
        ndk {
            abiFilters += listOf("x86_64", "arm64-v8a")
        }

        // Hardcoded secrets baked into the binary (MASVS-STORAGE-1 / -CRYPTO):
        // recoverable from BuildConfig or the decompiled smali.
        buildConfigField("String", "API_KEY", "\"msd_live_sk_8f3c1d77a94b42e0b6c5e9f0a1d2c3b4\"")
        // A backend route that never appears in the UI (MASVS-CODE, task 011).
        buildConfigField("String", "ADMIN_ENDPOINT", "\"https://api.vaultbank.example/internal/admin/ledger\"")
        // The flag revealed only when the premium gate is flipped (task 042/012).
        buildConfigField("String", "PREMIUM_FLAG", "\"FLAG{pr3m1um_g4t3_fl1pp3d}\"")
        // The flag returned by the runtime-computed reward method (task 041).
        buildConfigField("String", "REWARD_FLAG", "\"FLAG{runt1m3_r3w4rd_h00k3d}\"")
        // The flag behind the client-side root/anti-frida gate (task 009/091).
        buildConfigField("String", "VAULT_FLAG", "\"FLAG{r00t_ch3ck_bypass3d}\"")
        // RASP-technique gate flags, each revealed only when the matching runtime
        // self-protection check is defeated (tasks 093 / 094 / 096).
        buildConfigField("String", "EMU_FLAG", "\"FLAG{3mul4t0r_ch3ck_d3f34t3d}\"")
        buildConfigField("String", "DEBUG_FLAG", "\"FLAG{tr4c3rp1d_4nt1d3bug_byp4ss3d}\"")
        buildConfigField("String", "ATTEST_FLAG", "\"FLAG{4tt3st4t10n_stub_f0rg3d}\"")
        // The flag behind the anti-instrumentation / anti-Frida gate (task 091),
        // revealed only when AntiTamper.isInstrumented() is hooked to false.
        buildConfigField("String", "TAMPER_FLAG", "\"FLAG{4nt1_fr1d4_ch3ck_d3f34t3d}\"")
        // The grant token the exported confused-deputy receiver hands any caller
        // (task 084). Reversibly obfuscated in GrantReceiver, not stored cleartext.
        buildConfigField("String", "GRANT_FLAG", "\"FLAG{c0nfus3d_d3puty_pr1v_r3d3l3g4t3d}\"")
    }

    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
        }
        getByName("debug") {
            // Debuggable target so learners can attach jdb / Frida (MASVS-RESILIENCE).
            isDebuggable = true
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    // OkHttp — its CertificatePinner is the canonical SSL-pinning bypass target
    // (MASVS-NETWORK-2, task 061).
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
