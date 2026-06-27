# apps/ — intentionally-vulnerable training targets

Each subdirectory is a standalone Gradle Android project whose APK backs one or
more curriculum tasks. **These apps are deliberately insecure** — that's the
point. They contain no real user data and target no real backend.

| App | Package | Backs task | Vulnerability |
|-----|---------|-----------|---------------|
| `securenotes` | `org.masdojo.securenotes` | 001 (static_assert) | Hardcoded API key in the APK |
| `pulse` | `org.masdojo.pulse` | 005 (network_assert) | Cleartext telemetry token over HTTP |
| `vaultguard` | `org.masdojo.vaultguard` | 009 (frida_assert) | Client-side root check gating a feature |

## Building

You need a JDK 17 and the Android SDK (the runner image already has both). From
the repo root:

```bash
infra/build-apps.sh                 # build all apps -> tasks/*/app/target.apk
infra/build-apps.sh securenotes     # build just one
```

Each app uses the Gradle wrapper if present, otherwise a system `gradle`. The
build script copies the resulting debug APK to the matching task package.
