plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "org.masdojo.pulse"
    compileSdk = 34

    defaultConfig {
        applicationId = "org.masdojo.pulse"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        // The telemetry endpoint and the token the app leaks over cleartext HTTP.
        // 10.0.2.2 is the host loopback as seen from the Android emulator.
        buildConfigField("String", "TELEMETRY_URL", "\"http://10.0.2.2:8090/api/v1/telemetry\"")
        buildConfigField("String", "DEVICE_TOKEN", "\"FLAG{n3tw0rk_1nt3rc3pt3d}\"")
    }

    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
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
}
