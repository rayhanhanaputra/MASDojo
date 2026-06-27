plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "org.masdojo.securenotes"
    compileSdk = 34

    defaultConfig {
        applicationId = "org.masdojo.securenotes"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        // VULNERABILITY (MASVS-STORAGE-1): the backend API key is compiled into
        // the app. It ships in BuildConfig and is recoverable from the APK.
        buildConfigField(
            "String",
            "API_KEY",
            "\"msd_live_sk_8f3c1d77a94b42e0b6c5e9f0a1d2c3b4\"",
        )
    }

    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        // Build unminified so the training target stays easy to decompile.
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
