plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "org.masdojo.vaultguard"
    compileSdk = 34

    defaultConfig {
        applicationId = "org.masdojo.vaultguard"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        // The flag revealed only when the (client-side) root check is defeated.
        buildConfigField("String", "VAULT_FLAG", "\"FLAG{r00t_ch3ck_bypass3d}\"")
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
