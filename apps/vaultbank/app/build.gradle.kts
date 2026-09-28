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
        // Reward flags are XOR-obfuscated (Flags.reveal, key 0x5A) so `strings`
        // over the APK reveals no FLAG{...}; each is decoded at runtime only on
        // its guarded path. Plaintext values are documented next to each.
        // Premium gate (task 042/012): FLAG{pr3m1um_g4t3_fl1pp3d}
        buildConfigField("String", "PREMIUM_FLAG", "\"1c161b1d212a2869376b2f37053d6e2e69053c366b2a2a693e27\"")
        // Runtime-computed reward (task 041): FLAG{runt1m3_r3w4rd_h00k3d}
        buildConfigField("String", "REWARD_FLAG", "\"1c161b1d21282f342e6b37690528692d6e283e05326a6a31693e27\"")
        // Client-side root/anti-frida gate (task 009/091): FLAG{r00t_ch3ck_bypass3d}
        buildConfigField("String", "VAULT_FLAG", "\"1c161b1d21286a6a2e0539326939310538232a3b2929693e27\"")
        // RASP-technique gate flags (tasks 093 / 094 / 096):
        // EMU FLAG{3mul4t0r_ch3ck_d3f34t3d}
        buildConfigField("String", "EMU_FLAG", "\"1c161b1d2169372f366e2e6a28053932693931053e693c696e2e693e27\"")
        // DEBUG FLAG{tr4c3rp1d_4nt1d3bug_byp4ss3d}
        buildConfigField("String", "DEBUG_FLAG", "\"1c161b1d212e286e3969282a6b3e056e342e6b3e69382f3d0538232a6e2929693e27\"")
        // ATTEST FLAG{4tt3st4t10n_stub_f0rg3d}
        buildConfigField("String", "ATTEST_FLAG", "\"1c161b1d216e2e2e69292e6e2e6b6a3405292e2f38053c6a283d693e27\"")
        // Anti-instrumentation / anti-Frida gate (task 091): FLAG{4nt1_fr1d4_ch3ck_d3f34t3d}
        buildConfigField("String", "TAMPER_FLAG", "\"1c161b1d216e342e6b053c286b3e6e053932693931053e693c696e2e693e27\"")
        // Confused-deputy grant (task 084): FLAG{c0nfus3d_d3puty_pr1v_r3d3l3g4t3d}
        buildConfigField("String", "GRANT_FLAG", "\"1c161b1d21396a343c2f29693e053e692a2f2e23052a286b2c0528693e6936693d6e2e693e27\"")
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
